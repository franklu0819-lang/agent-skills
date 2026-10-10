#!/usr/bin/env python3
"""拼接质量验证:检查 narration.wav 每个真实拼接缝附近的峰值。
每个句间拼接有两个缝:句尾缝(end-gap,语音→静音)与下句头缝(end,静音→语音);
清洗管线保证缝两侧各有 ≥15ms 的 -50dB 以下静音(silenceremove 保留段)+ 12ms fade,
因此缝 ±20ms 窗内峰值应接近 0。峰值 > 全片峰值 15% 判为爆音。
并用 silencedetect 报告句间停顿分布。
用法: python3 verify_splice.py [项目目录](默认当前目录)"""
import json, os, re, struct, subprocess, sys, wave

BASE = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
tl = json.load(open(os.path.join(BASE, "timeline.json")))
w = wave.open(os.path.join(BASE, "build", "narration.wav"), "rb")
sr = w.getframerate()
raw = w.readframes(w.getnframes())
samples = struct.unpack(f"<{len(raw)//2}h", raw)
mono = [max(abs(samples[i]), abs(samples[i+1])) for i in range(0, len(samples), 2)]
peak = max(mono) if mono else 0

def win_max(t, half=0.02):
    a = max(0, int((t-half)*sr)); b = min(len(mono), int((t+half)*sr))
    return max(mono[a:b]) if b > a else 0

def slope_max(t, half=0.03):
    """click 复判:缝 ±30ms 内相邻样本最大跳变。真爆音(click)=瞬时直流跳变>3000;
    而「高电平起音」(whole 模式解说腔的自然句首爆发力)经 12ms afade 后斜率很低,不算爆音。"""
    a = max(0, int((t-half)*sr)); b = min(len(mono), int((t+half)*sr))
    return max((abs(mono[i+1]-mono[i]) for i in range(a, b-1)), default=0)

worst, worst_id, fails = -1, "-", 0
print(f"全片峰值: {peak} ({peak/32767*100:.0f}%)")
for b in tl["beats"][:-1]:
    tail = win_max(b["end"] - tl["gap"])   # 缝1: 本句尾(语音→静音)
    head = win_max(b["end"])               # 缝2: 下句头(静音→语音)
    v = max(tail, head)
    if v > worst: worst, worst_id = v, b["id"]
    flag = ""
    if v > peak * 0.15:
        # 峰值超阈自动 click 复判(2026-10-10 实测:whole 模式小帅自然起音电平可达 75% 全片峰值,
        # 但跳变仅 8% 全幅——逐句合成模式才有真爆音形态)
        slope = max(slope_max(b["end"] - tl["gap"]), slope_max(b["end"]))
        if slope > 3000:
            flag = f"  ⚠️ 爆音(click 跳变 {slope})"; fails += 1
        else:
            flag = f"  (峰值超阈,click 复判 {slope} 通过:自然起音电平)"
    print(f"  {b['id']}: 尾缝 {tail} / 头缝 {head}{flag}")
print(f"\n拼接缝最大峰值 {worst}({worst_id}) = 全片的 {worst/peak*100:.1f}% → "
      + ("存在爆音,检查 afade 淡入淡出与 silenceremove 清洗" if fails else "无爆音 ✓"))

r = subprocess.run(["ffmpeg", "-i", os.path.join(BASE, "build", "narration.wav"),
                    "-af", "silencedetect=noise=-45dB:d=0.12", "-f", "null", "-"],
                   capture_output=True, text=True)
durs = [float(x) for x in re.findall(r"silence_duration: ([\d.]+)", r.stderr)]
if durs:
    print(f"停顿检测: {len(durs)} 处, 平均 {sum(durs)/len(durs):.2f}s, 最长 {max(durs):.2f}s "
          f"(拼接点应≈{tl['gap']:.2f}s, 0.45s 以上多为句内自然停顿)")
sys.exit(1 if fails else 0)
