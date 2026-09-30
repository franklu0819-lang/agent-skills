#!/usr/bin/env bash
# 抖音视频下载辅助脚本：短链解析 / 视频下载 / 音轨抽取
# 用法:
#   fetch.sh resolve  <分享短链或 /video/ 链接或纯数字ID>   # 输出数字视频ID
#   fetch.sh download <视频流直链> <输出.mp4>               # 带 UA/Referer 下载并校验
#   fetch.sh audio    <视频.mp4> <输出.mp3>                 # ffmpeg 抽 16k 单声道音轨
set -euo pipefail

PROXY="${DOUYIN_PROXY:-http://127.0.0.1:7890}"
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36"
MOBILE_UA="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"

cmd="${1:-}"; [ -n "$cmd" ] || { sed -n '2,6p' "$0"; exit 1; }
shift

# curl 包装：默认走代理，失败自动降级直连（抖音 CDN 无需科学上网也可达）
cx() {
  curl -sL --max-time 30 -x "$PROXY" -A "$UA" "$@" \
    || curl -sL --max-time 30 -A "$UA" "$@"
}

case "$cmd" in
  resolve)
    input="${1:?缺少输入链接}"
    # 已是纯数字 ID
    if echo "$input" | grep -qE '^[0-9]{15,25}$'; then
      echo "$input"; exit 0
    fi
    # 链接里已带 /video/<ID> 则直接提取，不发网络请求
    id=$(echo "$input" | grep -oE '/video/([0-9]{15,25})' | head -1 | grep -oE '[0-9]{15,25}' || true)
    if [ -n "$id" ]; then echo "$id"; exit 0; fi
    # 短链：跟随 302 拿 Location（用移动端 UA，部分短链只对移动 UA 跳转）
    loc=$(curl -sI --max-time 20 -x "$PROXY" -A "$MOBILE_UA" "$input" \
       | grep -i '^location:' | head -1 | tr -d '\r' | awk '{print $2}')
    [ -n "$loc" ] || loc=$(curl -sI --max-time 20 -A "$MOBILE_UA" "$input" \
       | grep -i '^location:' | head -1 | tr -d '\r' | awk '{print $2}')
    id=$(echo "$loc" | grep -oE '/video/([0-9]{15,25})' | head -1 | grep -oE '[0-9]{15,25}' || true)
    [ -n "$id" ] || { echo "错误：无法从跳转地址解析视频 ID，Location=$loc" >&2; exit 1; }
    echo "$id"
    ;;

  download)
    url="${1:?缺少视频直链}"; out="${2:?缺少输出路径}"
    # 直链含 & ，必须加引号传入；本函数收到的已是单个参数
    code=$(curl -sL -w '%{http_code}' -o "$out" --max-time 300 \
      -x "$PROXY" -A "$UA" -H "Referer: https://www.douyin.com/" "$url" \
      || curl -sL -w '%{http_code}' -o "$out" --max-time 300 \
      -A "$UA" -H "Referer: https://www.douyin.com/" "$url")
    size=$(wc -c < "$out" | tr -d ' ')
    # 音轨/短视频可能只有几百 KB，阈值不宜过高
    if [ "$code" != "200" ] || [ "$size" -lt 100000 ]; then
      echo "错误：下载异常 http=$code size=${size}B（直链可能已过期，回浏览器重新提取 currentSrc）" >&2
      exit 1
    fi
    ftype=$(file -b "$out")
    echo "$ftype" | grep -q "ISO Media" || echo "警告：文件类型异常：$ftype（仍继续，请人工确认）" >&2
    echo "OK $out ($(( size / 1024 / 1024 ))MB) $ftype"
    ;;

  audio)
    in="${1:?缺少输入视频}"; out="${2:?缺少输出路径}"
    ffmpeg -y -hide_banner -loglevel error -i "$in" -vn -ac 1 -ar 16000 -b:a 64k "$out"
    echo "OK $out ($(du -h "$out" | cut -f1))"
    ;;

  *)
    echo "未知子命令：$cmd" >&2; sed -n '2,6p' "$0"; exit 1
    ;;
esac
