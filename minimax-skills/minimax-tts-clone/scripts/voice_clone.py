#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""voice_clone.py — MiniMax 声音复刻（/v1/files/upload + /v1/voice_clone，api.minimax.cn）

用法:
  voice_clone.py --create --audio ref.wav --voice-id feige2026 \
      --text "这是复刻后的试听文本" --demo-out feige_preview.mp3
  voice_clone.py --list                       # 列出本账号已复刻音色
  voice_clone.py --list --download ./previews # 顺带下载全部试听
  voice_clone.py --delete --voice-id feige2026 --yes   # 删除（不可恢复；须用户明示确认）

子命令:
  --create       上传参考音频 → 发起复刻 → 打印音色 ID + 下载试听
  --list         POST /v1/get_voice (voice_type=voice_cloning)
  --delete       POST /v1/delete_voice（加 --yes 才真删，删除后 voice_id 永久失效）

参考音频要求（官方硬限制，脚本校验）: mp3/m4a/wav、10 秒–5 分钟、单文件 ≤20MB；
单人干净人声、无 BGM/杂音/混响。voice-id 命名规则: 8–256 位、英文字母开头、
仅字母/数字/-/_、末位不可为 -/_、账号内不可重复。

前置: 账号须完成个人实名或企业认证（否则报 2038 无复刻权限）。
计费: ¥9.90/音色（生成时不收费、首次合成时扣）；复刻音色 7 天内未调用会被系统删除。
复刻产出: 自定义 voice_id，交给 minimax-tts 的 --voice 朗读任意文本。

凭证: platform.minimax.cn「账户管理→接口密钥」的 Key，export MINIMAX_API_KEY=...
（minimax- 家族统一只认此变量；key 不打印、不落盘）。
"""

import argparse
import http.client
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

DEFAULT_BASE = "https://api.minimax.cn"
OVERSEAS_BASE = "https://api.minimax.io"
UPLOAD_PATH = "/v1/files/upload"
CLONE_PATH = "/v1/voice_clone"
VOICE_LIST_PATH = "/v1/get_voice"
VOICE_DELETE_PATH = "/v1/delete_voice"

ALLOWED_EXT = (".mp3", ".m4a", ".wav")
MAX_SIZE = 20 * 1024 * 1024        # 20MB 硬限制
DURATION_RANGE = (10, 5 * 60)      # 官方建议 10s–5min（超出警告不阻断）

NETWORK_ERRORS = (urllib.error.URLError, http.client.IncompleteRead,
                  socket.timeout, ConnectionResetError, OSError)


def find_api_key(explicit: str) -> str:
    """解析顺序: --api-key（- 表示 stdin）→ 环境变量 MINIMAX_API_KEY → ~/.zshrc。"""
    if explicit:
        if explicit == "-":
            return sys.stdin.read().strip()
        return explicit
    names = ("MINIMAX_API_KEY",)
    for var in names:
        if os.environ.get(var):
            return os.environ[var]
    zshrc = os.path.expanduser("~/.zshrc")
    if os.path.isfile(zshrc):
        found = ""
        for line in open(zshrc, encoding="utf-8", errors="replace"):
            m = re.match(r'\s*export\s+(%s)=(?:"([^"]+)"|([^\s#]+))' % "|".join(names), line)
            if m:
                found = m.group(2) or m.group(3)
        return found
    return ""


def resolve_base(arg: str) -> str:
    if not arg:
        return os.environ.get("MINIMAX_BASE_URL", DEFAULT_BASE)
    if arg == "overseas":
        return OVERSEAS_BASE
    return arg.rstrip("/")


def die(msg: str) -> None:
    print(f"voice_clone.py: {msg}", file=sys.stderr)
    sys.exit(1)


def check_error(obj: dict) -> None:
    br = obj.get("base_resp")
    if isinstance(br, dict) and br.get("status_code") not in (0, None):
        hint = {"1004": "鉴权失败：Key 无效，或国内/海外站 Key 混用（两站独立）",
                "2038": "无复刻权限：账号须先完成个人实名或企业认证",
                "2013": "参数无效（检查 voice-id 命名规则与文件要求）",
                "1043": "text_validation 校验不过：参考音频与预期文本相似度低于阈值"}.get(
            str(br.get("status_code")), "")
        die(f"服务错误: base_resp.status_code={br.get('status_code')} {br.get('status_msg', '')} {hint}".strip())
    err = obj.get("error")
    if isinstance(err, dict):
        die(f"服务错误: HTTP {err.get('http_code', '?')} {err.get('message', '')}".strip())


def http_json(url: str, payload: dict, key: str) -> dict:
    """POST JSON（非流式，网络错误重试 1 次）。"""
    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    body = None
    for attempt in (1, 2):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = resp.read()
            break
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:500]
            try:
                obj = json.loads(detail)
            except json.JSONDecodeError:
                obj = {}
            err = obj.get("error") if isinstance(obj, dict) else None
            err = err if isinstance(err, dict) else {}
            hint = "（401 类: Key 无效，或国内/海外站 Key 混用）" if e.code in (401, 403) else ""
            die(f"HTTP {e.code}: {err.get('message', detail)} {hint}".strip())
        except NETWORK_ERRORS as e:
            if attempt == 2:
                die(f"网络错误（已重试 1 次仍失败）: {e}")
            print(f"  网络错误 {e}，2s 后重试…", file=sys.stderr)
            time.sleep(2)
    if not body:
        die("未取得响应体")
    try:
        obj = json.loads(body.decode("utf-8", "replace"))
    except json.JSONDecodeError:
        die(f"响应非 JSON: {body[:200]!r}")
    check_error(obj)
    return obj


def upload_file(path: str, purpose: str, key: str, base: str) -> int:
    """multipart 上传，返回 file_id（int64）。"""
    fname = os.path.basename(path)
    with open(path, "rb") as f:
        content = f.read()
    boundary = "----minimaxskill" + str(int(time.time() * 1000))
    parts = []
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="purpose"\r\n\r\n{purpose}\r\n'.encode())
    parts.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{fname}"\r\n'
        f'Content-Type: application/octet-stream\r\n\r\n'.encode() + content + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    data = b"".join(parts)
    body = None
    for attempt in (1, 2):
        req = urllib.request.Request(
            base + UPLOAD_PATH,
            data=data,
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                body = resp.read()
            break
        except urllib.error.HTTPError as e:
            die(f"上传失败 HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:300]}")
        except NETWORK_ERRORS as e:
            if attempt == 2:
                die(f"上传失败（网络错误，已重试 1 次仍失败）: {e}")
            print(f"  网络错误 {e}，2s 后重试…", file=sys.stderr)
            time.sleep(2)
    try:
        obj = json.loads(body.decode("utf-8", "replace"))
    except json.JSONDecodeError:
        die(f"上传响应非 JSON: {body[:200]!r}")
    check_error(obj)
    file_id = (obj.get("file") or {}).get("file_id")
    if file_id is None:
        die(f"上传响应缺 file.file_id: {json.dumps(obj, ensure_ascii=False)[:300]}")
    return int(file_id)


def probe_duration(path: str):
    """ffprobe 探测时长（秒）；无 ffprobe 返回 None。"""
    if shutil.which("ffprobe") is None:
        return None
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, timeout=30)
        return float(out.stdout.strip())
    except (ValueError, subprocess.TimeoutExpired, OSError):
        return None


def download(url: str, dest: str) -> bool:
    """下载试听音频；失败降级为警告返回 False（不阻断主流程，可稍后 --list --download 重取）。"""
    try:
        with urllib.request.urlopen(url, timeout=180) as resp, open(dest, "wb") as f:
            shutil.copyfileobj(resp, f)
        return True
    except NETWORK_ERRORS as e:
        print(f"警告: 下载失败 {dest}: {e}（不阻断；可稍后 --list --download 重取）", file=sys.stderr)
        return False


def valid_voice_id(vid: str) -> str:
    if not 8 <= len(vid) <= 256:
        return "长度须 8–256"
    if not re.match(r"^[A-Za-z][A-Za-z0-9_-]*$", vid) or vid.endswith(("-", "_")):
        return "须英文字母开头，仅字母/数字/-/_，末位不可为 -/_"
    return ""


def do_create(a, key: str, base: str) -> None:
    # 本地校验（音频/命名/文本长度）已在 main 提前完成；此处只剩需要 ffmpeg 的时长探测
    size = os.path.getsize(a.audio)
    dur = probe_duration(a.audio)
    if dur is not None and not DURATION_RANGE[0] <= dur <= DURATION_RANGE[1]:
        print(f"警告: 时长 {dur:.0f}s 超出官方建议区间 10s–5min，可能影响复刻质量", file=sys.stderr)
    if a.text and len(a.text) > 1000:
        die("--text 试听文本 ≤1000 字符")

    print(f"上传参考音频 {a.audio} ({size/1024:.0f}KB"
          + (f", {dur:.0f}s" if dur is not None else "") + ")…")
    file_id = upload_file(a.audio, "voice_clone", key, base)

    payload = {"file_id": file_id, "voice_id": a.voice_id}
    if a.denoise:
        payload["need_noise_reduction"] = True
    if a.normalize:
        payload["need_volume_normalization"] = True
    if a.text:
        payload["text"] = a.text
        payload["model"] = a.model
    print(f"发起复刻 voice_id={a.voice_id}…")
    obj = http_json(base + CLONE_PATH, payload, key)

    demo = obj.get("demo_audio") or ""
    extra = obj.get("extra_info") or {}
    print(f"\n复刻成功: voice_id = {a.voice_id}")
    print(f"计费说明: ¥9.90/音色（首次合成时扣）；复刻音色 7 天内未调用会被系统删除——"
          f"建议尽快用它合成一次")
    if extra.get("usage_characters") is not None:
        print(f"试听消耗 {extra.get('usage_characters')} 计费字符")
    if demo and a.demo_out:
        print(f"下载试听: {a.demo_out}")
        if download(demo, a.demo_out):
            print(f"试听: afplay {a.demo_out}")
    elif demo:
        print(f"试听链接（可直接浏览器打开）: {demo}")
    print(f"\n后续朗读: python3 <minimax-tts 技能>/scripts/tts.py --text \"任意文本\" "
          f"--voice {a.voice_id} --output out.wav")


def do_list(a, key: str, base: str) -> None:
    obj = http_json(base + VOICE_LIST_PATH, {"voice_type": "voice_cloning"}, key)
    voices = (obj.get("data") or {}).get("voices") or []
    if not voices:
        print("本账号暂无复刻音色（注意: 新复刻的音色须成功合成一次后才会出现在列表）")
        sys.exit(0)
    print(f"共 {len(voices)} 个复刻音色:")
    for v in voices:
        print(f"  {str(v.get('voice_id', '')):28s} 创建 {v.get('create_time', '?')}"
              f"  {v.get('description', '')}")
    if a.download:
        os.makedirs(a.download, exist_ok=True)
        for v in voices:
            url = v.get("demo_audio") or v.get("download_url") or ""
            vid = v.get("voice_id", "voice")
            if url:
                dest = os.path.join(a.download, f"{vid}.mp3")
                print(f"  下载 {vid} → {dest}")
                download(url, dest)   # 单个失败仅警告，继续其余下载


def do_delete(a, key: str, base: str) -> None:
    if not a.voice_id:
        die("--delete 需要 --voice-id")
    if not a.yes:
        die(f"删除不可恢复且 voice_id 永久失效。确认删除 {a.voice_id} 请加 --yes"
            f"（必须先取得用户明示确认）")
    obj = http_json(base + VOICE_DELETE_PATH,
                    {"voice_type": "voice_cloning", "voice_id": a.voice_id}, key)
    print(f"已删除: {a.voice_id}（响应: {json.dumps(obj, ensure_ascii=False)[:200]}）")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--create", action="store_true", help="上传参考音频并复刻")
    ap.add_argument("--audio", help="参考音频路径（mp3/m4a/wav，10s–5min，≤20MB）")
    ap.add_argument("--voice-id", help="自定义音色 ID（8–256 位，英文字母开头，字母/数字/-/_）")
    ap.add_argument("--text", default="", help="复刻后的试听文本 ≤1000 字符（提供则按所选模型合成试听）")
    ap.add_argument("--model", default="speech-2.8-hd",
                    choices=["speech-2.8-hd", "speech-2.8-turbo", "speech-2.6-hd",
                             "speech-2.6-turbo", "speech-02-hd", "speech-02-turbo"],
                    help="试听合成模型（与 --text 连用）")
    ap.add_argument("--denoise", action="store_true", help="复刻时开启降噪")
    ap.add_argument("--normalize", action="store_true", help="复刻时开启音量归一化")
    ap.add_argument("--demo-out", default="", help="试听音频保存路径（如 feige_preview.mp3）")
    ap.add_argument("--list", action="store_true", help="列出本账号复刻音色")
    ap.add_argument("--download", default="", metavar="DIR", help="与 --list 连用，下载全部试听到目录")
    ap.add_argument("--delete", action="store_true", help="删除复刻音色（须 --yes）")
    ap.add_argument("--yes", action="store_true", help="确认删除（必须先取得用户明示确认）")
    ap.add_argument("--base-url", default="", help=f"默认 {DEFAULT_BASE}；overseas={OVERSEAS_BASE}")
    ap.add_argument("--api-key", default="", help="API Key；传 - 从 stdin 读，默认自动解析环境变量")
    a = ap.parse_args()

    if not (a.create or a.list or a.delete):
        die("缺少子命令：--create / --list / --delete 至少一个（--help 看用法）")

    # 本地参数校验先于取 key（规则错误不依赖网络与凭证）
    if a.create:
        if not a.audio:
            die("--create 需要 --audio 参考音频路径")
        if not a.voice_id:
            die("--create 需要 --voice-id（自定义音色名，8–256 位字母开头）")
        err = valid_voice_id(a.voice_id)
        if err:
            die(f"--voice-id 不合规: {err}")
        if not os.path.isfile(a.audio):
            die(f"参考音频不存在: {a.audio}")
        if not a.audio.lower().endswith(ALLOWED_EXT):
            die(f"格式不支持: 仅 {', '.join(ALLOWED_EXT)}（其他格式先 ffmpeg -i in.xxx out.wav）")
        if os.path.getsize(a.audio) > MAX_SIZE:
            die(f"文件 {os.path.getsize(a.audio)/1024/1024:.1f}MB 超过 20MB 硬限制（裁剪后重试）")
        if a.text and len(a.text) > 1000:
            die("--text 试听文本 ≤1000 字符")
    if a.delete and not a.voice_id:
        die("--delete 需要 --voice-id")

    key = find_api_key(a.api_key)
    if not key:
        die("缺少 API Key：platform.minimax.cn「账户管理→接口密钥」获取，export MINIMAX_API_KEY=...，"
            "或用 --api-key 传入（--api-key - 从 stdin 读）")
    base = resolve_base(a.base_url)

    if a.create:
        do_create(a, key, base)
    if a.list:
        do_list(a, key, base)
    if a.delete:
        do_delete(a, key, base)


if __name__ == "__main__":
    main()
