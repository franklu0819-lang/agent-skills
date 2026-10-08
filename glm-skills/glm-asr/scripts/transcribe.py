#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""智谱 GLM-ASR（glm-asr-2512）：本地音频或 URL → 文字（直连智谱开放平台 API）。

单次请求硬限：wav/mp3、≤25MB、≤30 秒。本脚本自动处理：
  - 非 wav/mp3 或超 30 秒 → ffmpeg 统一转 wav 16k 单声道并按 --seg-seconds 分段
  - 分段间把上一段结果尾部作为 prompt 传入（官方推荐的上下文接力方式），保持跨段连贯
  - 热词表 --hotwords 提升专有名词/人名/代号识别率（≤100 个）
认证：环境变量 ZHIPU_API_KEY（glm- 家族统一只认此变量），
      未设置时解析 ~/.zshrc 里的 export（不读取、不存储、不落盘任何密钥）。
依赖：python3（标准库）、ffmpeg/ffprobe（超限或转码时）、curl（URL 输入时）。
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid

API_URL = os.environ.get("GLM_ASR_API_URL",
                         "https://open.bigmodel.cn/api/paas/v4/audio/transcriptions")
DEFAULT_MODEL = "glm-asr-2512"
MAX_SEGMENT_SECONDS = 29.0     # API 硬限 30s，留余量
DIRECT_PASS_SECONDS = 29.5     # ≤ 此时长且格式合规的输入跳过转码直传
MAX_FILE_BYTES = 24 * 1024 * 1024  # API 硬限 25MB，留余量
PROMPT_TAIL_CHARS = 500        # 分段接力取上一段结果尾部字数（官方建议全文 <8000 字）
RETRIES = 3                    # 429/5xx/网络错误退避重试次数
KEY_VARS = ["ZHIPU_API_KEY"]  # glm- 家族统一只认 ZHIPU_API_KEY

MIME = {".wav": "audio/wav", ".mp3": "audio/mpeg"}


def die(msg, code=1):
    print(f"错误: {msg}", file=sys.stderr)
    sys.exit(code)


def log(msg):
    print(msg, file=sys.stderr)


def resolve_api_key(explicit=""):
    """解析顺序: --api-key（- 表示 stdin，避免 key 进 shell history）→ 环境变量
    ZHIPU_API_KEY → ~/.zshrc 同名 export（取最后生效的）。
    glm- 家族统一只认 ZHIPU_API_KEY，与 glm-tts 的 find_api_key 同链。"""
    if explicit:
        if explicit == "-":
            return sys.stdin.read().strip()
        return explicit.strip()
    for var in KEY_VARS:
        v = os.environ.get(var, "").strip()
        if v:
            return v
    zshrc = os.path.expanduser("~/.zshrc")
    if os.path.isfile(zshrc):
        found = ""
        # key 是 ASCII，errors=replace 只影响无关行（如含中文注释的 zshrc）
        for line in open(zshrc, encoding="utf-8", errors="replace"):
            m = re.match(r'\s*export\s+(%s)=(?:"([^"]+)"|([^\s#]+))' % "|".join(KEY_VARS), line)
            if m:
                found = (m.group(2) or m.group(3) or "").strip()
        return found
    return ""


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def download(url, dest):
    log(f"下载 URL: {url}")
    r = sh(["curl", "-sSL", "--max-time", "300", "-o", dest, url])
    if r.returncode != 0 or not os.path.exists(dest) or os.path.getsize(dest) == 0:
        die(f"下载失败: {curl_err(r)}")


def curl_err(r):
    return (r.stderr or r.stdout or "").strip()[:300] or f"curl 退出码 {r.returncode}"


def probe_duration(path):
    r = sh(["ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "csv=p=0", path])
    try:
        return float(r.stdout.strip())
    except ValueError:
        return None


def fmt_ts(sec):
    sec = int(sec)
    h, rest = divmod(sec, 3600)
    m, s = divmod(rest, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def detect_silences(path):
    """返回 [(silence_start, silence_end), ...]，供切点对齐静音用（防切断词语）。"""
    r = sh(["ffmpeg", "-i", path, "-vn", "-af", "silencedetect=noise=-35dB:d=0.3",
            "-f", "null", "-"])
    starts = [float(x) for x in re.findall(r"silence_start:\s*([0-9.]+)", r.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end:\s*([0-9.]+)", r.stderr)]
    return list(zip(starts, ends))


def plan_cutpoints(duration, silences, seg_seconds):
    """贪心规划切点：目标每段 seg_seconds，切点优先取目标 ±4s 窗口内最近的静音中点
    （避免在词语中间硬切）；无静音可用则硬切。窗口夹在 [pos+5, pos+28.5] 保证
    段长始终 ≤29s（API 硬限 30s 留余量）。返回切点列表。"""
    cuts = []
    pos = 0.0
    while duration - pos > seg_seconds:
        target = pos + seg_seconds
        hard_lo, hard_hi = pos + 5.0, pos + MAX_SEGMENT_SECONDS - 0.5
        lo, hi = max(hard_lo, target - 4.0), min(hard_hi, target + 4.0)
        best = None
        for s, e in silences:
            mid = (s + e) / 2
            if lo <= mid <= hi and (best is None or abs(mid - target) < abs(best - target)):
                best = mid
        cut = best if best is not None else min(max(target, hard_lo), hard_hi)
        cuts.append(round(cut, 3))
        pos = cut
    return cuts


def extract_segment(src, a, b, dest):
    """从 src 抽取 [a, b) 转成 wav 16k 单声道。"""
    r = sh(["ffmpeg", "-y", "-v", "error", "-ss", f"{a:.3f}", "-i", src,
            "-t", f"{b - a:.3f}", "-vn", "-ac", "1", "-ar", "16000",
            "-acodec", "pcm_s16le", dest])
    return r.returncode == 0, r.stderr[:300]


def make_segments(src, workdir, seg_seconds):
    """返回 (分段路径列表, 各段起始偏移列表, 是否转码)。合规短输入直传原文件。"""
    ext = os.path.splitext(src)[1].lower()
    dur = probe_duration(src)
    if dur is not None and ext in MIME and dur <= DIRECT_PASS_SECONDS \
            and os.path.getsize(src) <= MAX_FILE_BYTES:
        return [src], [0.0], False
    if dur is None:
        die("ffprobe 无法读取音频时长（ffmpeg 未安装、文件损坏，或 URL 返回的不是音频内容）")
    if dur > DIRECT_PASS_SECONDS:
        reason = "超单次 30 秒上限"
    elif ext not in MIME:
        reason = "格式非 wav/mp3"
    else:
        reason = "文件超 25MB"
    silences = detect_silences(src)
    cuts = plan_cutpoints(dur, silences, seg_seconds)
    bounds = list(zip([0.0] + cuts, cuts + [dur]))
    aligned = sum(1 for c in cuts if any(s <= c <= e for s, e in silences))
    log(f"时长 {fmt_ts(dur)}（{reason}），转码分段 {len(bounds)} 段"
        f"（目标 {seg_seconds:g}s/段，{aligned}/{len(cuts)} 个切点对齐静音）...")
    segs, offsets = [], []
    for i, (a, b) in enumerate(bounds):
        dest = os.path.join(workdir, f"seg{i:04d}.wav")
        ok, err = extract_segment(src, a, b, dest)
        if not ok:
            die(f"ffmpeg 抽段失败 @ {a:.1f}s: {err}")
        sdur = probe_duration(dest)
        if sdur is not None and sdur > DIRECT_PASS_SECONDS + 0.5:
            die(f"第 {i + 1} 段实测 {sdur:.1f}s 超单次上限（分段逻辑异常，请反馈）")
        segs.append(dest)
        offsets.append(round(a, 2))
    if not segs:
        die("分段结果为空")
    return segs, offsets, True


def multipart(fields, file_path):
    """标准库手写 multipart/form-data；数组字段（hotwords）重复同名字段。"""
    boundary = uuid.uuid4().hex
    out = []
    for name, val in fields:
        if isinstance(val, list):
            for item in val:
                out.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{item}\r\n'.encode())
        else:
            out.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{val}\r\n'.encode())
    # 文件名仅留安全 ASCII（服务端只关心字节流；原名含中文/引号会破坏 Content-Disposition）
    fname = re.sub(r"[^A-Za-z0-9._-]", "_", os.path.basename(file_path)) or "audio.wav"
    mime = MIME.get(os.path.splitext(fname)[1].lower(), "application/octet-stream")
    out.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{fname}"\r\n'
               f'Content-Type: {mime}\r\n\r\n'.encode())
    with open(file_path, "rb") as f:
        out.append(f.read())
    out.append(f'\r\n--{boundary}--\r\n'.encode())
    return b"".join(out), f"multipart/form-data; boundary={boundary}"


def transcribe_segment(key, seg_path, model, prompt, hotwords, seg_label):
    fields = [("model", model), ("stream", "false"),
              ("request_id", uuid.uuid4().hex)]  # ≥6 字符，平台要求 UUID 风格
    if prompt:
        fields.append(("prompt", prompt))
    if hotwords:
        fields.append(("hotwords", hotwords))
    body, ctype = multipart(fields, seg_path)

    for attempt in range(1, RETRIES + 1):
        req = urllib.request.Request(
            API_URL, data=body, method="POST",
            headers={"Authorization": f"Bearer {key}", "Content-Type": ctype})
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                raw = resp.read().decode("utf-8", "replace")
            try:
                data = json.loads(raw)
            except ValueError:
                # 网关偶发返回 HTML 错误页等非 JSON，按可重试处理
                if attempt < RETRIES:
                    log(f"{seg_label} 响应非 JSON，{2 ** attempt}s 后重试（{attempt}/{RETRIES}）...")
                    time.sleep(2 ** attempt)
                    continue
                die(f"{seg_label} 响应非 JSON（已重试 {RETRIES} 次）: {raw[:200]}")
            text = data.get("text")
            if text is None:
                die(f"{seg_label} 响应缺少 text 字段: {json.dumps(data, ensure_ascii=False)[:300]}")
            return text, data.get("request_id", "")
        except urllib.error.HTTPError as e:
            body_txt = ""
            try:
                body_txt = e.read().decode()[:300]
            except Exception:
                pass
            if e.code in (429, 500, 502, 503, 504) and attempt < RETRIES:
                wait = 2 ** attempt
                log(f"{seg_label} HTTP {e.code}，{wait}s 后重试（{attempt}/{RETRIES}）...")
                time.sleep(wait)
                continue
            hint = {401: "API Key 无效或未开通智谱开放平台服务",
                    413: "请求体超限（分段异常？）"}.get(e.code, "")
            die(f"{seg_label} HTTP {e.code} {hint} {body_txt}")
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < RETRIES:
                wait = 2 ** attempt
                log(f"{seg_label} 网络错误（{e}），{wait}s 后重试...")
                time.sleep(wait)
                continue
            die(f"{seg_label} 网络错误（已重试 {RETRIES} 次）: {e}")
    die(f"{seg_label} 重试次数耗尽")  # 不可达，兜底


def main():
    ap = argparse.ArgumentParser(description="GLM-ASR 语音转文字（智谱 glm-asr-2512）")
    ap.add_argument("input", help="音频文件或 URL")
    ap.add_argument("-o", "--output", help="转写文本另存路径（stdout 始终输出）")
    ap.add_argument("--json", dest="json_out", help="完整结果单行 JSON 另存路径")
    ap.add_argument("--hotwords", help="热词表，逗号分隔（≤100 个），如 \"智谱,AutoGLM,潘家园\"")
    ap.add_argument("--seg-seconds", type=float, default=25.0,
                    help=f"长音频分段时长秒（默认 25，上限 {MAX_SEGMENT_SECONDS:.0f}）")
    ap.add_argument("--no-context", action="store_true",
                    help="关闭分段间 prompt 上下文接力")
    ap.add_argument("--keep-segments", action="store_true", help="保留分段临时文件（调试）")
    ap.add_argument("--model", default=DEFAULT_MODEL, help=f"模型编码（默认 {DEFAULT_MODEL}）")
    ap.add_argument("--api-key", default="",
                    help="API Key；传 - 从 stdin 读（避免进 shell history）。默认自动解析，见 resolve_api_key")
    args = ap.parse_args()

    if not (5 <= args.seg_seconds <= MAX_SEGMENT_SECONDS):
        die(f"--seg-seconds 需在 5~{MAX_SEGMENT_SECONDS:.0f} 之间")

    key = resolve_api_key(args.api_key)
    if not key:
        die(f"缺少 API Key：请在 bigmodel.cn「API Keys」页获取，export {' 或 '.join(KEY_VARS[:3])} "
            "或用 --api-key 传入（也支持写入 ~/.zshrc 自动解析）")

    hotwords = [w.strip() for w in args.hotwords.split(",") if w.strip()] if args.hotwords else []
    if len(hotwords) > 100:
        die("热词最多 100 个")

    started = time.time()
    workdir = tempfile.mkdtemp(prefix="glm-asr-")
    try:
        clean_ext = os.path.splitext(re.split(r"[?#]", args.input)[0])[1]
        src = os.path.join(workdir, "input" + (clean_ext if re.fullmatch(r"\.\w{1,5}", clean_ext) else ""))
        if re.match(r"^https?://", args.input):
            download(args.input, src)
        elif os.path.exists(args.input):
            src = os.path.abspath(args.input)
        else:
            die(f"文件不存在: {args.input}")

        segs, offsets, transcoded = make_segments(src, workdir, args.seg_seconds)
        total_dur = probe_duration(src) or 0.0
        log(f"共 {len(segs)} 段{'（已转码）' if transcoded else '（直传）'}"
            f"{'，热词 ' + str(len(hotwords)) + ' 个' if hotwords else ''}")

        texts, meta = [], []
        for i, seg in enumerate(segs, 1):
            label = f"[{i}/{len(segs)}]"
            prompt = (texts[-1][-PROMPT_TAIL_CHARS:] if texts and not args.no_context else "")
            log(f"{label} 转写中...")
            text, rid = transcribe_segment(key, seg, args.model, prompt, hotwords, label)
            texts.append(text)
            meta.append({"index": i, "offset_s": offsets[i - 1],
                         "file": os.path.basename(seg),
                         "text": text, "request_id": rid})
            log(f"{label} 完成（{len(text)} 字）")

        full = "".join(texts)
        print(full)
        if args.output:
            open(args.output, "w", encoding="utf-8").write(full + "\n")
        if args.json_out:
            result = {"ok": True, "model": args.model, "text": full,
                      "audio_duration_s": round(total_dur, 2),
                      "segments": meta, "hotwords": hotwords,
                      "context_relay": not args.no_context,
                      "elapsed_ms": int((time.time() - started) * 1000)}
            open(args.json_out, "w", encoding="utf-8").write(
                json.dumps(result, ensure_ascii=False))
    finally:
        if args.keep_segments:
            log(f"分段文件保留在 {workdir}")
        else:
            for f in os.listdir(workdir):
                try:
                    os.remove(os.path.join(workdir, f))
                except OSError:
                    pass
            os.rmdir(workdir)


if __name__ == "__main__":
    main()
