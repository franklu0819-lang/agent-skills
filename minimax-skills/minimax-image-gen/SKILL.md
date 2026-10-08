---
name: minimax-image-gen
description: MiniMax 文生图/主体参考图生图（image-01）：一条提示词生成指定比例（1:1/16:9/9:16/3:4/21:9 等八档）或自定义像素（512-2048）的图片，一次最多 9 张，支持固定种子复现、主体参考图保持人物一致性、image-01-live 风格化（漫画/元气/中世纪/水彩）。Use whenever the user mentions MiniMax 生图、image-01、海螺画图、用 MiniMax 生成图片/插画/海报 —— 点名 MiniMax 引擎的图片生成就用本技能；未指明引擎的通用文生图/图生图/多图层默认 ark-image-gen（豆包 Seedream 全系）；贴图组本地排版走 social-cards。Also triggered as /minimax-image-gen。
---

# MiniMax 文生图（image-01）

一条命令文生图，同步接口直出（`POST /v1/image_generation`），脚本自动下载落盘（图片 URL 仅 24 小时有效）。**¥0.025/张**。

> 引擎分工：点名 MiniMax/海螺引擎 → 本技能；通用文生图/图生图/组图/拆图层 → `ark-image-gen`（豆包 Seedream 全系，比例与分辨率档位更全）；小红书/公众号贴图组（本地文字排版）→ `social-cards`。

## 快速使用

```bash
# <技能基目录> 为本技能安装目录（技能加载时给出）
python3 <技能基目录>/scripts/image_gen.py --prompt "赛博朋克风格的夜市，霓虹灯，8k 细节" --out-dir ./imgs

# 指定比例与张数（16:9 横幅 ×2）
python3 .../image_gen.py --prompt "..." --ratio 16:9 -n 2

# 自定义像素（仅 image-01；各边 [512,2048] 且 8 的倍数，与 --ratio 同给时官方以 ratio 优先）
python3 .../image_gen.py --prompt "..." --size 1920 1080

# 主体参考：给一张角色图，换场景保持人物一致（本地路径或公网 URL 均可）
python3 .../image_gen.py --prompt "同一角色站在雪山之巅" --subject-ref char.png

# 固定种子复现 / image-01-live 风格化 / 零成本预检
python3 .../image_gen.py --prompt "..." --seed 42
python3 .../image_gen.py --prompt "..." --model image-01-live --style 漫画
python3 .../image_gen.py --prompt "..." --dry-run
```

## 参数速查

| 项 | 取值 |
|---|---|
| `--ratio` | `1:1`（默认）/ `16:9` / `4:3` / `3:2` / `2:3` / `3:4` / `9:16` / `21:9`（21:9 仅 image-01） |
| `--size W H` | 各边 [512,2048]、8 的倍数（仅 image-01） |
| `-n` | [1,9]，默认 1 |
| `--subject-ref` | 主体参考图（JPG/PNG ≤10MB 本地路径或公网 URL；type=character） |
| `--style` | 漫画 / 元气 / 中世纪 / 水彩（仅 image-01-live，国内站独有；`--style-weight` (0,1] 默认 0.8） |
| `--seed` | 固定种子可复现构图 |
| `--optimizer` | 提示词改写（官方默认**关**；开启后服务端会重写 prompt） |

prompt ≤1500 字符。响应在 `data.image_urls[]`（官方新版结构，注意与旧版 `data.data[0].image_url` 不同）。

## 凭证（需配置）

`~/.zshrc` 的 `MINIMAX_API_KEY`（platform.minimax.cn「账户管理 → 接口密钥」；minimax- 家族统一只认此变量）。解析顺序：`--api-key`（传 `-` 从 stdin 读）→ 环境变量 → ~/.zshrc。`image-01-live` 仅国内站；海外账号加 `--base-url overseas`（其枚举仅 image-01）。key 不打印、不落盘。

## 技术要点（2026-10 官方文档）

- 端点：`POST https://api.minimax.cn/v1/image_generation`（注意路径不是 `/v1/image/generation`），同步返回，Bearer 认证
- 主体参考（图生图）：`subject_reference` 数组，`type` 目前仅 `character`，`image_file` 接公网 URL 或 Base64 Data URL——本地图脚本自动转 Data URL（≤10MB）
- 图片 URL **24 小时有效**，脚本即时下载到 `--out-dir`（默认 `./minimax_images`），不做二次中转
- image-01（2025-04 发布）是当前唯一主力图像模型；无更分辨率档位体系（想要 Seedream 式的多档分辨率/组图/拆图层走 `ark-image-gen`）
- AIGC 水印默认关闭（`aigc_watermark` 默认 false）
- 计费 ¥0.025/张（海外 $0.0035）；网络错误自动重试 1 次
- 错误统一看 `base_resp.status_code`（1004 鉴权、1002 限流、2013 参数无效——多为 ratio/size/style 与模型不匹配）

## 常见错误

| 现象 | 原因与处理 |
|---|---|
| base_resp 1004 login fail | Key 无效或国内/海外 Key 混用（两站独立账号） |
| 2013 参数无效 | `21:9`/`--size` 仅 image-01；`--style` 仅 image-01-live；prompt 超 1500 字符 |
| 人物一致性差 | 参考图要单人、正面、干净背景；prompt 里明确"同一角色/保持外貌" |
| 想要更高分辨率 | image-01 上限 2048；更高走 `ark-image-gen`（Seedream 2K/4K 档） |
| 图片链接过期 | 脚本已自动下载落盘；自己直调 API 时注意 24 小时时效 |

## 与其他工作流的集成

- 角色设定图：`--subject-ref` 保持人物一致，多场景出图给小说/漫画做设定页。
- 配图流水线：本技能出底图 → `social-article` 的正文配图模板加工；带文字排版的贴图组一律 `social-cards`（文字本地排版，不进 AI 生成环节）。
- 视频：生成的图作为 `minimax-video-gen` 图生视频的首帧素材。
