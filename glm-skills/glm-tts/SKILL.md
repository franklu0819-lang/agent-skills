---
name: glm-tts
description: 智谱 GLM-TTS 语音合成：把文本合成为带情感的自然语音 wav（7 个系统音色：彤彤/锤锤/小陈/Jam/Kazi/豆吉/罗多，支持语速音量调整、长文本自动分段、24kHz）。Use whenever the user mentions glm-tts、GLM TTS、智谱语音合成、智谱 TTS、用 GLM/智谱把文本转语音、用彤彤/锤锤/小陈等智谱音色朗读、GLM 音色 —— 只要明确点名智谱/GLM 引擎或智谱系统音色的 TTS 就用本技能；未指明引擎的通用语音合成仍默认 ark-tts（飞哥复刻音色）。Also triggered as /glm-tts。
---

# 智谱 GLM-TTS 语音合成

一条命令把文本合成为 wav，模型 `glm-tts`（新一代智谱语音大模型，官方宣传口径：字错误率与情感表达达到开源 SOTA 水平）。上下文自动预判情绪语调，适合需要**自然情感表达**的朗读。

> 引擎分工：点名智谱/GLM 引擎或智谱系统音色 → 本技能；通用配音/飞哥复刻音色（S_q3oLhGy72）→ `ark-tts`；带戏成片音轨（多角色+BGM+音效）→ `ark-audio-gen`；语音转文字 → 点名智谱/GLM 用 `glm-asr`，通用转写用 `ark-asr`。

## 快速使用

```bash
# <技能基目录> 为本技能安装目录（技能加载时给出）
# 默认音色彤彤
python3 <技能基目录>/scripts/tts.py --text "大家好，欢迎来到智谱开放平台" --output out.wav

# 浏览系统音色（7 个）
python3 .../tts.py --list-voices

# 指定音色 + 语速 [0.5,2] + 音量 (0,10]
python3 .../tts.py --text "..." --voice xiaochen --speed 1.2 --volume 1.5 --output out.wav

# 长文本（超过 900 字符即自动分段——官方单请求硬上限 1024——按句合成后拼接；中断可续跑）
python3 .../tts.py --file script.txt --output out.wav

# 预检：看分段与真实请求体预览，不调 API 不耗额度（无需 --output）
python3 .../tts.py --file script.txt --dry-run
```

播放验证：`afplay out.wav`。需要 mp3 时 ffmpeg 转：`ffmpeg -i out.wav -b:a 128k out.mp3`。

## 音色

| voice | 名称 | 特点 |
|---|---|---|
| `tongtong` | 彤彤（默认） | 女声，标准普通话，通用讲解/旁白 |
| `chuichui` | 锤锤 | 女声，活泼 |
| `xiaochen` | 小陈 | 男声，沉稳 |
| `jam` / `kazi` / `douji` / `luodo` | 动动动物圈系列 | 童趣角色音色，适合儿童内容 |

复刻音色：bigmodel.cn 控制台声音复刻页获取 ID 后 `--voice <ID>` 直传。音色 ID 不存在时报 `code=1214 音色id不存在`。

## 凭证（需配置）

`~/.zshrc` 的 `ZHIPU_API_KEY`（bigmodel.cn 右上角个人中心「API Keys」页，形如 `<32位hex>.<16位hex>`；glm- 家族统一只认此变量）。解析顺序：`--api-key`（传 `-` 从 stdin 读，避免 key 进 shell history）→ `ZHIPU_API_KEY` 环境变量 → ~/.zshrc。**火山 ARK_SPEECH_API_KEY（旧名 SPEECH_API_KEY）在本服务不认**，401 时先查 Key 来源。key 不打印、不落盘。

## 技术要点（2026-10 官方文档）

- 接口：`POST https://open.bigmodel.cn/api/paas/v4/audio/speech`，标准 Bearer 认证（`Authorization: Bearer <Key>`）
- 请求体：`model=glm-tts`、`input`（**单次上限 1024 字符**，超限报参数错）、`voice`（必填）、`response_format: wav|pcm`、`speed` [0.5,2]、`volume` (0,10]、`stream`（流式仅支持 pcm，非流式即文件下载）
- 响应：非流式直接返回二进制音频文件，采样率 24000 Hz；流式为 SSE，`choices[0].delta.content` 是 base64 PCM
- **长文本**：脚本按 段落→句末标点（中英文）→逗号→最近空白→硬切 的优先级自动分段（超过 900 字符即分段，留余量），逐段合成后提取 PCM 拼接、按首段参数重写 wav 头——各段音频参数不一致会中止并报错
- **断点续跑**：多段合成逐段缓存于 `<output>.parts/`；网络失败/Ctrl-C 中断后重跑同一命令自动跳过已完成段续传（不重复计费），拼接成功后缓存自动清理；网络类错误自动重试 1 次
- 计费：**0.03 元/千字符**；`--dry-run` 可零成本预检分段与参数
- 输出默认带 AI 水印（政策要求，`watermark_enabled` 默认 true）；完成过去水印签署的用户可关闭

## 常见错误

| 现象 | 原因与处理 |
|---|---|
| HTTP 401 / code=1002 | Key 无效或用错了火山 Key——用 bigmodel.cn「API Keys」页的 `<id>.<secret>` 形式 Key |
| code=1214 音色id不存在 | voice 拼错或复刻音色 ID 不属于该账号，`--list-voices` 核对 |
| code=1211 参数不合法 | 多为 input 超 1024 字符（应交给脚本自动分段，不要手工绕过脚本直调） |
| 合成内容情感/断句不理想 | glm-tts 靠上下文预判情绪——优先把完整句子给足（别按词切碎）；长文本让脚本分段而不是人工切 |
| 需要 mp3/flac | 服务端仅出 wav/pcm，ffmpeg 本地转 |

## 与其他工作流的集成

- 视频教程解说：`video-tutorial-gen` 需要飞哥本人声音时用 `ark-tts`；需要智谱系统音色（如小陈男声）时用本技能生成 wav 后同样交给 assemble_tutorial.py。
- 效果验证：合成的音频可交给 `ark-asr` 转写回来比对文本。
