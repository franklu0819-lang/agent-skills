#!/usr/bin/env python3
"""批量 TTS 配音 + 音频清洗 + 测时长,生成 timeline.json(声画同步唯一权威时间轴)。
- TTS 产物:audio/beats/*.mp3(已有则跳过,可断点续跑)
- 清洗产物:audio/clean/*.wav —— 裁掉每句头尾静音(48kHz 立体声),句间只留 beat_gap
- timeline 基于清洗后时长,字幕/视频帧数/动画全部与之对齐"""
import json, subprocess, os, sys, math

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# ark-tts 技能脚本路径(可用 TTS_SH 覆盖);另依赖 ark-asr 做 ASR 终验(见 asr_check.py)
TTS = os.environ.get("TTS_SH", "/Users/leo/.agents/skills/ark-tts/scripts/tts.py")

def assert_no_placeholder(text, bid):
    """占位符守卫:模板占位文本直接送 TTS 会烧钱并产出废音频,发现即拒绝。"""
    marks = ["XXX", "（第", "（概念", "（数字", "（金句", "（可操作", "（抛出", "（机制", "（画面", "（一句话"]
    if any(m in text for m in marks) or text.strip().startswith("（"):
        print(f"[PLACEHOLDER] {bid} 仍是模板占位文案: {text[:40]}... 请先完成 script.json 替换", flush=True)
        sys.exit(1)

# 裁头尾静音:阈值 -50dB,两端各保留 15ms;反转技巧实现"裁尾"
CLEAN_FILTER = (
    "aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
    "silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.015,"
    "areverse,"
    "silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.015,"
    "areverse"
)

script = json.load(open(f"{BASE}/script.json"))
gap = script["beat_gap"]
fps = script["fps"]
os.makedirs(f"{BASE}/audio/clean", exist_ok=True)

beats = []
t = 0.0
for scene in script["scenes"]:
    for beat in scene["beats"]:
        mp3 = f"{BASE}/audio/beats/{beat['id']}.mp3"
        assert_no_placeholder(beat["text"], beat["id"])
        if not (os.path.exists(mp3) and os.path.getsize(mp3) > 1000):
            cmd = ["python3", TTS, "--text", beat["text"],
                   "--speaker", script["speaker"]]
            if beat.get("language"):
                cmd += ["--language", beat["language"]]
            cmd += ["--output", mp3]
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0 or not os.path.exists(mp3):
                print(f"[FAIL] {beat['id']}: {r.stdout} {r.stderr}", flush=True)
                sys.exit(1)
        clean = f"{BASE}/audio/clean/{beat['id']}.wav"
        r = subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", mp3, "-af", CLEAN_FILTER,
             "-c:a", "pcm_s16le", "-ar", "48000", clean],
            capture_output=True, text=True)
        if r.returncode != 0:
            print(f"[CLEAN FAIL] {beat['id']}: {r.stderr}", flush=True)
            sys.exit(1)
        p = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", clean],
            capture_output=True, text=True)
        dur = float(p.stdout.strip())
        seg = dur + gap
        beats.append({
            "id": beat["id"], "scene": scene["id"], "text": beat["text"],
            "audio": f"audio/beats/{beat['id']}.mp3",
            "clean": f"audio/clean/{beat['id']}.wav",
            "audio_dur": round(dur, 3),
            "start": round(t, 3), "end": round(t + seg, 3),
        })
        t += seg
        print(f"[ok] {beat['id']}  clean={dur:.2f}s  start={beats[-1]['start']:.2f}", flush=True)

total = round(t, 3)
timeline = {
    "fps": fps, "resolution": script["resolution"], "gap": gap,
    "beats": beats, "total": total, "frames": math.ceil(total * fps),
}
json.dump(timeline, open(f"{BASE}/timeline.json", "w"), ensure_ascii=False, indent=2)
print(f"\n== total {total:.2f}s, {timeline['frames']} frames ==")
