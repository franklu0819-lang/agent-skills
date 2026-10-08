#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GLM-OCR 文档解析（智谱开放平台 layout_parsing 端点，模型 glm-ocr）。

图片 / PDF / URL → Markdown 文本（表格出 HTML、公式原样、印章手写均可）。

用法:
  ocr.py scan.png                    识别 → stdout 输出 Markdown
  ocr.py doc.pdf -o doc.md           识别 → 存 .md 文件
  ocr.py doc.pdf --pages 3-10        PDF 只识别第 3-10 页
  ocr.py *.png -o outdir/            批量识别 → 目录下同名 .md
  ocr.py img.png --json raw.json     另存完整响应 JSON（含布局明细/坐标）
  ocr.py img.png --dry-run           只打印请求元信息，不发送

stdout 只有识别出的 Markdown（单文件且未用 -o 时）；进度、用量与批量汇总走 stderr。
退出码：0 成功，1 有失败项。

接口文档: https://docs.bigmodel.cn/api-reference/模型-api/文档解析
"""

import argparse
import base64
import json
import os
import re
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ENDPOINT = "https://open.bigmodel.cn/api/paas/v4/layout_parsing"
KEY_VARS = ("ZHIPU_API_KEY",)  # glm- 家族统一只认 ZHIPU_API_KEY
MODEL = "glm-ocr"
MAX_IMAGE_BYTES = 10 * 1024 * 1024   # 单图 ≤ 10MB
MAX_PDF_BYTES = 50 * 1024 * 1024     # PDF ≤ 50MB；页数上限 100 页由服务端校验
ATTEMPTS = 3                         # 连接层错误共尝试 3 次
RETRY_WAIT = 3.0

# magic bytes → (mime, 类别)
MAGIC = (
    (b"\x89PNG", "image/png", "image"),
    (b"\xff\xd8\xff", "image/jpeg", "image"),
    (b"%PDF", "application/pdf", "pdf"),
)
EXT_MIME = {".png": ("image/png", "image"), ".jpg": ("image/jpeg", "image"),
            ".jpeg": ("image/jpeg", "image"), ".pdf": ("application/pdf", "pdf")}


class ApiError(Exception):
    def __init__(self, msg, code=None):
        super().__init__(msg)
        self.code = code


def log(msg):
    print(msg, file=sys.stderr)


def find_api_key(explicit):
    """解析顺序: --api-key → 环境变量 ZHIPU_API_KEY → ~/.zshrc 里的同名 export（取最后生效的）。
    glm- 家族统一只认 ZHIPU_API_KEY。智谱 Key 形如 <32位hex>.<16位hex>。与 glm-tts/glm-asr 同链。"""
    if explicit:
        return explicit
    for var in KEY_VARS:
        if os.environ.get(var):
            return os.environ[var]
    zshrc = os.path.expanduser("~/.zshrc")
    try:
        found = ""
        with open(zshrc, encoding="utf-8", errors="replace") as f:
            for line in f:
                m = re.match(r'\s*export\s+(%s)=(?:"([^"]+)"|([^\s#]+))' % "|".join(KEY_VARS), line)
                if m:
                    found = m.group(2) or m.group(3) or ""
        return found
    except OSError:
        return ""


def sniff(data):
    for magic, mime, kind in MAGIC:
        if data.startswith(magic):
            return mime, kind
    return None, None


def build_file_field(target, dry_run=False):
    """输入 → (file 字段值, 说明, 类别)。URL 直传；本地文件按 magic bytes 判型转 base64 data URI。
    dry_run=True 时只判型不编码，file 字段值为 None。"""
    if target.lower().startswith(("http://", "https://")):
        return target, "url", "url"
    if not os.path.isfile(target):
        raise ApiError("文件不存在: %s" % target)
    size = os.path.getsize(target)
    # 读文件前先按绝对上限拦截（>50MB 无论何种类型必拒），防超大文件整读进内存
    if size > MAX_PDF_BYTES:
        raise ApiError("%s 大小 %.1fMB 超限（任何类型上限 %dMB）" % (target, size / 1048576, MAX_PDF_BYTES // 1048576))
    ext = os.path.splitext(target)[1].lower()
    mime, kind = EXT_MIME.get(ext, (None, None))
    if dry_run:
        if mime is None:
            raise ApiError("无法识别文件类型（支持 PNG / JPG / PDF）: %s" % target)
        limit = MAX_IMAGE_BYTES if kind == "image" else MAX_PDF_BYTES
        if size > limit:
            raise ApiError("%s 大小 %.1fMB 超限（%s 上限 %dMB）" % (target, size / 1048576, kind, limit // 1048576))
        return None, "base64(%s, %.1fMB)" % (mime, size / 1048576), kind
    try:
        with open(target, "rb") as f:
            data = f.read()
    except OSError as e:
        raise ApiError("读取文件失败: %s: %s" % (target, e))
    # magic bytes 优先于扩展名（防改后缀）
    m_mime, m_kind = sniff(data)
    if m_mime is not None:
        mime, kind = m_mime, m_kind
    if mime is None:
        raise ApiError("无法识别文件类型（支持 PNG / JPG / PDF）: %s" % target)
    limit = MAX_IMAGE_BYTES if kind == "image" else MAX_PDF_BYTES
    if size > limit:
        raise ApiError("%s 大小 %.1fMB 超限（%s 上限 %dMB）" % (target, size / 1048576, kind, limit // 1048576))
    b64 = base64.b64encode(data).decode("ascii")
    return "data:%s;base64,%s" % (mime, b64), "base64(%s, %.1fMB)" % (mime, size / 1048576), kind


def parse_pages(spec):
    """'3' → (3, None)；'3-10' → (3, 10)；非法抛错。"""
    if spec is None:
        return None, None
    try:
        if "-" in spec:
            a, b = spec.split("-", 1)
            a, b = int(a), int(b)
            if a < 1 or b < a:
                raise ValueError
            return a, b
        a = int(spec)
        if a < 1:
            raise ValueError
        return a, None
    except ValueError:
        raise ApiError("--pages 格式应为 N 或 N-M（从 1 起），收到: %s" % spec)


def parse_error_body(raw):
    """从 HTTP 错误响应体提取 (code, message)，失败返回 (None, 截断原文)。"""
    try:
        err = json.loads(raw.decode("utf-8", "replace")).get("error") or {}
        return err.get("code"), err.get("message") or raw.decode("utf-8", "replace")[:300]
    except (ValueError, AttributeError):
        return None, raw.decode("utf-8", "replace")[:300]


def call_api(payload, key, timeout):
    """发送请求，返回解析后的响应 dict。连接层错误与 5xx 共尝试 ATTEMPTS 次；
    4xx 业务错误立即抛 ApiError（带 error.code）。"""
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    errs = []
    for attempt in range(ATTEMPTS):
        req = urllib.request.Request(ENDPOINT, data=body, method="POST")
        req.add_header("Authorization", "Bearer " + key)
        req.add_header("Content-Type", "application/json")
        # open.bigmodel.cn 是国内节点，直连
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            with opener.open(req, timeout=timeout) as resp:
                raw = resp.read()
            try:
                parsed = json.loads(raw.decode("utf-8"))
            except (ValueError, UnicodeDecodeError) as e:
                raise ApiError("响应不是合法 JSON: %s" % e)
            if not isinstance(parsed, dict):
                raise ApiError("响应结构异常（非对象）: %.200s" % str(parsed))
            return parsed
        except urllib.error.HTTPError as e:
            code, msg = parse_error_body(e.read())
            if e.code >= 500 and attempt < ATTEMPTS - 1:
                errs.append("HTTP %s (%s)" % (e.code, msg))
                time.sleep(RETRY_WAIT)
                continue
            raise ApiError("HTTP %s: %s" % (e.code, msg), code=code)
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            host = urllib.parse.urlparse(ENDPOINT).hostname
            try:
                ip = socket.gethostbyname(host)
            except OSError:
                ip = "?"
            errs.append("第%d次[直连 → %s]: %s" % (attempt + 1, ip, e))
            if attempt < ATTEMPTS - 1:
                time.sleep(RETRY_WAIT)
    raise ApiError("网络请求失败（连接层错误已尝试 %d 次）：\n  " % ATTEMPTS + "\n  ".join(errs))


def looks_like_file_format_error(err):
    """error 信息是否指向 file 值格式问题（用于 data URI → 纯 base64 降级）。"""
    text = str(err).lower()
    if any(k in text for k in ("size", "large", "big", "too large", "超限", "大小")):
        return False
    return any(k in text for k in ("file", "base64", "格式", "format", "invalid", "url"))


def url_basename(target):
    """URL → 安全文件名（path 的 basename，去 query；为空则 download）。"""
    base = os.path.basename(urllib.parse.urlparse(target).path)
    return base or "download"


def output_path(target, output, used):
    """计算批量/落盘输出路径：本地文件 → 同名 .md；URL → 取 URL path 的 basename（去 query）。
    used 为本批次已占用路径集合，冲突时加 -2/-3 序号，防静默覆盖。"""
    is_url = target.lower().startswith(("http://", "https://"))
    if output:
        base = url_basename(target) if is_url else os.path.basename(target)
        cand = os.path.join(output, base + ".md")
    elif is_url:
        cand = url_basename(target) + ".md"   # URL 无 -o 时落到当前目录
    else:
        cand = target + ".md"
    if cand in used:
        stem, ext = os.path.splitext(cand)
        n = 2
        while "%s-%d%s" % (stem, n, ext) in used:
            n += 1
        cand = "%s-%d%s" % (stem, n, ext)
    used.add(cand)
    return cand


def ocr_one(target, key, args):
    """识别单个目标，返回 (md_text, 原始响应 dict)。"""
    file_field, how, kind = build_file_field(target, dry_run=args.dry_run)
    payload = {"model": MODEL}
    if file_field is not None:
        payload["file"] = file_field
    if args.crop:
        payload["return_crop_images"] = True
    if args.visualize:
        payload["need_layout_visualization"] = True
    start, end = parse_pages(args.pages)
    if start is not None or end is not None:
        if kind == "image":
            log("[提示] %s 是图片，忽略 --pages（该参数仅对 PDF 生效）" % os.path.basename(target))
        else:
            if start is not None:
                payload["start_page_id"] = start
            if end is not None:
                payload["end_page_id"] = end

    if args.dry_run:
        shown = file_field if how == "url" else (file_field[:48] + "...(%d 字符)" % len(file_field) if file_field else "<略>")
        log("[dry-run] POST %s\n  model=%s file=%s\n  params: crop=%s visualize=%s pages=%s"
            % (ENDPOINT, MODEL, shown, args.crop, args.visualize, args.pages or "全部"))
        return None, None

    try:
        resp = call_api(payload, key, args.timeout)
    except ApiError as e:
        # data URI 若不被接受（官方文档只写"支持 url 和 base64"，格式未细化），退回纯 base64 重试一次
        if how.startswith("base64") and file_field and "," in file_field and looks_like_file_format_error(e):
            log("data URI 被拒（%s），改用纯 base64 重试…" % e)
            payload["file"] = file_field.split(",", 1)[1]
            resp = call_api(payload, key, args.timeout)
        else:
            raise
    if resp.get("error"):
        raise ApiError("API 错误 %s: %s" % (resp["error"].get("code"), resp["error"].get("message")),
                       code=resp["error"].get("code"))
    md = resp.get("md_results")
    if md is None:
        raise ApiError("响应缺少 md_results 字段: %.300s" % json.dumps(resp, ensure_ascii=False))
    if not md.strip():
        log("[提示] %s 识别结果为空（空白图或纯图像页？）" % os.path.basename(target))
    return md, resp


def write_text(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text if text.endswith("\n") else text + "\n")


def main():
    ap = argparse.ArgumentParser(description="GLM-OCR 图片/PDF → Markdown（智谱 layout_parsing）")
    ap.add_argument("targets", nargs="+", help="图片/PDF 文件路径或 URL")
    ap.add_argument("-o", "--output", help="单文件=输出 md 路径；多文件=输出目录（默认源文件旁同名 .md；URL 目标取 basename）")
    ap.add_argument("--json", dest="json_path", help="完整响应 JSON 另存路径（仅单文件时有效）")
    ap.add_argument("--pages", help="PDF 页码范围：N 或 N-M（从 1 起）；作用于所有目标，图片目标忽略并提示")
    ap.add_argument("--crop", action="store_true", help="return_crop_images：返回元素截图信息")
    ap.add_argument("--visualize", action="store_true", help="need_layout_visualization：返回布局可视化图 URL")
    ap.add_argument("--timeout", type=int, default=300, help="单次请求超时秒数（默认 300，百页 PDF 需要更久）")
    ap.add_argument("--api-key", default="", help="API Key（默认自动解析，见 find_api_key）")
    ap.add_argument("--dry-run", action="store_true", help="只打印请求元信息，不发送")
    args = ap.parse_args()

    multi = len(args.targets) > 1
    if multi and args.json_path:
        log("--json 仅支持单文件")
        return 1
    if multi and args.output and not os.path.isdir(args.output):
        log("多文件时 -o 必须是已存在的目录: %s" % args.output)
        return 1

    key = find_api_key(args.api_key)
    if not key and not args.dry_run:
        log("缺少 API Key：请在 bigmodel.cn「API Keys」页获取，export ZHIPU_API_KEY=... 或用 --api-key 传入。"
            "（GLM Coding Plan 订阅 Key 不含本接口，需开放平台常规 API Key）")
        return 1

    used = set()
    failed = 0
    done = 0
    for target in args.targets:
        md = None
        try:
            md, resp = ocr_one(target, key, args)
            if args.dry_run:
                continue
            done += 1
            usage = resp.get("usage") or {}
            pages = (resp.get("data_info") or {}).get("num_pages")
            log("[%s] 完成%s，tokens=%s" % (url_basename(target),
                ("，%d 页" % pages) if pages else "", usage.get("total_tokens", "?")))
            if not multi:
                if args.json_path:
                    write_text(args.json_path, json.dumps(resp, ensure_ascii=False, indent=2))
                    log("完整 JSON → %s" % args.json_path)
                if args.output:
                    write_text(args.output, md)
                    log("Markdown → %s" % args.output)
                else:
                    print(md)
            else:
                out = output_path(target, args.output, used)
                write_text(out, md)
                log("Markdown → %s" % out)
        except ApiError as e:
            log("[错误] %s: %s" % (target, e))
            failed += 1
        except OSError as e:
            # API 已计费但结果落盘失败：单文件时把内容吐到 stdout，尽量保住结果
            log("[错误] %s: 写盘失败: %s" % (target, e))
            if not multi and md is not None:
                print(md)
                log("已将识别结果改道 stdout（上面输出），请自行保存")
            failed += 1
    if multi and not args.dry_run:
        log("批量完成: 成功 %d / 失败 %d（共 %d）" % (done, failed, len(args.targets)))
    elif failed:
        log("完成，失败 %d 项" % failed)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
