#!/usr/bin/env bash
# 火山引擎 Seed-Audio 1.0 音频创作：多角色对白 + 音效 + BGM 成片音轨（直连豆包语音 API）。
# 认证：环境变量 ARK_SPEECH_API_KEY（旧名 SPEECH_API_KEY 兼容），其次解析 ~/.zshrc 里的同名 export（新名优先）；本脚本不读取、不存储任何密钥。
# 注意：必须是豆包语音控制台的 UUID Key，方舟 ark- 开头的 Key 本服务不认。
# 依赖：python3、curl
set -euo pipefail

DEFAULT_MODEL="seed-audio-1.0"
BASE_URL="${SPEECH_BASE_URL:-https://openspeech.bytedance.com/api/v3/tts/create}"

usage() {
  cat <<'EOF'
用法: audio_gen.sh "全要素音频提示词" [选项]

提示词写法（四要素：谁在说 / 什么情绪 / 什么场景 / 有什么声响）:
  音效/环境/BGM 直接写进描述；角色用「男子1（中青年男性，嗓音低沉）用严肃语气说道："台词"」格式；
  多角色在一条提示词里依次编排即可。

选项:
  -o, --output PATH     输出音频路径（默认 ./ark_audio_<时间戳>.mp3）
  -f, --format FMT      输出格式 mp3（默认）或 wav
      --sample-rate N   采样率（默认 48000）
      --speech-rate N   语速 [-50,100]，默认 0
      --pitch-rate N    音调 [-50,100]，默认 0
      --loudness-rate N 音量 [-50,100]，默认 0
  -m, --model NAME      模型（默认 seed-audio-1.0）
      --timeout SEC     请求超时秒数（默认 300，生成 2 分钟音频约需 1-3 分钟）
      --dry-run         只打印将提交的参数 JSON，不实际生成
  -h, --help            显示本帮助

认证: export ARK_SPEECH_API_KEY=<豆包语音控制台 API Key管理 的 UUID Key>（旧名 SPEECH_API_KEY 兼容，或写在 ~/.zshrc）。

输出: 最后一行打印单行 JSON：
      {"ok":true,"audio_path":"/abs/out.mp3","format":"mp3","model":"seed-audio-1.0"}
      失败时 {"ok":false,"error":"..."} 并以非零码退出。
EOF
}

PROMPT="" OUTPUT="" FORMAT="mp3" SAMPLE_RATE="48000" SPEECH_RATE="0" PITCH_RATE="0" LOUDNESS_RATE="0" MODEL="$DEFAULT_MODEL" TIMEOUT="300" DRY_RUN="0"

while [ $# -gt 0 ]; do
  case "$1" in
    -o|--output) OUTPUT="$2"; shift 2;;
    -f|--format) FORMAT="$2"; shift 2;;
    --sample-rate) SAMPLE_RATE="$2"; shift 2;;
    --speech-rate) SPEECH_RATE="$2"; shift 2;;
    --pitch-rate) PITCH_RATE="$2"; shift 2;;
    --loudness-rate) LOUDNESS_RATE="$2"; shift 2;;
    -m|--model) MODEL="$2"; shift 2;;
    --timeout) TIMEOUT="$2"; shift 2;;
    --dry-run) DRY_RUN="1"; shift;;
    -h|--help) usage; exit 0;;
    -*) echo "未知选项: $1" >&2; usage >&2; exit 2;;
    *) if [ -z "$PROMPT" ]; then PROMPT="$1"; shift; else echo "多余的位置参数: $1" >&2; exit 2; fi;;
  esac
done

fail() { printf '{"ok":false,"error":%s}\n' "$(python3 -c 'import sys,json;print(json.dumps(sys.argv[1]))' "$1")"; exit 1; }

[ -n "$PROMPT" ] || { usage >&2; fail "缺少提示词"; }

find_api_key() {
  if [ -n "${ARK_SPEECH_API_KEY:-}" ]; then printf '%s' "$ARK_SPEECH_API_KEY"; return 0; fi
  if [ -n "${SPEECH_API_KEY:-}" ]; then printf '%s' "$SPEECH_API_KEY"; return 0; fi  # 旧名兼容
  local zshrc="${ZDOTDIR:-$HOME}/.zshrc"
  [ -f "$zshrc" ] || return 1
  { grep -E '^[[:space:]]*export[[:space:]]+ARK_SPEECH_API_KEY=' "$zshrc" | tail -1
    grep -E '^[[:space:]]*export[[:space:]]+SPEECH_API_KEY=' "$zshrc" | tail -1
  } | head -1 \
    | sed -E 's/^[[:space:]]*export[[:space:]]+(ARK_)?SPEECH_API_KEY="?([^"#+[:space:]]*)"?[[:space:]]*(#.*)?$/\2/'
}

PARAMS=$(python3 - "$PROMPT" "$MODEL" "$FORMAT" "$SAMPLE_RATE" "$SPEECH_RATE" "$PITCH_RATE" "$LOUDNESS_RATE" <<'PY'
import json, sys
prompt, model, fmt, sr, speech, pitch, loudness = sys.argv[1:8]
p = {"model": model, "text_prompt": prompt,
     "audio_config": {"format": fmt, "sample_rate": int(sr),
                      "speech_rate": int(speech), "pitch_rate": int(pitch),
                      "loudness_rate": int(loudness)},
     "watermark": {}}
print(json.dumps(p, ensure_ascii=False))
PY
) || fail "$PARAMS"

if [ "$DRY_RUN" = "1" ]; then
  printf '{"ok":true,"dry_run":true,"params":%s}\n' "$PARAMS"
  exit 0
fi

API_KEY=$(find_api_key) || true
[ -n "$API_KEY" ] || fail "缺少 API Key：请 export ARK_SPEECH_API_KEY=<豆包语音控制台 UUID Key>（旧名 SPEECH_API_KEY 仍兼容），或写入 ~/.zshrc（方舟 ark- Key 本服务不认）"

[ -n "$OUTPUT" ] || OUTPUT="./ark_audio_$(date +%Y%m%d_%H%M%S).${FORMAT}"

RESP=$(curl -sS --max-time "$TIMEOUT" -X POST "$BASE_URL" \
  -H "Content-Type: application/json" -H "X-Api-Key: $API_KEY" -d "$PARAMS") \
  || fail "curl 请求失败"

RESULT=$(python3 - "$OUTPUT" "$FORMAT" "$MODEL" "$RESP" <<'PY'
import base64, json, os, sys
output, fmt, model, resp = sys.argv[1], sys.argv[2], sys.argv[3], json.loads(sys.argv[4])
if isinstance(resp, dict) and resp.get("audio"):
    with open(output, "wb") as f:
        f.write(base64.b64decode(resp["audio"]))
    print(json.dumps({"ok": True, "audio_path": os.path.abspath(output), "format": fmt, "model": model}, ensure_ascii=False))
else:
    msg = resp.get("message") or resp.get("msg") or json.dumps(resp, ensure_ascii=False) if isinstance(resp, dict) else str(resp)[:300]
    print(json.dumps({"ok": False, "error": str(msg)[:300]}, ensure_ascii=False))
PY
) || fail "响应解析失败"

if printf '%s' "$RESULT" | python3 -c 'import sys,json; sys.exit(0 if json.load(sys.stdin).get("ok") else 1)' 2>/dev/null; then
  :
else
  ERR=$(printf '%s' "$RESULT" | python3 -c 'import sys,json;print(json.load(sys.stdin).get("error",""))' 2>/dev/null || echo "$RESULT")
  fail "$ERR"
fi
printf '%s\n' "$RESULT"
