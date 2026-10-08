#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tts.py — MiniMax 海螺语音合成（T2A /v1/t2a_v2，api.minimax.cn，非流式）

用法:
  tts.py --text "大家好，欢迎来到 MiniMax 开放平台" --output out.wav
  tts.py --file script.txt --output out.wav        # 长文本自动分段（>2800 计费字符）逐段合成拼接
  tts.py --list-voices                            # 内置精选音色
  tts.py --list-voices --online                    # 在线拉取全部系统音色（327 个，30+ 语言）
  tts.py --text "..." --voice female-yujie --emotion sad --pitch -2 --output out.wav
  tts.py --text "..." --mix "male-qn-qingse:70,female-shaonv:30" --output out.wav   # 多音色混合(≤4)
  tts.py --file script.txt --dry-run               # 分段与请求体预览，不调 API
  tts.py --text "..." --pronunciation "燕少飞/(yan4)(shao3)(fei1)" --output out.wav  # 发音字典

选项:
  --voice NAME      音色 ID，默认 female-tianmei（内置表见 --list-voices；复刻音色直接传 ID）
  --mix SPEC        多音色混合 "id1:权重1,id2:权重2"（≤4 个，权重 [1,100]；与 --voice 互斥）
  --model NAME      speech-2.8-hd（默认，¥3.5/万字符）| speech-2.8-turbo（¥2/万字符）| speech-2.6/02 系列
  --emotion E       happy/sad/angry/fearful/disgusted/surprised/calm；fluent/whisper 仅 2.6 系列
  --speed F         语速 [0.5,2] 默认 1
  --vol F           音量 (0,10] 默认 1
  --pitch F         音调 [-12,12] 默认 0（半音）
  --language TAG    language_boost（auto/Chinese/English/...，默认不传）
  --pronunciation S 发音替换 "原文本/替换读音"，可多次（拼音带声调 (yan4) 格式）
  --format F        输出容器 wav（默认，多段拼接唯一支持）| mp3（单段直出）；其他格式 ffmpeg 本地转
  --api-key KEY     API Key；传 - 从 stdin 读（避免进 shell history）。默认自动解析，见 find_api_key
  --base-url URL    默认 https://api.minimax.cn；overseas = https://api.minimax.io
  --dry-run         打印分段与请求体预览后退出（不耗额度）

停顿标记: 文本中可内嵌 <#秒#>（0.01–99.99，两位小数，不可连续），如 "等一下<#0.5#>再说"。

健壮性: 多段合成逐段缓存于 <output>.parts/，中断后重跑同一命令自动跳过已完成段续传；
网络错误自动重试 1 次。计费口径（官方，2026-10 实测校准）: 仅汉字 = 2 字符，
全角标点/字母/数字/空格各 1 字符。

凭证: platform.minimax.cn「账户管理→接口密钥」的 Key，export MINIMAX_API_KEY=...
（minimax- 家族统一只认此变量；key 不打印、不落盘）。
"""

import argparse
import hashlib
import http.client
import json
import os
import re
import shutil
import socket
import struct
import sys
import time
import urllib.error
import urllib.request

DEFAULT_BASE = "https://api.minimax.cn"
OVERSEAS_BASE = "https://api.minimax.io"
API_PATH = "/v1/t2a_v2"
VOICE_PATH = "/v1/get_voice"

DEFAULT_VOICE = "female-tianmei"
MAX_TEXT = 10_000          # 官方单请求 text 硬上限（字符）
SEGMENT_LIMIT = 2_800      # 超过即分段的目标长度（官方 >3000 建议流式，非流式留余量）
SAMPLE_RATE = 24_000

# 模型 → (元/万计费字符, 说明)
MODELS = {
    "speech-2.8-hd":     (3.50, "最新（2026-01），支持 23 种语气词标签如 (laughs)/(sighs)"),
    "speech-2.8-turbo":  (2.00, "最新高速版"),
    "speech-2.6-hd":     (3.50, "历史版，emotion 额外支持 fluent/whisper"),
    "speech-2.6-turbo":  (2.00, "历史版"),
    "speech-02-hd":      (3.50, "历史版"),
    "speech-02-turbo":   (2.00, "历史版"),
}
EMOTIONS_ALL = {"happy", "sad", "angry", "fearful", "disgusted", "surprised", "calm",
                "fluent", "whisper"}
EMOTIONS_26_ONLY = {"fluent", "whisper"}

# 内置精选系统音色（官方 voice_id 全量 327 个见 --list-voices --online）
SYSTEM_VOICES = [
    ("female-tianmei", "甜美女声（默认）", "女，通用讲解/旁白"),
    ("female-shaonv", "少女", "女，年轻清亮"),
    ("female-yujie", "御姐", "女，成熟沉稳"),
    ("wumei_yujie", "妩媚御姐", "女，磁性低音"),
    ("male-qn-qingse", "青涩青年", "男，少年感"),
    ("male-qn-badao", "霸道青年", "男，强势坚定"),
    ("junlang_nanyou", "俊朗男友", "男，温柔亲和"),
    ("Chinese (Mandarin)_News_Anchor", "新闻女声", "女，播报"),
    ("lovely_girl", "萌萌女童", "童声"),
    ("cartoon_pig", "卡通猪小琪", "童趣角色"),
]

NETWORK_ERRORS = (urllib.error.URLError, http.client.IncompleteRead,
                  socket.timeout, ConnectionResetError, OSError)


def find_api_key(explicit: str) -> str:
    """解析顺序: --api-key（- 表示 stdin）→ 环境变量 MINIMAX_API_KEY →
    ~/.zshrc 里的同名 export（取最后生效的）。minimax- 家族统一只认此变量。"""
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
    print(f"tts.py: {msg}", file=sys.stderr)
    sys.exit(1)


def bill_chars(text: str) -> int:
    """官方计费口径（2026-10 实测校准，usage_characters=78 精确吻合）：
    仅 CJK 汉字 = 2 字符；全角标点/字母/数字/空格 = 1 字符。"""
    return sum(2 if 0x4E00 <= ord(c) <= 0x9FFF else 1 for c in text)


def split_text(text: str, limit: int = SEGMENT_LIMIT) -> list:
    """按计费字符长度切成 <=limit 的段。边界优先级: 换行 > 句末标点 > 逗号 > 硬切（回退空白）。"""
    if bill_chars(text) <= limit:
        return [text]
    def bc(s):
        return bill_chars(s)
    atoms = [a for a in re.split(r"(?<=[\n。！？!?；;.])", text) if a]
    refined = []
    for a in atoms:
        if bc(a) <= limit:
            refined.append(a)
            continue
        for b in re.split(r"(?<=[，,])", a):
            if bc(b) <= limit:
                refined.append(b)
            else:
                refined.extend(_hard_split(b, limit))
    segs, cur = [], ""
    for a in refined:
        if bc(cur) + bc(a) <= limit:
            cur += a
        else:
            if cur:
                segs.append(cur)
            cur = a
    if cur:
        segs.append(cur)
    return segs


def _hard_split(s: str, limit: int) -> list:
    if bill_chars(s) <= limit:
        return [s]
    # 逐步找最大可切前缀（汉字占 2，从中间试探）
    lo, hi = 1, len(s)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if bill_chars(s[:mid]) <= limit:
            lo = mid
        else:
            hi = mid - 1
    cut = s[:lo]
    sp = cut.rfind(" ")
    if 0 < sp:
        cut = s[:sp]
    return [cut] + _hard_split(s[len(cut):].lstrip(), limit)


def parse_wav(data: bytes):
    """解析 RIFF/WAVE 字节流 → (fmt_params, pcm_bytes)；块完整性校验，损坏抛 ValueError。"""
    if len(data) < 44 or data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise ValueError("不是合法的 WAV 字节流（RIFF/WAVE 头缺失）")
    pos, fmt, pcm = 12, None, None
    while pos + 8 <= len(data):
        cid = data[pos:pos + 4]
        size = struct.unpack("<I", data[pos + 4:pos + 8])[0]
        if pos + 8 + size > len(data):
            raise ValueError(f"WAV {cid!r} 块声明 {size}B 超出响应体（数据被截断）")
        body = data[pos + 8:pos + 8 + size]
        if cid == b"fmt " and fmt is None:
            if size < 16:
                raise ValueError(f"WAV fmt 块过短({size}B)")
            fmt = struct.unpack("<HHIIHH", body[:16])
        elif cid == b"data" and pcm is None:
            pcm = body
        pos += 8 + size + (size & 1)
    if not fmt or pcm is None:
        raise ValueError("WAV 缺少 fmt/data 块")
    return fmt, pcm


def write_wav(path: str, pcm: bytes, fmt) -> None:
    audio_format, channels, rate, _, _, bits = fmt
    byte_rate = rate * channels * bits // 8
    block_align = channels * bits // 8
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", 36 + len(pcm), b"WAVE", b"fmt ", 16,
        audio_format, channels, rate, byte_rate, block_align, bits,
        b"data", len(pcm),
    )
    with open(path, "wb") as f:
        f.write(header)
        f.write(pcm)


def check_error(obj: dict) -> None:
    br = obj.get("base_resp")
    if isinstance(br, dict) and br.get("status_code") not in (0, None):
        hint = {"1004": "鉴权失败：Key 无效，或国内/海外站 Key 混用（两站独立）",
                "1002": "触发限流，稍后重试", "1039": "TPM 超限，稍后重试或减小分段",
                "1042": "文本非法字符占比 >10%，检查输入", "2013": "参数无效（检查 voice/emotion/模型名）"}.get(
            str(br.get("status_code")), "")
        die(f"服务错误: base_resp.status_code={br.get('status_code')} {br.get('status_msg', '')} {hint}".strip())


def build_payload(seg: str, a) -> dict:
    payload = {
        "model": a.model,
        "text": seg,
        "output_format": "hex",
        # 官方: 用 timbre_weights 混音时 voice_id 留空，voice_setting 其余键仍有效
        "voice_setting": {"voice_id": a.voice},
        "audio_setting": {"sample_rate": SAMPLE_RATE, "format": a.format, "channel": 1},
    }
    vs = payload["voice_setting"]
    if a.speed != 1:
        vs["speed"] = a.speed
    if a.vol != 1:
        vs["vol"] = a.vol
    if a.pitch != 0:
        vs["pitch"] = a.pitch
    if a.emotion:
        vs["emotion"] = a.emotion
    if a.language:
        payload["language_boost"] = a.language
    if a.mix:
        payload["timbre_weights"] = [
            {"voice_id": vid.strip(), "weight": int(w)} for vid, w in a.mix
        ]
    if a.pronunciation:
        payload["pronunciation_dict"] = {"tone": a.pronunciation}
    return payload


def synth_segment(seg: str, a, key: str, base: str) -> bytes:
    """合成单段，返回音频字节流（按 a.format 容器）。"""
    url = base + API_PATH
    req = urllib.request.Request(
        url,
        data=json.dumps(build_payload(seg, a), ensure_ascii=False).encode("utf-8"),
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
    data = obj.get("data") or {}
    hex_audio = data.get("audio")
    if not hex_audio:
        die(f"data.audio 为空（status={data.get('status')}）: {json.dumps(obj, ensure_ascii=False)[:300]}")
    try:
        raw = bytes.fromhex(hex_audio)
    except ValueError as e:
        die(f"hex 音频解码失败: {e}")
    extra = obj.get("extra_info") or {}
    used = extra.get("usage_characters")
    if used is not None:
        print(f"  本段计费 {used} 字符", file=sys.stderr)
    return raw


def list_voices_online(key: str, base: str) -> None:
    req = urllib.request.Request(
        base + VOICE_PATH,
        data=json.dumps({"voice_type": "system"}).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            obj = json.loads(resp.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        die(f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:300]}")
    except NETWORK_ERRORS as e:
        die(f"网络错误: {e}")
    check_error(obj)
    voices = (obj.get("data") or {}).get("voices") or []
    if not voices:
        die(f"在线音色列表为空: {json.dumps(obj, ensure_ascii=False)[:300]}")
    print(f"共 {len(voices)} 个系统音色（在线全量；字段以官方返回为准）:")
    for v in voices:
        print(f"  {str(v.get('voice_id', '')):40s} {v.get('voice_name', '')}")
    sys.exit(0)


def list_voices_local() -> None:
    print(f"内置精选 {len(SYSTEM_VOICES)} 个中文音色（全量 327 个: --list-voices --online）:")
    for vid, name, desc in SYSTEM_VOICES:
        print(f"  {vid:40s} {name:8s} {desc}")
    print("复刻音色: minimax-tts-clone 复刻出的自定义 voice_id 直接传 --voice")
    sys.exit(0)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--list-voices", action="store_true", help="列出音色（--online 拉全量）")
    ap.add_argument("--online", action="store_true", help="与 --list-voices 连用，在线拉全量系统音色")
    ap.add_argument("--text")
    ap.add_argument("--file", help="从文件读文本（UTF-8）")
    ap.add_argument("--output")
    ap.add_argument("--voice", default=DEFAULT_VOICE,
                    help=f"音色 ID，默认 {DEFAULT_VOICE}；内置表见 --list-voices，复刻音色传 ID")
    ap.add_argument("--mix", default="",
                    help='多音色混合 "id1:w1,id2:w2"（≤4 个，权重 [1,100]；与 --voice 互斥）')
    ap.add_argument("--model", default="speech-2.8-hd", choices=sorted(MODELS))
    ap.add_argument("--emotion", choices=sorted(EMOTIONS_ALL))
    ap.add_argument("--speed", type=float, default=1.0, help="[0.5,2] 默认 1")
    ap.add_argument("--vol", type=float, default=1.0, help="(0,10] 默认 1")
    ap.add_argument("--pitch", type=float, default=0.0, help="[-12,12] 半音，默认 0")
    ap.add_argument("--language", default="", help="language_boost: auto/Chinese/English/…（默认不传）")
    ap.add_argument("--pronunciation", action="append", default=[],
                    metavar="原/替换", help='发音替换，可多次，如 "燕少飞/(yan4)(shao3)(fei1)"')
    ap.add_argument("--format", choices=["wav", "mp3"], default="wav",
                    help="输出容器，默认 wav（多段拼接唯一支持）；mp3 仅单段直出，其余格式 ffmpeg 本地转")
    ap.add_argument("--base-url", default="", help=f"默认 {DEFAULT_BASE}；overseas={OVERSEAS_BASE}")
    ap.add_argument("--api-key", default="", help="API Key；传 - 从 stdin 读，默认自动解析环境变量")
    ap.add_argument("--dry-run", action="store_true", help="打印分段与请求预览，不调 API（无需 --output）")
    a = ap.parse_args()

    if a.list_voices:
        key = ""
        if a.online:
            key = find_api_key(a.api_key)
            if not key:
                die("缺少 API Key（在线音色表需要）：export MINIMAX_API_KEY=... 或 --api-key 传入")
            list_voices_online(key, resolve_base(a.base_url))
        list_voices_local()

    # 参数校验
    if not 0.5 <= a.speed <= 2:
        die("--speed 取值范围 [0.5, 2]")
    if not 0 < a.vol <= 10:
        die("--vol 取值范围 (0, 10]")
    if not -12 <= a.pitch <= 12:
        die("--pitch 取值范围 [-12, 12]")
    if a.emotion and a.emotion in EMOTIONS_26_ONLY and not a.model.startswith("speech-2.6"):
        die(f"emotion={a.emotion} 仅 speech-2.6 系列支持（2.8 不支持 whisper/fluent）")
    mix = []
    if a.mix:
        for part in a.mix.split(","):
            if ":" not in part:
                die(f'--mix 格式应为 "id:权重"，收到: {part!r}')
            vid, w = part.rsplit(":", 1)
            if not w.isdigit() or not 1 <= int(w) <= 100:
                die(f"--mix 权重 [1,100]，收到: {w}")
            mix.append((vid, int(w)))
        if not 1 <= len(mix) <= 4:
            die("--mix 最多 4 个音色")
        a.voice = ""  # timbre_weights 模式下 voice_id 留空
        # 存 list-of-list（而非 tuple）：与缓存 meta.json 读回的 JSON 数组相等比较
        a.mix = [[vid, w] for vid, w in mix]
        for vid, _ in mix:
            print(f"混合音色: {vid}")

    text = a.text or ""
    if a.file:
        try:
            with open(a.file, encoding="utf-8") as f:
                text += f.read()
        except FileNotFoundError:
            die(f"输入文件不存在: {a.file}")
        except UnicodeDecodeError as e:
            die(f"输入文件不是 UTF-8（{e}）；先 iconv -f GBK -t UTF-8 转码")
    text = text.strip()
    if not text:
        die("没有可合成的文本（--text 或 --file 至少给一个）")

    segs = split_text(text)
    # 防御性断言：分段目标 2800 计费字符 << 官方单请求 10000 字符上限，恒应通过
    for i, s in enumerate(segs, 1):
        if len(s) >= MAX_TEXT:
            die(f"段{i} {len(s)} 字符仍超官方单请求上限 {MAX_TEXT}（分段逻辑异常，请反馈）")
    unit_price = MODELS[a.model][0]
    est = bill_chars(text) / 10_000 * unit_price
    print(f"文本 {len(text)} 字符（计费口径约 {bill_chars(text)}），模型 {a.model} → {len(segs)} 段"
          f"（>2800 计费字符即分段，官方单请求上限 {MAX_TEXT}），预计计费 ≈{est:.3f} 元")
    for i, s in enumerate(segs, 1):
        head = s[:30].replace("\n", " ")
        print(f"  段{i}: 计费 {bill_chars(s)} 字符 | {head}...")

    if a.dry_run:
        preview = build_payload(segs[0][:50] + "…", a)
        print(f"请求预览: POST {resolve_base(a.base_url)}{API_PATH}\n  {json.dumps(preview, ensure_ascii=False)}")
        sys.exit(0)

    if not a.output:
        die("缺少 --output 输出路径（--dry-run 预检无需此参数）")
    out_dir = os.path.dirname(os.path.abspath(a.output))
    if not os.path.isdir(out_dir):
        die(f"输出目录不存在: {out_dir}")

    key = find_api_key(a.api_key)
    if not key:
        die("缺少 API Key：platform.minimax.cn「账户管理→接口密钥」获取，export MINIMAX_API_KEY=...，"
            "或用 --api-key 传入（--api-key - 从 stdin 读）")
    base = resolve_base(a.base_url)

    if a.format == "mp3" and len(segs) > 1:
        print("多段合成强制 wav 容器（mp3 无法可靠拼接）；要 mp3 请合成后 ffmpeg 转", file=sys.stderr)
        a.format = "wav"

    fmt0 = None
    if len(segs) == 1:
        raw = synth_segment(segs[0], a, key, base)
        try:
            with open(a.output, "wb") as f:
                f.write(raw)
            if a.format == "wav":
                fmt0, _ = parse_wav(raw)
        except (ValueError, OSError) as e:
            die(f"写入失败: {e}")
    else:
        # 多段: 逐段 wav 缓存于 <output>.parts/，失败保留已计费段，重跑续传
        parts_dir = a.output + ".parts"
        meta = {"model": a.model, "voice": a.voice, "mix": a.mix, "speed": a.speed,
                "vol": a.vol, "pitch": a.pitch, "emotion": a.emotion,
                "language": a.language, "pronunciation": a.pronunciation,
                "md5": hashlib.md5(text.encode("utf-8")).hexdigest()}
        meta_path = os.path.join(parts_dir, "meta.json")
        try:
            old = {}
            if os.path.isfile(meta_path):
                try:
                    with open(meta_path, encoding="utf-8") as f:
                        old = json.load(f)
                except json.JSONDecodeError:
                    old = {}   # 缓存损坏视同无缓存，走清空重建
            if os.path.isdir(parts_dir) and {k: v for k, v in old.items() if k != "fmt"} != meta:
                shutil.rmtree(parts_dir)
                old = {}
                print(f"缓存参数变化，已清空旧缓存: {parts_dir}")
            os.makedirs(parts_dir, exist_ok=True)
            fmt0 = tuple(old["fmt"]) if isinstance(old.get("fmt"), list) else None
            if fmt0:
                meta["fmt"] = list(fmt0)
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta, f)
        except OSError as e:
            die(f"缓存目录创建失败: {e}")

        merged, done = b"", 0
        try:
            for i, seg in enumerate(segs, 1):
                pcm_path = os.path.join(parts_dir, f"{i:03d}.pcm")
                if os.path.isfile(pcm_path) and os.path.getsize(pcm_path) > 0:
                    with open(pcm_path, "rb") as f:
                        pcm = f.read()
                    print(f"  段{i}/{len(segs)} 缓存命中 ({len(pcm)/1024:.0f}KB)")
                else:
                    raw = synth_segment(seg, a, key, base)
                    try:
                        fmt, pcm = parse_wav(raw)
                    except ValueError as e:
                        die(f"段{i} 响应损坏: {e}")
                    if fmt0 is None:
                        fmt0 = fmt
                        try:
                            meta["fmt"] = list(fmt)
                            with open(meta_path, "w", encoding="utf-8") as f:
                                json.dump(meta, f)
                        except OSError as e:
                            die(f"缓存元数据写入失败: {e}")
                    elif fmt != fmt0:
                        die(f"段{i} 音频参数与首段不一致: {fmt} vs {fmt0}，中止拼接")
                    with open(pcm_path, "wb") as f:
                        f.write(pcm)
                    print(f"  段{i}/{len(segs)} 完成 ({len(pcm)/1024:.0f}KB PCM)")
                merged += pcm
                done = i
        except KeyboardInterrupt:
            die(f"用户中断: 已完成 {done}/{len(segs)} 段，缓存于 {parts_dir}，重跑同一命令自动续传")
        except SystemExit:
            print(f"  已完成 {done}/{len(segs)} 段缓存于 {parts_dir}，重跑同一命令自动续传", file=sys.stderr)
            raise
        if not fmt0:
            die("未取得任何段，无法拼接")
        try:
            write_wav(a.output, merged, fmt0)
            shutil.rmtree(parts_dir)
        except (OSError, ValueError) as e:
            die(f"写出失败: {e}（分段缓存仍在 {parts_dir}）")
    size_kb = os.path.getsize(a.output) / 1024
    rate = fmt0[2] if fmt0 else SAMPLE_RATE
    print(f"完成: {a.output} ({size_kb:.0f}KB, {a.model}, {rate}Hz)")


if __name__ == "__main__":
    main()
