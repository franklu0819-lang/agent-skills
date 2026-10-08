---
name: glm-image-gen
description: 智谱 GLM-Image 文生图：旗舰画质 + 开源 SOTA 中英文文字渲染（海报标题、招牌、多格图文不乱码），指定比例（1:1/16:9/4:3 等推荐档或 32 对齐自定义像素），一次 1-9 张，0.1 元/张。Use whenever the user mentions glm-image、GLM 生图、GLM-Image、智谱画图、智谱生成图片、用智谱做海报/插画 —— 点名智谱/GLM 引擎的文生图，或图上要清晰中文/英文字排的海报、招牌、图文卡就用本技能；未指明引擎的通用文生图/图生图/组图/拆图层默认 ark-image-gen（豆包 Seedream 全系）；MiniMax/海螺引擎走 minimax-image-gen。Also triggered as /glm-image-gen。
---

# 智谱 GLM-Image 文生图

一条命令文生图，同步接口直出（`POST /api/paas/v4/images/generations`），脚本自动下载落盘（图片 URL 仅 30 天有效）。**0.1 元/张**。glm-image 是智谱旗舰图像生成模型（9B 自回归 + 7B DiT 扩散混合架构 + Glyph Encoder），**中英文文字渲染开源 SOTA**（CVTG-2K Word Accuracy 0.91，LongText-Bench 中文 0.98）——海报大字、招牌、多格图文这类"图上写字"场景是它的独门强项。

> 引擎分工：点名智谱/GLM 引擎的**文生图**，或要图上文字清晰不乱码 → 本技能；通用文生图/图生图/组图/多图层拆分 → `ark-image-gen`（豆包 Seedream 全系，功能最全）；MiniMax/海螺 + 主体参考人物一致性 → `minimax-image-gen`。**本技能仅文生图**（glm-image 无参考图输入模态）——点名智谱但要图生图/参考图时引导走 `ark-image-gen`。

## 快速使用

```bash
# <技能基目录> 为本技能安装目录（技能加载时给出）
# 默认 1:1 1280x1280
python3 <技能基目录>/scripts/image_gen.py --prompt "书店橱窗海报，暖光，大字标题「春日读书周」" -o poster.png

# 横版 16:9（官方推荐档 1728x960）
python3 .../image_gen.py --prompt "清晨海面的白色帆船，电影感" --ratio 16:9 -o sea.png

# 无推荐档的比例（如 21:9）按基准像素自动换算
python3 .../image_gen.py --prompt "..." --ratio 21:9

# 自定义像素：宽高均为 32 的整数倍、[512,2048]、总像素 ≤ 2^22
python3 .../image_gen.py --prompt "..." --size 1920x1088

# 一次出 4 张候选（逐张独立请求，各计费 0.1 元，输出自动加 -1..-4 序号）
python3 .../image_gen.py --prompt "..." --ratio 3:4 -n 4 -o concept

# 零成本预检：看请求体与换算结果，不调 API
python3 .../image_gen.py --prompt "..." --ratio 9:16 --dry-run
```

成功时最后输出（stdout 一行 JSON，交给调用方消费）：

```json
{"ok": true, "images": ["/abs/path/poster.png"], "model": "glm-image", "size": "1280x1280", "requested": 1, "failed": 0}
```

## 参数速查

| 项 | 取值 |
|---|---|
| `--prompt` | 必填，≤1000 字符（超限报错不截断） |
| `--ratio` | `1:1`（默认）/ `3:2` / `2:3` / `4:3` / `3:4` / `16:9` / `9:16` 命中官方推荐档；其他比例（最宽 4:1）按基准 1658880 像素换算成 32 对齐合法尺寸 |
| `--size` | `宽x高` 自定义：均为 32 的整数倍、[512,2048]、总像素 ≤ 2^22=4194304；边长 <1024 会提示（低于官方建议值）；与 `--ratio` 互斥 |
| `-n` | [1,9]，默认 1；API 单请求只出 1 张，脚本逐张独立请求，某张失败不影响其余 |
| `-o` | 输出路径（默认 `./glm_image_<时间戳>.png`；多张自动加 `-1/-2` 序号；扩展名按实际返回格式纠正） |
| `--no-watermark` | 关闭显式+隐式水印；**须先在 个人中心-安全管理-去水印管理 签署免责声明** |
| `--timeout` | 单次请求超时秒数，默认 120（hd 官方口径约 20 秒） |

无 `--seed`（API 不支持种子复现，重跑同一 prompt 每次构图不同）；`quality` 恒为 hd（glm-image 唯一支持档，也是默认，无需传）。

## 尺寸与推荐档

| 比例 | 尺寸（宽x高） |
|---|---|
| 1:1 | 1280x1280（默认） |
| 3:2 / 2:3 | 1568x1056 / 1056x1568 |
| 4:3 / 3:4 | 1472x1088 / 1088x1472 |
| 16:9 / 9:16 | 1728x960 / 960x1728 |

官方口径：模型原生支持任意比例生成，自定义时宽高为 32 的整数倍、[512,2048]、总像素 ≤ 2^22。`--ratio` 给推荐档之外的比例时脚本自动换算（±3% 内会吸附到最近推荐档），换算结果先用 `--dry-run` 核对。

## 凭证（需配置）

`~/.zshrc` 的 `ZHIPU_API_KEY`（[bigmodel.cn](https://bigmodel.cn/usercenter/proj-mgmt/apikeys) 右上角个人中心「API Keys」页，形如 `<32位hex>.<16位hex>`；glm- 家族统一只认此变量）。解析顺序：`--api-key`（传 `-` 从 stdin 读，避免 key 进 shell history）→ `ZHIPU_API_KEY` 环境变量 → ~/.zshrc（与 glm-tts / glm-asr / glm-ocr 同链）。**GLM Coding Plan 订阅 Key 不含本接口**，需开放平台常规 API Key；火山 `ARK_API_KEY` 本服务不认。key 不打印、不落盘。

## 技术要点（2026-10 官方文档）

- 端点：`POST https://open.bigmodel.cn/api/paas/v4/images/generations`，同步返回（hd 约 20 秒），标准 Bearer 认证；另有异步端点 `/async/images/generations`（提交任务+轮询，仅 glm-image），脚本走同步已够用
- 模型 `glm-image`：**仅文生图**，无图像输入模态；prompt ≤1000 字符；一次请求固定出 1 张（`-n` 是脚本层逐张请求）
- 响应：`data[0].url` 为临时链接**有效期 30 天**——脚本即时下载落盘，把本地路径交给用户；`content_filter[]`（role + level 0-3，0 最严重）非空时 stderr 展示
- 水印：`watermark_enabled` 默认 true（显式角标 + 隐式数字水印，政策要求）；关闭需先签署免责声明
- 计费 **0.1 元/张**（与分辨率无关）；连接层错误与 5xx 自动重试共 3 次（间隔 3 秒），4xx 业务错误立即报出不重试
- 擅长场景（官方口径）：商业海报、科普插画、多格图画、社交媒体图文、高质量人像——尤其图内中英文文字

## 常见错误

| 现象 | 原因与处理 |
|---|---|
| HTTP 401 / 鉴权失败 | Key 无效或用错——本服务只认智谱开放平台 `ZHIPU_API_KEY`；GLM Coding Plan 订阅 Key 调不了本接口 |
| 参数类 400 | prompt 超 1000 字符；尺寸不是 32 整数倍 / 超边长或总像素范围（脚本已本地校验拦截，直调 API 才会遇到） |
| 响应无图片 URL + content_filter level=0 | prompt 触发内容安全拦截，调整描述 |
| 关水印报错 | 账号未签署去水印免责声明（个人中心-安全管理-去水印管理），或直接保留水印 |
| 想图生图/参考图 | glm-image 不支持，走 `ark-image-gen`（Seedream 系列支持 images 参考图） |
| 想固定种子复现 | API 无 seed 参数，重跑构图必变；要相似构图用更具体的 prompt |

## 与其他工作流的集成

- 文字海报/图文卡底图：本技能出带清晰文字的底图；要本地精确排版文字的贴图组（小红书/公众号信息卡）一律 `social-cards`（文字本地排版，不依赖 AI 渲染）。
- 文章配图：`social-article` 正文配图可用本技能出底图（点名智谱引擎或图上要文字时）。
- 视频：生成的图可作为 `ark-video-gen` 图生视频的首帧素材。
- 效果核对：图上的文字对不对，用 `glm-ocr` 或直接视觉看图抽查——模型渲染的字可能个别笔画错。

## 实测记录（2026-10-08）

- 三次在线实测全过（共 0.3 元）：默认 1:1 `1280x1280`；`--ratio 16:9` → 推荐档 `1728x960`；`--ratio 21:9` → 换算 `1952x832`。
- **海报文字渲染验证**：大字标题「春日读书周」+ 小字「4月20日-26日 全场图书8折」逐字核验全部正确，无错别字乱码——文字渲染强项属实。
- **边长 <1024 可用**：`1952x832`（短边 832）服务端正常出图，1024 只是官方建议值而非硬限；硬下限以模型页口径 512 为准。脚本对短边 <1024 保留提示。
- 响应约 0.2MB/张、生成耗时秒级到 20 秒级；`data[0].url` 下载直连顺畅。返回 PNG（Content-Type 判型）。
