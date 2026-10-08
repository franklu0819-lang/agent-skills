#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""voice_clone.py — 智谱 glm-tts-clone 音色复刻管理（open.bigmodel.cn，纯标准库）

流程: 上传参考音频(/paas/v4/files, purpose=voice-clone-input) → 发起复刻
(/paas/v4/voice/clone, model=glm-tts-clone) → 得到复刻音色 ID，之后用
glm-tts 的 tts.py --voice <ID> 即可以该音色朗读任意文本。

用法:
  voice_clone.py --create --audio ref.wav --voice-name feige \\
      [--text "参考音频的文字内容"] [--preview-text "试听文本"] [--preview-out p.mp3]
  voice_clone.py --list [--type PRIVATE|OFFICIAL] [--name 关键词] [--download DIR]
  voice_clone.py --delete --voice voice_clone_xxx

选项:
  --create            复刻新音色（自动上传参考音频；创建前先查重名）
  --audio PATH        参考音频，mp3/wav，单文件 ≤10MB，建议时长 3~30 秒
  --voice-name NAME   唯一音色名（同账号重名会被拒绝，脚本先查 --list 预检）
  --text TEXT         参考音频的文字内容（选填，提供可提升复刻相似度）
  --preview-text TXT  复刻完成时官方用该文本生成试听音频（默认一句通用话）
  --preview-out PATH  试听音频落盘路径，默认 <voice_name>_preview.mp3；
                      试听下载失败只警告不阻断（核心产物是音色 ID）
  --list              列出音色（默认 PRIVATE=本账号复刻音色；OFFICIAL=官方音色）
  --name KEY          --list 时按 voice_name 模糊过滤
  --download DIR      --list 时把每个音色的试听音频(download_url)下载到该目录
  --type TYPE         PRIVATE（默认）/ OFFICIAL
  --delete            删除音色（不可恢复；agent 须先取得用户明示确认再调用）
  --voice ID          音色 ID（--delete 用；也兼容传 voice_name，脚本会先解析）
  --api-key KEY       API Key；传 - 从 stdin 读（避免进 shell history）。默认自动解析

凭证: 智谱开放平台 bigmodel.cn「API Keys」页的 Key，export ZHIPU_API_KEY=...
（glm- 家族统一只认 ZHIPU_API_KEY；key 不打印、不落盘）。
复刻计费: 官方 API 文档未标价，以控制台账单为准。
"""
import argparse
import http.client
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

BASE = "https://open.bigmodel.cn/api/paas/v4"
FILES_URL = BASE + "/files"
CLONE_URL = BASE + "/voice/clone"
LIST_URL = BASE + "/voice/list"
DELETE_URL = BASE + "/voice/delete"
MODEL = "glm-tts-clone"
PURPOSE = "voice-clone-input"
MAX_AUDIO_MB = 10          # 官方硬限制：参考音频 ≤10MB
DURATION_RANGE = (3, 30)   # 官方建议：3~30 秒（超出仅警告，不阻断）
ALLOWED_EXT = (".mp3", ".wav")
DEFAULT_PREVIEW_TEXT = "大家好，这是我的复刻音色，随便说点什么都很像。"

# 网络类异常（同 tts.py：urllib 不包装读响应阶段的异常，需显式捕获）
NETWORK_ERRORS = (urllib.error.URLError, http.client.IncompleteRead,
                  socket.timeout, ConnectionResetError, OSError)


def find_api_key(explicit: str) -> str:
    """解析顺序: --api-key（- 表示 stdin）→ 环境变量 ZHIPU_API_KEY →
    ~/.zshrc 里的同名 export（取最后生效的）。glm- 家族统一只认 ZHIPU_API_KEY。"""
    if explicit:
        if explicit == "-":
            return sys.stdin.read().strip()
        return explicit
    names = ("ZHIPU_API_KEY",)
    for var in names:
        if os.environ.get(var):
            return os.environ[var]
    zshrc = os.path.expanduser("~/.zshrc")
    if os.path.isfile(zshrc):
        found = ""
        # key 都是 ASCII，errors=replace 只影响无关行（如含中文注释的 zshrc）
        for line in open(zshrc, encoding="utf-8", errors="replace"):
            m = re.match(r'\s*export\s+(%s)=(?:"([^"]+)"|([^\s#]+))' % "|".join(names), line)
            if m:
                found = m.group(2) or m.group(3)
        return found
    return ""


def die(msg: str) -> None:
    print(f"voice_clone.py: {msg}", file=sys.stderr)
    sys.exit(1)


def api_error_hint(code: int, err: dict) -> str:
    if code in (401, 403) or str(err.get("code")) == "1002":
        return ("（401/1002 类: Key 无效或格式错，应为 bigmodel.cn「API Keys」页的 "
                "<id>.<secret> 形式 Key；火山 Key 本服务不认）")
    return ""


def http_json(url: str, key: str, *, method: str = "GET", payload: dict = None,
              timeout: int = 120) -> dict:
    """带 Bearer 认证的 JSON 请求，返回解析后的 dict。
    HTTP/业务错误直接 die（带官方 code/message）；网络类错误退避 2s 重试 1 次。"""
    data = None
    headers = {"Authorization": f"Bearer {key}"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    body = None
    for attempt in (1, 2):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read()
            break
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:500]
            try:
                obj = json.loads(detail)
                err = obj.get("error") if isinstance(obj, dict) else None
                err = err if isinstance(err, dict) else {}
                hint = f"code={err.get('code')} {err.get('message', '')}".strip()
            except json.JSONDecodeError:
                err, hint = {}, detail
            die(f"HTTP {e.code}: {hint} {api_error_hint(e.code, err)}".strip())
        except NETWORK_ERRORS as e:
            if attempt == 2:
                die(f"网络错误（已重试 1 次仍失败）: {e}")
            print(f"  网络错误 {e}，2s 后重试…", file=sys.stderr)
            time.sleep(2)
    if not body:
        die("未取得响应体")
    try:
        obj = json.loads(body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        die(f"响应非 JSON: {body[:200]!r}")
    if isinstance(obj, dict) and isinstance(obj.get("error"), dict):
        err = obj["error"]
        die(f"服务返回错误: code={err.get('code')} {err.get('message', '')}")
    return obj


def probe_duration(path: str):
    """ffprobe 读音频时长（秒）；无 ffprobe/读取失败返回 None（软校验）。"""
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, timeout=15)
        return float(r.stdout.strip())
    except Exception:
        return None


def upload_audio(path: str, key: str) -> str:
    """multipart 上传参考音频（purpose=voice-clone-input），返回 file_id。"""
    size = os.path.getsize(path)
    if size > MAX_AUDIO_MB * 1024 * 1024:
        die(f"参考音频 {size/1024/1024:.1f}MB 超过官方限制 {MAX_AUDIO_MB}MB")
    duration = probe_duration(path)
    if duration is not None and not DURATION_RANGE[0] <= duration <= DURATION_RANGE[1]:
        print(f"  警告: 参考音频时长 {duration:.1f}s，官方建议 {DURATION_RANGE[0]}~{DURATION_RANGE[1]}s，"
              "相似度可能受影响", file=sys.stderr)
    boundary = "----glmvoiceclone" + uuid.uuid4().hex
    filename = os.path.basename(path).replace('"', "'")
    with open(path, "rb") as f:
        content = f.read()
    body = b"".join([
        (f'--{boundary}\r\nContent-Disposition: form-data; name="purpose"\r\n\r\n'
         f'{PURPOSE}\r\n').encode("utf-8"),
        (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; '
         f'filename="{filename}"\r\nContent-Type: application/octet-stream\r\n\r\n'
         ).encode("utf-8") + content + b"\r\n",
        f"--{boundary}--\r\n".encode("utf-8"),
    ])
    req = urllib.request.Request(
        FILES_URL, data=body,
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST")
    print(f"上传参考音频: {filename} ({size/1024:.0f}KB"
          + (f", {duration:.1f}s" if duration else "") + ")…")
    resp = None
    for attempt in (1, 2):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                resp = json.loads(r.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:500]
            try:
                obj = json.loads(detail)
                err = obj.get("error") if isinstance(obj, dict) else None
                err = err if isinstance(err, dict) else {}
                hint = f"code={err.get('code')} {err.get('message', '')}".strip()
            except json.JSONDecodeError:
                err, hint = {}, detail
            die(f"上传失败 HTTP {e.code}: {hint} {api_error_hint(e.code, err)}".strip())
        except NETWORK_ERRORS as e:
            if attempt == 2:
                die(f"上传网络错误（已重试 1 次仍失败）: {e}")
            print(f"  网络错误 {e}，2s 后重试…", file=sys.stderr)
            time.sleep(2)
    if not isinstance(resp, dict) or not resp.get("id"):
        die(f"上传响应缺 id: {json.dumps(resp, ensure_ascii=False)[:300]}")
    print(f"  file_id: {resp['id']}")
    return resp["id"]


def list_voices(key: str, voice_type: str = None, name: str = None) -> list:
    """GET /voice/list，返回 voice_list（可按类型/名称过滤）。"""
    qs = []
    if voice_type:
        qs.append("voiceType=" + urllib.parse.quote(voice_type))
    if name:
        qs.append("voiceName=" + urllib.parse.quote(name))
    url = LIST_URL + ("?" + "&".join(qs) if qs else "")
    obj = http_json(url, key)
    vl = obj.get("voice_list", [])
    return vl if isinstance(vl, list) else []


def download_preview(url: str, dest: str) -> str:
    """下载试听音频并落盘，返回实际路径。
    download_url 实测返回 WAV 流（RIFF/PCM）而非 mp3，按魔数嗅探纠正扩展名，
    避免 afplay 按错误扩展名解析失败。失败抛异常由调用方决定是否阻断。"""
    with urllib.request.urlopen(url, timeout=60) as r:
        data = r.read()
    if len(data) < 200:
        raise ValueError(f"下载内容过小({len(data)}B)")
    ext = ""
    if data[:4] == b"RIFF":
        ext = ".wav"
    elif data[:3] == b"ID3" or (len(data) > 2 and data[0] == 0xFF and (data[1] & 0xE0) == 0xE0):
        ext = ".mp3"
    if ext and os.path.splitext(dest)[1].lower() != ext:
        dest = os.path.splitext(dest)[0] + ext
        print(f"  （试听内容实为 {ext[1:]} 格式，已存为 {dest}）")
    with open(dest, "wb") as f:
        f.write(data)
    return dest


def cmd_create(a, key: str) -> None:
    if not a.audio:
        die("--create 需要 --audio 参考音频路径（mp3/wav）")
    if not a.voice_name:
        die("--create 需要 --voice-name 唯一音色名")
    if not os.path.isfile(a.audio):
        die(f"参考音频不存在: {a.audio}")
    if os.path.splitext(a.audio)[1].lower() not in ALLOWED_EXT:
        die(f"参考音频格式仅支持 {'/'.join(ALLOWED_EXT)}（官方限制）: {a.audio}")

    # 预检重名（voice_name 要求账号内唯一，先查免一次必败调用）
    existed = [v for v in list_voices(key, "PRIVATE") if v.get("voice_name") == a.voice_name]
    if existed:
        die(f"音色名 {a.voice_name!r} 已存在（voice={existed[0].get('voice')}），"
            f"换一个名字或先 --delete")

    file_id = upload_audio(a.audio, key)
    payload = {"model": MODEL, "voice_name": a.voice_name,
               "input": a.preview_text or DEFAULT_PREVIEW_TEXT, "file_id": file_id,
               "request_id": uuid.uuid4().hex}
    if a.text:
        payload["text"] = a.text
    print(f"发起复刻（model={MODEL}, voice_name={a.voice_name}"
          + (", 附参考文本" if a.text else "") + "）…")
    obj = http_json(CLONE_URL, key, method="POST", payload=payload, timeout=300)
    voice = obj.get("voice", "")
    if not voice:
        die(f"复刻响应缺 voice: {json.dumps(obj, ensure_ascii=False)[:300]}")
    print(f"复刻成功 ✓")
    print(f"  音色 ID : {voice}   （长期有效，记入项目文档/笔记）")
    print(f"  音色名  : {a.voice_name}")

    # 试听: clone 响应的 file_id 没有直接下载端点（/files/{id}/content 仅支持 batch），
    # 试听地址从 /voice/list 的 download_url 取
    dest = a.preview_out or f"{a.voice_name}_preview.mp3"
    try:
        vl = [v for v in list_voices(key, "PRIVATE", name=a.voice_name)
              if v.get("voice") == voice or v.get("voice_name") == a.voice_name]
        url = vl[0].get("download_url", "") if vl else ""
        if url:
            dest = download_preview(url, dest)
            print(f"  试听音频: {dest} ({os.path.getsize(dest)/1024:.0f}KB)，afplay {dest}")
        else:
            raise ValueError("voice/list 未返回 download_url")
    except Exception as e:  # 试听失败不阻断——核心产物音色 ID 已到手
        print(f"  警告: 试听音频下载失败（{e}），可稍后 --list --download DIR 重取", file=sys.stderr)
    print(f"\n接下来用该音色朗读: python3 <glm-tts 技能>/scripts/tts.py "
          f'--text "任意文本" --voice {voice} --output out.wav')


def cmd_list(a, key: str) -> None:
    vtype = a.type if (a.type in ("PRIVATE", "OFFICIAL")) else None
    vl = list_voices(key, vtype, a.name)
    if not vl:
        print("没有匹配的音色"
              + f"（type={vtype or '全部'}, name={a.name or '全部'}）")
        return
    print(f"共 {len(vl)} 个音色:")
    for v in vl:
        print(f"  {v.get('voice', '?'):42s} {v.get('voice_name', '?'):20s} "
              f"{v.get('voice_type', '?'):9s} {v.get('create_time', '')}")
    if a.download:
        os.makedirs(a.download, exist_ok=True)
        for v in vl:
            url = v.get("download_url", "")
            if not url:
                continue
            name = re.sub(r'[^\w.-]+', "_", v.get("voice_name", "voice")) or "voice"
            dest = os.path.join(a.download, f"{name}_preview.mp3")
            try:
                dest = download_preview(url, dest)
                print(f"  试听已下载: {dest} ({os.path.getsize(dest)/1024:.0f}KB)")
            except Exception as e:
                print(f"  试听下载失败 {v.get('voice_name')}: {e}", file=sys.stderr)


def cmd_delete(a, key: str) -> None:
    if not a.voice:
        die("--delete 需要 --voice 音色 ID（或音色名）")
    target = a.voice
    # 音色 ID 实测为 UUID 形式（文档示例为 voice_clone_ 前缀，不可按前缀判断）：
    # 先按 voice ID 精确匹配；未命中再按 voice_name 唯一匹配，避免误删
    vl = list_voices(key, "PRIVATE")
    if not any(v.get("voice") == target for v in vl):
        matched = [v for v in vl if v.get("voice_name") == target]
        if len(matched) != 1:
            die(f"{target!r} 未精确匹配音色 ID，按名称匹配到 {len(matched)} 个；"
                f"请 --list 后用 --voice <音色ID> 精确指定")
        target = matched[0]["voice"]
    print(f"删除音色（不可恢复）: {target}")
    obj = http_json(DELETE_URL, key, method="POST", payload={"voice": target})
    print(f"已删除: {obj.get('voice', target)}  update_time={obj.get('update_time', '?')}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--create", action="store_true", help="复刻新音色（上传参考音频 + 发起复刻 + 下载试听）")
    mode.add_argument("--list", action="store_true", help="列出音色（默认 PRIVATE=本账号复刻音色）")
    mode.add_argument("--delete", action="store_true", help="删除音色（不可恢复，须先取得用户确认）")
    ap.add_argument("--audio", help="--create: 参考音频路径（mp3/wav，≤10MB，建议 3~30 秒）")
    ap.add_argument("--voice-name", help="--create: 唯一音色名")
    ap.add_argument("--text", help="--create: 参考音频的文字内容（选填，提升相似度）")
    ap.add_argument("--preview-text", help="--create: 试听合成文本（默认内置一句）")
    ap.add_argument("--preview-out", help="--create: 试听音频落盘路径")
    ap.add_argument("--name", help="--list: 按 voice_name 模糊过滤")
    ap.add_argument("--download", help="--list: 试听音频下载目录")
    ap.add_argument("--type", default="PRIVATE", choices=["PRIVATE", "OFFICIAL", "ALL"],
                    help="--list: 音色类型，默认 PRIVATE")
    ap.add_argument("--voice", help="--delete: 音色 ID（也接受 voice_name，脚本先解析）")
    ap.add_argument("--api-key", default="",
                    help="API Key；传 - 从 stdin 读（避免进 shell history），默认自动解析环境变量")
    a = ap.parse_args()

    key = find_api_key(a.api_key)
    if not key:
        die("缺少 API Key：请在 bigmodel.cn「API Keys」页获取，export ZHIPU_API_KEY=...，"
            "或用 --api-key 传入（--api-key - 从 stdin 读）")

    if a.create:
        cmd_create(a, key)
    elif a.list:
        cmd_list(a, key)
    else:
        cmd_delete(a, key)


if __name__ == "__main__":
    main()
