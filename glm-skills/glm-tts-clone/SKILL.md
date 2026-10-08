---
name: glm-tts-clone
description: 智谱 GLM 声音/音色复刻（glm-tts-clone）：上传一段 3~30 秒参考音频，API 一条龙复刻出专属音色 ID——自动上传音频、发起复刻、下载试听、列出/删除已复刻音色；复刻出的音色 ID 交给 glm-tts 朗读任意文本。Use whenever the user wants 复刻音色、音色复刻、声音复刻、克隆我的声音、用我的声音、复刻音色给智谱/GLM、生成自定义音色、voice clone、管理智谱复刻音色（列表/试听/删除）——只要涉及"造音色"就用本技能；"用已有音色朗读"走 glm-tts；火山/豆包系复刻（飞哥音色 S_q3oLhGy72）走 ark-tts。Also triggered as /glm-tts-clone。
---

# 智谱 glm-tts-clone 音色复刻

一条命令把参考音频复刻成专属音色 ID，之后用 `glm-tts` 以该音色朗读任意文本。无需去控制台网页操作。

> 分工：**造音色**（复刻/列表/试听/删除）→ 本技能；**用音色朗读**（系统音色或复刻 ID）→ `glm-tts`；火山豆包系复刻音色（如飞哥 S_q3oLhGy72）→ `ark-tts`。

## 快速使用

```bash
# <技能基目录> 为本技能安装目录（技能加载时给出）
# 复刻：上传参考音频 → 发起复刻 → 输出音色 ID + 下载试听 mp3
python3 <技能基目录>/scripts/voice_clone.py --create --audio ref.wav --voice-name feige \
    --text "参考音频里说的那句话" --preview-out feige_preview.mp3

# 列出本账号已复刻音色（含音色 ID/创建时间），--download 顺带下载全部试听
python3 .../voice_clone.py --list
python3 .../voice_clone.py --list --name fei --download ./previews

# 删除音色（不可恢复；必须先取得用户明示确认再执行）
python3 .../voice_clone.py --delete --voice voice_clone_xxx

# 复刻完成后，用 glm-tts 以新音色朗读
python3 <glm-tts 技能>/scripts/tts.py --text "任意文本" --voice voice_clone_xxx --output out.wav
```

试听验证：`afplay feige_preview.mp3`。复刻效果不满意时，换更干净的参考音频重刻一个新名字，旧的 `--delete` 清掉。

## 参考音频要求（官方限制）

| 项 | 要求 |
|---|---|
| 格式 | mp3 / wav（其他格式先 `ffmpeg -i in.m4a out.wav` 转） |
| 大小 | 单文件 ≤ 10MB（硬限制，脚本校验） |
| 时长 | 建议 3~30 秒（脚本用 ffprobe 检测，超出警告不阻断） |
| 质量 | 单人、干净人声、无 BGM/杂音/混响，音量稳定，自然语速 |
| `--text` | 参考音频的文字内容（选填，**提供可提升相似度**，建议照原文给出） |

## 凭证（需配置）

`~/.zshrc` 的 `ZHIPU_API_KEY`（bigmodel.cn 右上角个人中心「API Keys」页，形如 `<32位hex>.<16位hex>`；glm- 家族统一只认此变量）。解析顺序：`--api-key`（传 `-` 从 stdin 读，避免 key 进 shell history）→ `ZHIPU_API_KEY` 环境变量 → ~/.zshrc。**火山 ARK_SPEECH_API_KEY 在本服务不认**，401 时先查 Key 来源。key 不打印、不落盘。

## 技术要点（2026-10 官方文档）

- 复刻链路三步：① `POST /paas/v4/files`（multipart，`purpose=voice-clone-input`）上传参考音频得 `file_id`；② `POST /paas/v4/voice/clone`（`model=glm-tts-clone`、`voice_name` 唯一名、`input`=试听文本、`file_id`、`text`=参考文本选填）得 `voice` 音色 ID（**实测为 UUID 形式**，非文档示例的 `voice_clone_` 前缀）；③ 试听地址从 `GET /paas/v4/voice/list` 的 `download_url` 取（`/files/{id}/content` 仅支持 batch，不走；download_url 实测返回 **WAV 流**，脚本按魔数自动纠正扩展名）
- 管理：`GET /paas/v4/voice/list`（`voiceType=PRIVATE` 本账号复刻 / `OFFICIAL` 官方，返回 voice/voice_name/download_url/create_time）；`POST /paas/v4/voice/delete`（按 `voice` ID 删）
- `voice_name` 要求账号内唯一：脚本创建前先查重名；`--delete` 传名称时先解析成 ID 并要求唯一匹配
- 复刻出的音色 ID 长期有效，直接作为 glm-tts 的 `--voice` 参数（该能力 glm-tts 侧一直支持，本技能补齐的是**通过 API 造音色**这一环）
- 认证与 glm 家族一致：标准 Bearer；网络错误自动重试 1 次
- 计费：官方 API 文档未标复刻价格，以控制台账单为准；合成侧仍按 glm-tts 0.03 元/千字符

## 常见错误

| 现象 | 原因与处理 |
|---|---|
| HTTP 401 / code=1002 | Key 无效或用错火山 Key——用 bigmodel.cn「API Keys」页的 `<id>.<secret>` 形式 Key |
| 音色名已存在 | `voice_name` 账号内唯一，`--list` 核对后换名或先 `--delete` |
| 复刻相似度低 | 参考音频不够干净（多人/BGM/过短）；给准 `--text` 参考文本；换 10~20 秒清晰人声重刻 |
| 试听下载失败 | 不阻断（音色 ID 已到手），稍后 `--list --download DIR` 重取 |
| 上传报格式不支持 | 仅认 mp3/wav，m4a/aac 等先 ffmpeg 转 wav |

## 与其他工作流的集成

- 复刻 → 朗读：本技能产出音色 ID 后，长文本朗读交给 `glm-tts`（自动分段、断点续跑）。
- 效果验证：试听或合成音频可交 `glm-asr` / `ark-asr` 转写回来比对。
- 想复刻的声音只有视频文件时：`ffmpeg -i in.mp4 -vn -ac 1 -ar 24000 ref.wav` 抽音轨后再来复刻。
