---
name: minimax-tts-clone
description: MiniMax 声音/音色复刻：上传 10 秒–5 分钟参考音频（mp3/m4a/wav），API 一条龙复刻出自定义命名的专属音色 ID——自动上传音频、发起复刻、下载试听、列出/删除已复刻音色；复刻出的 voice_id 交给 minimax-tts 朗读任意文本。Use whenever the user wants 复刻音色给 MiniMax/海螺、用海螺复刻我的声音、MiniMax voice clone、管理 MiniMax 复刻音色（列表/试听/删除）——涉及给 MiniMax 造音色就用本技能；用已有音色朗读走 minimax-tts；智谱系复刻走 glm-tts-clone；火山豆包系复刻（飞哥音色）走 ark-tts。Also triggered as /minimax-tts-clone。
---

# MiniMax 声音复刻

一条命令把参考音频复刻成**自定义命名**的专属音色 ID（与 glm 系统分配 ID 不同，MiniMax 的 voice_id 由你自己取名），之后用 `minimax-tts` 以该音色朗读任意文本。免控制台网页操作。

> 分工：**造 MiniMax 音色**（复刻/列表/试听/删除）→ 本技能；**用音色朗读** → `minimax-tts`；智谱系复刻 → `glm-tts-clone`；火山豆包系复刻音色（飞哥 S_q3oLhGy72）→ `ark-tts`。

## 快速使用

```bash
# <技能基目录> 为本技能安装目录（技能加载时给出）
# 复刻：上传参考音频 → 发起复刻 → 输出自定义 voice_id + 试听
python3 <技能基目录>/scripts/voice_clone.py --create --audio ref.wav \
    --voice-id feige2026 --text "这是复刻后的试听文本" --demo-out feige_preview.mp3

# 参考音频不够干净时可加降噪/音量归一化
python3 .../voice_clone.py --create --audio raw.m4a --voice-id clean_voice_x --denoise --normalize

# 列出本账号已复刻音色；--download 顺带下载全部试听
python3 .../voice_clone.py --list
python3 .../voice_clone.py --list --download ./previews

# 删除音色（不可恢复，必须先取得用户明示确认）
python3 .../voice_clone.py --delete --voice-id feige2026 --yes

# 复刻完成后，用 minimax-tts 以新音色朗读
python3 <minimax-tts 技能>/scripts/tts.py --text "任意文本" --voice feige2026 --output out.wav
```

试听验证：`afplay feige_preview.mp3`。效果不满意时换更干净的参考音频、换名重刻，旧的 `--delete` 清掉。

## 参考音频要求（官方限制）

| 项 | 要求 |
|---|---|
| 格式 | mp3 / m4a / wav（其他格式先 `ffmpeg -i in.xxx out.wav` 转） |
| 大小 | 单文件 ≤ 20MB（硬限制，脚本校验） |
| 时长 | 10 秒–5 分钟（脚本用 ffprobe 检测，超出警告不阻断） |
| 质量 | 单人、干净人声、无 BGM/杂音/混响，音量稳定，自然语速 |

`--voice-id` 命名规则（官方）：8–256 位、英文字母开头、仅字母/数字/`-`/`_`、末位不可为 `-`/`_`、账号内不可重复——脚本本地校验。

## 凭证与前置（需配置）

`~/.zshrc` 的 `MINIMAX_API_KEY`（platform.minimax.cn「账户管理 → 接口密钥」；minimax- 家族统一只认此变量）。**复刻需账号先完成个人实名或企业认证**，否则报 2038 无复刻权限。解析顺序：`--api-key`（传 `-` 从 stdin 读）→ 环境变量 → ~/.zshrc。key 不打印、不落盘。

## 技术要点（2026-10 官方文档）

- 复刻链路两步：① `POST /v1/files/upload`（multipart，`purpose=voice_clone`）上传参考音频得 `file_id`；② `POST /v1/voice_clone`（`file_id` + 自定义 `voice_id` + 可选 `text`/`model` 试听、`need_noise_reduction`/`need_volume_normalization`）响应含 `demo_audio` 试听链接与 `extra_info`（usage_characters 等）
- 管理：`POST /v1/get_voice`（`voice_type=voice_cloning`）列表——**新复刻音色须先成功合成一次才会出现在列表**；`POST /v1/delete_voice` 删除（系统音色不可删；删除后 voice_id 永久失效）
- 计费：**¥9.90/音色**（生成时不收费、首次合成时扣）；试听按所选 T2A 模型单价计费
- **保鲜期：复刻音色 7 天内未正式调用会被系统删除**——复刻完尽快用 `minimax-tts` 合成一次
- 高级选项（官方另有，脚本未包）：`clone_prompt`（示例音频增强相似度）、`text_validation`（ASR 校验参考音频内容）、文生音色 Voice Design
- 网络错误自动重试 1 次；错误统一看 `base_resp.status_code`（2038 未实名、2013 命名不合规、1043 校验不过）

## 常见错误

| 现象 | 原因与处理 |
|---|---|
| base_resp 2038 无复刻权限 | 账号未实名/企业认证——控制台完成认证后重试 |
| 2013 参数无效 | `--voice-id` 不符命名规则或重名（`--list` 核对）；音频格式/大小/时长越界 |
| 复刻相似度低 | 参考音频不够干净（多人/BGM/过短）；加 `--denoise --normalize`；换 30 秒以上清晰人声重刻 |
| `--list` 里看不到新音色 | 官方行为：须先用该音色成功合成一次才会入列 |
| 音色突然失效 | 7 天未调用被系统删除——重刻一次并立即合成 |
| 上传报格式不支持 | 仅 mp3/m4a/wav；m4a 之外的先 ffmpeg 转 wav |

## 与其他工作流的集成

- 复刻 → 朗读：本技能产出 voice_id 后，长文本朗读交给 `minimax-tts`（自动分段、断点续跑）。
- 效果验证：试听或合成音频交 `minimax-asr` / `ark-asr` 转写回来比对。
- 想复刻的声音只有视频文件时：`ffmpeg -i in.mp4 -vn -ac 1 -ar 24000 ref.wav` 抽音轨后再来复刻。
