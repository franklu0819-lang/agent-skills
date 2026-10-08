---
name: minimax-tts
description: MiniMax 海螺语音合成（T2A，speech-2.8 系列）：文本合成带情感的自然语音 wav（327 系统音色精选 10 个内置：甜美女声/御姐/青涩青年/霸道青年/新闻女声等），支持情绪 emotion、音调 pitch、多音色混合、停顿标记、发音字典、长文本自动分段续跑。Use whenever the user mentions MiniMax 语音合成、海螺语音、海螺 TTS、speech-2.8、minimax TTS、用 MiniMax 音色朗读 —— 点名 MiniMax/海螺引擎就用本技能；未指明引擎的通用配音默认 ark-tts（飞哥复刻音色）；智谱系统音色走 glm-tts；带戏成片音轨（多角色+BGM+音效）走 ark-audio-gen。Also triggered as /minimax-tts。
---

# MiniMax 海螺语音合成（T2A）

一条命令把文本合成为语音，默认模型 **speech-2.8-hd**（2026-01 最新版，支持 `(laughs)`/`(sighs)` 等 23 种语气词标签），走 `POST /v1/t2a_v2`。

> 引擎分工：点名 MiniMax/海螺引擎或音色 → 本技能；通用配音/飞哥复刻音色 → `ark-tts`；智谱系统音色 → `glm-tts`；多角色+BGM+音效成片音轨 → `ark-audio-gen`；造 MiniMax 音色（复刻）→ `minimax-tts-clone`。

## 快速使用

```bash
# <技能基目录> 为本技能安装目录（技能加载时给出）
# 默认音色：甜美女声
python3 <技能基目录>/scripts/tts.py --text "大家好，欢迎来到 MiniMax 开放平台" --output out.wav

# 浏览内置精选音色（10 个中文）；--online 拉全量 327 个系统音色
python3 .../tts.py --list-voices
python3 .../tts.py --list-voices --online

# 情绪 + 音调：御姐声线读悲伤文本
python3 .../tts.py --text "..." --voice female-yujie --emotion sad --pitch -2 --output out.wav

# 多音色混合（≤4 个，权重 [1,100]，对话场景一人一句可混出双主播）
python3 .../tts.py --text "..." --mix "male-qn-qingse:70,female-shaonv:30" --output out.wav

# 长文本：超过 2800 计费字符自动分段逐段合成拼接；中断可续跑
python3 .../tts.py --file script.txt --output out.wav

# 发音字典（专有名词注音）+ 零成本预检
python3 .../tts.py --text "..." --pronunciation "燕少飞/(yan4)(shao3)(fei1)" --output out.wav
python3 .../tts.py --file script.txt --dry-run
```

播放验证：`afplay out.wav`。需要 mp3 时 ffmpeg 转：`ffmpeg -i out.wav -b:a 128k out.mp3`（单段也可 `--format mp3` 直出）。

## 音色（精选）与文本标记

| voice_id | 名称 | 特点 |
|---|---|---|
| `female-tianmei` | 甜美女声（默认） | 女，通用讲解/旁白 |
| `female-shaonv` / `female-yujie` / `wumei_yujie` | 少女 / 御姐 / 妩媚御姐 | 女，清亮 / 成熟 / 磁性 |
| `male-qn-qingse` / `male-qn-badao` / `junlang_nanyou` | 青涩青年 / 霸道青年 / 俊朗男友 | 男声三档 |
| `Chinese (Mandarin)_News_Anchor` | 新闻女声 | 播报 |
| `lovely_girl` / `cartoon_pig` | 萌萌女童 / 卡通猪小琪 | 童趣 |

全量 327 个（30+ 语言，含粤语主持等）用 `--list-voices --online` 在线浏览。复刻音色（`minimax-tts-clone` 产出）直接 `--voice <自定义ID>`。

文本内嵌标记：停顿 `<#0.5#>`（0.01–99.99 秒，两位小数，不可连续）；语气词 `(laughs)` `(sighs)` `(breath)` 等（2.8 系列）。

## 凭证（需配置）

`~/.zshrc` 的 `MINIMAX_API_KEY`（platform.minimax.cn「账户管理 → 接口密钥」；minimax- 家族统一只认此变量）。解析顺序：`--api-key`（传 `-` 从 stdin 读）→ `MINIMAX_API_KEY` 环境变量 → ~/.zshrc。国内站默认 `api.minimax.cn`；海外账号加 `--base-url overseas`。key 不打印、不落盘。

## 技术要点（2026-10 官方文档）

- 端点：`POST https://api.minimax.cn/v1/t2a_v2`（同步非流式），Bearer 认证，无需 GroupId；响应 `data.audio` 为 **hex 编码**音频（脚本自动解码），`extra_info.usage_characters` 是计费字符数
- `text` 单请求硬上限 10,000 字符，超 3,000 官方建议流式——脚本按计费字符 2,800 分段（**计费口径 2026-10 实测校准：仅汉字 = 2 字符，全角标点/字母/数字/空格各 1**；预估与官方 `usage_characters` 精确吻合），逐段合成 wav 提取 PCM 拼接、重写 wav 头，参数不一致会中止
- `voice_setting`：`voice_id`（timbre_weights 混音时留空）、`speed` [0.5,2]、`vol` (0,10]、`pitch` [-12,12]（半音）、`emotion`（happy/sad/angry/fearful/disgusted/surprised/calm；**fluent/whisper 仅 2.6 系列，2.8 不支持**，脚本拦截）
- `audio_setting`：默认 24kHz 单声道 wav（多段拼接唯一容器；mp3 无法可靠拼接，脚本多段时自动切 wav）；原生还支持 mp3/flac/pcm/opus
- `pronunciation_dict.tone`：`原文本/替换读音` 数组，替换用带声调拼音 `(yan4)`、IPA 或粤拼
- `timbre_weights`（注意拼写 timbre）：最多混 4 个音色，权重 [1,100]
- 断点续跑：多段逐段缓存于 `<output>.parts/`，网络失败/Ctrl-C 后重跑同命令自动跳过已完成段（不重复计费）；网络错误自动重试 1 次
- 计费：speech-2.8-hd **¥3.50/万计费字符**、2.8-turbo ¥2.00（2.6/02 系列同价）；复刻音色 **7 天内不调用会被系统删除**（见 minimax-tts-clone）
- **错误格式坑**：国内站错误在 HTTP 200 的 `base_resp.status_code`（1004 鉴权、1002/1039 限流、1042 非法字符>10%、2013 参数无效）——脚本已统一检查

## 常见错误

| 现象 | 原因与处理 |
|---|---|
| base_resp 1004 login fail | Key 无效或国内/海外 Key 混用（两站独立账号）；核对 MINIMAX_API_KEY 来源 |
| 2013 参数无效 | voice_id 拼错（`--list-voices --online` 核对）、emotion 与模型不匹配、mix 权重越界 |
| 1042 非法字符 | 文本含 >10% 非法字符（乱码/特殊符号），检查输入编码 |
| data.audio 为空 | 文本全被标记占用或为空；换正常文本重试 |
| whisper/fluent 报错 | 这两个 emotion 仅 speech-2.6 系列；2.8 换 calm 或切 `--model speech-2.6-hd` |
| 想要 24kHz 之外采样率 | 脚本固定 24kHz；特殊需求 ffmpeg 重采样 `ffmpeg -i out.wav -ar 44100` |

## 与其他工作流的集成

- 视频教程解说：需要海螺音色时用本技能出 wav，交给 `video-tutorial-gen` 的 assemble_tutorial.py 合成。
- 造音色：参考音频复刻专属音色走 `minimax-tts-clone`，产出的 voice_id 回到本技能 `--voice` 朗读。
- 效果验证：合成音频交给 `minimax-asr` / `ark-asr` 转写回来比对。
- 长篇小说朗读：`--file` 整本喂入自动分段；段落级断点续跑保证长任务可中断恢复。
