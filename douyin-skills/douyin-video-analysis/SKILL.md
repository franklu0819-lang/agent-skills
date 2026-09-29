---
name: douyin-video-analysis
description: "下载抖音视频并深度剖析：短链解析 → 真浏览器提取视频流与元数据（纯 curl 拿不到）→ 下载转写（豆包 ASR）→ 结构化剖析（观点还原/可信度分层/盲区/建议）。Use whenever the user pastes a v.douyin.com 或 douyin.com 链接并想 下载这个抖音视频、视频转文字、提取字幕/文案、剖析/分析/总结这个视频、视频里的观点靠谱吗、帮我看这个视频讲了什么、深度拆解视频内容 —— 即使没说"抖音"两个字，只要给了抖音链接加分析意图就用本技能。Also triggered as /douyin-video-analysis."
---

# 抖音视频下载与深度剖析

把一条抖音视频变成「元数据 + 全文转写 + 结构化剖析」的完整交付物。整条流水线于 2026-09-28 实测跑通（9 分 15 秒视频，端到端约 5 分钟）。

前置条件：
- **chrome-devtools MCP 可用**（关键：抖音页面是纯前端渲染，纯 curl 拿不到视频数据，必须真浏览器）
- ark-asr 技能已安装（转写用）

## 流水线总览

```
短链解析 → 浏览器打开视频页 → 提取元数据+视频流直链 → curl 下载
        → ffmpeg 抽音轨 → ark-asr 转写 → 深度剖析报告
```

## Step 1 解析视频 ID

用本技能脚本（自动处理代理与 UA）：

```bash
bash <本技能目录>/scripts/fetch.sh resolve "<分享短链或已知的 /video/ 链接>"
```

原理：`v.douyin.com/XXXX/` 短链 302 到 `www.iesdouyin.com/share/video/<数字ID>/...`，从 Location 头提取数字 ID。输入本身已是 `douyin.com/video/<ID>` 形式则直接提取，跳过网络请求。

## Step 2 浏览器打开视频页，提取元数据

1. `new_page` 打开 `https://www.douyin.com/video/<ID>`（无需登录即可渲染和播放）
2. `wait_for` 等待 `["赞", "分享"]` 出现（播放器初始化完成的信号）
3. `take_snapshot`，从 a11y 树提取以下元数据（都在页面文本里）：
   - **标题/文案**（含话题标签）— 在 RootWebArea title 和正文区
   - **作者**：昵称、粉丝数、获赞数
   - **互动数据**：赞 / 评论 / **收藏** / 分享（收藏数 > 点赞数 = 干货教程型内容的强信号）
   - **发布时间**
   - **「章节要点」**：抖音自动生成的内容摘要 + 带时间戳的章节列表——快速把握全片的捷径，先读它再听全文
   - **热评**：高赞评论常有人指出视频的硬伤或补充背景，是剖析的重要素材

## Step 3 提取视频流直链

```js
// evaluate_script
() => { const v = document.querySelector('video'); return v ? v.currentSrc : ''; }
```

两种情况：

- **直链模式**：返回 `v*.douyinvod.com/...` 的完整 MP4 地址，可直接 curl；`duration` 应与页面时长一致，用作校验；
- **blob: 模式（MSE，2026-09 起概率升高）**：`currentSrc` 是 `blob:https://...`，真实地址在 `performance.getEntriesByType('resource')` 里过滤 `douyinvod.com`，通常得到两条分轨：`media-video-hvc1`（视频）+ `media-audio-und-mp4a`（音频）。**返回完整 URL，严禁在脚本里 slice 截断**（截断即签名不完整、下载失败）。分轨分别下载后合成：

```bash
ffmpeg -i video.m4s -i audio.m4s -c copy out.mp4
```

音轨可能只有几百 KB（低码率短音频属正常），脚本阈值已按此放宽。

**作者归属（账号分析场景必做）**：视频页内 `a[href*="/user/MS4"]` 的 href 含作者 sec_uid——若视频来自外部搜索结果（而非本人主页），必须与目标账号 sec_uid 比对，防止把带 `#账号名` 标签的粉丝仿写内容当成本人视频（详见 douyin-account-analysis 技能 Step 4）。

## Step 4 下载 + Step 5 抽音轨

```bash
bash <本技能目录>/scripts/fetch.sh download "<视频流直链>" /tmp/dy_video.mp4
bash <本技能目录>/scripts/fetch.sh audio /tmp/dy_video.mp4 /tmp/dy_audio.mp3
```

注意：
- **直链带签名有时效，提取后立刻下载**，不要隔轮次再下
- 下载后用 `file` 验证是 `ISO Media, MP4`、体积 > 1MB

## Step 6 转写

**依赖**：ark-asr 技能（本仓库 ark-skills/ark-asr；mp4 不受支持，必须先抽好音轨）。转写脚本按以下顺序定位，避免绑死安装路径：① 环境变量 $ARK_ASR_HOME/scripts/transcribe.sh；② 安装根目录下的 ark-asr/scripts/transcribe.sh（与 ark-skills 同级安装时）；③ ~/.agents/skills/ark-asr/scripts/transcribe.sh。

```bash
bash <ark-asr 技能目录>/scripts/transcribe.sh /tmp/dy_audio.mp3 \
  -o transcript.txt --json transcript.json --utterances
```

长视频（>30 分钟）按 ark-asr 的长音频流程处理。

**解读转写稿前先识别 ASR 英文误听**：专有名词常被听成中文谐音（实测：Claude Code →"龙虾/爱马仕"、ChatGPT →"OpenCL"、Figma →"菲格玛"）。对照视频标题/简介/字幕里的正确拼写修正后再引用，不要把误听当术语写进分析。

## 交付物

在当前工作区建 `调研-<主题>/` 目录：
- `原视频-<时长>.mp4`
- `语音转写全文.txt`
- 剖析报告写在最终回复里（用户直接可读）；用户明确要求落盘时才另存 md

## 深度剖析框架

先**还原**、再**评判**、后**建议**，评判分三层：

- **✅ 站得住** — 与行业数据/常识互证的观点，说明为什么成立
- **⚠️ 方向对但说过头** — 指出夸大部分并用数据校准（虚荣指标、幸存者偏差、窗口期红利、以偏概全）
- **❌ 盲区** — 视频完全没讲、但对听众决策关键的点（合规、真实成本、留存、变现数据、利益相关）

逐条过核查清单：
1. 关键指标是虚荣指标吗？（注册数 ≠ DAU ≠ 收入）
2. 有幸存者偏差吗？作者结尾的自谦之词通常是最好的切口
3. 商业闭环缺了哪环？（获客 → 留存 → 变现 → 合规）
4. 作者利益相关：是真经验还是内容钩子/卖课引流？互动数据结构能说明什么？
5. 关键数字能否与公开行业数据交叉验证？（用 WebSearch/tavily 抽查，不确定的标注"未经核实"）

最后给**中肯建议**：结合用户自身上下文（本会话此前在做什么、用户的身份与目标）给可执行建议，不要复述视频内容凑数。

## 边界与降级

- 用户只要文字版/字幕 → 做到 Step 6 为止，不写剖析
- **不要走 douyin.com/search 站内搜索**（含 type=video/user）：未登录会触发验证码中间页，反复访问升级风控、连带污染同一会话的视频页。找视频用外部搜索引擎（Exa 搜 `作者名 douyin.com/video`）或抖音精选频道 `jingxuan.douyin.com`（正文常带完整口播稿）
- 浏览器被登录墙或风控拦截 → 降级为轻量剖析：仅用元数据 + 章节要点 + 热评，并明确告知用户"未获得全文"
- chrome-devtools MCP 不可用 → 如实告知无法完整执行。**不要浪费时间试旧 API**：`/web/api/v2/aweme/iteminfo/` 已返回空，iesdouyin 分享页的 `_ROUTER_DATA` 只含配置不含视频数据（2026-09 实测）
- 用户给的是抖音 live/用户主页/图文链接 → 本技能不适用，告知后按普通网页处理
