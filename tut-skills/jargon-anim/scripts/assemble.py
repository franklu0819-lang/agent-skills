#!/usr/bin/env python3
"""组装:narration.wav 拼接 → final.srt 字幕 → 与 silent.mp4 合成 final.mp4
可重复执行。前置:timeline.json、audio/beats/*.mp3、build/silent.mp4 已就绪。"""
import json, os, re, subprocess, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EP = json.load(open(f"{BASE}/script.json"))
OUT_NAME = f"AI黑话图鉴-EP{EP['episode']:02d}-{EP.get('slug', 'untitled')}.mp4"
tl = json.load(open(f"{BASE}/timeline.json"))
beats = tl["beats"]
GAP = tl["gap"]

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

# ---------- 3. 最终合成:烧录字幕 + 混流 ----------
style = ("FontName=PingFang SC,FontSize=15,PrimaryColour=&H00FFFFFF&,"
         "OutlineColour=&HA0000000&,BorderStyle=1,Outline=1.3,Shadow=0,MarginV=40")
cmd = ["ffmpeg", "-y", "-i", "build/silent.mp4", "-i", "build/narration.wav",
       "-vf", f"subtitles=final.srt:force_style='{style}'",
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
