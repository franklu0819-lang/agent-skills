#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""image_gen.py — MiniMax 文生图/主体参考图生图（/v1/image_generation，model=image-01）

用法:
  image_gen.py --prompt "赛博朋克风格的夜市，霓虹灯，8k 细节" --out-dir ./imgs
  image_gen.py --prompt "..." --ratio 16:9 -n 2                 # 指定比例与张数
  image_gen.py --prompt "..." --size 1920 1080                  # 自定义像素（512-2048，8 的倍数）
  image_gen.py --prompt "同一角色在雪山之巅" --subject-ref char.png   # 主体参考图生图
  image_gen.py --prompt "..." --seed 42                         # 固定种子可复现构图
  image_gen.py --prompt "..." --dry-run                         # 请求体预览，不调 API

选项:
  --model NAME       image-01（默认）| image-01-live（国内站，支持 --style 漫画/元气/中世纪/水彩）
  --ratio R          1:1(默认)/16:9/4:3/3:2/2:3/3:4/9:16/21:9（21:9 仅 image-01）
  --size W H         自定义宽高 [512,2048] 且 8 的倍数（仅 image-01；与 --ratio 同时给时官方以 ratio 优先）
  -n N               张数 [1,9] 默认 1
  --subject-ref F    主体参考图（本地路径 JPG/PNG ≤10MB 或公网 URL）；type=character 保持人物一致性
  --style S          仅 image-01-live: 漫画/元气/中世纪/水彩
  --style-weight F   (0,1] 默认 0.8（配合 --style）
  --optimizer        开启 prompt_optimizer（官方默认关；开启会改写提示词）
  --seed N           随机种子
  --out-dir DIR      输出目录（默认 ./minimax_images）
  --api-key KEY      API Key；传 - 从 stdin 读。默认自动解析
  --base-url URL     默认 https://api.minimax.cn；overseas = https://api.minimax.io

响应图片 URL 24 小时有效——脚本直接下载落盘。计费: ¥0.025/张。

凭证: platform.minimax.cn「账户管理→接口密钥」的 Key，export MINIMAX_API_KEY=...
（minimax- 家族统一只认此变量；key 不打印、不落盘）。
"""

import argparse
import base64
import http.client
import json
import mimetypes
import os
import re
import shutil
import socket
import sys
import time
import urllib.error
import urllib.request

DEFAULT_BASE = "https://api.minimax.cn"
OVERSEAS_BASE = "https://api.minimax.io"
API_PATH = "/v1/image_generation"

RATIOS = ["1:1", "16:9", "4:3", "3:2", "2:3", "3:4", "9:16", "21:9"]
MAX_PROMPT = 1500
PRICE = 0.025  # 元/张

NETWORK_ERRORS = (urllib.error.URLError, http.client.IncompleteRead,
                  socket.timeout, ConnectionResetError, OSError)


def find_api_key(explicit: str) -> str:
    """解析顺序: --api-key（- 表示 stdin）→ 环境变量 MINIMAX_API_KEY → ~/.zshrc。"""
    if explicit:
        if explicit == "-":
            return sys.stdin.read().strip()
        return explicit
    names = ("MINIMAX_API_KEY",)
    for var in names:
        if os.environ.get(var):
            return os.environ[var]
    zshrc = os.path.expanduser("~/.zshrc")
    if os.path.isfile(zshrc):
        found = ""
        for line in open(zshrc, encoding="utf-8", errors="replace"):
            m = re.match(r'\s*export\s+(%s)=(?:"([^"]+)"|([^\s#]+))' % "|".join(names), line)
            if m:
                found = m.group(2) or m.group(3)
        return found
    return ""


def resolve_base(arg: str) -> str:
    if not arg:
        return os.environ.get("MINIMAX_BASE_URL", DEFAULT_BASE)
    if arg == "overseas":
        return OVERSEAS_BASE
    return arg.rstrip("/")


def die(msg: str) -> None:
    print(f"image_gen.py: {msg}", file=sys.stderr)
    sys.exit(1)


def check_error(obj: dict) -> None:
    br = obj.get("base_resp")
    if isinstance(br, dict) and br.get("status_code") not in (0, None):
        hint = {"1004": "鉴权失败：Key 无效，或国内/海外站 Key 混用（两站独立）",
                "1002": "触发限流，稍后重试", "2013": "参数无效（检查 ratio/model/prompt 长度）"}.get(
            str(br.get("status_code")), "")
        die(f"服务错误: base_resp.status_code={br.get('status_code')} {br.get('status_msg', '')} {hint}".strip())
    err = obj.get("error")
    if isinstance(err, dict):
        die(f"服务错误: HTTP {err.get('http_code', '?')} {err.get('message', '')}".strip())


def to_data_url(path: str) -> str:
    """本地图片 → Base64 Data URL（主体参考图官方支持 公网URL 或 Data URL）。"""
    if not os.path.isfile(path):
        die(f"参考图不存在: {path}")
    if os.path.getsize(path) > 10 * 1024 * 1024:
        die(f"参考图 {os.path.getsize(path)/1024/1024:.1f}MB 超 10MB 限制（JPG/PNG）")
    mime = mimetypes.guess_type(path)[0] or "image/png"
    if path.lower().endswith((".jpg", ".jpeg")):
        mime = "image/jpeg"
    with open(path, "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode("ascii")


def build_payload(a, dry_run: bool = False) -> dict:
    payload = {"model": a.model, "prompt": a.prompt, "n": a.n}
    if a.ratio != "1:1" or not a.size:
        payload["aspect_ratio"] = a.ratio
    if a.size:
        payload["width"] = a.size[0]
        payload["height"] = a.size[1]
    if a.optimizer:
        payload["prompt_optimizer"] = True
    if a.seed is not None:
        payload["seed"] = a.seed
    if a.subject_ref:
        if dry_run:
            image_val = "<base64/URL 已省略>"
        elif re.match(r"^https?://", a.subject_ref):
            image_val = a.subject_ref
        else:
            image_val = to_data_url(a.subject_ref)
        payload["subject_reference"] = [{"type": "character", "image_file": image_val}]
    if a.style:
        payload["style"] = {"style_type": a.style, "style_weight": a.style_weight}
    return payload


def download(url: str, dest: str) -> None:
    try:
        with urllib.request.urlopen(url, timeout=300) as resp, open(dest, "wb") as f:
            shutil.copyfileobj(resp, f)
    except NETWORK_ERRORS as e:
        die(f"图片下载失败: {e}（URL 24 小时有效，可稍后手工下载: {url}）")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--prompt", required=True, help=f"提示词 ≤{MAX_PROMPT} 字符")
    ap.add_argument("--model", default="image-01", choices=["image-01", "image-01-live"],
                    help="image-01（默认）；image-01-live 仅国内站，支持 --style")
    ap.add_argument("--ratio", default="1:1", choices=RATIOS, help="画面比例，默认 1:1")
    ap.add_argument("--size", type=int, nargs=2, metavar=("W", "H"), default=None,
                    help="自定义像素宽高 [512,2048]、8 的倍数（仅 image-01；与 --ratio 同给时官方 ratio 优先）")
    ap.add_argument("-n", type=int, default=1, help="张数 [1,9] 默认 1")
    ap.add_argument("--subject-ref", default="", metavar="PATH_OR_URL",
                    help="主体参考图（本地 JPG/PNG ≤10MB 或公网 URL），人物/角色一致性")
    ap.add_argument("--style", default="", choices=["漫画", "元气", "中世纪", "水彩"],
                    help="仅 image-01-live，四选一")
    ap.add_argument("--style-weight", type=float, default=0.8, help="(0,1] 默认 0.8")
    ap.add_argument("--optimizer", action="store_true", help="开启提示词改写（官方默认关）")
    ap.add_argument("--seed", type=int, default=None, help="随机种子（固定可复现）")
    ap.add_argument("--out-dir", default="./minimax_images", help="输出目录")
    ap.add_argument("--base-url", default="", help=f"默认 {DEFAULT_BASE}；overseas={OVERSEAS_BASE}")
    ap.add_argument("--api-key", default="", help="API Key；传 - 从 stdin 读，默认自动解析环境变量")
    ap.add_argument("--dry-run", action="store_true", help="打印请求体预览，不调 API")
    a = ap.parse_args()

    if len(a.prompt) > MAX_PROMPT:
        die(f"prompt {len(a.prompt)} 字符超上限 {MAX_PROMPT}")
    if not 1 <= a.n <= 9:
        die("-n 取值范围 [1, 9]")
    if a.size:
        w, h = a.size
        for v in (w, h):
            if not 512 <= v <= 2048 or v % 8:
                die(f"--size 须各边 [512,2048] 且为 8 的倍数，收到 {w}x{h}")
        if a.model != "image-01":
            die("--size 仅 image-01 支持")
    if a.ratio == "21:9" and a.model != "image-01":
        die("--ratio 21:9 仅 image-01 支持")
    if a.style and a.model != "image-01-live":
        die("--style 仅 image-01-live 支持")
    if a.model == "image-01-live" and resolve_base(a.base_url) == OVERSEAS_BASE:
        die("image-01-live 仅国内站提供（海外站枚举仅 image-01）；去掉 --model 或切回国内站")
    if not 0 < a.style_weight <= 1:
        die("--style-weight 取值范围 (0, 1]")

    base = resolve_base(a.base_url)
    payload = build_payload(a, dry_run=a.dry_run)
    print(f"模型 {a.model}，比例 {a.ratio}"
          + (f"，{a.size[0]}x{a.size[1]}" if a.size else "")
          + f"，{a.n} 张，预计计费 ¥{a.n * PRICE:.3f}"
          + ("（主体参考）" if a.subject_ref else ""))

    if a.dry_run:
        preview = dict(payload)
        if len(a.prompt) > 50:
            preview["prompt"] = a.prompt[:50] + "…"
        print(f"请求预览: POST {base}{API_PATH}\n  {json.dumps(preview, ensure_ascii=False)}")
        sys.exit(0)

    key = find_api_key(a.api_key)
    if not key:
        die("缺少 API Key：platform.minimax.cn「账户管理→接口密钥」获取，export MINIMAX_API_KEY=...，"
            "或用 --api-key 传入（--api-key - 从 stdin 读）")

    req = urllib.request.Request(
        base + API_PATH,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    body = None
    for attempt in (1, 2):
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                body = resp.read()
            break
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:500]
            try:
                obj = json.loads(detail)
            except json.JSONDecodeError:
                obj = {}
            err = obj.get("error") if isinstance(obj, dict) else None
            err = err if isinstance(err, dict) else {}
            hint = "（401 类: Key 无效，或国内/海外站 Key 混用）" if e.code in (401, 403) else ""
            die(f"HTTP {e.code}: {err.get('message', detail)} {hint}".strip())
        except NETWORK_ERRORS as e:
            if attempt == 2:
                die(f"网络错误（已重试 1 次仍失败）: {e}")
            print(f"  网络错误 {e}，2s 后重试…", file=sys.stderr)
            time.sleep(2)
    if not body:
        die("未取得响应体")
    try:
        obj = json.loads(body.decode("utf-8", "replace"))
    except json.JSONDecodeError:
        die(f"响应非 JSON: {body[:200]!r}")
    check_error(obj)

    meta = obj.get("metadata") or {}
    urls = (obj.get("data") or {}).get("image_urls") or []
    if not urls:
        die(f"未取得图片（success={meta.get('success_count')} fail={meta.get('failed_count')}）: "
            f"{json.dumps(obj, ensure_ascii=False)[:300]}")
    os.makedirs(a.out_dir, exist_ok=True)
    ts = time.strftime("%H%M%S")
    saved = []
    for i, url in enumerate(urls, 1):
        ext = ".png" if ".png" in url.lower() else ".jpg"
        dest = os.path.join(a.out_dir, f"minimax_{ts}_{i}{ext}")
        download(url, dest)
        saved.append(dest)
        print(f"  已保存: {dest} ({os.path.getsize(dest)/1024:.0f}KB)")
    print(f"完成: {len(saved)} 张（失败 {meta.get('failed_count', 0)} 张），目录 {a.out_dir}")


if __name__ == "__main__":
    main()
