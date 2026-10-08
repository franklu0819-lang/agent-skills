#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""video_gen.py — MiniMax 视频生成（v2: MiniMax-H3/H3-Max；v1 legacy: Hailuo-2.3/02）

用法:
  video_gen.py --prompt "雨夜霓虹街头，镜头缓缓推进" --ratio 16:9 --duration 6        # v2 H3 文生视频
  video_gen.py --prompt "..." --resolution 2K --duration 10                            # v2 2K 高清
  video_gen.py --prompt "让画面动起来" --first-frame scene.png                          # v2 图生视频(自适应比例)
  video_gen.py --prompt "..." --api v1 --model MiniMax-Hailuo-02 --resolution 512P --duration 6   # 便宜档
  video_gen.py --prompt "..." --dry-run                                                # 成本预估+请求体预览
  video_gen.py --prompt "..." --no-wait                                                # 只建任务，打印 task_id
  video_gen.py --query TASK_ID            # 查询任务并下载成片（7 天内可查；断点续传下载）
  video_gen.py --cancel TASK_ID           # 取消排队任务(不扣费)/删除已完成任务记录

两代 API（官方 2026-10）:
  v2（默认）POST /v2/video_generation，模型 MiniMax-H3（768P/2K，4-15s，按秒计费 0.5/0.8 元）
            与 MiniMax-H3-Max（480P/768P，5-15s，0.33/0.5 元）；GET /v2/query/video_generation/{id}
            轮询（官方建议 10s 间隔），成功后 task.content.url 为限时下载地址。
  v1（--api v1，legacy Hailuo，按条计费）POST /v1/video_generation → task_id →
            GET /v1/query/video_generation?task_id=（成功得 file_id）→
            GET /v1/files/retrieve?file_id=（download_url 仅 1 小时有效，脚本及时下载）。

省钱纪律: 生成前打印成本预估；首片用低档（v2 480P/768P 或 v1 512P）验证构图，满意再上 2K；
图生视频比文生视频可控（首帧用 minimax-image-gen 出图后微调）。

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

V2_CREATE = "/v2/video_generation"
V2_QUERY = "/v2/query/video_generation"       # + /{task_id}
V2_CANCEL = "/v2/video_generation"            # DELETE + /{task_id}
V1_CREATE = "/v1/video_generation"
V1_QUERY = "/v1/query/video_generation"       # ?task_id=
V1_RETRIEVE = "/v1/files/retrieve"            # ?file_id=

# v2 计价（元/秒）；None = 该模型不支持该分辨率
V2_PRICE = {
    ("MiniMax-H3", "480P"): None, ("MiniMax-H3", "768P"): 0.50, ("MiniMax-H3", "2K"): 0.80,
    ("MiniMax-H3-Max", "480P"): 0.33, ("MiniMax-H3-Max", "768P"): 0.50, ("MiniMax-H3-Max", "2K"): None,
}
V2_DUR_RANGE = {"MiniMax-H3": (4, 15), "MiniMax-H3-Max": (5, 15)}
V2_RATIOS = ["21:9", "16:9", "4:3", "1:1", "3:4", "9:16"]

# v1 计价（元/条，T2V/I2V 同价）；缺键 = 不支持
V1_PRICE = {
    ("MiniMax-Hailuo-2.3", "768P", 6): 2.00, ("MiniMax-Hailuo-2.3", "768P", 10): 4.00,
    ("MiniMax-Hailuo-2.3", "1080P", 6): 3.50,
    ("MiniMax-Hailuo-2.3-Fast", "768P", 6): 1.35, ("MiniMax-Hailuo-2.3-Fast", "768P", 10): 2.25,
    ("MiniMax-Hailuo-2.3-Fast", "1080P", 6): 2.31,
    ("MiniMax-Hailuo-02", "512P", 6): 0.60, ("MiniMax-Hailuo-02", "512P", 10): 1.00,
    ("MiniMax-Hailuo-02", "768P", 6): 2.00, ("MiniMax-Hailuo-02", "768P", 10): 4.00,
    ("MiniMax-Hailuo-02", "1080P", 6): 3.50,
}
V1_MODELS = sorted({k[0] for k in V1_PRICE})

MAX_V2_PROMPT = 7000
MAX_V1_PROMPT = 2000
MAX_FIRST_FRAME_MB = {"v2": 30, "v1": 20}   # 官方: v2 图片 ≤30MB；v1 <20MB、短边 >300px
POLL_INTERVAL = 10            # 官方建议轮询间隔

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
    print(f"video_gen.py: {msg}", file=sys.stderr)
    sys.exit(1)


def check_error(obj: dict) -> None:
    """v2 错误是 OpenAI 风格 error.message；v1/部分端点是 base_resp；两种都查。"""
    err = obj.get("error")
    if isinstance(err, dict) and err.get("message"):
        die(f"服务错误: HTTP {err.get('http_code', '?')} {err.get('message')}".strip())
    br = obj.get("base_resp")
    if isinstance(br, dict) and br.get("status_code") not in (0, None):
        hint = {"1004": "鉴权失败：Key 无效，或国内/海外站 Key 混用（两站独立）",
                "1002": "触发限流，稍后重试", "2013": "参数无效（检查模型/分辨率/时长矩阵）"}.get(
            str(br.get("status_code")), "")
        die(f"服务错误: base_resp.status_code={br.get('status_code')} {br.get('status_msg', '')} {hint}".strip())


def request_json(url: str, key: str, method: str = "GET", payload: dict = None) -> dict:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    headers = {"Authorization": f"Bearer {key}"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    body = None
    for attempt in (1, 2):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
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
    return obj


def to_image_value(path_or_url: str, api: str) -> str:
    """本地图片 → Base64 Data URI；http(s) URL 原样返回。v2 ≤30MB，v1 <20MB。"""
    if re.match(r"^https?://", path_or_url):
        return path_or_url
    if not os.path.isfile(path_or_url):
        die(f"首帧图不存在: {path_or_url}")
    limit = MAX_FIRST_FRAME_MB[api]
    if os.path.getsize(path_or_url) > limit * 1024 * 1024:
        die(f"首帧图超 {api} 上限 {limit}MB（压缩或降分辨率后重试；v1 另要求短边 >300px）")
    mime = mimetypes.guess_type(path_or_url)[0] or "image/png"
    if path_or_url.lower().endswith((".jpg", ".jpeg")):
        mime = "image/jpeg"
    with open(path_or_url, "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode("ascii")


def build_v2_payload(a, dry_run: bool = False) -> dict:
    content = [{"type": "text", "text": a.prompt}]
    if a.first_frame:
        image_val = "<base64/URL 已省略>" if dry_run else to_image_value(a.first_frame, "v2")
        content.append({"type": "image_url", "image_url": image_val,
                        "role": "first_frame"})
    payload = {"model": a.model, "content": content, "resolution": a.resolution,
               "duration": a.duration}
    if a.first_frame:
        payload["ratio"] = "adaptive"   # 官方: 图生视频恒按 adaptive（比例由首帧决定）
    else:
        payload["ratio"] = a.ratio      # 文生视频必填且不可 adaptive
    return payload


def build_v1_payload(a, dry_run: bool = False) -> dict:
    payload = {"model": a.model, "prompt": a.prompt, "duration": a.duration,
               "resolution": a.resolution}
    if a.optimizer:
        payload["prompt_optimizer"] = True
    if a.first_frame:
        payload["first_frame_image"] = ("<base64/URL 已省略>" if dry_run
                                        else to_image_value(a.first_frame, "v1"))
    return payload


def est_cost(a) -> str:
    if a.api == "v2":
        unit = V2_PRICE.get((a.model, a.resolution))
        if unit is None:
            return "不支持"
        return f"≈¥{unit * a.duration:.2f}（¥{unit}/秒 × {a.duration}s，按秒计费）"
    price = V1_PRICE.get((a.model, a.resolution, a.duration))
    if price is None:
        return "不支持"
    return f"≈¥{price:.2f}（按条计费）"


def download(url: str, dest: str) -> None:
    try:
        with urllib.request.urlopen(url, timeout=600) as resp, open(dest, "wb") as f:
            shutil.copyfileobj(resp, f)
    except NETWORK_ERRORS as e:
        die(f"成片下载失败: {e}\n下载地址有时效（v2 限时/v1 1 小时），过期后重新 --query 刷新")


def poll_v2(task_id: str, key: str, base: str, no_wait: bool) -> None:
    print(f"任务 {task_id}（v2 查询仅支持最近 7 天）…")
    obj = request_json(f"{base}{V2_QUERY}/{task_id}", key)
    task = obj.get("task") or {}
    status = task.get("status", "?")
    print(f"状态: {status}")
    if status in ("succeeded",):
        url = ((task.get("content") or {}).get("url")) or ""
        dest = f"minimax_{task_id[:8]}.mp4"
        if url:
            download(url, dest)
            print(f"完成: {dest} ({os.path.getsize(dest)/1024/1024:.1f}MB)")
        else:
            die(f"成功但未取得下载地址: {json.dumps(task, ensure_ascii=False)[:300]}")
        usage = task.get("usage") or {}
        if usage:
            print(f"usage: {json.dumps(usage, ensure_ascii=False)}")
        return
    if status in ("failed", "cancelled"):
        die(f"任务未成功: {json.dumps(task.get('error') or task, ensure_ascii=False)[:300]}")
    if no_wait:
        print(f"仍在 {status}。稍后重跑: video_gen.py --query {task_id}")
    else:
        _wait_loop_v2(task_id, key, base)


def _wait_loop_v2(task_id: str, key: str, base: str) -> None:
    deadline = time.time() + 30 * 60  # 最多轮询 30 分钟
    while time.time() < deadline:
        time.sleep(POLL_INTERVAL)
        obj = request_json(f"{base}{V2_QUERY}/{task_id}", key)
        task = obj.get("task") or {}
        status = task.get("status", "?")
        print(f"  [{time.strftime('%H:%M:%S')}] {status}")
        if status == "succeeded":
            url = ((task.get("content") or {}).get("url")) or ""
            if not url:
                die(f"成功但未取得下载地址: {json.dumps(task, ensure_ascii=False)[:300]}")
            dest = f"minimax_{task_id[:8]}.mp4"
            download(url, dest)
            print(f"完成: {dest} ({os.path.getsize(dest)/1024/1024:.1f}MB)")
            return
        if status in ("failed", "cancelled"):
            die(f"任务未成功: {json.dumps(task.get('error') or task, ensure_ascii=False)[:300]}")
    die("轮询超时（30 分钟）——稍后用 --query 续查")


def poll_v1(task_id: str, key: str, base: str, no_wait: bool) -> None:
    obj = request_json(f"{base}{V1_QUERY}?task_id={task_id}", key)
    status = obj.get("status", "?")
    print(f"状态: {status}")
    if status == "Success":
        file_id = obj.get("file_id")
        if not file_id:
            die(f"成功但缺 file_id: {json.dumps(obj, ensure_ascii=False)[:300]}")
        obj2 = request_json(f"{base}{V1_RETRIEVE}?file_id={file_id}", key)
        url = (obj2.get("file") or {}).get("download_url")
        if not url:
            die(f"未取得 download_url: {json.dumps(obj2, ensure_ascii=False)[:300]}")
        dest = f"minimax_{task_id[:8]}.mp4"
        download(url, dest)
        print(f"完成: {dest} ({os.path.getsize(dest)/1024/1024:.1f}MB)"
              f"（{obj.get('video_width')}x{obj.get('video_height')}）")
        return
    if status == "Fail":
        die(f"任务失败: {json.dumps(obj, ensure_ascii=False)[:300]}")
    if no_wait:
        print(f"仍在 {status}。稍后重跑: video_gen.py --query {task_id} --api v1")
    else:
        deadline = time.time() + 30 * 60
        while time.time() < deadline:
            time.sleep(POLL_INTERVAL)
            obj = request_json(f"{base}{V1_QUERY}?task_id={task_id}", key)
            status = obj.get("status", "?")
            print(f"  [{time.strftime('%H:%M:%S')}] {status}")
            if status == "Success":
                file_id = obj.get("file_id")
                obj2 = request_json(f"{base}{V1_RETRIEVE}?file_id={file_id}", key)
                url = (obj2.get("file") or {}).get("download_url")
                dest = f"minimax_{task_id[:8]}.mp4"
                download(url, dest)
                print(f"完成: {dest} ({os.path.getsize(dest)/1024/1024:.1f}MB)")
                return
            if status == "Fail":
                die(f"任务失败: {json.dumps(obj, ensure_ascii=False)[:300]}")
        die("轮询超时（30 分钟）——稍后用 --query 续查")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--prompt", default="", help="文生视频提示词（v2 ≤7000 / v1 ≤2000 字符；v1 图生视频可为空）")
    ap.add_argument("--first-frame", default="", metavar="PATH_OR_URL",
                    help="首帧图（本地路径或 URL）：图生视频；v2 比例自适应首帧，v1 分辨率跟随首帧")
    ap.add_argument("--api", choices=["v2", "v1"], default="v2",
                    help="v2=MiniMax-H3（默认，按秒计费）；v1=Hailuo 2.3/02（legacy，按条计费便宜档）")
    ap.add_argument("--model", default="", help="v2: MiniMax-H3(默认)/MiniMax-H3-Max；v1: MiniMax-Hailuo-2.3(默认)/-02/-2.3-Fast")
    ap.add_argument("--resolution", default="",
                    help="v2: 480P/768P/2K（H3 默认 768P）；v1: 512P/768P/1080P（默认 768P）")
    ap.add_argument("--duration", type=int, default=0,
                    help="v2: 4-15 秒（H3 默认 6）；v1: 6|10（默认 6）")
    ap.add_argument("--ratio", default="16:9", choices=V2_RATIOS,
                    help="v2 文生视频画幅（图生视频恒 adaptive 不用传），默认 16:9")
    ap.add_argument("--optimizer", action="store_true",
                    help="开启提示词改写（v1 prompt_optimizer，默认关；开启后服务端会重写 prompt）")
    ap.add_argument("--query", default="", metavar="TASK_ID", help="查询任务并下载成片")
    ap.add_argument("--cancel", default="", metavar="TASK_ID",
                    help="取消排队任务（不扣费）/删除已完成任务记录（running 不可操作）")
    ap.add_argument("--no-wait", action="store_true", help="只创建/查询一次，不阻塞轮询")
    ap.add_argument("--base-url", default="", help=f"默认 {DEFAULT_BASE}；overseas={OVERSEAS_BASE}")
    ap.add_argument("--api-key", default="", help="API Key；传 - 从 stdin 读，默认自动解析环境变量")
    ap.add_argument("--dry-run", action="store_true", help="打印成本预估与请求体预览，不调 API")
    a = ap.parse_args()
    base = resolve_base(a.base_url)

    # ── 查询/取消：需要 key，不需要 prompt ──
    if a.query or a.cancel:
        key = find_api_key(a.api_key)
        if not key:
            die("缺少 API Key：platform.minimax.cn「账户管理→接口密钥」获取，export MINIMAX_API_KEY=...，"
                "或用 --api-key 传入（--api-key - 从 stdin 读）")
        if a.query:
            (poll_v1 if a.api == "v1" else poll_v2)(a.query, key, base, a.no_wait)
        if a.cancel:
            if a.api == "v2":
                obj = request_json(f"{base}{V2_CANCEL}/{a.cancel}", key, method="DELETE")
            else:
                die("v1 无取消/删除任务接口（等任务自然结束）")
            print(f"已处理: {json.dumps(obj, ensure_ascii=False)[:200]}")
        sys.exit(0)

    # ── 创建任务：参数归一与校验 ──
    if not a.prompt and not a.first_frame:
        die("缺少输入：--prompt（文生视频）或 --first-frame（图生视频）至少一个（--query/--cancel 管理任务）")
    if a.api == "v2":
        a.model = a.model or "MiniMax-H3"
        a.resolution = a.resolution or "768P"
        a.duration = a.duration or 6
        if a.model not in ("MiniMax-H3", "MiniMax-H3-Max"):
            die(f"v2 模型仅 MiniMax-H3 / MiniMax-H3-Max（收到 {a.model}；Hailuo 系走 --api v1）")
        lo, hi = V2_DUR_RANGE[a.model]
        if not lo <= a.duration <= hi:
            die(f"{a.model} 时长范围 [{lo},{hi}] 秒（H3-Max 不支持 4 秒）")
        if V2_PRICE.get((a.model, a.resolution)) is None:
            die(f"{a.model} 不支持 {a.resolution}（H3: 768P/2K；H3-Max: 480P/768P）")
        if len(a.prompt) > MAX_V2_PROMPT:
            die(f"prompt {len(a.prompt)} 字符超 v2 上限 {MAX_V2_PROMPT}")
        payload = build_v2_payload(a, a.dry_run)
        create_url = base + V2_CREATE
    else:
        a.model = a.model or "MiniMax-Hailuo-2.3"
        a.resolution = a.resolution or "768P"
        a.duration = a.duration or 6
        if a.model not in V1_MODELS:
            die(f"v1 模型可选 {V1_MODELS}（收到 {a.model}）")
        if a.duration not in (6, 10):
            die("v1 时长仅 6 或 10 秒")
        if a.resolution == "512P" and not a.first_frame:
            die("v1 512P 仅图生视频支持（--first-frame）；文生视频最低 768P"
                "（¥2/条起，Hailuo-2.3-Fast ¥1.35）——2026-10 实测官方 2013 报错确认")
        if (a.model, a.resolution, a.duration) not in V1_PRICE:
            die(f"{a.model} 不支持 {a.resolution}×{a.duration}s 组合"
                f"（Hailuo-02: 512P 6/10s、768P 6/10s、1080P 6s；2.3/2.3-Fast: 768P 6/10s、1080P 6s）")
        if len(a.prompt) > MAX_V1_PROMPT:
            die(f"prompt {len(a.prompt)} 字符超 v1 上限 {MAX_V1_PROMPT}")
        payload = build_v1_payload(a, a.dry_run)
        create_url = base + V1_CREATE

    mode = "图生视频" if a.first_frame else "文生视频"
    print(f"{a.api} {mode}：{a.model}，{a.resolution}，{a.duration}s，"
          f"{'' if a.first_frame else '画幅 ' + a.ratio + '，'}成本 {est_cost(a)}")

    if a.dry_run:
        preview = json.loads(json.dumps(payload))
        if preview.get("content"):
            preview["content"][0]["text"] = preview["content"][0]["text"][:50] + "…"
        if len(preview.get("prompt", "")) > 50:
            preview["prompt"] = preview["prompt"][:50] + "…"
        print(f"请求预览: POST {create_url}\n  {json.dumps(preview, ensure_ascii=False)}")
        sys.exit(0)

    key = find_api_key(a.api_key)
    if not key:
        die("缺少 API Key：platform.minimax.cn「账户管理→接口密钥」获取，export MINIMAX_API_KEY=...，"
            "或用 --api-key 传入（--api-key - 从 stdin 读）")
    base = resolve_base(a.base_url)

    obj = request_json(create_url, key, method="POST", payload=payload)
    task_id = obj.get("task_id")
    if not task_id:
        die(f"未取得 task_id: {json.dumps(obj, ensure_ascii=False)[:300]}")
    print(f"任务已创建: {task_id}")
    if a.no_wait:
        print(f"稍后查询: video_gen.py --query {task_id}" + (" --api v1" if a.api == "v1" else ""))
        sys.exit(0)
    (poll_v1 if a.api == "v1" else poll_v2)(task_id, key, base, a.no_wait)


if __name__ == "__main__":
    main()
