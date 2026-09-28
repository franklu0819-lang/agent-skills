#!/usr/bin/env bash
# 火山方舟视频生成一条龙：本地校验 → 提交任务 → 轮询状态 → 下载 MP4（直连 Ark API，无 arkcli 依赖）。
# 认证：环境变量 ARK_API_KEY，其次解析 ~/.zshrc 里的 export ARK_API_KEY；本脚本不读取、不存储任何密钥。
# 设计原则：一切能在本地拦住的错误（参数越界、互斥模式、模型能力不符）都在提交前拦住，
#           并在提交前打印成本预估——视频生成按成功任务计费，少一次无效提交就少一分钱。
# 参数传递：请求体全程走临时文件（不经过 argv）——macOS ARG_MAX 约 1MB，
#           base64 素材动辄数 MB，经 argv 传给 python/curl 会直接 E2BIG。
# 依赖：python3、curl；ffprobe 可选（存在时用于校验本地参考媒体总时长）
set -euo pipefail

DEFAULT_MODEL="25"   # doubao-seedance-2-5-260628
BASE_URL="${ARK_BASE_URL:-https://ark.cn-beijing.volces.com/api/v3}"

usage() {
  cat <<'EOF'
用法: ark_video.sh "视频提示词" [选项]

选项:
  -o, --output PATH      输出 MP4 路径（默认 ./ark_video_<task_id>.mp4）
  -m, --model NAME       模型别名（默认 25 = doubao-seedance-2-5-260628）:
                           25 / 2.5   Seedance 2.5 —— 复杂场景/短剧/长口播首选（单段最长 30s，参考 30图/10视频/10音频）
                           2mini      2.0 mini（最便宜试提示词；仅 480p/720p，最长 15s）
                           2fast      2.0 fast（仅 480p/720p，最长 15s）
                           2 / 2pro   2.0 标准版（最长 15s，支持 4k）
                           1pro       1.0 pro —— 简单视频（无声，最长 12s）
                           1fast      1.0 pro fast（无声）
                         仅支持以上白名单；1.0-lite 系与 1.5pro 已随官方下线移除。
                         -s/--camera-fixed 仅 1pro/1fast 系有效；2.x 固定机位请写进提示词（"镜头固定不动、画面平稳"）
  -d, --duration SEC     视频时长秒数（默认 5；2.5 上限 30，2.0 系上限 15，1.0 系上限 12；
                         --task-type edit 时必须传 -d -1，表示时长跟随参考视频）
  -r, --ratio RATIO      画幅比例：16:9 / 9:16 / 1:1 / adaptive
                         （2.5 的首帧/首尾帧/extend/edit 任务必须 adaptive，否则 API 拒绝）
  -R, --resolution RES   分辨率：480p / 720p / 1080p（2.0 标准版另支持 4k；mini/fast 不支持 1080p 以上）
  -s, --seed N           固定随机种子 —— 仅 1.0 系支持，2.x 传了会被忽略并提示（官方文档：相同 seed 也不保证一致）
      --camera-fixed     锁定虚拟相机 —— 仅 1.0 系支持；2.x 会忽略并提示
      --no-audio         不生成同步音频（1.0 系无音频能力，自动忽略）
      --watermark        画面加水印
      --draft            草稿模式：更快更便宜、画质低 —— 试提示词专用；2.5 配合"draft 480p 样片→正式重出"流程
      --image PATH|URL   首帧图（图生视频）；与 --ref-* 互斥（首帧、首尾帧、全模态参考是 3 种互斥模式）；
                         2.5 上本参数要求 -r adaptive
      --last-frame PATH|URL  尾帧图（首尾帧模式，须与 --image 同用；ratio 用 adaptive）
      --ref-image PATH|URL   参考图（可重复多次）：角色大头照+全身照、场景空镜等，提示词里用 "@图片N" 引用
      --ref-video PATH|URL   参考视频（可重复）：动作/运镜/风格/延长素材，提示词里用 "@视频N" 引用
      --ref-audio PATH|URL   参考音频（可重复）：音色参考，台词口型同步；提示词里用 "@音频N" 引用
      --return-last-frame    额外返回生成视频的尾帧图（存为 <output>_last_frame.jpg）—— 跨段接力的标准做法
      --task-type TYPE   仅 2.5：auto(默认)/reference/edit/extend；extend=视频延长、edit=视频编辑
                         （edit/extend 要求 -r adaptive；edit 还要求 -d -1 且至少 1 段 --ref-video）
      --timeout SEC      轮询超时秒数（默认 900；1080p/30s 长任务建议 1800）
      --keep-url         结果 JSON 里额外保留 video_url（TOS 签名 24 小时过期）
      --dry-run          只做本地校验并打印将提交的参数 JSON 与成本预估，不实际创建任务
  -h, --help             显示本帮助

认证: export ARK_API_KEY=<火山方舟控制台 API Key>（ark- 开头；或写在 ~/.zshrc）。
      可用 ARK_BASE_URL 覆盖 API 基址（默认 https://ark.cn-beijing.volces.com/api/v3）。

输出: 最后一行打印单行 JSON：
      {"ok":true,"task_id":"cgt-...","status":"succeeded","video_path":"...","last_frame_path":"...","usage_total_tokens":...}
      失败时 {"ok":false,"stage":"args|submit|poll|download","error":"..."} 并以非零码退出。
EOF
}

PROMPT="" OUTPUT="" MODEL="$DEFAULT_MODEL" DURATION="5" RATIO="16:9" RESOLUTION="720p"
SEED="" AUDIO="1" WATERMARK="0" CAMERA_FIXED="0" DRAFT="0" IMAGE="" LAST_FRAME=""
REF_IMAGES=() REF_VIDEOS=() REF_AUDIOS=()
RETURN_LAST_FRAME="0" TASK_TYPE="" TIMEOUT="900" KEEP_URL="0" DRY_RUN="0"

while [ $# -gt 0 ]; do
  case "$1" in
    -o|--output) OUTPUT="$2"; shift 2;;
    -m|--model) MODEL="$2"; shift 2;;
    -d|--duration) DURATION="$2"; shift 2;;
    -r|--ratio) RATIO="$2"; shift 2;;
    -R|--resolution) RESOLUTION="$2"; shift 2;;
    -s|--seed) SEED="$2"; shift 2;;
    --no-audio) AUDIO="0"; shift;;
    --watermark) WATERMARK="1"; shift;;
    --camera-fixed) CAMERA_FIXED="1"; shift;;
    --draft) DRAFT="1"; shift;;
    --image) IMAGE="$2"; shift 2;;
    --last-frame) LAST_FRAME="$2"; shift 2;;
    --ref-image) REF_IMAGES+=("$2"); shift 2;;
    --ref-video) REF_VIDEOS+=("$2"); shift 2;;
    --ref-audio) REF_AUDIOS+=("$2"); shift 2;;
    --return-last-frame) RETURN_LAST_FRAME="1"; shift;;
    --task-type) TASK_TYPE="$2"; shift 2;;
    --timeout) TIMEOUT="$2"; shift 2;;
    --keep-url) KEEP_URL="1"; shift;;
    --dry-run) DRY_RUN="1"; shift;;
    -h|--help) usage; exit 0;;
    -*) echo "未知选项: $1" >&2; usage >&2; exit 2;;
    *) if [ -z "$PROMPT" ]; then PROMPT="$1"; shift; else echo "多余的位置参数: $1" >&2; exit 2; fi;;
  esac
done

fail() { printf '{"ok":false,"stage":"%s","error":%s}\n' "$1" "$(python3 -c 'import sys,json;print(json.dumps(sys.argv[1]))' "$2")"; exit 1; }

[ -n "$PROMPT" ] || { usage >&2; fail "args" "缺少提示词"; }

find_api_key() {
  if [ -n "${ARK_API_KEY:-}" ]; then printf '%s' "${ARK_API_KEY}"; return 0; fi
  local zshrc="${ZDOTDIR:-$HOME}/.zshrc"
  [ -f "$zshrc" ] || return 1
  grep -E '^[[:space:]]*export[[:space:]]+ARK_API_KEY=' "$zshrc" | tail -1 \
    | sed -E 's/^[[:space:]]*export[[:space:]]+ARK_API_KEY="?([^"#+[:space:]]*)"?[[:space:]]*(#.*)?$/\1/'
}

# 数组以 \x1f 连接成单个参数传给 python（兼容 bash 3.2 的空数组）
join_arr() {
  local name="$1" total=0
  eval "total=\${#$name[@]}"
  if [ "$total" -eq 0 ]; then printf ''; return; fi
  eval "local IFS=\$'\\x1f'; printf '%s' \"\${$name[*]}\""
}
REF_IMAGES_J=$(join_arr REF_IMAGES)
REF_VIDEOS_J=$(join_arr REF_VIDEOS)
REF_AUDIOS_J=$(join_arr REF_AUDIOS)

# ---- 阶段 1：构造参数 + 全部本地校验（此时素材还是路径/URL，体积小，可走 argv；不产生任何 API 调用）----
PARAMS=$(python3 - "$PROMPT" "$MODEL" "$DURATION" "$RATIO" "$RESOLUTION" "$SEED" "$AUDIO" \
  "$WATERMARK" "$CAMERA_FIXED" "$DRAFT" "$IMAGE" "$LAST_FRAME" "$RETURN_LAST_FRAME" "$TASK_TYPE" \
  "$REF_IMAGES_J" "$REF_VIDEOS_J" "$REF_AUDIOS_J" <<'PY'
import json, sys

argv = sys.argv[1:]
(prompt, model, duration, ratio, resolution, seed, audio, watermark, camera_fixed,
 draft, image, last_frame, return_last_frame, task_type) = argv[:14]
ref_images = [x for x in argv[14].split("\x1f") if x]
ref_videos = [x for x in argv[15].split("\x1f") if x]
ref_audios = [x for x in argv[16].split("\x1f") if x]

def die(msg):
    # 错误打到 stdout（会被命令替换捕获进 fail JSON），非零码退出
    print(msg)
    sys.exit(1)

# ---- 模型能力矩阵（与官方文档 2026-09 口径一致）----
# name: (模型ID, 有声, draft, 时长区间, 分辨率集合, 支持 seed/camera_fixed, 价格{分辨率档: (不含视频, 含视频) 元/百万tokens})
MODELS = {
    "25":     ("doubao-seedance-2-5-260628", True, True, (4, 30), {"480p", "720p", "1080p"}, False,
               {"480p": (70, 42), "720p": (70, 42), "1080p": (77, 46)}),
    "25pro":  ("doubao-seedance-2-5-260628", True, True, (4, 30), {"480p", "720p", "1080p"}, False,
               {"480p": (70, 42), "720p": (70, 42), "1080p": (77, 46)}),
    "2mini":  ("doubao-seedance-2-0-mini-260615", True, True, (4, 15), {"480p", "720p"}, False,
               {"480p": (23, 14), "720p": (23, 14)}),
    "20mini": ("doubao-seedance-2-0-mini-260615", True, True, (4, 15), {"480p", "720p"}, False,
               {"480p": (23, 14), "720p": (23, 14)}),
    "2fast":  ("doubao-seedance-2-0-fast-260128", True, True, (4, 15), {"480p", "720p"}, False,
               {"480p": (37, 22), "720p": (37, 22)}),
    "20fast": ("doubao-seedance-2-0-fast-260128", True, True, (4, 15), {"480p", "720p"}, False,
               {"480p": (37, 22), "720p": (37, 22)}),
    "2":      ("doubao-seedance-2-0-260128", True, True, (4, 15), {"480p", "720p", "1080p", "4k"}, False,
               {"480p": (46, 28), "720p": (46, 28), "1080p": (51, 31), "4k": (26, 16)}),
    "20":     ("doubao-seedance-2-0-260128", True, True, (4, 15), {"480p", "720p", "1080p", "4k"}, False,
               {"480p": (46, 28), "720p": (46, 28), "1080p": (51, 31), "4k": (26, 16)}),
    "2pro":   ("doubao-seedance-2-0-260128", True, True, (4, 15), {"480p", "720p", "1080p", "4k"}, False,
               {"480p": (46, 28), "720p": (46, 28), "1080p": (51, 31), "4k": (26, 16)}),
    "1pro":   ("doubao-seedance-1-0-pro-250528", False, False, (5, 12), {"480p", "720p", "1080p"}, True, {}),
    "10pro":  ("doubao-seedance-1-0-pro-250528", False, False, (5, 12), {"480p", "720p", "1080p"}, True, {}),
    "1":      ("doubao-seedance-1-0-pro-250528", False, False, (5, 12), {"480p", "720p", "1080p"}, True, {}),
    "1fast":  ("doubao-seedance-1-0-pro-fast-251015", False, False, (5, 12), {"480p", "720p", "1080p"}, True, {}),
    "10fast": ("doubao-seedance-1-0-pro-fast-251015", False, False, (5, 12), {"480p", "720p", "1080p"}, True, {}),
}
norm = model.lower().replace(".", "").replace("-", "").replace("_", "")
if norm not in MODELS:
    die(f"不支持的模型 {model}。可用：25（默认）/ 2mini / 2fast / 2 / 1pro / 1fast；"
        f"1.0-lite 系与 1.5pro 已随官方下线移除，勿再使用")
model_id, audio_cap, draft_cap, dur_range, res_set, seed_cap, price = MODELS[norm]
is_25 = "2-5" in model_id
is_10 = model_id.startswith("doubao-seedance-1-0")

# ---- 时长（edit 任务为 -1，须先解析）----
try:
    dur = int(duration)
except ValueError:
    die(f"时长必须是整数秒（edit 任务用 -1），收到: {duration}")

# ---- task-type（仅 2.5；必须在时长范围检查之前处理 edit 的 -1）----
if task_type:
    if not is_25:
        die("--task-type 仅 Seedance 2.5 支持（omni_reference_task_type）")
    if task_type not in ("auto", "reference", "edit", "extend"):
        die(f"--task-type 只能是 auto/reference/edit/extend，收到: {task_type}")
    if task_type in ("edit", "extend") and ratio != "adaptive":
        die(f"2.5 {task_type} 任务 ratio 必须为 adaptive（加 -r adaptive）")
    if task_type == "edit":
        if dur != -1:
            die("2.5 edit 任务 duration 必须为 -1（加 -d -1，输出时长跟随参考视频）")
        if not ref_videos:
            die("2.5 edit 任务必须至少包含 1 段参考视频（--ref-video）")
    if task_type == "extend" and not ref_videos:
        die("2.5 extend 任务必须至少包含 1 段参考视频（--ref-video，即被延长的素材）")

# ---- 时长范围（edit 已豁免）----
if task_type != "edit":
    lo, hi = dur_range
    if not (lo <= dur <= hi):
        die(f"模型 {model_id} 时长须在 {lo}-{hi}s（收到 {dur}s）。要更长内容请用分段生成+拼接或 2.5 的 extend 延长，不要硬提时长")

# ---- 分辨率 ----
if resolution not in res_set:
    die(f"模型 {model_id} 不支持 {resolution}，可用: {'/'.join(sorted(res_set))}")

# ---- 互斥模式：首帧 / 首尾帧 / 全模态参考 ----
has_first = bool(image)
has_last = bool(last_frame)
has_refs = bool(ref_images or ref_videos or ref_audios)
if has_last and not has_first:
    die("--last-frame 必须与 --image（首帧）同用")
if has_first and has_refs:
    die("首帧/首尾帧与全模态参考是 3 种互斥模式：--image/--last-frame 不能与 --ref-* 混在一次请求（混用=模型忽略你的图，纯浪费一次提交）")
if is_10 and has_refs:
    die("1.0 系不支持 --ref-* 参考素材（仅 --image 首帧图生视频；参考生视频请用 2.0/2.5）")
if has_first and is_25 and ratio != "adaptive":
    die("Seedance 2.5 的首帧/首尾帧任务 ratio 仅支持 adaptive（加 -r adaptive；画幅跟随首帧图）")

# ---- 参考素材数量（2.0: 9图/3视频/3音频；2.5: 30图/10视频/10音频；总时长在阶段2校验本地文件）----
lim = (9, 3, 3) if not is_25 else (30, 10, 10)
if len(ref_images) > lim[0]: die(f"参考图最多 {lim[0]} 张（收到 {len(ref_images)}）")
if len(ref_videos) > lim[1]: die(f"参考视频最多 {lim[1]} 段（收到 {len(ref_videos)}）")
if len(ref_audios) > lim[2]: die(f"参考音频最多 {lim[2]} 段（收到 {len(ref_audios)}）")
# 2.0 音频不可单独输入；2.5 允许纯音频
if ref_audios and not ref_images and not ref_videos and not is_25:
    die("2.0 系不支持纯音频输入：参考音频须至少搭配 1 张参考图或 1 段参考视频（2.5 才支持纯音频驱动）")

# ---- seed / camera_fixed 仅 1.0 系 ----
warn = []
if seed and not seed_cap:
    warn.append("已忽略 --seed：官方文档 seed 仅 Seedance 1.0 pro 系支持，且相同 seed 也不保证跨片段一致——一致性请靠固定参考素材集")
if camera_fixed == "1" and not seed_cap:
    warn.append("已忽略 --camera-fixed：仅 1.0 系支持——2.x 固定机位请写进提示词（'镜头固定不动、画面平稳'）")
if draft == "1" and not draft_cap:
    warn.append("已忽略 --draft：draft 仅 2.x 系支持")

# ---- 组装 content（本地路径先原样放入，阶段 2 统一转 data URI）----
content = [{"type": "text", "text": prompt}]

for p in ref_images:
    content.append({"type": "image_url", "image_url": {"url": p}, "role": "reference_image"})
for p in ref_videos:
    content.append({"type": "video_url", "video_url": {"url": p}, "role": "reference_video"})
for p in ref_audios:
    content.append({"type": "audio_url", "audio_url": {"url": p}, "role": "reference_audio"})
if has_first:
    # 首尾帧模式下官方要求两个 image_url 的 role 都必填；单独首帧不写 role
    content.append({"type": "image_url", "image_url": {"url": image},
                    **({"role": "first_frame"} if has_last else {})})
if has_last:
    content.append({"type": "image_url", "image_url": {"url": last_frame}, "role": "last_frame"})

p = {"model": model_id, "content": content, "duration": dur, "ratio": ratio,
     "resolution": resolution, "watermark": watermark == "1"}
if audio_cap:
    p["generate_audio"] = audio == "1"
elif audio == "0":
    warn.append("该 1.0 系模型无音频能力，--no-audio 已忽略")
if seed and seed_cap:
    p["seed"] = int(seed)
if camera_fixed == "1" and seed_cap:
    p["camera_fixed"] = True
if draft == "1" and draft_cap:
    p["draft"] = True
if task_type:
    p["omni_reference_task_type"] = task_type
if return_last_frame == "1":
    p["return_last_frame"] = True

p["_warn"] = warn
p["_est"] = {"res": resolution, "ratio": ratio, "dur": dur,
             "price": price, "has_ref_video": bool(ref_videos)}
print(json.dumps(p, ensure_ascii=False))
PY
) || fail "args" "$PARAMS"

# ---- 阶段 2：请求体落临时文件，后续所有处理走文件（规避 argv 1MB 上限）----
PARAMS_FILE=$(mktemp "${TMPDIR:-/tmp}/ark_video_params.XXXXXX.json")
trap 'rm -f "$PARAMS_FILE"' EXIT
printf '%s' "$PARAMS" > "$PARAMS_FILE"

# 本地素材 → data URI + 单文件/总量上限 + （有 ffprobe 时）参考视频/音频总时长上限
if ! python3 - "$PARAMS_FILE" <<'PY'
import base64, json, mimetypes, os, subprocess, sys

path = sys.argv[1]
params = json.load(open(path))
content = params["content"]
MEDIA = {"image_url", "video_url", "audio_url"}

def fail(msg):
    print(f"素材错误: {msg}", file=sys.stderr)
    sys.exit(1)

def probe_dur(f):
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "csv=p=0", f], capture_output=True, text=True, timeout=10)
        if r.returncode == 0 and r.stdout.strip():
            return float(r.stdout.strip().splitlines()[0])
    except Exception:
        pass
    return None

total_bytes = 0
local_media = {"video_url": [], "audio_url": []}
for item in content:
    if item["type"] not in MEDIA:
        continue
    key, url = item["type"], item[item["type"]]["url"]
    if url.startswith(("http://", "https://", "data:", "asset://")):
        continue
    if not os.path.isfile(url):
        fail(f"文件不存在: {url}")
    size = os.path.getsize(url)
    total_bytes += size
    cap = {"image_url": 30, "video_url": 60, "audio_url": 15}[key]
    if size > cap * 1048576:
        fail(f"{url} {size/1048576:.1f}MB 超过 {cap}MB 本地上限——请压缩或改用公网 URL/方舟素材库 asset://")
    if key in local_media:
        d = probe_dur(url)
        if d is not None:
            local_media[key].append(d)

if total_bytes > 45 * 1048576:
    fail(f"本地素材合计 {total_bytes/1048576:.1f}MB，base64 编码后将超出官方 64MB 请求体上限——请改用公网 URL 或 asset://")

# 参考媒体总时长上限（官方：2.0 视频/音频各 ≤15s，2.5 各 ≤30s；仅能校验本地文件）
lim_s = 30 if "2-5" in params["model"] else (15 if "2-0" in params["model"] else None)
if lim_s:
    for key, label in (("video_url", "参考视频"), ("audio_url", "参考音频")):
        durs = local_media[key]
        if durs and sum(durs) > lim_s + 0.5:
            fail(f"{label}总时长 {sum(durs):.1f}s 超过 {lim_s}s 上限（本地可测部分）——请删减素材或分段")

for item in content:
    if item["type"] not in MEDIA:
        continue
    key, url = item["type"], item[item["type"]]["url"]
    if url.startswith(("http://", "https://", "data:", "asset://")):
        continue
    mime = mimetypes.guess_type(url)[0] or ("image/jpeg" if key == "image_url" else "video/mp4" if key == "video_url" else "audio/mpeg")
    item[key]["url"] = "data:" + mime + ";base64," + base64.b64encode(open(url, "rb").read()).decode()
json.dump(params, open(path, "w"), ensure_ascii=False)
PY
then
  fail "args" "本地素材处理失败（原因见上方错误信息）"
fi

# ---- 阶段 3：警告与成本预估（stderr），顺手把 _warn/_est 从请求体剔除 ----
if ! python3 - "$PARAMS_FILE" <<'PY'
import json, sys

path = sys.argv[1]
p = json.load(open(path))
for w in p.get("_warn", []):
    print(f"提示: {w}", file=sys.stderr)
est = p.get("_est") or {}
p.pop("_warn", None); p.pop("_est", None)
price = est.get("price") or {}
dur = est.get("dur", 0)
if not price or est.get("ratio") == "adaptive" or dur <= 0:
    print("成本预估: 无法估算（adaptive 画幅/时长跟随素材/该模型未纳入价目），提交后以 usage 为准", file=sys.stderr)
else:
    # 档位=像素预算（实测校准 2026-09-27：480p/1:1 实际输出 640×640@24fps，
    # usage=实际时长×宽×高×24/1024 精确吻合；官方 16:9/480p 示例 0.67 元/s 亦与预算 409600 一致）
    budget = {"480p": 409600, "720p": 921600, "1080p": 2073600, "4k": 8294400}[est["res"]]
    short = {"480p": 480, "720p": 720, "1080p": 1080, "4k": 2160}[est["res"]]
    r = est["ratio"]
    if r == "16:9":
        w, h = round(budget / short), short
    elif r == "9:16":
        w, h = short, round(budget / short)
    else:  # 1:1 等：按像素预算开方（480p→640×640，不是 480×480）
        w = h = round(budget ** 0.5)
    tokens = dur * w * h * 24 / 1024
    unit = price[est["res"]][1 if est.get("has_ref_video") else 0]
    print(f"成本预估: ≈{tokens/1e6*unit:.2f} 元（{dur}s/{est['res']}/{r}，约 {round(tokens)} tokens，单价 {unit} 元/百万tokens，以 usage 为准）"
          f"——先用 --draft/480p 低档验证，满意再出正式片（draft 不降单价）", file=sys.stderr)
json.dump(p, open(path, "w"), ensure_ascii=False)
PY
then
  fail "args" "成本预估阶段失败"
fi

if [ "$DRY_RUN" = "1" ]; then
  # dry-run 输出对 data URI 脱敏（否则会打印数 MB 的 base64）
  python3 - "$PARAMS_FILE" <<'PY'
import json, sys
p = json.load(open(sys.argv[1]))
for it in p.get("content", []):
    if it.get("type") in ("image_url", "video_url", "audio_url"):
        u = it[it["type"]]["url"]
        if u.startswith("data:"):
            it[it["type"]]["url"] = f"<data:URI 约{len(u)//1024}KB，已脱敏>"
print(json.dumps({"ok": True, "dry_run": True, "params": p}, ensure_ascii=False))
PY
  exit 0
fi

API_KEY=$(find_api_key) || true
[ -n "$API_KEY" ] || fail "env" "缺少 API Key：请 export ARK_API_KEY=<火山方舟 ark- 开头的 Key>，或写入 ~/.zshrc"

err_msg() { python3 -c 'import sys,json
try:
  d=json.load(sys.stdin); e=d.get("error") or {}
  print(e.get("message") or d.get("message") or json.dumps(d,ensure_ascii=False))
except Exception:
  print(sys.stdin.read())' 2>/dev/null <<<"$1"; }

# http METHOD URL：POST 体固定取 $PARAMS_FILE（大请求体不经 argv）；stdout=响应体，RESP_CODE=HTTP 状态码
http() {
  local method="$1" url="$2" t
  t=$(mktemp)
  if [ "$method" = "POST" ]; then
    RESP_CODE=$(curl -sS -X POST -H "Authorization: Bearer $API_KEY" \
      -H "Content-Type: application/json" --data-binary @"$PARAMS_FILE" -w '%{http_code}' -o "$t" "$url") \
      || { rm -f "$t"; fail "network" "curl 请求失败: $url"; }
  else
    RESP_CODE=$(curl -sS -X "$method" -H "Authorization: Bearer $API_KEY" \
      -w '%{http_code}' -o "$t" "$url") || { rm -f "$t"; fail "network" "curl 请求失败: $url"; }
  fi
  RESP=$(cat "$t"); rm -f "$t"
}

# 1) 提交任务
http POST "$BASE_URL/contents/generations/tasks"
[ "$RESP_CODE" = "200" ] || fail "submit" "创建任务失败(HTTP $RESP_CODE): $(err_msg "$RESP")"
TASK_ID=$(printf '%s' "$RESP" | python3 -c 'import sys,json;print(json.load(sys.stdin)["id"])' 2>/dev/null) \
  || fail "submit" "无法从响应解析任务 id: $RESP"

# 2) 轮询直到终态（queued → running → succeeded/failed）
STATUS=""; POLL=10; ELAPSED=0
while [ "$ELAPSED" -lt "$TIMEOUT" ]; do
  http GET "$BASE_URL/contents/generations/tasks/$TASK_ID"
  [ "$RESP_CODE" = "200" ] || fail "poll" "查询任务失败(HTTP $RESP_CODE): $(err_msg "$RESP")"
  STATUS=$(printf '%s' "$RESP" | python3 -c 'import sys,json;print(json.load(sys.stdin).get("status",""))' 2>/dev/null) \
    || fail "poll" "无法解析任务状态: $RESP"
  case "$STATUS" in
    succeeded|failed|cancelled) break;;
  esac
  sleep "$POLL"; ELAPSED=$((ELAPSED + POLL))
done
[ "$ELAPSED" -lt "$TIMEOUT" ] || fail "poll" "轮询超时（${TIMEOUT}s），任务 $TASK_ID 可能仍在生成；确认结果可 GET $BASE_URL/contents/generations/tasks/$TASK_ID（重跑本脚本会重新计费）"
[ "$STATUS" = "succeeded" ] || fail "poll" "任务 $TASK_ID 终态为 $STATUS: $RESP"

# 3) 下载视频（TOS 签名 URL 24 小时过期，务必立即下载）
URL=$(printf '%s' "$RESP" | python3 -c 'import sys,json;print(json.load(sys.stdin)["content"]["video_url"])' 2>/dev/null) \
  || fail "download" "无法解析 video_url: $RESP"
[ -n "$OUTPUT" ] || OUTPUT="./ark_video_${TASK_ID}.mp4"
curl -sSL --fail -o "$OUTPUT" "$URL" || fail "download" "下载失败: $URL"

# 4) return_last_frame：尾帧图一并下载（跨段接力的素材）
LAST_FRAME_PATH=""
if [ "$RETURN_LAST_FRAME" = "1" ]; then
  LF_URL=$(printf '%s' "$RESP" | python3 -c 'import sys,json;print((json.load(sys.stdin).get("content") or {}).get("last_frame_url",""))' 2>/dev/null) || LF_URL=""
  if [ -n "$LF_URL" ]; then
    LAST_FRAME_PATH="${OUTPUT%.*}_last_frame.jpg"
    curl -sSL --fail -o "$LAST_FRAME_PATH" "$LF_URL" || LAST_FRAME_PATH=""
  fi
fi

RESULT=$(python3 - "$TASK_ID" "$OUTPUT" "$LAST_FRAME_PATH" "$RESP" "$KEEP_URL" "$(python3 -c 'import json;print(json.load(open("'"$PARAMS_FILE"'"))["model"])')" <<'PY'
import json, os, sys
task_id, output, lf, resp, keep_url, model = sys.argv[1], sys.argv[2], sys.argv[3], json.loads(sys.argv[4]), sys.argv[5] == "1", sys.argv[6]
out = {
    "ok": True,
    "task_id": task_id,
    "model": model,
    "status": resp.get("status"),
    "video_path": os.path.abspath(output),
    "duration": resp.get("duration"),
    "ratio": resp.get("ratio"),
    "resolution": resp.get("resolution"),
    "seed": resp.get("seed"),
    "usage_total_tokens": (resp.get("usage") or {}).get("total_tokens"),
}
if lf:
    out["last_frame_path"] = os.path.abspath(lf)
if keep_url:
    out["video_url"] = (resp.get("content") or {}).get("video_url", "")
print(json.dumps(out, ensure_ascii=False))
PY
) || fail "download" "汇总结果失败"
printf '%s\n' "$RESULT"
