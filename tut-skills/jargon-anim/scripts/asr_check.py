#!/usr/bin/env python3
"""英文词发音终验:对 script.json 文案中含英文单词的句子跑 ASR 转写,
检查每个英文词是否出现在转写结果(宽松匹配:去空格标点后大小写不敏感)。
不合格的句子改写文本或加 "language": "crosslingual" 重录(删对应 beats/*.mp3 后重跑 gen_timeline)。
用法: python3 asr_check.py [项目目录](默认当前目录)
注意:ASR 有上下文纠错能力,此验证保证"读的不是别的词";口音是否标准需用户人耳终判。"""
import json, os, re, subprocess, sys

BASE = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
ASR = os.environ.get("ASR_SH", "/Users/leo/.agents/skills/ark-asr/scripts/transcribe.sh")
script = json.load(open(os.path.join(BASE, "script.json")))

def norm(s):
    return re.sub(r"[\s,，.。:：;；?？!！'’()（）\-—…·]", "", s).upper()

fails = []
infra_fails = []
for sc in script["scenes"]:
    for b in sc["beats"]:
        # ≥2 字符的英文词;单字母(I/O 的 I 等)不检(ASR 不可靠,属已知限制);
        # 尾部连字符去掉(GPT- → GPT,norm 匹配时连字符已被剥离)
        words = sorted(set(w.rstrip("-&") for w in re.findall(r"[A-Za-z][A-Za-z&-]{1,}", b["text"])))
        if not words:
            continue
        mp3 = os.path.join(BASE, "audio", "beats", f"{b['id']}.mp3")
        if not os.path.exists(mp3):
            infra_fails.append((b["id"], "音频不存在,先跑 gen_timeline.py"))
            continue
        r = subprocess.run(["bash", ASR, mp3], capture_output=True, text=True)
        out = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
        if r.returncode != 0 or not out:
            infra_fails.append((b["id"], f"ASR 调用失败(rc={r.returncode}),检查 ark-asr 技能/SPEECH_API_KEY/网络"))
            continue
        t = norm(out)
        missing = [w for w in words if norm(w) not in t]
        mark = "OK " if not missing else "BAD"
        if missing:
            fails.append((b["id"], missing))
        print(f"[{mark}] {b['id']}: {out}" + (f"  缺:{missing}" if missing else ""))

for bid, msg in infra_fails:
    print(f"[ERR] {bid}: {msg}")
if infra_fails:
    print("\n存在基建故障,先修复再判发音(发音问题与调用失败不能混为一谈)")
    sys.exit(2)

if fails:
    print("\n不合格句子(改词或 crosslingual 重录后复验):")
    for bid, miss in fails:
        print(f"  {bid}: 缺 {miss}")
    sys.exit(1)
print("\n全部英文词验证通过 ✓(口音标准与否请用户复听终判)")
