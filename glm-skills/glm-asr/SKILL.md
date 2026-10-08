---
name: glm-asr
description: 智谱 GLM-ASR 语音识别（glm-asr-2512）：本地音频或 URL 转文字，自动 ffmpeg 分段突破单次 30 秒限制并做段间上下文接力，支持热词表提升专有名词识别率，中文方言与中英混说识别强。Use whenever the user 提到 GLM-ASR、glm-asr、智谱语音识别、bigmodel 语音转文字、用 GLM 模型转写，或需要热词定制/方言识别的语音转写场景；通用语音转写默认走 ark-asr（豆包 Seed-ASR，支持说话人分离与超长音频）。Also triggered as /glm-asr。
---

# GLM-ASR 语音识别（直连智谱开放平台）

用封装脚本直连 `POST https://open.bigmodel.cn/api/paas/v4/audio/transcriptions`（模型 `glm-asr-2512`），把本地音频或 URL 转写成带标点的文字。API 单次硬限 **wav/mp3、≤25MB、≤30 秒**，脚本自动 ffmpeg 转码分段，并把上一段结果尾部作为 `prompt` 传给下一段（官方推荐的上下文接力方式），保证长音频跨段连贯。

> ASR 分工：点名智谱/GLM 引擎、要热词定制或方言识别 → 本技能；通用语音转写/说话人分离/小时级长音频 → `ark-asr`（豆包 Seed-ASR）。

## 凭证（需配置）

`ZHIPU_API_KEY`（[bigmodel.cn](https://bigmodel.cn/usercenter/proj-mgmt/apikeys) 右上角个人中心「API Keys」页，形如 `<32位hex>.<16位hex>`；glm- 家族统一只认此变量）。解析顺序：`--api-key` → `ZHIPU_API_KEY` 环境变量 → `~/.zshrc`（与 glm-tts 同链）。**火山 ARK_SPEECH_API_KEY（旧名 SPEECH_API_KEY）在本服务不认**，401 时先查 Key 来源；脚本不读取、不传递、不落盘任何 key。

## 标准流程：直接跑脚本

```bash
# 基本：stdout 输出纯文本
python3 <技能目录>/scripts/transcribe.py meeting.mp3

# 存文本 + 热词（人名/项目代号/领域术语识别率提升明显）
python3 <技能目录>/scripts/transcribe.py meeting.mp3 -o meeting.txt \
  --hotwords "智谱,AutoGLM,潘家园"

# 音频 URL + 完整 JSON（含每段结果与 request_id）
python3 <技能目录>/scripts/transcribe.py https://example.com/a.wav --json out.json
```

stdout 输出转写文本（进度走 stderr，如 `[2/3] 转写中...`）；`--json` 另存完整结果（`offset_s` 为该段在原音频中的起始秒数，可定位回源）：

```json
{"ok":true,"model":"glm-asr-2512","text":"你好，这是一段测试。","audio_duration_s":68.1,"segments":[{"index":1,"offset_s":0,"file":"seg0000.wav","text":"...","request_id":"..."}],"hotwords":["智谱"],"context_relay":true,"elapsed_ms":24530}
```

常用参数：

| 选项 | 说明 | 默认 |
|---|---|---|
| `-o` | 转写文本另存路径 | 仅 stdout |
| `--json` | 完整结果单行 JSON 另存路径 | 无 |
| `--hotwords` | 热词表，逗号分隔（≤100 个） | 无 |
| `--seg-seconds` | 长音频分段时长（5~29 秒） | 25 |
| `--no-context` | 关闭段间 prompt 上下文接力 | 开启接力 |
| `--keep-segments` | 保留分段临时文件（调试） | 自动清理 |
| `--model` | 模型编码 | glm-asr-2512 |

## 机制与限制（依据官方文档 2026-10）

- **单次硬限 30 秒 / 25MB / 仅 wav/mp3**：脚本对超限或其他格式（m4a/aac/ogg/flac/mov 音轨等）自动 `ffmpeg` 转 wav 16k 单声道分段；分段后单段约 1MB，不会触碰 25MB 上限。合规短输入跳过转码直传原文件。
- **切点对齐静音**：切点优先落在目标位置 ±4 秒窗口内最近的静音中点（silencedetect，-35dB/0.3s），避免把词切成两半；连续无停顿的音频自动退化为硬切。段长始终夹在 5~28.5 秒。
- **上下文接力**：段间把上一段结果尾部 500 字作为 `prompt` 传入（官方参数设计即为此用途，建议全文 <8000 字），弥补切点处的语义断裂；`--no-context` 可关闭。
- **无说话人分离**：需要区分说话人走 `ark-asr`。
- **语种自动判别**（无 language 参数）：普通话与方言（粤语、四川话、闽南语、吴语等）、多口音英语、法/德/日/韩/西/阿拉伯等数十种语言。
- 流式 `stream=true` 走 SSE 增量返回，文件转写场景用同步即可，脚本未封装流式。

## 报错速查

- `缺少 API Key` → 未设置环境变量且 `~/.zshrc` 无 export；key 在 [bigmodel.cn「API Keys」页](https://bigmodel.cn/usercenter/proj-mgmt/apikeys) 获取，也可 `--api-key` 传入。
- HTTP 401 → Key 无效或服务未开通；误用火山 `ARK_SPEECH_API_KEY`（旧名 `SPEECH_API_KEY`）也会 401（本服务只认智谱 Key）。
- HTTP 429/5xx → 脚本已自动退避重试 3 次，仍失败稍后再跑。
- `ffprobe 无法读取音频时长` → ffmpeg 未安装（`brew install ffmpeg`）、文件损坏，或 URL 返回的不是音频内容。
