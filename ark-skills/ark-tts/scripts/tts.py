#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tts.py — 火山引擎语音合成（豆包大模型 TTS V3 单向流式 HTTP 接口）

用法:
  tts.py --text "你好" --output out.mp3
  tts.py --file script.txt --output out.mp3
  tts.py --list-voices [关键词]        # 浏览音色库（解说/女声/客服/英语…）
  tts.py --text "..." --speaker zh_male_jieshuoxiaoming_uranus_bigtts --output out.mp3
  tts.py --text "..." --speed -20 --output out.mp3    # 语速 [-50,100]，+100≈2倍速

选项:
  --speaker ID      音色。默认 S_q3oLhGy72（飞哥复刻音色）；音色库见 references/voices.md
  --speed N         语速 [-50,100]（默认 0）：+100≈2倍速，-50≈0.5倍速（放 audio_params.speech_rate，实测生效）
  --custom-id ID    后付费自定义音色代号：设置后 speaker 传固定值 custom_speaker_id（文档 6561/2534906）
  --resource-id ID  强制指定资源 ID（一般不用，按音色自动推断）
  --format FMT      音频格式 mp3/pcm/ogg_opus（默认 mp3）
  --sample-rate N   采样率（默认 24000）
  --emotion E       情感（如 happy，仅部分 1.0 公版音色支持，复刻/2.0 音色忽略）
  --api-key KEY     API Key（默认自动解析 SPEECH_API_KEY / ARK_API_KEY）

响应协议: 流式多段 JSON，每段 data 字段为 base64 音频块，拼接解码得到完整音频。

凭证: 豆包语音控制台 > API Key管理 的 Key（UUID 格式），export SPEECH_API_KEY=... （不落盘）
"""
import argparse
import base64
import json
import os
import re
import sys
import urllib.request
import uuid

API_URL = "https://openspeech.bytedance.com/api/v3/tts/unidirectional"
DEFAULT_SPEAKER = "S_q3oLhGy72"  # 飞哥的声音复刻音色
VOICES_MD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "references", "voices.md")


def find_api_key(explicit: str) -> str:
    """解析顺序: --api-key 参数 → SPEECH_API_KEY → ARK_API_KEY → ~/.zshrc export（取最后生效的）。
    注意: 必须是豆包语音控制台 API Key管理 里的 Key（UUID 格式）；方舟 ark- 开头的 Key 本服务不认。"""
    if explicit:
        return explicit
    for var in ("SPEECH_API_KEY", "ARK_API_KEY"):
        if os.environ.get(var):
            return os.environ[var]
    zshrc = os.path.expanduser("~/.zshrc")
    if os.path.isfile(zshrc):
        found = ""
        for line in open(zshrc, encoding="utf-8"):
            m = re.match(r'\s*export\s+(SPEECH_API_KEY|ARK_API_KEY)=(?:"([^"]+)"|([^\s#]+))', line)
            if m:
                found = m.group(2) or m.group(3)
        return found
    return ""


def resource_id_for(speaker: str, custom_id: str) -> str:
    """按音色推断 resource-id（2026-09-17 实测矩阵）:
    S_/custom 复刻音色 → seed-icl-2.0
    音色名含 uranus（2.0 代，zh_*_uranus_bigtts 与 ICL_uranus_*）→ seed-tts-2.0
    其他 _bigtts（1.0 代，moon/mars 等）→ volc.service_type.10029
    配错不报 401，而是 HTTP 200 + code=55000000 空音频"""
    if custom_id or speaker.startswith("S_"):
        return "seed-icl-2.0"
    if "uranus" in speaker:
        return "seed-tts-2.0"
    return "volc.service_type.10029"


def die(msg: str) -> None:
    print(f"tts.py: {msg}", file=sys.stderr)
    sys.exit(1)


def list_voices(keyword: str = "") -> None:
    """打印音色库（references/voices.md 的表格行），可选关键词过滤"""
    if not os.path.isfile(VOICES_MD):
        die(f"音色库文件缺失: {VOICES_MD}")
    rows = []
    for line in open(VOICES_MD, encoding="utf-8"):
        stripped = line.strip()
        if not stripped.startswith("|") or "voice_type" in stripped:
            continue
        if set(stripped) <= {"|", "-", " "}:
            continue  # 分隔线 |---|---|
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) >= 3 and ("bigtts" in cells[2] or "_tob" in cells[2]):
            rows.append((cells[0], cells[1], cells[2], cells[3] if len(cells) > 3 else ""))
    kw = (keyword or "").lower()
    hits = [r for r in rows if not kw or kw in "|".join(r).lower()]
    if not hits:
        die(f"没有匹配「{keyword}」的音色；不带参数可看全部 {len(rows)} 个")
    print(f"共 {len(hits)}/{len(rows)} 个音色" + (f"（关键词: {keyword}）" if kw else ""))
    for scene, name, vt, lang in hits:
        print(f"  {vt:55s} {scene} · {name} · {lang}")
    sys.exit(0)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--list-voices", nargs="?", const="", metavar="关键词",
                    help="列出音色库（可带关键词过滤，如: 解说/女/客服/英语），不合成")
    ap.add_argument("--text")
    ap.add_argument("--file")
    ap.add_argument("--output")
    ap.add_argument("--speaker", default=DEFAULT_SPEAKER)
    ap.add_argument("--custom-id", dest="custom_id", default="",
                    help="后付费自定义音色代号：设置后 speaker 传固定值 custom_speaker_id")
    ap.add_argument("--resource-id")
    ap.add_argument("--format", default="mp3", choices=["mp3", "pcm", "ogg_opus"])
    ap.add_argument("--sample-rate", type=int, default=24000)
    ap.add_argument("--speed", type=int, default=0)
    ap.add_argument("--emotion")
    ap.add_argument("--language", default="",
                    help="语种 explicit_language: zh-cn/en/ja/es-mx/id/pt-br/de/fr/crosslingual"
                         "（默认空=中文普通话中英混）")
    ap.add_argument("--dialect", default="",
                    help="方言 explicit_dialect: yue/dongbei/sichuan/shaanxi/beijing/henan/tianjin/shanghai"
                         "（仅部分精品音色生效，与 --language 二选一）")
    ap.add_argument("--api-key", default="")
    a = ap.parse_args()

    if a.list_voices is not None:
        list_voices(a.list_voices)

    key = find_api_key(a.api_key)
    text = a.text or (open(a.file, encoding="utf-8").read() if a.file else "")
    text = text.strip()
    if not text:
        die("没有可合成的文本（--text 或 --file 至少给一个）")
    if not a.output:
        die("缺少 --output 输出路径")
    if not key:
        die("缺少 API Key：请 export SPEECH_API_KEY=<豆包语音控制台 API Key管理 的 Key>，或用 --api-key 传入")

    audio_params = {"format": a.format, "sample_rate": a.sample_rate}
    if a.speed:
        # 实测(2026-09-17): 必须放 audio_params 内才生效(放 req_params 顶层会被静默忽略);
        # 范围[-50,100], +100≈2倍速, -50≈0.5倍速, 超界服务端钳制
        audio_params["speech_rate"] = a.speed
    req_params = {
        "text": text,
        "speaker": a.speaker,
        "audio_params": audio_params,
    }
    if a.custom_id:
        # 后付费自定义音色: speaker 固定值 + custom_speaker_id 传实际代号
        req_params["speaker"] = "custom_speaker_id"
        req_params["custom_speaker_id"] = a.custom_id
    if a.emotion and not (a.custom_id or a.speaker.startswith("S_") or "uranus" in a.speaker):
        req_params["emotion"] = a.emotion
    if a.language or a.dialect:
        additions = {}
        if a.language:
            additions["explicit_language"] = a.language
        if a.dialect:
            if a.language:
                die("--language 与 --dialect 二选一，不能同时指定")
            additions["explicit_dialect"] = a.dialect
        # 实测(2026-09-17): additions 是 JSON 字符串而非嵌套对象，传对象会被服务端拒(unmarshal object into string)
        req_params["additions"] = json.dumps(additions, ensure_ascii=False)

    req = urllib.request.Request(
        API_URL,
        data=json.dumps({"req_params": req_params}).encode("utf-8"),
        headers={
            "X-Api-Key": key,
            "X-Api-Resource-Id": a.resource_id or resource_id_for(a.speaker, a.custom_id),
            "X-Api-Request-Id": str(uuid.uuid4()),  # 文档要求必选
            "Content-Type": "application/json",
            "Connection": "keep-alive",
        },
        method="POST",
    )

    try:
        resp = urllib.request.urlopen(req, timeout=300)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:500]
        hint = "（若 code=45000010：Key 不对或未绑定语音服务，须用控制台 API Key管理 的 UUID Key）" \
               if "45000010" in detail else ""
        die(f"HTTP {e.code}: {detail} {hint}")
    except urllib.error.URLError as e:
        die(f"网络错误: {e.reason}")

    # 流式多段 JSON: 每行一个 {"code":..,"message":..,"data":"<base64块>"}
    parts, errors = [], []
    for line in resp.read().decode("utf-8", "replace").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("code") not in (0, None) and obj.get("data") is None:
            errors.append(f'code={obj.get("code")} {obj.get("message", "")}')
        if obj.get("data"):
            parts.append(obj["data"])
    if not parts:
        hint = "（55000000 = 音色与 resource-id 不匹配，检查音色代际：uranus→seed-tts-2.0，其他 _bigtts→10029，S_→seed-icl-2.0）" \
               if "55000000" in "; ".join(errors) else ""
        die("服务未返回音频: " + ("; ".join(errors) or "响应为空") + hint)
    audio = base64.b64decode("".join(parts))
    if len(audio) < 1000:
        die(f"音频数据异常偏小({len(audio)}B)：" + ("; ".join(errors) or "请检查音色 ID"))

    with open(a.output, "wb") as f:
        f.write(audio)
    print(f"完成: {a.output} ({len(audio)/1024:.0f}KB, {a.custom_id or a.speaker})")


if __name__ == "__main__":
    main()
