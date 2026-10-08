---
name: ark-audio-gen
description: 火山引擎 Seed-Audio 1.0 音频创作：一条提示词端到端生成含多角色对白、情绪语气、背景音乐、环境音效的成片级音轨（最长约 2 分钟）。Use whenever the user wants 生成音频、音频创作、情景音频、广播剧/有声剧片段、带音效的配音、多人对话音频、生成一段有背景音的音频、做一段音效 —— 区别于纯朗读：只要音频里有"戏"（多角色/音乐/音效/环境声）就用本技能；纯文字朗读/旁白用 ark-tts。Also triggered as /ark-audio-gen。
---

# Seed-Audio 1.0 音频创作（直连豆包语音 API）

用封装脚本直连 `https://openspeech.bytedance.com/api/v3/tts/create`（`model: seed-audio-1.0`）做音频创作：对白、情绪、BGM、音效一条 prompt 直出成片音轨，无需多轨剪辑。认证用 `ARK_SPEECH_API_KEY`（豆包语音控制台 UUID Key，旧名 `SPEECH_API_KEY` 仍兼容）——不要读取、传递或落盘任何 API key，脚本自己从环境变量或 `~/.zshrc` 解析；**方舟 ark- Key 本服务不认**。

> ark- 家族分工：纯朗读/旁白/复刻音色配音用 `ark-tts`；带戏的成片音轨（多角色+音效+BGM）用本技能；录音转文字用 `ark-asr`。

## 提示词四要素（写全效果才好）

**谁在说（年龄性别+音色特征）+ 什么情绪 + 什么场景 + 有什么声响（BGM/环境音/音效）。**

```
先是一声轻轻的敲门声。年轻女性用温柔的语气说：欢迎光临，请问需要点什么？背景有咖啡厅轻柔的爵士乐。
```

多角色直接在一条 prompt 里依次编排，角色描述用括号：

```
男子1（中青年男性，嗓音低沉浑厚）用严肃语气说道："钟sir，你是什么时候被收买的？"
老年男性（声线苍老，带着笑意）缓缓答道："从我进门的那一刻起。"
此时雨声渐起，紧张的弦乐进入。
```

## 标准流程：直接跑脚本

```bash
bash <技能目录>/scripts/audio_gen.sh "先是一声手机震动。男子1（青年，台湾口音）接起电话用疲惫语气说：喂，哪位？背景是深夜办公室的键盘声。" -o ./output/scene.mp3
```

成功时最后输出：

```json
{"ok":true,"audio_path":"/abs/path/scene.mp3","format":"mp3","model":"seed-audio-1.0"}
```

常用参数：

| 选项 | 说明 | 默认 |
|---|---|---|
| `-o` | 输出音频路径 | `./ark_audio_<时间戳>.mp3` |
| `-f` | `mp3` 或 `wav` | mp3 |
| `--sample-rate` | 采样率 | 48000 |
| `--speech-rate` | 语速 [-50,100] | 0 |
| `--pitch-rate` | 音调 [-50,100] | 0 |
| `--loudness-rate` | 音量 [-50,100] | 0 |
| `--dry-run` | 只打印参数 JSON 不实际生成 | 关 |

## 实测确认（2026-09-17）

- 接口同步返回 `{"audio":"<base64>"}`，脚本已解码落盘；生成约几十秒的音频耗时 1 分钟内（`--timeout` 默认 300s）。
- 单次生成最长约 2 分钟；提示词里的音效/环境描写会被真实合成（敲门声、雨声、BGM 均可）。
- 非语言细节（笑声、叹息、停顿、方言口音）直接写进 prompt 即可。
- 生成内容可用于视频配音轨：需要 wav 时 `-f wav` 或事后 ffmpeg 转（`-ar 48000 -ac 2`）。

## 报错速查

- 401/Invalid X-Api-Key → Key 不是语音控制台 UUID Key（不能用方舟 ark- Key）。
- 超时 → 音频越长生成越久，加大 `--timeout` 或缩短 prompt 时长预期。
