#!/bin/bash
# gen_cover.sh — 调用火山方舟公共接入点（模型名直调）生成封面图
# 用法:
#   gen_cover.sh --prompt "提示词" [--prompt-file f] [--out 目录] [--name 文件基名]
#                [--size 1536x2048] [--seed N] [--count 1] [--model ID] [--api-key KEY]
# Key 解析顺序: --api-key > $ARK_API_KEY > ~/.arkcli/config.yaml 默认 platform 配置档
# 输出: 每张图一行摘要 `路径 <TAB> 宽x高 <TAB> 字节数`；失败时打印 API 错误并退出 1
# 安全: Key 只进请求头，不回显、不落盘
set -euo pipefail

MODEL="doubao-seedream-4-0-250828"
SIZE="1536x2048"
SEED=""
COUNT=1
OUT="."
NAME="cover"
PROMPT=""
PROMPT_FILE=""
API_KEY=""
ARK_API="https://ark.cn-beijing.volces.com/api/v3/images/generations"

while [ $# -gt 0 ]; do
  case "$1" in
    --prompt) PROMPT="$2"; shift 2 ;;
    --prompt-file) PROMPT_FILE="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;;
    --name) NAME="$2"; shift 2 ;;
    --size) SIZE="$2"; shift 2 ;;
    --seed) SEED="$2"; shift 2 ;;
    --count) COUNT="$2"; shift 2 ;;
    --model) MODEL="$2"; shift 2 ;;
    --api-key) API_KEY="$2"; shift 2 ;;
    *) echo "未知参数: $1" >&2; exit 2 ;;
  esac
done

# --- Key 解析（不回显） ---
if [ -z "$API_KEY" ]; then
  API_KEY="${ARK_API_KEY:-}"
fi
if [ -z "$API_KEY" ] && [ -f "$HOME/.arkcli/config.yaml" ]; then
  API_KEY=$(awk '
    /^default_profile:/ { prof=substr($2, 1, length($2)) }
    /^profiles:/ { inprof=1; cur="" }
    inprof && /^  [A-Za-z0-9_-]+:$/ { cur=substr($1, 1, length($1)-1); sub(/^  /, "", cur) }
    cur != "" && cur == prof && /^    api_key:/ { print $2; exit }
  ' "$HOME/.arkcli/config.yaml")
fi
if [ -z "$API_KEY" ]; then
  echo "错误: 找不到 API Key。请设置 ARK_API_KEY 环境变量、传 --api-key，或先运行 arkcli auth login volc-sso" >&2
  exit 3
fi

# --- Prompt ---
if [ -n "$PROMPT_FILE" ]; then
  [ -f "$PROMPT_FILE" ] || { echo "错误: prompt 文件不存在: $PROMPT_FILE" >&2; exit 2; }
  PAYLOAD=$(jq -n --rawfile p "$PROMPT_FILE" --arg m "$MODEL" --arg s "$SIZE" \
    '{model:$m, prompt:$p, size:$s, response_format:"url", watermark:false}')
elif [ -n "$PROMPT" ]; then
  PAYLOAD=$(jq -n --arg p "$PROMPT" --arg m "$MODEL" --arg s "$SIZE" \
    '{model:$m, prompt:$p, size:$s, response_format:"url", watermark:false}')
else
  echo "错误: 需要 --prompt 或 --prompt-file" >&2; exit 2
fi

mkdir -p "$OUT"

gen_one() {
  local idx="$1" seed_part=""
  [ -n "$SEED" ] && seed_part=$(jq -nc --argjson s "$((SEED + idx))" '{seed:$s}')
  local body seed_body
  if [ -n "$seed_part" ]; then
    seed_body=$(echo "$PAYLOAD" | jq -c --slurpfile extra <(echo "$seed_part") '. + $extra[0]')
  else
    seed_body="$PAYLOAD"
  fi

  local resp
  resp=$(curl -sS --max-time 180 -X POST "$ARK_API" \
    -H "Authorization: Bearer $API_KEY" -H "Content-Type: application/json" \
    -d "$seed_body") || { echo "错误: 请求失败（网络）" >&2; return 1; }

  if echo "$resp" | jq -e '.error' >/dev/null 2>&1; then
    echo "API 错误: $(echo "$resp" | jq -c '.error')" >&2; return 1
  fi

  local url
  url=$(echo "$resp" | jq -r '.data[0].url // empty')
  [ -n "$url" ] || { echo "错误: 响应无图片 URL: $(echo "$resp" | head -c 300)" >&2; return 1; }

  local base ext
  if [ "$COUNT" -gt 1 ]; then base="${NAME}-$((idx+1))"; else base="$NAME"; fi
  local tmp="$OUT/.${base}.bin"
  curl -sS --max-time 90 -o "$tmp" "$url" || { echo "错误: 下载失败" >&2; return 1; }

  # 按魔数定扩展名（服务端对 url 通常返回 JPEG，即便请求 png）
  if head -c 2 "$tmp" | od -An -tx1 | grep -qi 'ff d8'; then ext="jpg"
  elif head -c 4 "$tmp" | od -An -tx1 | grep -qi '89 50'; then ext="png"
  else ext="jpg"; fi
  local final="$OUT/${base}.${ext}"
  mv "$tmp" "$final"

  local w h bytes
  w=$(sips -g pixelWidth "$final" 2>/dev/null | awk '/pixelWidth/{print $2}')
  h=$(sips -g pixelHeight "$final" 2>/dev/null | awk '/pixelHeight/{print $2}')
  bytes=$(stat -f%z "$final")
  echo -e "${final}\t${w}x${h}\t${bytes} bytes"
}

rc=0
for ((i=0; i<COUNT; i++)); do
  gen_one "$i" || rc=1
done
exit $rc
