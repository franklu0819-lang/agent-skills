# agent-skills

个人 Agent 技能仓库，托管面向 ZCode 等 Agent CLI 的技能（SKILL.md + 配套脚本），按技能家族分目录组织，安装到 `~/.agents/skills/` 即可使用。

## 目录说明

| 目录 | 家族 | 内容 |
|------|------|------|
| [ark-skills/](ark-skills/) | 火山引擎方舟（Ark）/ 豆包系 | 语音、音频、图片、视频生成共 5 个技能 |

后续其他技能家族会以各自目录加入。

## ark-skills：方舟系技能

| 技能 | 用途 | 默认模型/服务 |
|------|------|---------------|
| [ark-tts](ark-skills/ark-tts/) | 语音合成（TTS），支持复刻音色朗读任意中文文本，内置 289 个音色库 | 豆包大模型 TTS |
| [ark-asr](ark-skills/ark-asr/) | 语音识别（ASR），本地音频文件或 URL 转写为带标点的文字，支持说话人分离 | Seed-ASR 录音文件识别 |
| [ark-audio-gen](ark-skills/ark-audio-gen/) | 音频创作：一条提示词直出含多角色对白、情绪、BGM、音效的成片音轨（约 2 分钟内） | Seed-Audio 1.0 |
| [ark-image-gen](ark-skills/ark-image-gen/) | 文生图 / 图生图 / 组图 / 多图层拆分，支持指定比例与分辨率档位 | Seedream 全系（5.0 lite/flash/pro、4.5、4.0） |
| [ark-video-gen](ark-skills/ark-video-gen/) | 文生视频 / 图生视频 / 参考生视频，内置本地参数校验、draft 先行、成本预估等省钱纪律，支持尾帧接力保持画面连续 | doubao-seedance-2-5 |

## 安装

```bash
git clone https://github.com/franklu0819-lang/agent-skills.git
cp -r agent-skills/ark-skills/ark-* ~/.agents/skills/
```

## 密钥配置

技能与脚本**不读取、不存储、不落盘任何 API key**，认证统一从环境变量解析：

| 环境变量 | 用途 | 获取方式 |
|----------|------|----------|
| `ARK_API_KEY` | 方舟数据面 API（图片/视频生成） | [火山方舟控制台](https://console.volcengine.com/ark)，`ark-` 开头 |
| `SPEECH_API_KEY` | 豆包语音服务（TTS/ASR/音频创作），**方舟 ark- Key 本服务不认** | 豆包语音控制台 API Key 管理页，UUID 格式 |

写入 `~/.zshrc` 即可，脚本会自动解析：

```bash
export ARK_API_KEY=ark-xxxxxxxx
export SPEECH_API_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

## 目录结构

```
agent-skills/
└── ark-skills/
    ├── ark-asr/          # 语音识别
    │   ├── SKILL.md
    │   └── scripts/transcribe.sh
    ├── ark-audio-gen/    # 音频创作
    │   ├── SKILL.md
    │   └── scripts/audio_gen.sh
    ├── ark-image-gen/    # 图片生成
    │   ├── SKILL.md
    │   └── scripts/image_gen.sh
    ├── ark-tts/          # 语音合成
    │   ├── SKILL.md
    │   ├── references/voices.md
    │   └── scripts/tts.py
    └── ark-video-gen/    # 视频生成
        ├── SKILL.md
        └── scripts/ark_video.sh
```
