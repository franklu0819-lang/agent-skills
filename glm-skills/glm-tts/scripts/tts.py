#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tts.py — 智谱 GLM-TTS 语音合成（open.bigmodel.cn /paas/v4/audio/speech，非流式）

用法:
  tts.py --text "你好，欢迎来到智谱开放平台" --output out.wav
  tts.py --file script.txt --output out.wav     # 长文本自动分段（>900 字符；官方单请求硬上限 1024）
  tts.py --list-voices                          # 查看 7 个系统音色
  tts.py --text "..." --voice chuichui --speed 1.2 --volume 2 --output out.wav
  tts.py --file script.txt --dry-run            # 只打印分段与请求预览，不需要 --output，不调 API

选项:
  --voice NAME    音色（默认 tongtong 彤彤）。7 个系统音色见 --list-voices；复刻音色直接传 ID
  --speed F       语速 [0.5, 2]，默认 1.0（1.2 约为轻度加速，2 为两倍速）
  --volume F      音量 (0, 10]，默认 1.0
  --api-key KEY   API Key；传 - 从 stdin 读（避免进 shell history）。默认自动解析，见 find_api_key
  --dry-run       打印分段结果与真实请求体预览后退出（校验参数/分段，不耗额度）

健壮性: 多段合成逐段缓存于 <output>.parts/，中途失败（网络/Ctrl-C）后重跑同一命令自动跳过
已完成段续传，避免重复计费；拼接成功后缓存目录自动清理。网络类错误自动重试 1 次。

凭证: 智谱开放平台 bigmodel.cn 右上角个人中心「API Keys」页的 Key，export ZHIPU_API_KEY=...
（glm- 家族统一只认 ZHIPU_API_KEY；key 不打印、不落盘）。
计费: 0.03 元/千字符（2026-10 官方定价）。输出 24kHz wav；要 mp3 用 ffmpeg -i out.wav 转。
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

API_URL = "https://open.bigmodel.cn/api/paas/v4/audio/speech"
DEFAULT_VOICE = "tongtong"
MAX_INPUT = 1024          # 官方单次请求 input 硬上限（字符数）
SEGMENT_LIMIT = 900       # 超过即分段的目标长度（留余量，标点/空格计入）
SAMPLE_RATE_HINT = 24000  # 官方建议采样率

# 系统音色（voice 参数的枚举值，官方 2026-10 文档）
SYSTEM_VOICES = [
    ("tongtong", "彤彤", "女声，默认音色，标准普通话，通用讲解/旁白"),
    ("chuichui", "锤锤", "女声，活泼"),
    ("xiaochen", "小陈", "男声，沉稳"),
    ("jam", "Jam", "动动动物圈 jam 音色，童趣"),
    ("kazi", "Kazi", "动动动物圈 kazi 音色，童趣"),
    ("douji", "豆吉", "动动动物圈 douji 音色，童趣"),
    ("luodo", "罗多", "动动动物圈 luodo 音色，童趣"),
]

# 网络类异常（读响应阶段抛出，urllib 不包装，需显式捕获）
NETWORK_ERRORS = (urllib.error.URLError, http.client.IncompleteRead,
                  socket.timeout, ConnectionResetError, OSError)


def find_api_key(explicit: str) -> str:
    """解析顺序: --api-key（- 表示 stdin）→ 环境变量 ZHIPU_API_KEY →
    ~/.zshrc 里的同名 export（取最后生效的）。glm- 家族统一只认 ZHIPU_API_KEY。"""
    if explicit:
        if explicit == "-":
            return sys.stdin.read().strip()
        return explicit
    names = ("ZHIPU_API_KEY",)
    for var in names:
        if os.environ.get(var):
            return os.environ[var]
    zshrc = os.path.expanduser("~/.zshrc")
    if os.path.isfile(zshrc):
        found = ""
        # key 都是 ASCII，errors=replace 只影响无关行（如含中文注释的 zshrc）
        for line in open(zshrc, encoding="utf-8", errors="replace"):
            m = re.match(r'\s*export\s+(%s)=(?:"([^"]+)"|([^\s#]+))' % "|".join(names), line)
            if m:
                found = m.group(2) or m.group(3)
        return found
    return ""


def die(msg: str) -> None:
    print(f"tts.py: {msg}", file=sys.stderr)
    sys.exit(1)


def list_voices() -> None:
    print(f"共 {len(SYSTEM_VOICES)} 个系统音色（voice 参数值 + 复刻音色直接传 ID）:")
    for vid, name, desc in SYSTEM_VOICES:
        print(f"  {vid:10s} {name:4s} {desc}")
    print("复刻音色: 在 bigmodel.cn 控制台声音复刻页获取 ID 后 --voice <ID> 直传")
    sys.exit(0)


def read_text(path: str) -> str:
    """读输入文件，UTF-8 优先；GBK 等其他编码给出转码提示而非 traceback。"""
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        die(f"输入文件不存在: {path}")
    except UnicodeDecodeError as e:
        die(f"输入文件不是 UTF-8 编码（{e}）；请先转码: iconv -f GBK -t UTF-8 {path} > {path}.utf8")


def split_text(text: str, limit: int = SEGMENT_LIMIT) -> list:
    """把长文本切成 <=limit 的段。原子化边界优先级: 换行 > 句末标点(。！？!?；;.) >
    逗号(，,) > 最近空白 > 硬切。英文句号计入边界，避免在单词中间切断。"""
    if len(text) <= limit:
        return [text]
    atoms = [a for a in re.split(r"(?<=[\n。！？!?；;.])", text) if a]
    refined = []
    for a in atoms:
        if len(a) <= limit:
            refined.append(a)
            continue
        for b in re.split(r"(?<=[，,])", a):
            if len(b) <= limit:
                refined.append(b)
            else:
                refined.extend(_hard_split(b, limit))
    segs, cur = [], ""
    for a in refined:
        if len(cur) + len(a) <= limit:
            cur += a
        else:
            if cur:
                segs.append(cur)
            cur = a
    if cur:
        segs.append(cur)
    return segs


def _hard_split(s: str, limit: int) -> list:
    """无标点长串：从 limit 处回退到最近的空白处切，避免切断英文单词；中文无空白则真硬切。"""
    if len(s) <= limit:
        return [s]
    cut = s.rfind(" ", 0, limit + 1)
    if cut <= 0:
        cut = limit
    return [s[:cut]] + _hard_split(s[cut:].lstrip(), limit)


def parse_wav(data: bytes):
    """解析 RIFF/WAVE 字节流，返回 (fmt_params, pcm_bytes)。
    fmt_params = (audio_format, channels, sample_rate, byte_rate, block_align, bits)。
    校验块完整性（fmt 块 >=16B、data 块声明长度不超出响应体），损坏按 ValueError 抛出。"""
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
                raise ValueError(f"WAV fmt 块过短({size}B)，响应损坏")
            fmt = struct.unpack("<HHIIHH", body[:16])
        elif cid == b"data" and pcm is None:
            pcm = body
        pos += 8 + size + (size & 1)  # 块按 2 字节对齐
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


def build_payload(seg: str, voice: str, speed: float, volume: float) -> dict:
    """构造请求体；speed/volume 为默认值 1.0 时不发送（与官方默认等价）。dry-run 预览复用。"""
    payload = {"model": "glm-tts", "input": seg, "voice": voice, "response_format": "wav"}
    if speed != 1.0:
        payload["speed"] = speed
    if volume != 1.0:
        payload["volume"] = volume
    return payload


def synth_segment(seg: str, voice: str, speed: float, volume: float, key: str) -> bytes:
    """合成单段，返回 wav 字节流。HTTP/业务错误直接 die（带官方 code/message）；
    网络类错误退避 2s 重试 1 次。"""
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(build_payload(seg, voice, speed, volume), ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    body = None
    for attempt in (1, 2):
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                body = resp.read()
            break
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:500]
            try:
                err = json.loads(detail)
                err = err.get("error") if isinstance(err, dict) else None
                err = err if isinstance(err, dict) else {}
                hint = f"code={err.get('code')} {err.get('message', '')}".strip()
            except json.JSONDecodeError:
                hint = detail
            extra = "（401/1002 类: Key 无效或格式错，应为 bigmodel.cn「API Keys」页的 <id>.<secret> 形式 Key）" \
                if e.code in (401, 403) or str(err.get("code")) == "1002" else ""
            die(f"HTTP {e.code}: {hint} {extra}".strip())
        except NETWORK_ERRORS as e:
            if attempt == 2:
                die(f"网络错误（已重试 1 次仍失败）: {e}")
            print(f"  网络错误 {e}，2s 后重试…", file=sys.stderr)
            time.sleep(2)
    if not body:
        die("未取得响应体")
    # 成功时响应体是二进制音频；若返回 JSON 说明是业务层错误（如 voice 不存在）
    if body[:1] in (b"{", b"["):
        try:
            obj = json.loads(body.decode("utf-8", "replace"))
        except json.JSONDecodeError:
            die(f"响应非音频且非 JSON: {body[:200]!r}")
        err = obj.get("error") if isinstance(obj, dict) else None
        if isinstance(err, dict):
            die(f"服务返回错误: code={err.get('code')} {err.get('message', '')}（voice={voice}）")
        die(f"响应为 JSON 而非音频: {body[:200]!r}")
    if len(body) < 100:
        die(f"音频数据异常偏小({len(body)}B)，请检查 voice 与文本")
    return body


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--list-voices", action="store_true", help="列出系统音色，不合成")
    ap.add_argument("--text")
    ap.add_argument("--file")
    ap.add_argument("--output")
    ap.add_argument("--voice", default=DEFAULT_VOICE,
                    help=f"音色，默认 {DEFAULT_VOICE}；系统音色见 --list-voices，复刻音色传 ID")
    ap.add_argument("--speed", type=float, default=1.0, help="语速 [0.5, 2]，默认 1.0")
    ap.add_argument("--volume", type=float, default=1.0, help="音量 (0, 10]，默认 1.0")
    ap.add_argument("--api-key", default="",
                    help="API Key；传 - 从 stdin 读（避免进 shell history），默认自动解析环境变量")
    ap.add_argument("--dry-run", action="store_true", help="打印分段与请求预览，不调 API（无需 --output）")
    a = ap.parse_args()

    if a.list_voices:
        list_voices()

    if not 0.5 <= a.speed <= 2:
        die("--speed 取值范围 [0.5, 2]")
    if not 0 < a.volume <= 10:
        die("--volume 取值范围 (0, 10]")

    text = a.text or (read_text(a.file) if a.file else "")
    text = text.strip()
    if not text:
        die("没有可合成的文本（--text 或 --file 至少给一个）")

    segs = split_text(text)
    total_charge = len(text) / 1000 * 0.03
    print(f"文本 {len(text)} 字符 → {len(segs)} 段（>900 即分段，官方单请求硬上限 {MAX_INPUT}），"
          f"voice={a.voice}, speed={a.speed}, volume={a.volume}，预计计费 ≈{total_charge:.3f} 元")
    for i, s in enumerate(segs, 1):
        head = s[:30].replace("\n", " ")
        print(f"  段{i}: {len(s)} 字符 | {head}...")

    if a.dry_run:
        preview = build_payload(segs[0][:50] + "…", a.voice, a.speed, a.volume)
        print(f"请求预览: POST {API_URL}\n  {json.dumps(preview, ensure_ascii=False)}")
        sys.exit(0)

    if not a.output:
        die("缺少 --output 输出路径（--dry-run 预检无需此参数）")
    out_dir = os.path.dirname(os.path.abspath(a.output))
    if not os.path.isdir(out_dir):
        die(f"输出目录不存在: {out_dir}")

    key = find_api_key(a.api_key)
    if not key:
        die("缺少 API Key：请在 bigmodel.cn「API Keys」页获取，export ZHIPU_API_KEY=...，"
            "或用 --api-key 传入（--api-key - 从 stdin 读）")

    if len(segs) == 1:
        # 单段: 服务端 wav 校验后原样落盘
        wav = synth_segment(segs[0], a.voice, a.speed, a.volume, key)
        try:
            fmt0, _ = parse_wav(wav)
            with open(a.output, "wb") as f:
                f.write(wav)
        except (ValueError, OSError) as e:
            die(f"写入失败: {e}")
    else:
        # 多段: 逐段 PCM 缓存于 <output>.parts/，失败保留已计费段，重跑续传
        parts_dir = a.output + ".parts"
        meta = {"voice": a.voice, "speed": a.speed, "volume": a.volume,
                "md5": hashlib.md5(text.encode("utf-8")).hexdigest()}
        meta_path = os.path.join(parts_dir, "meta.json")
        try:
            old = {}
            if os.path.isfile(meta_path):
                with open(meta_path, encoding="utf-8") as f:
                    old = json.load(f)
            # 核心参数比较时排除 fmt（首段成功后才写入），否则续跑恒判不一致而误清缓存
            if os.path.isdir(parts_dir) and {k: v for k, v in old.items() if k != "fmt"} != meta:
                shutil.rmtree(parts_dir)
                old = {}
                print(f"缓存参数变化，已清空旧缓存: {parts_dir}")
            os.makedirs(parts_dir, exist_ok=True)
            fmt0 = tuple(old["fmt"]) if isinstance(old.get("fmt"), list) else None
            if fmt0:
                meta["fmt"] = list(fmt0)  # 回写时保留 fmt，供再中断后的续跑恢复
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
                    wav = synth_segment(seg, a.voice, a.speed, a.volume, key)
                    try:
                        fmt, pcm = parse_wav(wav)
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
            die(f"用户中断: 已完成 {done}/{len(segs)} 段，缓存于 {parts_dir}，"
                f"重跑同一命令自动续传")
        except SystemExit:
            print(f"  已完成 {done}/{len(segs)} 段缓存于 {parts_dir}，重跑同一命令自动续传",
                  file=sys.stderr)
            raise
        if not fmt0:
            die("未取得任何段，无法拼接")
        try:
            write_wav(a.output, merged, fmt0)
            shutil.rmtree(parts_dir)
        except (OSError, ValueError) as e:
            die(f"写出失败: {e}（分段缓存仍在 {parts_dir}）")
    print(f"完成: {a.output} ({os.path.getsize(a.output)/1024:.0f}KB, {a.voice}, {fmt0[2]}Hz)")


if __name__ == "__main__":
    main()
