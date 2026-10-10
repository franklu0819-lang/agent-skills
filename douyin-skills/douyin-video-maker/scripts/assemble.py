#!/usr/bin/env python3
"""组装:narration.wav 拼接 → final.srt 字幕 → 与 silent.mp4 合成 final.mp4(可选 BGM 闪避混音)。
可重复执行。前置:timeline.json、audio/beats/*.mp3、build/silent.mp4 已就绪。
用法:
  python3 tools/assemble.py                    # 常规合成
  python3 tools/assemble.py --bgm bgm.mp3      # 混入 BGM(自动循环裁齐片长,解说闪避)
  python3 tools/assemble.py --bgm bgm.mp3 --bgm-vol 0.3"""
import argparse, json, os, re, subprocess, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EP = json.load(open(f"{BASE}/script.json"))

# 成片命名:合集名(collection.json.name) + 期号 + slug;无合集配置时退回 script.json.collection
col_path = f"{BASE}/../collection.json"
col = json.load(open(col_path)) if os.path.exists(col_path) else {}
col_name = col.get("name") or EP.get("collection") or "抖音视频"
OUT_NAME = f"{col_name}-第{EP['episode']:02d}期-{EP.get('slug', 'untitled')}.mp4"

tl = json.load(open(f"{BASE}/timeline.json"))
beats = tl["beats"]
GAP = tl["gap"]

# 竖屏 1080x1920 字幕:烧录用 final.ass(自带 PlayRes=视频分辨率,坐标即像素,不受 libass 对 SRT 的
# 384x288 默认坐标系影响——SRT+force_style 的 MarginV>288 会把字幕推出画面,2026-10 实测踩坑)
ASS_FONT = "Hiragino Sans GB"
ASS_FONTSIZE = 44      # PlayRes=视频尺寸时即像素字号
ASS_MARGIN_V = 300     # 字幕底边距视频底部像素(底部避让抖音 UI,底边落在约 y1620)

# ---------- 1. 音频拼接:清洗后每句首尾 12ms 淡入淡出(防拼接爆音)+ gap 静音 → concat ----------
inputs = []
for b in beats:
    inputs += ["-i", f"{BASE}/{b['clean']}"]
filters = []
for i in range(len(beats)):
    filters.append(
        f"[{i}:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
        f"afade=t=in:st=0:d=0.012,areverse,afade=t=in:st=0:d=0.012,areverse,"
        f"apad=pad_dur={GAP}[a{i}]")
mix = "".join(f"[a{i}]" for i in range(len(beats))) + f"concat=n={len(beats)}:v=0:a=1[out]"
cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(filters) + ";" + mix,
       "-map", "[out]", "-c:a", "pcm_s16le", "-ar", "48000", f"{BASE}/build/narration.wav"]
r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode != 0:
    print(r.stderr[-2000:]); sys.exit(1)
print("narration.wav ok")

# ---------- 2. 字幕:每句按标点拆短条,时长按字符数比例分配 ----------
STRIP = r"[,，。？?！!、;；]+$"   # 尾标点剥离,半角/全角对称(拆句字符集的补集)

def split_clauses(text):
    out, buf = [], ""
    for ch in text:
        buf += ch
        if ch in ",，?？!！。、":
            c = re.sub(STRIP, "", buf.strip())
            buf = ""
            if c: out.append(c)
    if buf.strip():
        out.append(re.sub(STRIP, "", buf.strip()))
    return out

def fmt(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = int(t % 60); ms = int(round(t % 1 * 1000))
    if ms == 1000: s += 1; ms = 0
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

srt = []
for b in beats:
    cls = split_clauses(b["text"])
    weights = [len(c) for c in cls]
    total_w = sum(weights)
    t = b["start"]
    for c, w in zip(cls, weights):
        dur = b["audio_dur"] * w / total_w
        srt.append((t, t + dur - 0.05, c))
        t += dur

with open(f"{BASE}/final.srt", "w") as f:
    for i, (a, z, c) in enumerate(srt, 1):
        f.write(f"{i}\n{fmt(a)} --> {fmt(z)}\n{c}\n\n")
print(f"final.srt ok ({len(srt)} 条)")

def fmt_ass(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = int(t % 60); cs = int(round(t % 1 * 100))
    if cs == 100: s += 1; cs = 0
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

W, H = tl["resolution"]
ass_header = (
    "[Script Info]\nScriptType: v4.00+\n"
    f"PlayResX: {W}\nPlayResY: {H}\nWrapStyle: 0\nScaledBorderAndShadow: yes\n\n"
    "[V4+ Styles]\n"
    "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
    "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
    "Alignment, MarginL, MarginR, MarginV, Encoding\n"
    f"Style: Douyin,{ASS_FONT},{ASS_FONTSIZE},&H00FFFFFF,&H000000FF,&HA0000000,&HA0000000,"
    f"0,0,0,0,100,100,0,0,1,2.2,0,2,60,60,{ASS_MARGIN_V},1\n\n"
    "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
)
with open(f"{BASE}/final.ass", "w") as f:
    f.write(ass_header)
    for a, z, c in srt:
        f.write(f"Dialogue: 0,{fmt_ass(a)},{fmt_ass(z)},Douyin,,0,0,0,,{c}\n")
print(f"final.ass ok ({len(srt)} 条, PlayRes {W}x{H})")

# ---------- 3. 最终合成:烧录字幕 + 混流(+ 可选 BGM 循环/闪避) ----------
ap = argparse.ArgumentParser()
ap.add_argument("--bgm", default="", help="BGM 音频文件路径(自动循环并裁齐片长)")
ap.add_argument("--bgm-vol", type=float, default=0.25, help="BGM 基础音量(0~1,默认 0.25)")
args, _ = ap.parse_known_args()

cmd = ["ffmpeg", "-y", "-i", "build/silent.mp4", "-i", "build/narration.wav"]
if args.bgm:
    dur = tl["total"]
    # BGM 无限循环→裁齐片长→降基础音量;解说作 sidechain 把 BGM 压低(闪避),再混音
    fc = (
        f"[2:a]aloop=loop=-1:size=2000000000,atrim=0:{dur},"
        f"aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,volume={args.bgm_vol}[bg];"
        f"[1:a]asplit=2[na][nk];"
        f"[bg][nk]sidechaincompress=threshold=0.02:ratio=6:attack=100:release=500[bgd];"
        f"[bgd][na]amix=inputs=2:duration=first:normalize=0[aout]"
    )
    cmd += ["-i", args.bgm, "-filter_complex", fc, "-map", "0:v", "-map", "[aout]"]
else:
    cmd += ["-map", "0:v", "-map", "1:a"]
cmd += ["-vf", "subtitles=final.ass",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest",
        OUT_NAME]
r = subprocess.run(cmd, capture_output=True, text=True, cwd=BASE)
if r.returncode != 0:
    print(r.stderr[-2000:]); sys.exit(1)
p = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration,size",
                    "-of", "json", f"{BASE}/{OUT_NAME}"], capture_output=True, text=True)
if p.returncode != 0 or not p.stdout.strip():
    print(f"⚠️ 成片已写出但 ffprobe 校验失败: {p.stderr[-300:]}"); sys.exit(1)
info = json.loads(p.stdout)["format"]
print(f"{OUT_NAME} ok  {float(info['duration']):.1f}s  {int(info['size'])/1e6:.1f}MB")
