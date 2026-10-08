#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""asr.py — MiniMax 语音识别（/v1/speech_to_text，model=asr-1.0，api.minimax.cn）

用法:
  asr.py --audio meeting.mp3                        # 纯文本转写，打印并存 out.txt
  asr.py --audio interview.wav -o interview.srt     # SRT 字幕
  asr.py --audio podcast.mp3 --format verbose-json  # 说话人分离 + 逐段时间戳
  asr.py --audio clip.m4a --word-timestamps         # 词级时间戳（verbose/srt/vtt）
  asr.py --audio long_conf.m4a                      # >500s 自动 ffmpeg 分段转写拼接（时间轴偏移修正）
  asr.py --audio en.wav --language en               # 指定语言（默认自动混合识别）

选项:
  --format F        text（默认）| srt | vtt | verbose-json
  -o / --output     输出文件；text 缺省 <音频名>.txt，字幕缺省同名 .srt/.vtt
  --language TAG    BCP-47 语言提示（zh/yue/en/ja/ko/…共 20 种）；不传=自动混合识别
  --word-timestamps 词级时间戳（仅 verbose-json/srt/vtt 有效）
  --api-key KEY     API Key；传 - 从 stdin 读（避免进 shell history）。默认自动解析
  --base-url URL    默认 https://api.minimax.cn；overseas = https://api.minimax.io

限制（官方）: 单次 ≤500 秒且 ≤50MB（超出脚本自动 ffmpeg 切成 ≤480s 段逐段转写拼接，
SRT/VTT/verbose-json 时间戳按段起点偏移修正）；仅支持文件（无 URL 输入，先下载）。
格式: mp3/aac/opus/wav/flac/m4a/ogg/aiff（裸 PCM 不支持）。
计费: ¥2.50/小时（按音频实际时长）。

凭证: platform.minimax.cn「账户管理→接口密钥」的 Key，export MINIMAX_API_KEY=...
（minimax- 家族统一只认此变量；key 不打印、不落盘）。
"""

import argparse
import http.client
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

DEFAULT_BASE = "https://api.minimax.cn"
OVERSEAS_BASE = "https://api.minimax.io"
API_PATH = "/v1/speech_to_text"

MAX_SECONDS = 500     # 官方单次时长硬上限（超出 400，不截断）
MAX_SIZE = 50 * 1024 * 1024
SEGMENT_SECONDS = 480  # 超限自动分段的目标时长
ALLOWED_EXT = (".mp3", ".aac", ".opus", ".wav", ".flac", ".m4a", ".ogg", ".aiff")
PRICE_PER_HOUR = 2.50

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
    print(f"asr.py: {msg}", file=sys.stderr)
    sys.exit(1)


def check_error(obj: dict) -> None:
    br = obj.get("base_resp")
    if isinstance(br, dict) and br.get("status_code") not in (0, None):
        hint = {"1004": "鉴权失败：Key 无效，或国内/海外站 Key 混用（两站独立）",
                "1002": "触发限流，稍后重试", "2013": "参数无效（检查音频格式/语言代码）"}.get(
            str(br.get("status_code")), "")
        die(f"服务错误: base_resp.status_code={br.get('status_code')} {br.get('status_msg', '')} {hint}".strip())
    err = obj.get("error")
    if isinstance(err, dict):
        die(f"服务错误: HTTP {err.get('http_code', '?')} {err.get('message', '')}".strip())


def ffprobe_duration(path: str) -> float:
    if shutil.which("ffprobe") is None:
        die("需要 ffprobe 探测时长（brew install ffmpeg）；或手动切成 ≤500s 段后逐段转写")
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, timeout=60)
        return float(out.stdout.strip())
    except (ValueError, subprocess.TimeoutExpired, OSError):
        die(f"ffprobe 无法读取时长: {path}")


def split_audio(path: str, seg_seconds: int, workdir: str) -> list:
    """ffmpeg 按固定秒切段（重编码 aac 保证切点精确），返回段文件列表与各自起点秒。"""
    dur = ffprobe_duration(path)
    n = int(dur // seg_seconds) + (1 if dur % seg_seconds > 0.5 else 0)
    segs = []
    for i in range(n):
        start = i * seg_seconds
        out = os.path.join(workdir, f"seg_{i:03d}.m4a")
        cmd = ["ffmpeg", "-y", "-v", "error", "-i", path, "-ss", str(start),
               "-t", str(seg_seconds), "-ac", "1", "-ar", "16000", "-c:a", "aac", out]
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=600)
        except subprocess.CalledProcessError as e:
            die(f"ffmpeg 切段失败（段{i}）: {e.stderr.decode('utf-8', 'replace')[:200]}")
        segs.append((out, start))
    return segs


def transcribe(path: str, a, key: str, base: str) -> dict:
    """单段转写，返回 API 原始 JSON（json/verbose_json/srt/vtt 由调用方处理）。"""
    with open(path, "rb") as f:
        content = f.read()
    fname = os.path.basename(path)
    boundary = "----minimaxskill" + str(int(time.time() * 1000))

    def field(name, value):
        return (f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n'
                f'{value}\r\n').encode()

    data = b"".join([
        field("model", "asr-1.0"),
        field("response_format", a.format),
        field("timestamp_level", "word" if a.word_timestamps else "sentence"),
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{fname}"\r\n'
        f'Content-Type: application/octet-stream\r\n\r\n'.encode() + content + b"\r\n",
        f"--{boundary}--\r\n".encode(),
    ])
    headers = {"Authorization": f"Bearer {key}",
               "Content-Type": f"multipart/form-data; boundary={boundary}"}
    if a.language:
        headers["language"] = a.language
    req = urllib.request.Request(base + API_PATH, data=data, headers=headers, method="POST")
    body = None
    for attempt in (1, 2):
        try:
            with urllib.request.urlopen(req, timeout=600) as resp:
                body = resp.read()
            break
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:500]
            hint = ""
            if e.code == 400:
                hint = "（400: 常为超 500 秒或格式不支持；脚本已自动分段的话请反馈）"
            elif e.code == 413:
                hint = "（413: 超 50MB）"
            elif e.code in (401, 403):
                hint = "（401 类: Key 无效，或国内/海外站 Key 混用）"
            die(f"HTTP {e.code}: {detail[:300]} {hint}".strip())
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


def fmt_ts(seconds: float, comma: bool) -> str:
    ms = int(round(seconds * 1000))
    h, rem = divmod(ms, 3600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    sep = "," if comma else "."
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def shift_srt(text: str, offset: float) -> str:
    """把一段 SRT 的全部时间戳平移 offset 秒。"""
    def repl(m):
        t1 = sum(float(x.replace(",", ".")) * f for x, f in
                 zip(reversed(m.group(1).split(":")), [1, 60, 3600]))
        t2 = sum(float(x.replace(",", ".")) * f for x, f in
                 zip(reversed(m.group(2).split(":")), [1, 60, 3600]))
        return f"{fmt_ts(t1 + offset, True)} --> {fmt_ts(t2 + offset, True)}"
    return re.sub(r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})", repl, text)


def renumber_srt(text: str, start: int) -> tuple:
    """把一段 SRT 的 cue 序号从 start 起连续重编（各段 API 返回的序号都从 1 开始，
    直接拼接会重复）。返回 (新文本, 下一个可用序号)。"""
    blocks = re.split(r"\n\s*\n", text.strip())
    out, n = [], start
    for b in blocks:
        lines = b.strip("\n").split("\n")
        if not [ln for ln in lines if ln.strip()]:
            continue
        if lines[0].strip().isdigit():
            lines[0] = str(n)
        else:
            lines.insert(0, str(n))   # 缺序号行的 cue 补一个
        out.append("\n".join(lines))
        n += 1
    return "\n\n".join(out), n


def shift_vtt(text: str, offset: float) -> str:
    """把一段 WebVTT 的全部时间戳平移 offset 秒（小时位可省略，mm:ss.mmm 合法）。"""
    def repl(m):
        def to_sec(h, rest):
            return float(rest.split(":")[0]) * 60 + float(rest.split(":")[1]) + (float(h) * 3600 if h else 0)
        t1 = to_sec(m.group(1), m.group(2)) + offset
        t2 = to_sec(m.group(3), m.group(4)) + offset
        return f"{fmt_ts(t1, False)} --> {fmt_ts(t2, False)}"
    return re.sub(r"(?:(\d{2}):)?(\d{2}:\d{2}\.\d{3}) --> (?:(\d{2}):)?(\d{2}:\d{2}\.\d{3})", repl, text)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--audio", required=True, help="本地音频文件（mp3/aac/opus/wav/flac/m4a/ogg/aiff）")
    ap.add_argument("--format", dest="format", choices=["text", "srt", "vtt", "verbose-json"],
                    default="text", help="输出格式，默认 text 纯文本")
    ap.add_argument("-o", "--output", default="", help="输出文件；缺省按音频名与格式推")
    ap.add_argument("--language", default="", help="BCP-47 语言（zh/yue/en/ja/ko…共 20 种）；不传=自动混合")
    ap.add_argument("--word-timestamps", action="store_true",
                    help="词级时间戳（仅 verbose-json/srt/vtt 生效）")
    ap.add_argument("--base-url", default="", help=f"默认 {DEFAULT_BASE}；overseas={OVERSEAS_BASE}")
    ap.add_argument("--api-key", default="", help="API Key；传 - 从 stdin 读，默认自动解析环境变量")
    a = ap.parse_args()

    if not os.path.isfile(a.audio):
        die(f"音频文件不存在: {a.audio}")
    if not a.audio.lower().endswith(ALLOWED_EXT):
        die(f"格式不支持: 官方仅 {', '.join(ALLOWED_EXT)}（裸 PCM 不支持；其他容器 ffmpeg 转 wav）")
    size = os.path.getsize(a.audio)
    if size > MAX_SIZE:
        die(f"文件 {size/1024/1024:.1f}MB 超 50MB 限制（先压缩: ffmpeg -i in.wav -b:a 64k out.m4a）")

    key = find_api_key(a.api_key)
    if not key:
        die("缺少 API Key：platform.minimax.cn「账户管理→接口密钥」获取，export MINIMAX_API_KEY=...，"
            "或用 --api-key 传入（--api-key - 从 stdin 读）")
    base = resolve_base(a.base_url)

    dur = ffprobe_duration(a.audio)
    est_cost = dur / 3600 * PRICE_PER_HOUR
    print(f"音频 {dur:.0f}s（{size/1024:.0f}KB），格式 {a.format}，"
          f"预计计费 ≈{est_cost:.3f} 元（¥{PRICE_PER_HOUR}/小时）")

    need_split = dur > MAX_SECONDS
    if need_split:
        print(f"超过单次 {MAX_SECONDS}s 上限：ffmpeg 自动切为 ≤{SEGMENT_SECONDS}s 段逐段转写，"
              f"字幕时间轴按段起点偏移修正（说话人编号为段内独立口径）")

    api_format = {"text": "json", "verbose-json": "verbose_json"}.get(a.format, a.format)
    a.format = api_format

    out_path = a.output
    if not out_path:
        stem = os.path.splitext(a.audio)[0]
        out_path = {"json": stem + ".txt", "srt": stem + ".srt", "vtt": stem + ".vtt",
                    "verbose_json": stem + ".verbose.json"}.get(a.format, stem + ".txt")

    pieces = []  # (api_json, 段起点秒)
    if not need_split:
        pieces.append((transcribe(a.audio, a, key, base), 0.0))
    else:
        with tempfile.TemporaryDirectory(prefix="minimax_asr_") as td:
            segs = split_audio(a.audio, SEGMENT_SECONDS, td)
            for i, (seg, start) in enumerate(segs, 1):
                print(f"  段{i}/{len(segs)} 转写中（起点 {start:.0f}s）…", file=sys.stderr)
                pieces.append((transcribe(seg, a, key, base), float(start)))

    # ── 拼装输出 ──
    if a.format == "json":
        text = "\n".join((p[0].get("text") or "").strip() for p in pieces)
        text = text.strip()
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        dur_total = sum(p[0].get("duration") or 0 for p in pieces)
        print(f"完成: {out_path}（音频 {dur_total:.0f}s，转写 {len(text)} 字）")
        print("── 转写内容 ──")
        print(text[:3000] + ("…" if len(text) > 3000 else ""))
    elif a.format in ("srt", "vtt"):
        chunks, next_num = [], 1
        for obj, start in pieces:
            if a.format == "srt":
                body, next_num = renumber_srt(shift_srt(obj.get("text") or "", start), next_num)
                chunks.append(body)
            else:
                chunks.append(shift_vtt(obj.get("text") or "", start))
        with open(out_path, "w", encoding="utf-8") as f:
            head = "WEBVTT\n\n" if a.format == "vtt" else ""
            f.write(head + "\n\n".join(c.strip() for c in chunks if c.strip()) + "\n")
        print(f"完成: {out_path}（{len(pieces)} 段拼接，时间轴偏移修正，cue 以空行分隔）")
    else:  # verbose_json
        merged = {"n_speakers": 0, "segments": []}
        if need_split:
            merged["per_part_note"] = "超长音频自动分段：speaker 编号为段内独立口径，时间轴已按段起点偏移"
        seg_id = 0
        for obj, start in pieces:
            merged["n_speakers"] += obj.get("n_speakers") or 0
            for s in (obj.get("segments") or []):
                seg_id += 1
                merged["segments"].append({
                    "id": seg_id,
                    "start": round((s.get("start") or 0) + start, 3),
                    "end": round((s.get("end") or 0) + start, 3),
                    "speaker": s.get("speaker"),
                    "text": s.get("text", ""),
                })
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)
        print(f"完成: {out_path}（{len(merged['segments'])} 段，说话人 {merged['n_speakers']} 个）")


if __name__ == "__main__":
    main()
