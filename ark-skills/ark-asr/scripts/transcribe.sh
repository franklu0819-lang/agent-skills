#!/usr/bin/env bash
# 豆包录音文件识别大模型（Seed-ASR）：本地音频或 URL → 文字（直连豆包语音 API）。
# 认证：环境变量 SPEECH_API_KEY，其次解析 ~/.zshrc 里的 export SPEECH_API_KEY；本脚本不读取、不存储任何密钥。
# 注意：必须是豆包语音控制台的 UUID Key，方舟 ark- 开头的 Key 本服务不认；录音文件识别需在控制台开通。
# 依赖：python3、curl、uuidgen
set -euo pipefail

RESOURCE="volc.bigasr.auc"   # 录音文件识别大模型 1.0；2.0 为 volc.seedasr.auc（需单独开通）
SUBMIT_URL="${SPEECH_ASR_SUBMIT_URL:-https://openspeech.bytedance.com/api/v3/auc/bigmodel/submit}"
QUERY_URL="${SPEECH_ASR_QUERY_URL:-https://openspeech.bytedance.com/api/v3/auc/bigmodel/query}"

usage() {
  cat <<'EOF'
用法: transcribe.sh <音频文件或URL> [选项]

选项:
  -o, --output PATH     转写文本另存路径（stdout 始终输出纯文本）
      --json PATH       完整结果单行 JSON 另存路径
      --speakers        说话人分离（结果按说话人分段，stdout 变为带标签文本）
      --utterances      输出分句与时间戳（写入 --json；stdout 若无 --speakers 仍为纯文本）
      --no-punc         关闭自动标点（默认开启）
      --no-itn          关闭逆文本归一化（"一九七零年"→"1970年"，默认开启）
      --language LANG   指定语种（默认空=中文普通话，自动支持中英混与常见方言）。
                        取值: zh-CN / en-US / ja-JP / ko-KR / yue-CN(粤语) / de-DE / fr-FR /
                        es-MX / pt-BR / id-ID / th-TH / vi-VN / ru-RU / ar-SA 等 locale 码
      --format FMT      音频格式；URL 输入时建议显式指定（本地文件自动按扩展名推断）
      --resource ID     服务资源 ID（默认 volc.bigasr.auc=大模型1.0；2.0 传 volc.seedasr.auc）
      --timeout SEC     轮询超时秒数（默认 300）
      --submit-only     只提交，打印 request_id 后退出（配合 --query 稍后取结果）
      --query ID        用已有 request_id 查询结果
  -h, --help            显示本帮助

支持格式: wav / mp3 / ogg / m4a / aac（其他格式先 ffmpeg 转换）。

输出: stdout 输出纯文本转写（进度走 stderr）；
      --json 另存 {"ok":true,"request_id":"...","text":"...","duration_ms":2639,"utterances":[...]}。

示例:
  transcribe.sh meeting.mp3 -o meeting.txt --speakers
  transcribe.sh https://example.com/a.mp3 --format mp3 --json out.json
EOF
}

SRC="" OUTPUT="" JSON_OUT="" SPEAKERS="0" UTTERANCES="0" PUNC="1" ITN="1" LANGUAGE="" FMT="" TIMEOUT="300" SUBMIT_ONLY="0" QUERY_ID=""

while [ $# -gt 0 ]; do
  case "$1" in
    -o|--output) OUTPUT="$2"; shift 2;;
    --json) JSON_OUT="$2"; shift 2;;
    --speakers) SPEAKERS="1"; shift;;
    --utterances) UTTERANCES="1"; shift;;
    --no-punc) PUNC="0"; shift;;
    --no-itn) ITN="0"; shift;;
    --language) LANGUAGE="$2"; shift 2;;
    --format) FMT="$2"; shift 2;;
    --resource) RESOURCE="$2"; shift 2;;
    --timeout) TIMEOUT="$2"; shift 2;;
    --submit-only) SUBMIT_ONLY="1"; shift;;
    --query) QUERY_ID="$2"; shift 2;;
    -h|--help) usage; exit 0;;
    -*) echo "未知选项: $1" >&2; usage >&2; exit 2;;
    *) if [ -z "$SRC" ] && [ -z "$QUERY_ID" ]; then SRC="$1"; shift; else echo "多余的位置参数: $1" >&2; exit 2; fi;;
  esac
done

fail() { printf '{"ok":false,"error":%s}\n' "$(python3 -c 'import sys,json;print(json.dumps(sys.argv[1]))' "$1")" >&2; exit 1; }

find_api_key() {
  if [ -n "${SPEECH_API_KEY:-}" ]; then printf '%s' "$SPEECH_API_KEY"; return 0; fi
  local zshrc="${ZDOTDIR:-$HOME}/.zshrc"
  [ -f "$zshrc" ] || return 1
  grep -E '^[[:space:]]*export[[:space:]]+SPEECH_API_KEY=' "$zshrc" | tail -1 \
    | sed -E 's/^[[:space:]]*export[[:space:]]+SPEECH_API_KEY="?([^"#+[:space:]]*)"?[[:space:]]*(#.*)?$/\1/'
}

API_KEY=$(find_api_key) || true
[ -n "$API_KEY" ] || fail "缺少 API Key：请 export SPEECH_API_KEY=<豆包语音控制台 UUID Key>，或写入 ~/.zshrc（方舟 ark- Key 本服务不认）"

RID="${QUERY_ID:-$(uuidgen | tr 'A-Z' 'a-z')}"

if [ -z "$QUERY_ID" ]; then
  [ -n "$SRC" ] || { usage >&2; fail "缺少音频文件或 URL"; }

  if [ "$SRC" = "${SRC#http://}" ] && [ "$SRC" = "${SRC#https://}" ]; then
    [ -f "$SRC" ] || fail "音频文件不存在: $SRC"
    FMT="${FMT:-${SRC##*.}}"
    case "$FMT" in wav|mp3|ogg|m4a|aac) ;; *) fail "无法识别音频格式 .$FMT，请用 --format 指定（wav/mp3/ogg/m4a/aac）或先 ffmpeg 转换";; esac
    SIZE=$(stat -f%z "$SRC")
    [ "$SIZE" -le 52428800 ] || fail "文件 $(python3 -c "print(f'{$SIZE/1048576:.0f}')")MB 超过 base64 直传建议上限 50MB，请压缩或改用可公网访问的 URL"
    AUDIO_B64=$(mktemp); AUDIO_FIELD_F=$(mktemp)
    base64 -i "$SRC" | tr -d '\n' > "$AUDIO_B64"
    # base64 音频可达数 MB，走 argv 会撞 E2BIG（macOS 单参数 256KB 上限），改经临时文件传递
    AUDIO_FIELD=$(python3 -c 'import json,sys
d = {"data": open(sys.argv[1]).read().strip(), "format": sys.argv[2], "codec": "raw", "rate": 16000, "bits": 16, "channel": 1}
if sys.argv[3]: d["language"] = sys.argv[3]
open(sys.argv[4], "w").write(json.dumps(d))' "$AUDIO_B64" "$FMT" "$LANGUAGE" "$AUDIO_FIELD_F") || { rm -f "$AUDIO_B64" "$AUDIO_FIELD_F"; fail "音频编码失败"; }
    rm -f "$AUDIO_B64"
  else
    FMT="${FMT:-mp3}"
    AUDIO_FIELD=$(python3 -c 'import json,sys
d = {"url": sys.argv[1], "format": sys.argv[2], "codec": "raw", "rate": 16000, "bits": 16, "channel": 1}
if sys.argv[3]: d["language"] = sys.argv[3]
print(json.dumps(d))' "$SRC" "$FMT" "$LANGUAGE")
  fi

  if [ -n "${AUDIO_FIELD_F:-}" ] && [ -f "$AUDIO_FIELD_F" ]; then
    BODY=$(python3 -c 'import json,sys
u, p, i = sys.argv[1] == "1", sys.argv[2] == "1", sys.argv[3] == "1"
print(json.dumps({"user": {"uid": "ark-asr"}, "audio": json.load(open(sys.argv[4])),
                  "request": {"model_name": "bigmodel", "enable_itn": i, "enable_punc": p,
                              "enable_ddc": False, "enable_speaker_info": u,
                              "enable_channel_split": False, "show_utterances": u or i,
                              "vad_segment": False}}))' "$SPEAKERS" "$PUNC" "$UTTERANCES" "$AUDIO_FIELD_F") || { rm -f "$AUDIO_FIELD_F"; fail "请求体构造失败"; }
    rm -f "$AUDIO_FIELD_F"
  else
  BODY=$(python3 -c 'import json,sys
u, p, i = sys.argv[1] == "1", sys.argv[2] == "1", sys.argv[3] == "1"
print(json.dumps({"user": {"uid": "ark-asr"}, "audio": json.loads(sys.argv[4]),
                  "request": {"model_name": "bigmodel", "enable_itn": i, "enable_punc": p,
                              "enable_ddc": False, "enable_speaker_info": u,
                              "enable_channel_split": False, "show_utterances": u or i,
                              "vad_segment": False}}))' "$SPEAKERS" "$PUNC" "$UTTERANCES" "$AUDIO_FIELD") || fail "请求体构造失败"
  fi

  # 请求体同样可能超 argv 上限，curl 改从临时文件读（-d @file）
  BODY_F=$(mktemp)
  printf '%s' "$BODY" > "$BODY_F"
  RESP=$(curl -sS --max-time 60 -X POST "$SUBMIT_URL" \
    -H "Content-Type: application/json" -H "X-Api-Key: $API_KEY" \
    -H "X-Api-Resource-Id: $RESOURCE" -H "X-Api-Request-Id: $RID" -H "X-Api-Sequence: -1" \
    --data-binary @"$BODY_F") || { rm -f "$BODY_F"; fail "提交请求失败"; }
  rm -f "$BODY_F"
  [ "$RESP" = "{}" ] || fail "提交失败: $RESP"
  echo "已提交任务 request_id=$RID" >&2
fi

if [ "$SUBMIT_ONLY" = "1" ]; then
  printf '%s\n' "$RID"
  exit 0
fi

# 轮询直到拿到 result（未完成时响应为空对象）
POLL=5; ELAPSED=0; RESP=""
while [ "$ELAPSED" -lt "$TIMEOUT" ]; do
  RESP=$(curl -sS --max-time 60 -X POST "$QUERY_URL" \
    -H "Content-Type: application/json" -H "X-Api-Key: $API_KEY" \
    -H "X-Api-Resource-Id: $RESOURCE" -H "X-Api-Request-Id: $RID" -d "{}") \
    || fail "查询请求失败"
  HAS=$(printf '%s' "$RESP" | python3 -c 'import sys,json
try: print(1 if (json.load(sys.stdin).get("result") or {}).get("text") else 0)
except Exception: print(0)') || HAS=0
  [ "$HAS" = "1" ] && break
  sleep "$POLL"; ELAPSED=$((ELAPSED + POLL))
done
[ "$HAS" = "1" ] || fail "轮询超时（${TIMEOUT}s），任务可能仍在识别；稍后可用 --query $RID 取结果"

RESULT_JSON=$(python3 -c 'import json,sys
r = json.loads(sys.argv[1])
res = r.get("result") or {}
out = {"ok": True, "request_id": sys.argv[2], "text": res.get("text", ""),
       "duration_ms": (r.get("audio_info") or {}).get("duration")}
ut = res.get("utterances")
if ut: out["utterances"] = ut
spk = res.get("speaker_info") or res.get("additions", {}).get("speaker_info")
if spk: out["speaker_info"] = spk
print(json.dumps(out, ensure_ascii=False))' "$RESP" "$RID") || fail "结果解析失败: $(printf '%s' "$RESP" | head -c 300)"

# stdout: 纯文本（--speakers 时按说话人分段）；--json: 完整 JSON 落盘
python3 -c 'import json,sys
out = json.loads(sys.argv[1])
if sys.argv[2] == "1" and out.get("utterances"):
    lines, cur = [], None
    for u in out["utterances"]:
        tag = str((u.get("speaker") or 0)) if u.get("speaker") is not None else ""
        lines.append((f"Speaker {tag}: " if tag else "") + (u.get("text") or ""))
    print("\n".join(lines))
else:
    print(out.get("text", ""))
if sys.argv[3]:
    open(sys.argv[3], "w").write(json.dumps(out, ensure_ascii=False) + "\n")' "$RESULT_JSON" "$SPEAKERS" "$JSON_OUT"

if [ -n "$OUTPUT" ]; then
  python3 -c 'import json,sys;open(sys.argv[2],"w").write(json.loads(sys.argv[1])["text"]+"\n")' "$RESULT_JSON" "$OUTPUT"
fi
