#!/usr/bin/env python3
"""火山 v1 HTTP TTS(1.0 大模型音色库,BV 系 = 剪映同款命名):
  影视解说小帅 BV411_streaming / 活力解说男 BV410_streaming / 影视解说小美 BV412_streaming /
  解说小帅-多情感 BV437_streaming / 沉稳解说男 BV142_streaming / 阳光男声 BV056_streaming …
完整表见官方文档「豆包语音-音色列表」(docs.volcengine.com 6561/97465 视频配音场景)。

与 tts.py(v3 unidirectional, uranus/2.0 库)按 speaker 前缀分派:BV 开头走本脚本,其余走 tts.py。
注意(2026-10-10 实测):v1 网关只服务 _bigtts/BV 系;老「精品发音人」短 ID(如 zh_male_xiaoming
影视解说)的 sami workflow 已不路由,报 Invalid workflow,勿再尝试。

凭证(不落盘):appid=ARK_SPEECH_V1_APPID;token=ARK_SPEECH_V1_TOKEN(缺省回退 ARK_SPEECH_API_KEY)。
鉴权:Authorization: Bearer;{token};body 内 app.token 是无实义 Fake 字段。
用法:
  python3 tts_v1.py --text "..." --speaker BV411_streaming --output out.mp3 [--speed 10]
  python3 tts_v1.py --list-voices   # 打印内置高频 BV 系音色
"""
import argparse, base64, json, os, re, sys, time, urllib.request, uuid

URL = "https://openspeech.bytedance.com/api/v1/tts"

VOICES = [
    ("BV411_streaming", "影视解说小帅(剪映同款·解说标配)"),
    ("BV437_streaming", "解说小帅-多情感(7情感)"),
    ("BV410_streaming", "活力解说男(活力向解说)"),
    ("BV412_streaming", "影视解说小美(剪映同款女声)"),
    ("BV142_streaming", "沉稳解说男"),
    ("BV056_streaming", "阳光男声"),
    ("BV009_streaming", "知性女声"),
    ("BV004_streaming", "开朗青年"),
    ("BV102_streaming", "儒雅青年"),
    ("BV700_streaming", "灿灿(22情感)"),
]

def read_zshrc_var(name):
    m = re.search(rf'export {name}="?([A-Za-z0-9_.-]+)"?', open(os.path.expanduser("~/.zshrc")).read())
    return m.group(1) if m else ""

def creds(args):
    appid = args.appid or os.environ.get("ARK_SPEECH_V1_APPID") or read_zshrc_var("ARK_SPEECH_V1_APPID")
    token = args.api_key or os.environ.get("ARK_SPEECH_V1_TOKEN") or read_zshrc_var("ARK_SPEECH_V1_TOKEN") \
            or os.environ.get("ARK_SPEECH_API_KEY") or read_zshrc_var("ARK_SPEECH_API_KEY")
    if not appid or not token:
        die("缺凭证:需 ARK_SPEECH_V1_APPID(数字 AppID)+ ARK_SPEECH_V1_TOKEN(缺省回退 ARK_SPEECH_API_KEY)")
    return appid, token

def die(msg):
    print(f"tts_v1.py: {msg}", file=sys.stderr)
    sys.exit(1)

def tts(text, voice, out, speed_pct=0, retries=3, appid="", token=""):
    ratio = max(0.5, min(2.0, 1.0 + speed_pct / 100.0))
    body = {
        "app": {"appid": appid, "token": "access_token", "cluster": "volcano_tts"},
        "user": {"uid": "douyin-video-maker"},
        "audio": {"voice_type": voice, "encoding": "mp3", "speed_ratio": ratio,
                  "volume_ratio": 1.0, "pitch_ratio": 1.0},
        "request": {"reqid": str(uuid.uuid4()), "text": text,
                    "text_type": "plain", "operation": "query"},
    }
    for i in range(retries):
        try:
            req = urllib.request.Request(URL, data=json.dumps(body).encode(), method="POST",
                headers={"Content-Type": "application/json", "Authorization": f"Bearer;{token}"})
            d = json.loads(urllib.request.urlopen(req, timeout=30).read())
            if d.get("code") == 3000 and d.get("data"):
                open(out, "wb").write(base64.b64decode(d["data"]))
                print(f"完成: {out} ({os.path.getsize(out)}B, {voice})")
                return True
            die(f"服务未返回音频: code={d.get('code')} {str(d.get('message',''))[:150]}")
        except urllib.error.HTTPError as e:
            msg = e.read()[:200]
            if e.code in (400, 401):
                die(f"HTTP {e.code} {msg.decode('utf-8', 'ignore')}(检查 appid/token 与音色 ID 是否 BV 系)")
            print(f"⚠️ HTTP {e.code} 第{i+1}次,重试…", file=sys.stderr)
        except Exception as e:
            print(f"⚠️ {type(e).__name__}: {e} 第{i+1}次,重试…", file=sys.stderr)
        time.sleep(5)
    die("重试耗尽(网络异常)")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--text")
    ap.add_argument("--file", help="从文件读文本")
    ap.add_argument("--speaker", default="BV411_streaming")
    ap.add_argument("--output", default="out.mp3")
    ap.add_argument("--speed", type=int, default=0, help="语速百分比 [-50,100],内部换算 speed_ratio")
    ap.add_argument("--appid", default="")
    ap.add_argument("--api-key", dest="api_key", default="")
    ap.add_argument("--list-voices", action="store_true")
    args = ap.parse_args()
    if args.list_voices:
        for v, desc in VOICES:
            print(f"  {v:24s} {desc}")
        sys.exit(0)
    text = args.text or (args.file and open(args.file, encoding="utf-8").read().strip())
    if not text:
        die("需 --text 或 --file")
    appid, token = creds(args)
    sys.exit(0 if tts(text, args.speaker, args.output, args.speed, appid=appid, token=token) else 1)
