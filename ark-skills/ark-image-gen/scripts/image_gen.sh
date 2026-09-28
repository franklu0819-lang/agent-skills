#!/usr/bin/env bash
# 火山方舟 Seedream 系列图片生成：文生图 / 图生图 / 组图（直连 Ark API，无 arkcli 依赖）。
# 支持 seedream 全系模型别名、--ratio 比例换算、按模型像素范围自动钳制。
# 认证：环境变量 ARK_API_KEY，其次解析 ~/.zshrc 里的 export ARK_API_KEY；本脚本不读取、不存储任何密钥。
# 依赖：python3、curl
set -euo pipefail

DEFAULT_MODEL="doubao-seedream-5-0-260128"
BASE_URL="${ARK_BASE_URL:-https://ark.cn-beijing.volces.com/api/v3}"

usage() {
  cat <<'EOF'
用法: image_gen.sh "图片提示词" [选项]
      image_gen.sh --layers --ref 输入图.jpg [-m 5flash|5pro] ["要拆出的元素"] [选项]   # 多图层拆分

选项:
  -o, --output PATH     输出路径或前缀（默认 ./ark_image_<时间戳>；多图/组图自动加 -1/-2… 后缀；
                        多图层模式加 _z<序号>_<图层名> 后缀，并额外写 <前缀>_layers.json 元数据）
  -m, --model SPEC      模型：别名 5 / 5lite / 5flash / 5pro / 4.5 / 4，或完整模型名（默认 5 = doubao-seedream-5-0-260128）
  -s, --size SPEC       分辨率：宽x高 或 1K/2K/4K（快捷名直接透传，由服务端自适应比例）；
                        --layers 模式只接受 1K/1.5K/2K/auto 档位或不传（实测像素形式 400）
  -r, --ratio W:H       画面比例（如 16:9 / 9:16 / 4:3 / 3:2 / 21:9），与 -s 的像素基准配合换算：
                        `--ratio 16:9 -s 2K` = 2K 总像素的 16:9；只传 --ratio 用模型默认基准；
                        换算结果按模型像素范围自动钳制并提示
  -g, --group N         生成 N 张内容关联的组图（1-14；仅 5/5lite/4.5/4 支持，5flash/5pro 直接报错）
      --layers          多图层拆分：把 --ref 传入的 1 张图拆成 1 张底图 + 各元素透明 PNG 图层
                        （仅 5flash/5pro 支持；提示词可省略=自动全量拆分，也可点名元素；耗时约 1 分钟，按图层张数计费）
  --ref PATH|URL        参考图（可重复传多次做图生图/多图生图，最多 10 张；本地文件自动转 base64，建议 <3MB；
                        --layers 模式必须恰好 1 张）
  --seed N              固定随机种子（复现用）
  --watermark           画面加 AI 水印（默认不加）
  --b64                 响应用 b64_json 直接解码落盘（默认走 url 下载）
  --timeout SEC         请求超时秒数（默认 300）
      --dry-run         只打印将提交的参数 JSON，不实际生成
  -h, --help            显示本帮助

模型与像素范围（总像素，5/4.5/4/5pro 实测 2026-09-17，5flash 实测 2026-09-28）:
  5      doubao-seedream-5-0-260128       3,686,400 ~ 16,777,216（官方名 Seedream 5.0 lite；组图）
  5lite  同 5
  5flash doubao-seedream-5-0-flash-260915   921,600 ~  4,624,220（快速版；多图层；小图便宜）
  5pro   doubao-seedream-5-0-pro-260628     921,600 ~  4,624,220（多图层）
  4.5    doubao-seedream-4-5-251128       3,686,400 ~ 16,777,216（组图）
  4      doubao-seedream-4-0-250828         921,600 ~ 16,777,216（组图）

认证: export ARK_API_KEY=<火山方舟 ark- 开头的 Key>（或写在 ~/.zshrc）。

输出: 最后一行打印单行 JSON：
      {"ok":true,"images":["/abs/p-1.jpg"],"model":"...","size":"2560x1440","usage_total_tokens":14400}
      失败时 {"ok":false,"error":"..."} 并以非零码退出。
EOF
}

PROMPT="" OUTPUT="" MODEL="" SIZE_SPEC="" RATIO="" GROUP="" SEED="" WATERMARK="0" B64="0" TIMEOUT="300" DRY_RUN="0" LAYERS="0"
REFS=""

while [ $# -gt 0 ]; do
  case "$1" in
    -o|--output) OUTPUT="$2"; shift 2;;
    -m|--model) MODEL="$2"; shift 2;;
    -s|--size) SIZE_SPEC="$2"; shift 2;;
    -r|--ratio) RATIO="$2"; shift 2;;
    -g|--group) GROUP="$2"; shift 2;;
    --ref) REFS="$REFS
$2"; shift 2;;
    --seed) SEED="$2"; shift 2;;
    --watermark) WATERMARK="1"; shift;;
    --layers) LAYERS="1"; shift;;
    --b64) B64="1"; shift;;
    --timeout) TIMEOUT="$2"; shift 2;;
    --dry-run) DRY_RUN="1"; shift;;
    -h|--help) usage; exit 0;;
    -*) echo "未知选项: $1" >&2; usage >&2; exit 2;;
    *) if [ -z "$PROMPT" ]; then PROMPT="$1"; shift; else echo "多余的位置参数: $1" >&2; exit 2; fi;;
  esac
done

fail() { printf '{"ok":false,"error":%s}\n' "$(python3 -c 'import sys,json;print(json.dumps(sys.argv[1]))' "$1")"; exit 1; }

[ -n "$PROMPT" ] || [ "$LAYERS" = "1" ] || { usage >&2; fail "缺少提示词（--layers 多图层拆分模式下可省略）"; }

find_api_key() {
  if [ -n "${ARK_API_KEY:-}" ]; then printf '%s' "$ARK_API_KEY"; return 0; fi
  local zshrc="${ZDOTDIR:-$HOME}/.zshrc"
  [ -f "$zshrc" ] || return 1
  grep -E '^[[:space:]]*export[[:space:]]+ARK_API_KEY=' "$zshrc" | tail -1 \
    | sed -E 's/^[[:space:]]*export[[:space:]]+ARK_API_KEY="?([^"#+[:space:]]*)"?[[:space:]]*(#.*)?$/\1/'
}

PARAMS=$(python3 - "$PROMPT" "${MODEL:-5}" "$SIZE_SPEC" "$RATIO" "$GROUP" "$SEED" "$WATERMARK" "$B64" "$REFS" "$LAYERS" <<'PY'
import base64, json, math, mimetypes, os, sys
prompt, model_spec, size_spec, ratio, group, seed, watermark, b64, refs, layers = sys.argv[1:11]

def die(msg):
    print(msg, file=sys.stderr)   # 终端直接可读
    print(msg)                    # 经命令替换进入 fail 的 error 字段，结果 JSON 可读
    sys.exit(1)

# ---- 模型注册表（5/4.5/4/5pro 像素范围实测 2026-09-17；5flash 实测 2026-09-28）----
# 条目: (完整模型名, 最小总像素, 最大总像素, 默认基准像素, 能力: "group"=组图 / "layers"=多图层)
MODELS = {
    "5":    ("doubao-seedream-5-0-260128",    3686400, 16777216, 3686400, "group"),
    "50":   ("doubao-seedream-5-0-260128",    3686400, 16777216, 3686400, "group"),
    "5lite":("doubao-seedream-5-0-260128",    3686400, 16777216, 3686400, "group"),
    "50lite":("doubao-seedream-5-0-260128",   3686400, 16777216, 3686400, "group"),
    "lite": ("doubao-seedream-5-0-260128",    3686400, 16777216, 3686400, "group"),
    "5flash": ("doubao-seedream-5-0-flash-260915", 921600, 4624220, 4194304, "layers"),
    "50flash":("doubao-seedream-5-0-flash-260915", 921600, 4624220, 4194304, "layers"),
    "flash":  ("doubao-seedream-5-0-flash-260915", 921600, 4624220, 4194304, "layers"),
    "5pro": ("doubao-seedream-5-0-pro-260628",  921600,  4624220, 1048576, "layers"),
    "50pro":("doubao-seedream-5-0-pro-260628",  921600,  4624220, 1048576, "layers"),
    "pro":  ("doubao-seedream-5-0-pro-260628",  921600,  4624220, 1048576, "layers"),
    "45":   ("doubao-seedream-4-5-251128",    3686400, 16777216, 3686400, "group"),
    "4":    ("doubao-seedream-4-0-250828",      921600, 16777216, 1048576, "group"),
    "40":   ("doubao-seedream-4-0-250828",      921600, 16777216, 1048576, "group"),
}
for _k in list(MODELS):  # 完整模型名也命中注册表，获得同样的像素钳制与能力校验
    MODELS[MODELS[_k][0].lower().replace(".", "").replace("-", "").replace("_", "")] = MODELS[_k]
norm = model_spec.lower().replace(".", "").replace("-", "").replace("_", "")
if norm in MODELS:
    model, minp, maxp, base_default, caps = MODELS[norm]
elif model_spec.startswith("doubao-"):
    model, minp, maxp, base_default, caps = model_spec, None, None, None, None
else:
    die(f"未知模型 {model_spec}：可用别名 5 / 5lite / 5flash / 5pro / 4.5 / 4，或 doubao- 开头的完整模型名")

# ---- 能力校验（服务端对不支持的能力：lite 静默忽略 layer_decomposition，flash/pro 报错拒组图，都不能依赖服务端兜底）----
n_refs = len([r for r in refs.split("\n") if r])
if layers == "1":
    if caps is not None and caps != "layers":
        die(f"{model} 不支持多图层（layer_decomposition）：仅 5flash / 5pro 支持（lite/4.5/4 会被静默按普通单图生成并计费）")
    if group:
        die("--layers 与 -g 组图不能同时使用")
    if n_refs != 1:
        die(f"多图层模式需要恰好 1 张参考图（当前 {n_refs} 张）：把要拆层的图用 --ref 传入")
    if ratio:
        die("多图层模式不支持 --ratio 比例换算：size 只接受 1K/1.5K/2K/auto 档位或不传")
    if size_spec and size_spec.lower() not in ("1k", "1.5k", "2k", "auto"):
        die("多图层模式不支持像素形式的 -s（实测 400）：size 只接受 1K/1.5K/2K/auto 档位或不传")
if group and caps is not None and caps != "group":
    die(f"{model} 不支持组图（sequential_image_generation，服务端直接 400）：仅 5/5lite/4.5/4 支持，多图层请用 --layers")

QUICK = {"1k": 1048576, "2k": 4194304, "4k": 16777216}
def parse_wxh(s):
    try:
        w, h = s.lower().split("x")
        return int(w), int(h)
    except Exception:
        die(f"尺寸 {s} 无法解析：应为 宽x高（如 1920x1920）或 1K/2K/4K")

size_field = None
if layers == "1":
    if size_spec:   # 能力校验已保证只可能是 1K/1.5K/2K/auto
        size_field = size_spec.lower()
elif ratio:
    try:
        rw, rh = [int(x) for x in ratio.split(":")]
        assert rw > 0 and rh > 0
    except Exception:
        die(f"比例 {ratio} 无法解析：应为 宽:高（如 16:9）")
    base = base_default
    if size_spec:
        if size_spec.lower() in QUICK:
            base = QUICK[size_spec.lower()]
        else:
            w0, h0 = parse_wxh(size_spec)
            base = w0 * h0
    note = []
    if minp is not None:
        if base < minp:
            base = minp; note.append(f"像素基准低于模型下限，已提升到 {minp}")
        if base > maxp:
            base = maxp; note.append(f"像素基准高于模型上限，已压到 {maxp}")
    w = round(math.sqrt(base * rw / rh))
    h = round(w * rh / rw)
    if minp is not None and w * h < minp:
        w = math.ceil(math.sqrt(minp * rw / rh)); h = round(w * rh / rw)
    if maxp is not None and w * h > maxp:
        w = math.floor(math.sqrt(maxp * rw / rh)); h = round(w * rh / rw)
        if w * h > maxp:   # h 的 round 可能回补超界，向下压回
            h = maxp // w
    if note:
        print("提示: " + "；".join(note), file=sys.stderr)
    size_field = f"{w}x{h}"
elif size_spec:
    if size_spec.lower() in QUICK:
        size_field = size_spec.lower()   # 1K/2K/4K 透传，服务端自适应比例
    else:
        w, h = parse_wxh(size_spec)
        if minp is not None:
            px = w * h
            if px < minp or px > maxp:
                px2 = min(max(px, minp), maxp)
                k = math.sqrt(px2 / px)
                w, h = round(w * k), round(h * k)
                print(f"提示: 像素 {px} 超出模型范围 [{minp}, {maxp}]，已调整为 {w}x{h}", file=sys.stderr)
        size_field = f"{w}x{h}"
# 都不传 size/ratio → 不带 size 字段，走服务端默认

content_p = {"model": model, "watermark": watermark == "1",
             "response_format": "b64_json" if b64 == "1" else "url"}
if prompt or layers != "1":   # 多图层模式允许无提示词（自动全量拆分；空 prompt 键会破坏该语义，整个不发）
    content_p["prompt"] = prompt
if size_field:
    content_p["size"] = size_field

ref_list = [r for r in refs.split("\n") if r]
if ref_list:
    urls = []
    for r in ref_list:
        if r.startswith(("http://", "https://", "data:")):
            urls.append(r)
        else:
            if not os.path.isfile(r):
                die(f"参考图不存在: {r}")
            with open(r, "rb") as f:
                raw = f.read()
                if layers == "1":
                    mime = mimetypes.guess_type(r)[0] or "image/jpeg"
                    urls.append(f"data:{mime};base64," + base64.b64encode(raw).decode())  # 图层模式：单数 image + data URL 前缀（2026-09-28 实测唯一被接受的形态）
                else:
                    urls.append(base64.b64encode(raw).decode())  # 裸 b64（2026-09-18 实测：images:[b64] 唯一被接受的形态）
    if layers == "1":
        content_p["image"] = urls[0]      # 单数 image 字段（images 数组会报 requires exactly one input image）
        content_p["layer_decomposition"] = True
    else:
        content_p["images"] = urls        # 顶层 images 数组（单数 image 字段实测 400）
if group:
    content_p["sequential_image_generation"] = "auto"
    content_p["sequential_image_generation_options"] = {"max_images": int(group)}
if seed:
    content_p["seed"] = int(seed)
print(json.dumps(content_p, ensure_ascii=False))
PY
) || fail "$PARAMS"

if [ "$DRY_RUN" = "1" ]; then
  printf '{"ok":true,"dry_run":true,"params":%s}\n' "$PARAMS"
  exit 0
fi

API_KEY=$(find_api_key) || true
[ -n "$API_KEY" ] || fail "缺少 API Key：请 export ARK_API_KEY=<火山方舟 ark- 开头的 Key>，或写入 ~/.zshrc"

PARAMS_FILE=$(mktemp)
printf '%s' "$PARAMS" > "$PARAMS_FILE"
RESP=$(curl -sS --max-time "$TIMEOUT" -X POST "$BASE_URL/images/generations" \
  -H "Authorization: Bearer $API_KEY" -H "Content-Type: application/json" -d @"$PARAMS_FILE") \
  || { rm -f "$PARAMS_FILE"; fail "curl 请求失败"; }
rm -f "$PARAMS_FILE"
CODE_INFO=$(printf '%s' "$RESP" | python3 -c 'import sys,json
try:
  d=json.load(sys.stdin)
  print("ERR " + (d["error"].get("message") or json.dumps(d["error"], ensure_ascii=False)) if "error" in d else "OK")
except Exception:
  print("BADJSON")') || CODE_INFO="BADJSON"
[ "$CODE_INFO" = "OK" ] || fail "生成失败: ${CODE_INFO#ERR }（HTTP 响应: $(printf '%s' "$RESP" | head -c 300)）"

PARAMS_FILE=$(mktemp); RESP_FILE=$(mktemp)
printf '%s' "$PARAMS" > "$PARAMS_FILE"; printf '%s' "$RESP" > "$RESP_FILE"
RESULT=$(python3 - "$OUTPUT" "$PARAMS_FILE" "$RESP_FILE" <<'PY'
import base64, json, mimetypes, os, re, subprocess, sys, time
output = sys.argv[1]
params = json.loads(open(sys.argv[2]).read())
resp = json.loads(open(sys.argv[3]).read())
items = resp.get("data") or []
if not items:
    print(json.dumps({"ok": False, "error": "响应无 data 数组: " + json.dumps(resp, ensure_ascii=False)[:300]}, ensure_ascii=False))
    sys.exit(1)
ts = time.strftime("%Y%m%d_%H%M%S")
base = output or f"./ark_image_{ts}"
layer_mode = items[0].get("z_index") is not None   # 多图层响应：底图 z_index=0 + 各图层
def safe_name(s):
    # 单引号写作 \x27：heredoc 内出现不配对的 ' 会破坏 bash 3.2（macOS 自带）对 $( ) 内 heredoc 的解析
    s = re.sub(r"[/\\:*?\"<>|\x27\s]+", "_", s or "")
    return s[:30].strip("_") or "layer"
paths, layer_meta = [], []
for i, im in enumerate(items):
    if layer_mode:
        root, _ = os.path.splitext(base)
        tag = "base" if im.get("z_index", 0) == 0 and not im.get("name") else safe_name(im.get("name"))
        path = f"{root}_z{im.get('z_index', i):02d}_{tag}" + (".png" if im.get("output_format") == "png" else ".jpg")
    elif len(items) > 1:
        root, ext = os.path.splitext(base)
        path = f"{root}-{i+1}{ext or '.jpg'}"
    else:
        path = base if os.path.splitext(base)[1] else base + ".jpg"
    if im.get("b64_json"):
        with open(path, "wb") as f:
            f.write(base64.b64decode(im["b64_json"]))
    else:
        url = im.get("url")
        if not url:
            print(json.dumps({"ok": False, "error": "data 项缺少 url/b64_json"}, ensure_ascii=False)); sys.exit(1)
        subprocess.run(["curl", "-sSL", "--fail", "-o", path, url], check=True)
    kind = subprocess.run(["file", "-b", "--mime-type", path], capture_output=True, text=True).stdout.strip()
    ext_map = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
    want = ext_map.get(kind)
    if want and not path.lower().endswith(want):
        new = os.path.splitext(path)[0] + want
        os.replace(path, new)
        path = new
    absp = os.path.abspath(path)
    paths.append(absp)
    if layer_mode:
        layer_meta.append({"path": absp, "z_index": im.get("z_index"), "name": im.get("name"),
                           "description": im.get("description"), "size": im.get("size"),
                           "output_format": im.get("output_format"), "bounding_box": im.get("bounding_box")})
layers_json = None
if layer_mode:   # 叠放次序/边界框/名称元数据，供后续按 z_index 还原或单独编辑图层
    root, _ = os.path.splitext(base)
    layers_json = os.path.abspath(root + "_layers.json")
    with open(layers_json, "w") as f:
        json.dump(layer_meta, f, ensure_ascii=False, indent=2)
usage = resp.get("usage") or {}
result = {"ok": True, "images": paths, "model": params.get("model"),
          "size": params.get("size", "adaptive"),
          "usage_total_tokens": usage.get("total_tokens"),
          "generated_images": usage.get("generated_images")}
if layers_json:
    result["layers_json"] = layers_json
print(json.dumps(result, ensure_ascii=False))
PY
)
rm -f "$PARAMS_FILE" "$RESP_FILE"

if printf '%s' "$RESULT" | python3 -c 'import sys,json; sys.exit(0 if json.load(sys.stdin).get("ok") else 1)' 2>/dev/null; then
  :
else
  ERR=$(printf '%s' "$RESULT" | python3 -c 'import sys,json;print(json.load(sys.stdin).get("error",""))' 2>/dev/null || echo "$RESULT")
  fail "$ERR"
fi
printf '%s\n' "$RESULT"
