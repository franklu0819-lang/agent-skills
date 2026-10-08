---
name: ark-asr
description: 豆包录音文件识别大模型（Seed-ASR）语音转文字：本地音频文件或 URL 转写为带标点的文本，支持说话人分离。Use whenever the user wants 语音识别、转写、录音转文字、把这段录音/音频转成文字、ASR、这段音频说了什么、会议记录转文字 —— 对本地音频文件或音频 URL 做语音转文字就用本技能。Also triggered as /ark-asr。
---

# 豆包录音文件识别大模型（直连豆包语音 API）

用封装脚本直连 `https://openspeech.bytedance.com/api/v3/auc/bigmodel/submit`（提交）+ `/query`（轮询），把本地音频或 URL 转写成文字。认证用 `ARK_SPEECH_API_KEY`（豆包语音控制台 UUID Key，旧名 `SPEECH_API_KEY` 仍兼容）——不要读取、传递或落盘任何 API key；**方舟 ark- Key 本服务不认**；录音文件识别服务需在豆包语音控制台开通。

> ark- 家族分工：文字→语音用 `ark-tts`/`ark-audio-gen`；语音→文字用本技能。

## 标准流程：直接跑脚本

```bash
# 基本：stdout 输出纯文本
bash <技能目录>/scripts/transcribe.sh meeting.mp3

# 存文本 + 说话人分离
bash <技能目录>/scripts/transcribe.sh meeting.mp3 -o meeting.txt --speakers

# 音频 URL（免上传）+ 完整 JSON
bash <技能目录>/scripts/transcribe.sh https://example.com/a.mp3 --format mp3 --json out.json
```

stdout 输出转写文本（进度走 stderr，如 `已提交任务 request_id=...`）；`--json` 另存完整结果：

```json
{"ok":true,"request_id":"...","text":"你好，这是一段音频生成测试。","duration_ms":2639}
```

常用参数：

| 选项 | 说明 | 默认 |
|---|---|---|
| `-o` | 转写文本另存路径 | 仅 stdout |
| `--json` | 完整结果单行 JSON 另存路径 | 无 |
| `--speakers` | 说话人分离（stdout 按说话人分段） | 关 |
| `--utterances` | 分句+时间戳（写入 JSON） | 关 |
| `--no-punc` / `--no-itn` | 关闭自动标点 / 逆文本归一化 | 均开启 |
| `--language` | 指定语种：`zh-CN`/`en-US`/`ja-JP`/`ko-KR`/`yue-CN`(粤语)/`de-DE`/`fr-FR`/`es-MX`/`pt-BR`/`th-TH`/`vi-VN`/`ru-RU` 等 locale 码 | 空=中文普通话（自动中英混+常见方言） |
| `--resource` | `volc.bigasr.auc`（大模型1.0，默认）/ `volc.seedasr.auc`（2.0，需单独开通） | 1.0 |
| `--submit-only` / `--query ID` | 长音频先提交后手动查询 | 一次完成 |

## 实测确认的坑（2026-09-17）

- 提交成功响应是空 `{}`（不是错误）；自己生成的 UUID 即任务 ID，轮询 `/query` 直到 `result.text` 出现。
- 短音频几秒出结果；长音频用默认轮询（5s 间隔 / 300s 超时），超时可 `--query <request_id>` 续查，不重复计费。
- 本地文件走 base64 直传（建议 ≤50MB）；更大的音频放 TOS/可公网访问的 URL 用 URL 方式。
- 格式支持 wav/mp3/ogg/m4a/aac（按扩展名自动推断）；其他格式先 `ffmpeg -i in.mov out.mp3` 转换。
- 提交体里的 rate/bits/channel 按参考实现固定 16000/16/1，服务端自动适配，无需按源音频修改。

## 报错速查

- 401/Invalid X-Api-Key → Key 不是语音控制台 UUID Key，或录音文件识别服务未开通。
- 一直空 `{}` → 任务还在排队/识别，继续等或加大 `--timeout`。
