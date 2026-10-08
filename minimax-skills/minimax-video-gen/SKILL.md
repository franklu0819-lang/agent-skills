---
name: minimax-video-gen
description: MiniMax 视频生成（v2 MiniMax-H3/H3-Max + v1 legacy Hailuo-2.3/02）：文生视频/图生视频异步任务一条龙（创建→轮询→下载落盘），4-15 秒最高 2K，内置成本预估、分辨率×时长矩阵校验、任务查询续传与取消。Use whenever the user mentions MiniMax 视频、海螺视频、Hailuo 生视频、MiniMax-H3、用 MiniMax 做视频/图生视频 —— 点名 MiniMax/海螺引擎的视频生成就用本技能；未指明引擎的通用文生/图生/参考生视频默认 ark-video-gen（豆包 Seedance）；首帧图可用 minimax-image-gen 生成。Also triggered as /minimax-video-gen。
---

# MiniMax 视频生成（H3 / Hailuo）

一条命令文生视频/图生视频：创建异步任务 → 自动轮询（官方建议 10s 间隔）→ 成片及时下载落盘（下载地址有时效）。两代 API 并存，脚本默认 **v2（MiniMax-H3）**，便宜场景切 `--api v1`（Hailuo）。

> 引擎分工：点名 MiniMax/海螺/H3/Hailuo → 本技能；通用视频生成/参考生视频/短剧一致性方法论 → `ark-video-gen`（豆包 Seedance）；首帧底图 → `minimax-image-gen`。

## 快速使用

```bash
# <技能基目录> 为本技能安装目录（技能加载时给出）
# v2 H3 文生视频（768P 6s 16:9 ≈¥3）
python3 <技能基目录>/scripts/video_gen.py --prompt "雨夜霓虹街头，镜头缓缓推进" --ratio 16:9 --duration 6

# 成本预估 + 请求体预检（不花钱）
python3 .../video_gen.py --prompt "..." --dry-run

# 图生视频：比例自适应首帧图；首帧可用 minimax-image-gen 先出
python3 .../video_gen.py --prompt "让画面动起来，镜头缓缓拉远" --first-frame scene.png

# 2K 高清（仅 MiniMax-H3，0.8 元/秒）
python3 .../video_gen.py --prompt "..." --resolution 2K --duration 10

# v1 便宜档：Hailuo-02 512P 6s 仅 ¥0.6（验证构图用）
python3 .../video_gen.py --prompt "..." --api v1 --model MiniMax-Hailuo-02 --resolution 512P --duration 6

# 只建任务不等待 / 断点续查（v2 任务 7 天内可查）/ 取消排队任务（不扣费）
python3 .../video_gen.py --prompt "..." --no-wait
python3 .../video_gen.py --query TASK_ID
python3 .../video_gen.py --cancel TASK_ID
```

## 两代 API 与价格（2026-10 官方）

| | v2（默认） | v1（--api v1，legacy） |
|---|---|---|
| 模型 | `MiniMax-H3`（默认）/ `MiniMax-H3-Max` | `MiniMax-Hailuo-2.3`（默认）/ `-02` / `-2.3-Fast` |
| 分辨率×时长 | H3：768P/2K × 4-15s；H3-Max：480P/768P × 5-15s | 2.3/2.3-Fast：768P 6/10s、1080P 6s；02 另有 512P 6/10s |
| 计费 | **按秒**：H3 768P ¥0.5/s、2K ¥0.8/s；H3-Max ¥0.33-0.5/s | **按条**：2.3/02 768P ¥2(6s)/¥4(10s)、1080P ¥3.5；02 512P ¥0.6(6s)（**512P 仅图生视频**，2026-10 实测确认；文生视频最低 768P） |
| 画幅 | 文生视频必填 `--ratio`（21:9/16:9/4:3/1:1/3:4/9:16）；图生视频恒自适应首帧 | 官方称输出分辨率跟随首帧图——脚本仍要求显式 `--resolution`（成本预估与矩阵校验需要），请按首帧比例选择；prompt 支持 `[左移] [推进] [固定]` 等 15 种运镜指令 |
| 下载时效 | `task.content.url` 限时地址，过期重新 `--query` 刷新 | `download_url` **仅 1 小时**（file_id → files/retrieve 换取） |

脚本内置完整"模型×分辨率×时长"矩阵校验与成本预估，不支持的组合直接拦下。首帧图：v1 <20MB、短边 >300px；v2 ≤30MB。v1 提示词改写（prompt_optimizer）默认关，加 `--optimizer` 开启（开启后服务端会重写 prompt）。

## 凭证（需配置）

`~/.zshrc` 的 `MINIMAX_API_KEY`（platform.minimax.cn「账户管理 → 接口密钥」；minimax- 家族统一只认此变量）。解析顺序：`--api-key`（传 `-` 从 stdin 读）→ 环境变量 → ~/.zshrc。海外账号加 `--base-url overseas`。key 不打印、不落盘。

## 技术要点（2026-10 官方文档）

- v2 端点：`POST /v2/video_generation`（`content` 数组多模态：text ≤7000 字符 + `image_url` 带 role=first_frame/reference_image 等）；`GET /v2/query/video_generation/{task_id}`（仅支持最近 **7 天**）；`DELETE /v2/video_generation/{task_id}` 取消（queued 不扣费）或删除记录（running 不可操作）。状态 queued/running/succeeded/failed/cancelled
- v1 端点三步：`POST /v1/video_generation`（prompt ≤2000、`first_frame_image` 接 URL 或 Base64 Data URL）→ `GET /v1/query/video_generation?task_id=`（状态 Preparing/Queueing/Processing/Success/Fail，成功得 file_id）→ `GET /v1/files/retrieve?file_id=` 换 download_url（1 小时时效，脚本立即下载）
- 轮询间隔 10s（官方建议），脚本最多阻塞 30 分钟后让位给 `--query` 续查；网络错误自动重试 1 次
- AIGC 水印默认关闭；v2 另有 H3-Context-IR（结构化增强提示词）与成片再生成（768P→2K）衍生任务，脚本未包
- 错误格式：v2 是 OpenAI 风格 `error.message`，v1 是 `base_resp.status_code`——脚本两种都检查

## 常见错误

| 现象 | 原因与处理 |
|---|---|
| 2013 / error 参数无效 | 模型×分辨率×时长组合不合法——看上方矩阵；v2 文生视频必须给 `--ratio` |
| --query 报任务不存在 | v2 任务仅 7 天内可查；过期任务无法找回 |
| 下载链接失效 | v1 链接仅 1 小时、v2 限时——重新 `--query` 刷新地址再下 |
| 首帧图被拒 | v1 要求 <20MB、短边 >300px、宽高比 2:5~5:2；v2 图片 ≤30MB |
| 想取消扣费中的任务 | 只有 queued 可免费取消；running 已计费，等完成或删除记录 |
| 图生视频比例不对 | v2 图生视频恒自适应首帧（`--ratio` 被忽略）；要指定画幅先裁首帧图 |

## 与其他工作流的集成

- **省钱流水线**：`minimax-image-gen` 出首帧（构图可控、失败重画便宜）→ 本技能图生视频；先用 v1 512P 或 v2 480P 验证动态，满意再上 2K。
- 多片段一致性：与 `ark-video-gen` 的素材包/尾帧接力方法论通用——统一角色参考图 + 相邻片段用上一段尾帧当首帧。
- 成片后处理：ffmpeg 转码/拼接/配音（`minimax-tts` 出解说音轨）。
