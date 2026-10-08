---
name: minimax-asr
description: MiniMax 语音识别（asr-1.0）：本地音频文件转文字，支持说话人分离（verbose-json）、SRT/VTT 字幕直出、词级时间戳、20 种语言与混合识别；超过单次 500 秒自动 ffmpeg 分段转写并按段起点修正时间轴。Use whenever the user mentions MiniMax 语音识别、海螺 ASR、minimax 转写、用 MiniMax 把录音转文字、asr-1.0 —— 点名 MiniMax 引擎的语音转文字就用本技能；未指明引擎的通用转写/说话人分离默认 ark-asr（豆包 Seed-ASR，支持 URL 与超长音频）；智谱引擎走 glm-asr（热词/方言）。Also triggered as /minimax-asr。
---

# MiniMax 语音识别（asr-1.0）

一条命令把本地音频转成文字，走 `POST /v1/speech_to_text`（multipart），支持纯文本、SRT/VTT 字幕、说话人分离三种产出。

> 引擎分工：点名 MiniMax/海螺引擎 → 本技能；通用转写/说话人分离/超长录音/URL 输入 → `ark-asr`；智谱引擎/热词定制/方言 → `glm-asr`。MiniMax ASR **仅支持本地文件**（无 URL 输入），单次 ≤500 秒。

## 快速使用

```bash
# <技能基目录> 为本技能安装目录（技能加载时给出）
# 纯文本转写（打印并存 <音频名>.txt）
python3 <技能基目录>/scripts/asr.py --audio meeting.mp3

# SRT 字幕（直出带时间戳，配视频直接用）
python3 .../asr.py --audio interview.wav -o interview.srt

# 说话人分离：verbose-json 含 n_speakers 与逐段 speaker 标注
python3 .../asr.py --audio podcast.mp3 --format verbose-json

# 词级时间戳 / 指定语言（默认自动混合识别）
python3 .../asr.py --audio clip.m4a --word-timestamps
python3 .../asr.py --audio en.wav --language en

# 超长录音（>500s）：自动 ffmpeg 切段转写，字幕时间轴按段起点偏移修正
python3 .../asr.py --audio long_conf.m4a -o conf.srt
```

## 输出格式

| --format | 产出 | 适用 |
|---|---|---|
| `text`（默认） | 纯文本 `.txt` | 纪要、摘要素材（交给会话模型总结） |
| `srt` / `vtt` | 字幕文件 | 视频/播客配字幕 |
| `verbose-json` | `n_speakers` + `segments[]`（start/end/speaker/text） | 会议分人整理、访谈分析 |

`--word-timestamps` 词级时间戳（verbose-json/srt/vtt 有效）。语言：`--language` 传 BCP-47（zh/yue/en/ja/ko/th/vi/id/ms/fil/ar/tr/fr/de/es/it/pt/pl/ru/uk 共 20 种），不传自动混合识别。

## 凭证（需配置）

`~/.zshrc` 的 `MINIMAX_API_KEY`（platform.minimax.cn「账户管理 → 接口密钥」；minimax- 家族统一只认此变量）。解析顺序：`--api-key`（传 `-` 从 stdin 读）→ 环境变量 → ~/.zshrc。国内站默认；海外账号加 `--base-url overseas`。key 不打印、不落盘。

## 技术要点（2026-10 官方文档）

- 端点：`POST https://api.minimax.cn/v1/speech_to_text`，multipart（`file` 二进制 + `model=asr-1.0` + `response_format`），Bearer 认证，无需 GroupId
- 硬限制：单次 **≤500 秒且 ≤50MB**（超时长的输入**直接 400 不截断**）——脚本对超限音频自动 ffmpeg 切成 480s 段（单声道 16kHz 重编码）逐段转写，SRT/VTT 时间戳按段起点偏移修正；**说话人编号为段内独立口径**（跨段同一人不保证同号）
- 格式：mp3/aac/opus/wav/flac/m4a/ogg/aiff；无容器裸 PCM 不支持；建议单声道 16kHz
- 计费：**¥2.50/小时**，按音频实际时长（`duration` 字段）；脚本按 ffprobe 时长预估
- 依赖：ffprobe/ffmpeg（探测时长与超限分段）；网络错误自动重试 1 次
- 错误格式坑：国内站错误在 HTTP 200 的 `base_resp.status_code`（1004 鉴权、1002 限流、2013 参数无效）；400/413 分别对应超时长/超大

## 常见错误

| 现象 | 原因与处理 |
|---|---|
| base_resp 1004 login fail | Key 无效或国内/海外 Key 混用（两站独立账号） |
| HTTP 400 | 超 500 秒或格式不支持——脚本已自动分段的话请检查 ffprobe/ffmpeg 是否安装 |
| HTTP 413 | 超 50MB：`ffmpeg -i in.wav -b:a 64k out.m4a` 压缩后再转写 |
| 专有名词识别差 | ASR 无热词参数；转写后交给会话模型按上下文纠正，或改用 `glm-asr`（支持热词表）/ `ark-asr` |
| 说话人跨段编号乱 | 分段拼接的固有限制（编号段内独立）；短音频（≤500s）单次直出无此问题 |
| 需要 URL 直接转写 | 本技能不支持 URL；先下载或改用 `ark-asr`（支持 URL） |

## 与其他工作流的集成

- 会议纪要：`--format verbose-json` 分人转写 → 交给会话模型总结成纪要。
- 视频字幕：与 `video-edit` 工作流衔接——本技能直出 SRT 供校对烧录；或 `ark-asr` 生成草稿后比对。
- 双引擎校验：重要转写用 `ark-asr` 与本技能各跑一遍，diff 差异段落人工复核。
