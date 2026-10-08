---
name: ark-tts
description: 火山引擎语音合成（豆包大模型 TTS），默认使用飞哥的复刻音色 S_q3oLhGy72 —— 用飞哥本人的声音朗读任意中文文本。Use whenever the user wants 语音合成、文字转语音、配音、朗读文本、把这段话转成语音/音频、用我的声音说 XX、TTS —— 包括视频教程旁白、demo 音频、提示音等；生成的 mp3 可直接用或交给视频工作流。Also triggered as /ark-tts。
---

# 火山引擎语音合成（复刻音色）

一条命令把文本合成为音频，默认音色是**飞哥本人在火山引擎复刻的声音**（`S_q3oLhGy72`）。

> ark- 家族分工：纯朗读/旁白/复刻音色配音用本技能；带戏的成片音轨（多角色+音效+BGM）用 `ark-audio-gen`；语音转文字用 `ark-asr`；图片用 `ark-image-gen`；视频用 `ark-video-gen`。

## 快速使用

```bash
# 默认复刻音色
# <技能基目录> 为本技能安装目录（技能加载时给出）
python3 <技能基目录>/scripts/tts.py --text "大家好，欢迎来到飞哥的AI课堂" --output out.mp3

# 浏览音色库（289 个，支持关键词过滤：解说/女声/客服/英语/角色…）
python3 .../tts.py --list-voices
python3 .../tts.py --list-voices 解说

# 用库中音色 + 语速（-50~100，+100≈2倍速）
python3 .../tts.py --text "..." --speaker zh_male_jieshuoxiaoming_uranus_bigtts --speed -20 --output out.mp3

# 1.0 情感音色
python3 .../tts.py --text "..." --speaker zh_male_beijingxiaoye_emo_v2_mars_bigtts --emotion happy --output out.mp3

# 后付费自定义音色代号（文档 6561/2534906 的 custom_speaker_id 结构）
python3 .../tts.py --text "..." --custom-id custom_zh_xxx --output out.mp3
```

播放验证：`afplay out.mp3`。视频工作流需要 wav 时 ffmpeg 转（`-ar 48000 -ac 2`）。

## 音色库

完整列表在 `references/voices.md`（200+ 个 2.0 音色：通用/视频配音/有声阅读/教育/客服/角色扮演/多语种，`zh_*_uranus_bigtts` 与 `ICL_uranus_*` 两类命名）。为教程选解说音色时先 `--list-voices 解说`。选音色要点：

| 音色类型 | 识别特征 | resource（自动推断） |
|---|---|---|
| 个人复刻 | `S_` 开头 | seed-icl-2.0 |
| 2.0 公版 | 名含 `uranus` | seed-tts-2.0 |
| 1.0 公版 | 其他 `_bigtts`（moon/mars 等） | volc.service_type.10029 |

配错不报 401，而是 HTTP 200 + code 55000000 空音频（脚本会提示）。

## 凭证（已配置）

`~/.zshrc` 的 `ARK_SPEECH_API_KEY`（豆包语音控制台 > API Key管理 的 Key，**UUID 格式**，旧名 `SPEECH_API_KEY` 仍兼容）。解析顺序：`--api-key` → `ARK_SPEECH_API_KEY` → `SPEECH_API_KEY` → `ARK_API_KEY` → ~/.zshrc。

**重要**：方舟 `ark-` 开头的 Key 本服务**不认**（返回 45000010 Invalid X-Api-Key，2026-09-17 实测 4 把 ark Key 全拒）；必须是语音控制台 API Key管理 里的 UUID Key。

## 技术要点（2026-09-17 实测确认）

- 接口：`POST https://openspeech.bytedance.com/api/v3/tts/unidirectional`，请求头 `X-Api-Key` + `X-Api-Resource-Id` + `X-Api-Request-Id`（必选，uuid）
- **响应是流式多段 JSON**：每行 `{"code":0,"message":"","data":"<base64音频块>"}`，拼接全部 data 再 base64 解码才是完整音频（tts.py 已处理）
- resource-id 自动推断：复刻音色（S_ 前缀或 --custom-id）→ `seed-icl-2.0`；公版音色 → `volc.service_type.10029`
- **语速**：`--speed` [-50,100]，实测 +100≈2倍速、-50≈0.5倍速、超界被钳制；字段必须放 `audio_params.speech_rate`（放 req_params 顶层会被静默忽略）
- 复刻音色/2.0 音色不支持 emotion（自动忽略）；1.0 情感音色（如 `*_emo_v2_mars_bigtts`）支持 `--emotion`
- 输出 mp3 24kHz。视频工作流需要 wav 时用 ffmpeg 转换（`-ar 48000 -ac 2`）

## 语种与方言（默认中文普通话）

不带参数 = 中文普通话（中英混读）。需要其他语种/方言时：

```bash
# 指定语种（explicit_language）：zh-cn / en / ja / es-mx / id / pt-br / de / fr / crosslingual(多语种前端)
python3 <技能目录>/scripts/tts.py --text "Hello everyone, welcome to the show." --speaker zh_male_jieshuoxiaoming_uranus_bigtts --language en --output out.mp3

# 指定方言（explicit_dialect）：yue(粤语) / dongbei / sichuan / shaanxi / beijing / henan / tianjin / shanghai
python3 <技能目录>/scripts/tts.py --text "大家好，今日带大家行下广州老街。" --dialect yue --output out.mp3
```

- `--language` 与 `--dialect` 二选一；两者挂在 `req_params.additions`（**JSON 字符串**，不是嵌套对象——传对象会被服务端以 unmarshal 错误拒绝，2026-09-17 实测）
- 方言仅部分精品音色生效，公版/复刻音色传方言可能被忽略；语种对复刻音色读非中英文文本时尤为重要
- 合成效果验证技巧：交给 `ark-asr` 的 `transcribe.sh --language en-US`（或 `yue-CN`）转写回来比对

## 常见错误

| 现象 | 原因与处理 |
|---|---|
| 401 code=45000010 Invalid X-Api-Key | Key 不对或未绑定语音服务——用控制台 API Key管理 的 UUID Key，不要用方舟 ark- Key |
| HTTP 200 但 code=55000000 无数据 | speaker 与 resource 不匹配（如复刻音色配了公版 resource），按上节推断 |
| 音色不存在 | 复刻音色在控制台「声音复刻」页查 S_ ID |
| 语种混读异常 | 复刻音色用非中英文文本时用 `--language` 指定语种（如 ja）；方言口音用 `--dialect`（仅部分精品音色生效） |
| 网络错误 | 直连即可（国内节点）；如走了代理检查直连规则 |

## 与视频教程工作流的集成

`video-tutorial-gen` 技能的 `assemble_tutorial.py` 已接入：storyboard.json 设 `"speaker": "S_q3oLhGy72"` 即整片解说用复刻音色（自动调本技能，Key 自动从环境/zshrc 解析）。
