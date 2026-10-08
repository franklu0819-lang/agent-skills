#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""image_gen.py — 智谱 GLM-Image 文生图（/api/paas/v4/images/generations，model=glm-image）

用法:
  image_gen.py --prompt "书店橱窗海报，写大字「春日读书周」" -o poster.png
  image_gen.py --prompt "..." --ratio 16:9               # 推荐档横版
  image_gen.py --prompt "..." --ratio 21:9               # 无推荐档时按像素基准换算
  image_gen.py --prompt "..." --size 1920x1088           # 自定义（32 的整数倍，512-2048）
  image_gen.py --prompt "..." -n 4                       # 一次 4 张（逐张独立请求计费）
  image_gen.py --prompt "..." --dry-run                  # 请求体预览，不调 API

选项:
  --ratio W:H        1:1(默认)/3:2/2:3/4:3/3:4/16:9/9:16 命中推荐档；其他比例按基准像素换算
  --size WxH         自定义宽高：均为 32 的整数倍、[512,2048]、总像素 ≤ 2^22（与 --ratio 互斥）
  -n N               张数 [1,9] 默认 1（API 单请求只出 1 张，脚本逐张独立请求，各计费一次）
  -o PATH            输出路径（默认 ./glm_image_<时间戳>.png；多张自动加 -1/-2 序号；扩展名按实际格式纠正）
  --no-watermark     关闭水印（官方要求先在 个人中心-安全管理-去水印管理 签署免责声明）
  --timeout N        单次请求超时秒数，默认 120（hd 画质官方口径约 20 秒）
  --api-key KEY      API Key；传 - 从 stdin 读。默认自动解析
  --dry-run          只打印请求体，不发送

glm-image 仅文生图（无参考图输入模态，图生图走 ark-image-gen）；quality 恒为 hd（唯一支持档）。
响应 data[].url 有效期 30 天——脚本即时下载落盘。计费 0.1 元/张。

凭证: bigmodel.cn「API Keys」页的 Key，export ZHIPU_API_KEY=...
（glm- 家族统一只认此变量；GLM Coding Plan 订阅 Key 不含本接口。key 不打印、不落盘）。
"""

import argparse
import json
import math
import os
import re
import socket
import sys
import time
import urllib.error
import urllib.request

ENDPOINT = "https://open.bigmodel.cn/api/paas/v4/images/generations"
KEY_VARS = ("ZHIPU_API_KEY",)  # glm- 家族统一只认 ZHIPU_API_KEY
MODEL = "glm-image"
MAX_PROMPT = 1000      # 官方口径：prompt ≤ 1000 字符
PRICE = 0.1            # 元/张
SIDE_MIN, SIDE_MAX = 512, 2048      # 自定义边长范围（模型页口径；API 页建议 ≥1024）
STEP = 32              # 边长须为 32 的整数倍
MAX_PIXELS = 1 << 22   # 4194304，总像素上限
ATTEMPTS = 3           # 连接层错误共尝试 3 次（与 glm-ocr 一致）
RETRY_WAIT = 3.0

# 官方推荐尺寸档（glm-image）：比例接近（±3%）时直接采用，服务端最稳
RATIO_SIZES = (
    ("1:1", 1280, 1280), ("3:2", 1568, 1056), ("2:3", 1056, 1568),
    ("4:3", 1472, 1088), ("3:4", 1088, 1472), ("16:9", 1728, 960), ("9:16", 960, 1728),
)
BASE_PIXELS = 1728 * 960  # 比例换算像素基准（与推荐档像素量级一致）
MAX_RATIO = SIDE_MAX // SIDE_MIN  # 边长范围允许的最极端宽高比（4:1）

MIME_EXT = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}


class ApiError(Exception):
    def __init__(self, msg, code=None):
        super().__init__(msg)
        self.code = code


def log(msg):
    print(msg, file=sys.stderr)


def find_api_key(explicit):
    """解析顺序: --api-key（- 表示从 stdin 读，避免 key 进 shell history）→ 环境变量
    ZHIPU_API_KEY → ~/.zshrc 同名 export（取最后生效的）。glm- 家族统一只认 ZHIPU_API_KEY。"""
    if explicit:
        if explicit == "-":
            return sys.stdin.read().strip()
        return explicit
    for var in KEY_VARS:
        if os.environ.get(var):
            return os.environ[var]
    zshrc = os.path.expanduser("~/.zshrc")
    found = ""
    try:
        with open(zshrc, encoding="utf-8", errors="replace") as f:
            for line in f:
                m = re.match(r'\s*export\s+(%s)=(?:"([^"]+)"|([^\s#]+))' % "|".join(KEY_VARS), line)
                if m:
                    found = m.group(2) or m.group(3) or ""
    except OSError:
        pass
    return found


def parse_ratio(spec):
    try:
        a, b = spec.split(":", 1)
        rw, rh = float(a), float(b)
        if rw <= 0 or rh <= 0:
            raise ValueError
    except ValueError:
        raise ApiError("--ratio 格式应为 宽:高（如 16:9），收到: %s" % spec)
    return rw, rh


def check_size(w, h):
    """校验尺寸合法性，返回 (w, h)；不合法抛错。"""
    if w % STEP or h % STEP:
        raise ApiError("宽高均须为 %d 的整数倍，收到 %dx%d" % (STEP, w, h))
    if not (SIDE_MIN <= w <= SIDE_MAX and SIDE_MIN <= h <= SIDE_MAX):
        raise ApiError("宽高均须在 [%d,%d] 内，收到 %dx%d" % (SIDE_MIN, SIDE_MAX, w, h))
    if w * h > MAX_PIXELS:
        raise ApiError("总像素 %d 超上限 %d（%dx%d）" % (w * h, MAX_PIXELS, w, h))
    if min(w, h) < 1024:
        log("[提示] 边长 %d 低于官方建议值 1024，服务端可能拒绝，被拒时换推荐档或调大"
            % min(w, h))
    return w, h


def ratio_to_size(rw, rh):
    """比例 → (w, h, 说明)。±3% 内命中推荐档；否则按基准像素换算 + 32 对齐 + 边长钳制。"""
    target = rw / rh
    if target > MAX_RATIO or target < 1.0 / MAX_RATIO:
        raise ApiError("比例 %s 超出边长范围可表达区间（最宽 %d:1 / 最窄 1:%d）"
                       % (("%g:%g" % (rw, rh)).rstrip("0.").rstrip(":"), MAX_RATIO, MAX_RATIO))
    best = min(RATIO_SIZES, key=lambda t: abs(t[1] / t[2] - target))
    if abs(best[1] / best[2] - target) / target <= 0.03:
        return best[1], best[2], "官方推荐档 %s" % best[0]
    w = int(round(math.sqrt(BASE_PIXELS * target) / STEP)) * STEP
    h = int(round(w / target / STEP)) * STEP
    w = max(SIDE_MIN, min(SIDE_MAX, w))
    h = max(SIDE_MIN, min(SIDE_MAX, h))
    if w * h > MAX_PIXELS:  # 钳制后极端情况兜底：先收窄长边
        long_side = int(math.sqrt(MAX_PIXELS * target) / STEP) * STEP
        w = min(w, long_side)
        h = int(round(w / target / STEP)) * STEP
    check_size(w, h)
    return w, h, "按基准 %d 像素换算（实际比例约 %.3f）" % (BASE_PIXELS, w / h)


def parse_size_spec(spec):
    try:
        a, b = spec.lower().split("x", 1)
        w, h = int(a), int(b)
        if w <= 0 or h <= 0:
            raise ValueError
    except ValueError:
        raise ApiError("--size 格式应为 宽x高（如 1728x960），收到: %s" % spec)
    return check_size(w, h)


def parse_error_body(raw):
    try:
        err = json.loads(raw.decode("utf-8", "replace")).get("error") or {}
        return err.get("code"), err.get("message") or raw.decode("utf-8", "replace")[:300]
    except (ValueError, AttributeError):
        return None, raw.decode("utf-8", "replace")[:300]


def http_bytes(url, key, payload, timeout):
    """POST JSON 返回响应 bytes。连接层错误与 5xx 共尝试 ATTEMPTS 次；4xx 立即抛错。"""
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    errs = []
    for attempt in range(ATTEMPTS):
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Authorization", "Bearer " + key)
        req.add_header("Content-Type", "application/json")
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))  # 国内节点直连
        try:
            with opener.open(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            code, msg = parse_error_body(e.read())
            if e.code >= 500 and attempt < ATTEMPTS - 1:
                errs.append("HTTP %s (%s)" % (e.code, msg))
                time.sleep(RETRY_WAIT)
                continue
            raise ApiError("HTTP %s: %s" % (e.code, msg), code=code)
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            errs.append("第%d次: %s" % (attempt + 1, e))
            if attempt < ATTEMPTS - 1:
                time.sleep(RETRY_WAIT)
    raise ApiError("网络请求失败（连接层错误已尝试 %d 次）：\n  " % ATTEMPTS + "\n  ".join(errs))


def download(url, timeout):
    """下载图片 bytes + Content-Type。连接层错误重试 1 次。"""
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    for attempt in range(2):
        try:
            with opener.open(urllib.request.Request(url), timeout=timeout) as resp:
                return resp.read(), resp.headers.get("Content-Type", "")
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            if attempt:
                raise ApiError("图片下载失败（URL 有效期 30 天，可重跑）: %s" % e)
            time.sleep(RETRY_WAIT)


def sniff_ext(data, content_type):
    """按 Content-Type / 魔数定扩展名，兜底 .png。"""
    ct = (content_type or "").split(";")[0].strip().lower()
    if ct in MIME_EXT:
        return MIME_EXT[ct]
    if data[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return ".png"


def numbered_path(path, idx, total, data, content_type):
    """输出路径：单张用原路径；多张插 -<idx> 序号；扩展名按实际格式纠正。"""
    stem, ext = os.path.splitext(path)
    ext = ext.lower()
    want = sniff_ext(data, content_type)
    if ext not in MIME_EXT.values():  # 未指定/陌生扩展名 → 按实际格式
        ext = want
    if total > 1:
        stem = "%s-%d" % (stem, idx)
    return stem + ext


def describe_filters(content_filter):
    rows = []
    for f in content_filter or []:
        rows.append("role=%s level=%s" % (f.get("role"), f.get("level")))
    return "; ".join(rows)


def main():
    ap = argparse.ArgumentParser(description="GLM-Image 文生图（智谱 images/generations，仅文生图）")
    ap.add_argument("--prompt", required=True, help="图像描述（≤%d 字符）" % MAX_PROMPT)
    ap.add_argument("--ratio", help="画面比例 宽:高（命中推荐档 1:1/3:2/2:3/4:3/3:4/16:9/9:16，其余换算）")
    ap.add_argument("--size", help="自定义像素 宽x高（32 的整数倍、[%d,%d]、总像素 ≤ 2^22）" % (SIDE_MIN, SIDE_MAX))
    ap.add_argument("-n", type=int, default=1, help="张数 [1,9]，默认 1（逐张独立请求计费）")
    ap.add_argument("-o", "--output", help="输出路径（默认 ./glm_image_<时间戳>.png；多张自动加序号）")
    ap.add_argument("--no-watermark", action="store_true",
                    help="关闭水印（须先在 个人中心-安全管理-去水印管理 签署免责声明）")
    ap.add_argument("--timeout", type=int, default=120, help="单次请求超时秒数（默认 120，hd 约 20 秒）")
    ap.add_argument("--api-key", default="", help="API Key（默认自动解析，见 find_api_key；- 从 stdin 读）")
    ap.add_argument("--dry-run", action="store_true", help="只打印请求体，不发送")
    args = ap.parse_args()

    if len(args.prompt) > MAX_PROMPT:
        log("prompt %d 字符超上限 %d，请精简描述" % (len(args.prompt), MAX_PROMPT))
        return 1
    if not 1 <= args.n <= 9:
        log("-n 范围 [1,9]")
        return 1
    if args.ratio and args.size:
        log("--ratio 与 --size 互斥，二选一")
        return 1

    if args.size:
        w, h = parse_size_spec(args.size)
        size_note = "自定义"
    else:
        rw, rh = parse_ratio(args.ratio) if args.ratio else (1, 1)
        w, h, size_note = ratio_to_size(rw, rh)
    size = "%dx%d" % (w, h)

    payload = {"model": MODEL, "prompt": args.prompt, "size": size}
    if args.no_watermark:
        payload["watermark_enabled"] = False

    if args.dry_run:
        log("[dry-run] POST %s\n  %s" % (ENDPOINT, json.dumps(
            {**payload, "prompt": payload["prompt"][:60] + ("…" if len(payload["prompt"]) > 60 else "")},
            ensure_ascii=False, indent=2)))
        log("  size=%s（%s）  n=%d  预计 %.2f 元" % (size, size_note, args.n, PRICE * args.n))
        return 0

    key = find_api_key(args.api_key)
    if not key:
        log("缺少 API Key：请在 bigmodel.cn「API Keys」页获取，export ZHIPU_API_KEY=... 或用 --api-key 传入。"
            "（GLM Coding Plan 订阅 Key 不含本接口，需开放平台常规 API Key）")
        return 1

    if args.no_watermark:
        log("[提示] watermark_enabled=false 仅对已签署免责声明的账号生效（个人中心-安全管理-去水印管理）")

    base = args.output or "glm_image_%s.png" % time.strftime("%Y%m%d_%H%M%S")
    images, failed = [], 0
    for i in range(1, args.n + 1):
        tag = "[第 %d/%d 张]" % (i, args.n) if args.n > 1 else "[生成]"
        try:
            raw = http_bytes(ENDPOINT, key, payload, args.timeout)
            try:
                resp = json.loads(raw.decode("utf-8"))
            except (ValueError, UnicodeDecodeError) as e:
                raise ApiError("响应不是合法 JSON: %s" % e)
            if resp.get("error"):
                raise ApiError("API 错误 %s: %s"
                               % (resp["error"].get("code"), resp["error"].get("message")),
                               code=resp["error"].get("code"))
            cf = resp.get("content_filter")
            if cf:
                log("%s content_filter: %s" % (tag, describe_filters(cf)))
            data = resp.get("data") or []
            url = next((d.get("url") for d in data if d.get("url")), None)
            if not url:
                note = "（内容安全拦截，见上方 content_filter）" if cf else ": %.300s" % json.dumps(resp, ensure_ascii=False)
                raise ApiError("响应无图片 URL%s" % note)
            data_bytes, ctype = download(url, args.timeout)
            out = numbered_path(base, i, args.n, data_bytes, ctype)
            with open(out, "wb") as f:
                f.write(data_bytes)
            images.append(os.path.abspath(out))
            log("%s size=%s → %s（%.1fMB）" % (tag, size, out, len(data_bytes) / 1048576))
        except ApiError as e:
            log("%s [错误] %s" % (tag, e))
            failed += 1
        except OSError as e:
            log("%s [错误] 写盘失败: %s（图片 URL 有效期 30 天，可从上方日志取 URL 手动保存）" % (tag, e))
            failed += 1

    if failed and not images:
        return 1
    print(json.dumps({"ok": not failed, "images": images, "model": MODEL, "size": size,
                      "requested": args.n, "failed": failed}, ensure_ascii=False))
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ApiError as e:
        log("image_gen.py: %s" % e)
        sys.exit(1)
