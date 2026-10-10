#!/usr/bin/env python3
"""批量 TTS 配音 + 音频清洗 + 测时长,生成 timeline.json(声画同步唯一权威时间轴)。
两种合成模式(--tts-mode,默认 auto):
  whole    整段一次合成 → 按停顿 DP 对齐切句。韵律连贯(模型统筹全篇语速),推荐解说腔音色
           (影视解说小帅 BV411 逐句合成时各句自定快慢,实测语速极差 41%,整段模式消除)。
           缓存 = audio/whole.mp3(改词必须删它重跑)。
  per-beat 逐句合成(逐句时间轴最精确,适合韵律平稳音色/断点续跑),缓存 = audio/beats/XX.mp3。
  auto     BV 前缀(剪映同款解说系,韵律起伏大)→whole;其余(v3 的 2.0 库/复刻)→per-beat。
- 清洗产物:audio/clean/*.wav —— 裁掉每句头尾静音(48kHz 立体声),句间只留 beat_gap
- timeline 基于清洗后时长,字幕/视频帧数/动画全部与之对齐
- 音色/语速解析顺序:script.json(本期覆盖) > ../collection.json(合集) > 内置默认"""
import argparse, json, math, os, re, subprocess, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 双引擎按音色前缀分派(2026-10-10 实测):
#   BV 开头(剪映同款 1.0 大模型库,如影视解说小帅 BV411)→ 本技能 tts_v1.py(v1 HTTP API)
#   其余(uranus 2.0 库/复刻)→ ark-tts 技能 tts.py(v3 unidirectional,可用 TTS_SH 覆盖)
TTS = os.environ.get("TTS_SH", "/Users/leo/.agents/skills/ark-tts/scripts/tts.py")
TTS_V1 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tts_v1.py")
DEFAULT_SPEAKER = "BV411_streaming"  # 影视解说小帅(剪映同款,v1 引擎),用户 2026-10-10 定为默认
DEFAULT_SPEED = 0  # 语速百分比(v3 [-50,100];v1 内部换算 speed_ratio),抖音口播合集常配 5~15 轻加速

def assert_no_placeholder(text, bid):
    """占位符守卫:模板占位文本直接送 TTS 会烧钱并产出废音频,发现即拒绝。"""
    marks = ["XXX", "（钩子", "（概念", "（要点", "（例子", "（数字", "（金句", "（引导",
             "（机制", "（画面", "（一句话", "（第一", "（第二"]
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

def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)

# ---------------- per-beat:逐句合成 ----------------
def synth_per_beat(beat, speaker, speed):
    mp3 = f"{BASE}/audio/beats/{beat['id']}.mp3"
    if os.path.exists(mp3) and os.path.getsize(mp3) > 1000:
        return mp3
    if speaker.upper().startswith("BV"):
        cmd = ["python3", TTS_V1, "--text", beat["text"],
               "--speaker", speaker, "--speed", str(speed), "--output", mp3]
        if beat.get("language"):
            print(f"[WARN] {beat['id']}: v1 引擎不支持 language 参数,已忽略", flush=True)
    else:
        cmd = ["python3", TTS, "--text", beat["text"],
               "--speaker", speaker, "--speed", str(speed)]
        if beat.get("language"):
            cmd += ["--language", beat["language"]]
        cmd += ["--output", mp3]
    r = run(cmd)
    if r.returncode != 0 or not os.path.exists(mp3):
        print(f"[FAIL] {beat['id']}: {r.stdout} {r.stderr}", flush=True)
        sys.exit(1)
    return mp3

# ---------------- whole:整段合成 + 停顿 DP 对齐切句 ----------------
def detect_pauses(media):
    """silencedetect 解析 → [(start,end),...];返回 (停顿列表, 总时长, 语音起点)"""
    r = run(["ffmpeg", "-i", media, "-af", "silencedetect=noise=-45dB:d=0.15", "-f", "null", "-"])
    pairs, start = [], None
    for line in r.stderr.splitlines():
        m = re.search(r"silence_start: ([\d.]+)", line)
        if m: start = float(m.group(1))
        m = re.search(r"silence_end: ([\d.]+) \| silence_duration: ([\d.]+)", line)
        if m and start is not None:
            pairs.append((start, float(m.group(1)))); start = None
    p = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", media])
    total = float(p.stdout.strip())
    speech_start = 0.0
    if pairs and pairs[0][0] < 0.1:          # 头静音
        speech_start = pairs[0][1]
        pairs = pairs[1:]
    return pairs, total, speech_start

def dp_align(pauses, total, speech_start, texts):
    """把停顿分配给句子(DP 全局最优):句 i 的语音长应 ≈ 字数×平均字率。
    返回每句的 (音频起点, 音频终点=其结束停顿的 start);最后一句到 total。"""
    # cum[j] = 第 j 个停顿结束时累计的语音长(j=0..n, j=0 即语音起点前=0)
    cum, prev = [0.0], speech_start
    for s, e in pauses:
        cum.append(cum[-1] + max(0.0, s - prev)); prev = e
    cum.append(cum[-1] + max(0.0, total - prev))   # 末位=音频尾
    n_pause = len(pauses)
    chars = [len(t) for t in texts]
    rate = cum[-1] / sum(chars) if chars else 0
    INF = 1e18
    # f[i][j]:前 i 句恰好用前 j 个停顿作句尾的最小代价(最后一句允许用"音频尾"= n_pause+1)
    f = [[INF] * (n_pause + 2) for _ in range(len(texts) + 1)]
    pre = [[-1] * (n_pause + 2) for _ in range(len(texts) + 1)]
    f[0][0] = 0.0
    for i in range(1, len(texts) + 1):
        last = n_pause + 1 if i == len(texts) else n_pause
        for j in range(i, last + 1):
            for jp in range(i - 1, j):
                if f[i - 1][jp] >= INF: continue
                seg = cum[j] - cum[jp]
                cost = (seg - chars[i - 1] * rate) ** 2
                if f[i - 1][jp] + cost < f[i][j]:
                    f[i][j] = f[i - 1][jp] + cost; pre[i][j] = jp
    # 回溯
    js = [0] * len(texts)
    j = n_pause + 1 if f[len(texts)][n_pause + 1] <= f[len(texts)][n_pause] else n_pause
    if f[len(texts)][j] >= INF:
        print("[FAIL] 停顿-句子 DP 对齐失败(停顿数不足或分布异常),可换 --tts-mode per-beat", flush=True)
        sys.exit(1)
    for i in range(len(texts), 0, -1):
        js[i - 1] = j; j = pre[i][j]
    # 句子区间:起点=上一句停顿的 end(首句=speech_start),终点=本句停顿 start(末句=total)
    spans, start_t = [], speech_start
    for i, j in enumerate(js):
        end_t = total if j > n_pause else pauses[j - 1][0]
        spans.append((start_t, end_t))
        start_t = total if j > n_pause else pauses[j - 1][1]
    return spans, rate

def synth_whole_all(beats, speaker, speed):
    """整段一次合成 → 停顿切句 → 每句落 audio/beats/XX.mp3(复听用)。返回 {bid: mp3}"""
    whole = f"{BASE}/audio/whole.mp3"
    text = "".join(b["text"] for b in beats)
    if not (os.path.exists(whole) and os.path.getsize(whole) > 10000):
        if speaker.upper().startswith("BV"):
            cmd = ["python3", TTS_V1, "--text", text, "--speaker", speaker,
                   "--speed", str(speed), "--output", whole]
        else:
            cmd = ["python3", TTS, "--text", text, "--speaker", speaker,
                   "--speed", str(speed), "--output", whole]
        r = run(cmd)
        if r.returncode != 0 or not os.path.exists(whole):
            print(f"[FAIL] 整段合成: {r.stdout} {r.stderr}", flush=True)
            sys.exit(1)
    # mp3 帧对齐有 ±48ms 误差,切口会落在语音里造成句首硬切(拼接爆音)——转 wav 后样本级精确裁
    whole_wav = f"{BASE}/audio/whole.wav"
    if not os.path.exists(whole_wav):
        r = run(["ffmpeg", "-y", "-v", "error", "-i", whole,
                 "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", whole_wav])
        if r.returncode != 0:
            print(f"[DECODE FAIL] whole.wav: {r.stderr}", flush=True)
            sys.exit(1)
    pauses, total, speech_start = detect_pauses(whole_wav)
    spans, rate = dp_align(pauses, total, speech_start, [b["text"] for b in beats])
    out = {}
    for b, (a, z) in zip(beats, spans):
        mp3 = f"{BASE}/audio/beats/{b['id']}.mp3"
        if z - a <= 0.2:
            print(f"[FAIL] {b['id']} 切分区间异常 {a:.2f}~{z:.2f}s(停顿对齐漂移),可换 --tts-mode per-beat", flush=True)
            sys.exit(1)
        r = run(["ffmpeg", "-y", "-v", "error", "-ss", f"{a:.3f}", "-to", f"{z:.3f}",
                 "-i", whole_wav, "-c:a", "libmp3lame", "-q:a", "4", mp3])
        if r.returncode != 0:
            print(f"[CUT FAIL] {b['id']}: {r.stderr}", flush=True)
            sys.exit(1)
        out[b["id"]] = mp3
    print(f"[whole] {len(beats)} 句按 {len(pauses)} 个停顿 DP 对齐切分(平均 {rate:.2f} 字/s)", flush=True)
    return out

# ---------------- 主流程 ----------------
ap = argparse.ArgumentParser()
ap.add_argument("--tts-mode", choices=["auto", "whole", "per-beat"], default="auto",
                help="auto:BV 前缀走 whole、其余 per-beat")
args, _ = ap.parse_known_args()

script = json.load(open(f"{BASE}/script.json"))
gap = script["beat_gap"]
fps = script["fps"]

col_path = f"{BASE}/../collection.json"
col = json.load(open(col_path)) if os.path.exists(col_path) else {}
speaker = script.get("speaker") or col.get("speaker") or DEFAULT_SPEAKER
speed = script.get("speed")
if speed is None:
    speed = col.get("speed", DEFAULT_SPEED)
mode = args.tts_mode
if mode == "auto":
    mode = script.get("tts_mode") or col.get("tts_mode") or \
           ("whole" if speaker.upper().startswith("BV") else "per-beat")
os.makedirs(f"{BASE}/audio/clean", exist_ok=True)
os.makedirs(f"{BASE}/audio/beats", exist_ok=True)
print(f"speaker={speaker}  speed={speed}  mode={mode}", flush=True)

flat = []
for scene in script["scenes"]:
    for beat in scene["beats"]:
        assert_no_placeholder(beat["text"], beat["id"])
        flat.append((scene["id"], beat))

whole_cache = synth_whole_all([b for _, b in flat], speaker, speed) if mode == "whole" else None

beats, t = [], 0.0
for scene_id, beat in flat:
    if whole_cache is not None:
        mp3 = whole_cache[beat["id"]]
    else:
        mp3 = synth_per_beat(beat, speaker, speed)
    clean = f"{BASE}/audio/clean/{beat['id']}.wav"
    r = run(["ffmpeg", "-y", "-v", "error", "-i", mp3, "-af", CLEAN_FILTER,
             "-c:a", "pcm_s16le", "-ar", "48000", clean])
    if r.returncode != 0:
        print(f"[CLEAN FAIL] {beat['id']}: {r.stderr}", flush=True)
        sys.exit(1)
    p = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", clean])
    dur = float(p.stdout.strip())
    seg = dur + gap
    beats.append({
        "id": beat["id"], "scene": scene_id, "text": beat["text"],
        "audio": f"audio/beats/{beat['id']}.mp3",
        "clean": f"audio/clean/{beat['id']}.wav",
        "audio_dur": round(dur, 3),
        "start": round(t, 3), "end": round(t + seg, 3),
    })
    t += seg
    print(f"[ok] {beat['id']}  clean={dur:.2f}s  start={beats[-1]['start']:.2f}", flush=True)

# 语速均匀性体检(whole 模式的均匀性由 DP 对齐保证,见 [whole] 日志);per-beat 报逐句字速极差
if mode == "per-beat":
    sp = [len(b["text"]) / b["audio_dur"] for b in beats if b["audio_dur"] > 0]
    if sp:
        rng = (max(sp) / min(sp) - 1) * 100
        print(f"[语速体检] {min(sp):.2f}~{max(sp):.2f} 字/s, 极差 {rng:.0f}%" +
              ("  ⚠️ 偏大,考虑 whole 模式或换韵律平稳音色" if rng > 25 else ""), flush=True)

total = round(t, 3)
timeline = {
    "fps": fps, "resolution": script["resolution"], "gap": gap,
    "beats": beats, "total": total, "frames": math.ceil(total * fps),
}
json.dump(timeline, open(f"{BASE}/timeline.json", "w"), ensure_ascii=False, indent=2)
print(f"\n== total {total:.2f}s, {timeline['frames']} frames ==")
