# 动画生成与 Agent Skills 生态调研报告

> 调研日期：2026-10-09
> 调研方法：GitHub REST API 逐一核实仓库 star 数 / 许可证 / 最近推送时间（star 数均为 **2026-10-09** 数据）；项目详情交叉核对仓库 README 与文件树（`gh api` + raw.githubusercontent.com）；生态信息来自官方文档（remotion.dev、anthropics/skills README）与聚合仓库（VoltAgent/awesome-agent-skills 等）。
> 面向读者：维护个人 agent-skills 仓库（SKILL.md 格式），已有 video-edit、video-tutorial-gen、ark-video-gen、minimax-video-gen、douyin-video-maker、jargon-anim 等视频/动画技能。

---

## 核心结论速览

1. **"LLM 写代码生成动画"已形成完整生态位**：讲解/动画类内容的主流技术路线不是端到端生成模型，而是 **LLM 生成 Remotion/Manim/SVG 代码 → 本地渲染 → ffmpeg 合成**。Manim（94.8k stars）与 Remotion（62.7k stars）是两大引擎，且都官方支持 AI（Remotion 文档提供 `.md` 后缀直出 Markdown、`Accept: text/markdown` 内容协商；GSAP 官方直接发布 16k stars 的 AI skills）。
2. **Agent Skills 格式的视频技能在 2026 年爆发**：出现了多个千星级仓库——OpenMontage（65.7k，agentic 视频制作系统，内嵌 700+ 技能）、video-shotcraft（11.0k，Remotion 镜头卡技能）、MoneyPrinterTurbo（129.3k，AI 短视频流水线）、火宝短剧（15.9k，一站式短剧平台）、gsap-skills（16.1k）、chengfeng-videocut-skills（3.0k，视频剪辑 agent）、zenstory drama-skills（2.7k，11 技能短剧工作流）、story-to-handdrawn-video（2.2k，中文故事→手绘动画）。
3. **官方 anthropics/skills（180.1k stars）没有专门的视频技能**，最接近的是 slack-gif-creator（PIL 逐帧 GIF）、algorithmic-art（p5.js 生成艺术）；但官方仓库自带 Agent Skills 规范（spec/）与模板（template/），是所有第三方技能的组织基准。
4. **短剧/漫剧是最热的中文垂类**：剧本→分镜→角色资产→图/视频提示词→成片的五段式流水线（drama-skills 称"五份 Markdown 就是创作事实"）已成为可复用的方法论，且普遍采用"先落盘预览、用户确认、再花钱调生成 API"的成本控制设计。
5. **SKILL.md 的成熟组织模式已收敛**为：`SKILL.md`（入口+工作流+触发词）+ `references/`（领域知识/风格库/镜头卡）+ `scripts/`（确定性工具与验证）+ `assets/`（音频/字体/模板）+ `examples/`（金标准样片）。验证闭环（渲染后自动探测、截图、量化评分）是头部技能的共同特征。

---

# 主题一：GitHub 动画生成相关开源项目

## 对比总表

| 项目 | Star* | 定位 | 与 LLM/Agent 结合 | 活跃度 | 许可证 |
|---|---|---|---|---|---|
| [3b1b/manim](https://github.com/3b1b/manim) | 94,801 | 数学动画引擎（原版） | 大量下游 LLM 项目以它为渲染后端 | 2026-09 推送 | MIT |
| [ManimCommunity/manim](https://github.com/ManimCommunity/manim) | 41,372 | 社区版 Manim（LLM 训练语料主流版本） | 同上 | 2026-10 推送 | MIT |
| [remotion-dev/remotion](https://github.com/remotion-dev/remotion) | 62,732 | React 程序化视频 | 官方 AI 友好文档 + 众多第三方 agent skill | 2026-10 推送 | 自定义（源码可得） |
| [motion-canvas/motion-canvas](https://github.com/motion-canvas/motion-canvas) | 19,263 | TypeScript 代码驱动动画 | 无头部专门 LLM 项目，靠通用编码 agent | 2026-07 推送 | MIT |
| [marcelo-earth/generative-manim](https://github.com/marcelo-earth/generative-manim) | 931 | GPT-4o/Claude 生成 Manim 视频（早期爆款 Web 应用） | 本身即 LLM 应用 | 2026-09 推送 | Apache-2.0 |
| [adithya-s-k/manim_skill](https://github.com/adithya-s-k/manim_skill) | 1,152 | Agent Skills 格式的 Manim 技能（3B1B 风格） | 本身即 skill | 2026-01 推送 | MIT |
| [calesthio/OpenMontage](https://github.com/calesthio/OpenMontage) | 65,738 | 开源 agentic 视频制作系统（12 管线 / 700+ 技能） | 本身即 agent 系统 | 2026-10 推送 | AGPL-3.0 |
| [HVision-NKU/StoryDiffusion](https://github.com/HVision-NKU/StoryDiffusion) | 6,473 | 一致性角色故事图像/漫画生成 | 提示词驱动 | 停更（2024-09） | Apache-2.0 |
| [Doubiiu/ToonCrafter](https://github.com/Doubiiu/ToonCrafter) | 6,032 | 卡通首尾帧插值动画 | 提示词驱动 | 2025-03 推送 | Apache-2.0 |
| [bilibili/Index-anisora](https://github.com/bilibili/Index-anisora) | 2,525 | B 站开源动画视频生成模型（V3.2） | 提供复合引导；官方在研 agent 项目 AniMe | 2026-07 推送 | Apache-2.0（V2/V3 权重） |
| [Wan-Video/Wan2.2](https://github.com/Wan-Video/Wan2.2) | 17,812 | 阿里万相视频大模型（含角色动画 Animate） | ComfyUI/diffusers 本地 + 官方 API | 2026-09 推送 | Apache-2.0 |
| [guoyww/AnimateDiff](https://github.com/guoyww/AnimateDiff) | 12,276 | 动态扩散模块（动画运动先验） | ComfyUI 生态调用 | 停更（2024-07） | Apache-2.0 |
| [zai-org/CogVideo](https://github.com/zai-org/CogVideo) | 13,066 | 智谱 CogVideoX 视频/图生视频 | 本地 diffusers + 智谱 API | 2025-11 推送 | Apache-2.0 |
| [Tencent-Hunyuan/HunyuanVideo](https://github.com/Tencent-Hunyuan/HunyuanVideo) | 12,606 | 腾讯混元视频大模型 | 本地推理为主 | 2026-10 推送 | 腾讯社区许可 |
| [Lightricks/LTX-Video](https://github.com/Lightricks/LTX-Video) | 11,058 | 实时级快速视频生成 | 本地 + fal.ai/Replicate API | 2026-01 推送 | Apache-2.0 |
| [greensock/gsap-skills](https://github.com/greensock/gsap-skills) | 16,080 | GSAP 官方 AI skills（Web 动画） | 本身即 agent skills | 2026-07 推送 | MIT |
| [jianzongwu/DiffSensei](https://github.com/jianzongwu/DiffSensei) | 925 | 多模态 LLM + 扩散的漫画页生成 | 论文原型 | 2025-02 推送 | 未标注 |

\* Star 数均为 2026-10-09 GitHub API 数据。

---

## 1.1 代码式动画引擎 + LLM 结合

### 引擎层（简述）

- **Manim 双版本**：原版 [3b1b/manim](https://github.com/3b1b/manim)（94,801 stars，MIT，2026-09 仍在推送）与 [ManimCommunity/manim](https://github.com/ManimCommunity/manim)（41,372 stars，MIT，2026-10-08 推送，最活跃）。LLM 语料与几乎所有第三方技能都用社区版（`manimce`）。
- **Remotion**（62,732 stars）：用 React 写视频，H.264/WebM 导出。官方 AI 支持机制（[remotion.dev/docs/ai](https://www.remotion.dev/docs/ai) 实测核实）：① 每页文档一键 Copy as Markdown；② 任意文档 URL 加 `.md` 后缀返回 Markdown 版；③ 支持 `Accept: text/markdown` 内容协商——把 Remotion 文档链接丢进 Claude Code 等 agent 会自动抓到 Markdown 版。**这是"官方文档为 agent 优化"的标杆做法。** 许可证为自定义源码可得许可（公司规模超过阈值需付费，个人/小团队免费）。
- **Motion Canvas**（19,263 stars，MIT，2026-07 推送）：TypeScript 代码驱动动画，常被与 Manim/Remotion 并列。**调研未发现以 Motion Canvas 为后端的头部 LLM 项目**（仅零星个人小仓库），实际使用中主要由通用编码 agent 直接写 Motion Canvas 代码——此点未找到权威统计，标注为"未找到专门项目"。

### LLM/Agent 驱动 Manim 的代表项目

| 项目 | Star* | 说明 | 可借鉴点 |
|---|---|---|---|
| [marcelo-earth/generative-manim](https://github.com/marcelo-earth/generative-manim) | 931 | 2023 年最早的 GPT-4→Manim Web 应用之一，支持 GPT-4o/Claude/开源模型，附在线 demo | "生成→渲染→报错回传→自动修复"的迭代循环 |
| [rohitg00/manim-video-generator](https://github.com/rohitg00/manim-video-generator) | 305 | 自然语言→数学动画的轻量应用 | 极简流水线（NL→代码→渲染→MP4） |
| [Mack290208/ai-video-generator](https://github.com/Mack290208/ai-video-generator) | 1 | 中文项目：LLM + Manim + GPT-SoVITS 课程视频自动生成 | 中文配音 + Manim 组合管线 |

### Manim/动画类 Agent Skill（重点，与读者仓库直接相关）

| 技能仓库 | Star* | 功能与设计 | 组织方式 |
|---|---|---|---|
| [adithya-s-k/manim_skill](https://github.com/adithya-s-k/manim_skill) | 1,152 | 最流行的 Manim skill：`manim-composer`（叙事模式、场景模板、视觉技巧 references）+ `manimce-best-practices`（**20+ 个 rules/*.md 条例文件**：axes、camera、latex、timing、updaters…）+ `manimgl-best-practices`，附模板 .py 与可运行 examples | SKILL.md + references/ + templates/ + rules/ + examples/ 五层，条例化拆分最细 |
| [shuyicc/MathLens](https://github.com/shuyicc/MathLens) | 364 | 中文：数学题截图→8 步全自动讲解视频（题目分析→SVG 可视化讲解页→分镜→edge-tts 配音→音频时长验证回写→Manim 脚手架→逐幕动画→渲染验证） | 亮点机制：`wait_for_narration(keyword)` 让动画在读白说到关键词时精准触发；`assert_geometry()` 自校验几何坐标；渲染失败自动修复 |
| [Yusuke710/manim-skill](https://github.com/Yusuke710/manim-skill) | 167 | 单文件 SKILL.md + tools/（tts-generate.py、lint-subtitles.py、video_viewer.py）；kokoro 本地 TTS 默认开启；字幕 lint 与逐条时间戳 | **会话目录隔离**：所有产物写入 `~/.manim-skill/<slug>/`，绝不污染用户工作区；契约式表达"持续工作直到 video.mp4 存在" |
| [AmitSubhash/3brown1blue](https://github.com/AmitSubhash/3brown1blue) | 37 | 第一性原理的 Manim skill，论文讲解模式 | 风格规避"AI slop"审美 |
| [liangdabiao/math-concept-film](https://github.com/liangdabiao/math-concept-film) | 30 | 中文：数学概念→带旁白动画短片，面向 Claude Code/Codex 的技能 | 概念→影片的中文叙事模板 |

### Remotion 侧的 LLM 实践

- **[Vincentwei1021/anything2explainer](https://github.com/Vincentwei1021/anything2explainer)**（2,367 stars，PolyForm Noncommercial）："主题进、讲解视频出"的 Claude Code/Codex skill。黑画布动态图形 + TTS 旁白 + 词级对齐字幕 + 章节进度条；**每镜头一个 Remotion 组件、由并行 build agent 同时编写**，QC agent 对照书面标准检查渲染帧；中英双语共用分镜、按配音重定时。文档给出长度→字数→镜头数→并行 agent 数→耗时的量化对照表。
- **[wshuyi/remotion-video-skill](https://github.com/wshuyi/remotion-video-skill)**（394 stars）：轻量 Remotion skill，场景化架构 + MiniMax/Edge TTS 二选一。
- **[buainoai/remotion-skills](https://github.com/buainoai/remotion-skills)**（123 stars）：中文的 Remotion 最佳实践技能库。
- **[haidrrrry/claude-remotion-skill](https://github.com/haidrrrry/claude-remotion-skill)**（317 stars，MIT）、**[Alexwtlf/agentic-product-demo](https://github.com/Alexwtlf/agentic-product-demo)**（380 stars，"UI 是代码不是录屏"的产品 demo 视频）等。
- **[calesthio/OpenMontage](https://github.com/calesthio/OpenMontage)**（65,738 stars，AGPL-3.0，2026-03 创建，GitHub Trending #1）：目前最大的 agentic 视频制作系统。`.agents/skills/` 内嵌 **700+ 技能**（avatar-video、create-video、ffmpeg、canvas-procedural-animation、character-rigging、comfyui、bfl-api、elevenlabs、dashscope、doubao-tts、d3-viz 等，每个均按 references/ 分层）；12 条生产管线；除图生视频外主打"免费库存素材语料检索→真实剪辑时间线→Remotion/Blender/FFmpeg 渲染"；README 公示样片成本（60 秒 Pixar 风短片 **$1.33**、50 秒变换影片约 **$4**）。

**小结**：Manim 路线胜在"数学/图表表达力 + 渲染免费"，Remotion 路线胜在"React 生态 + 布局/文字能力强"，两者都把 LLM 当"写代码的动画师"而非视频生成器。专门项目从 2023 年的 Web 应用（generative-manim）演化到 2026 年的 Agent Skills（manim_skill/MathLens/anything2explainer），交付形态明显向 SKILL.md 收敛。

---

## 1.2 故事→动画/漫画生成

| 项目 | Star* | 定位与现状 | 可借鉴点 |
|---|---|---|---|
| [HVision-NKU/StoryDiffusion](https://github.com/HVision-NKU/StoryDiffusion) | 6,473 | NeurIPS 2024：Consistent Self-Attention 训练无关地保持跨图角色一致，支持条漫/多格漫画序列 + 运动 predicted 生成转场视频。**已停更（2024-09）**，社区转向 ComfyUI/在线服务 | "一致性锁"思想——把角色特征作为可复用机制而非每次即兴 |
| [Doubiiu/ToonCrafter](https://github.com/Doubiiu/ToonCrafter) | 6,032 | SIGGRAPH Asia 2024：卡通草图首尾帧插值生成中间动画，ComfyUI 有集成（AIGODLIKE/ComfyUI-ToonCrafter，376 stars） | 分镜"首尾帧→中间帧"的两段式生成，比直接文生视频可控 |
| [bilibili/Index-anisora](https://github.com/bilibili/Index-anisora) | 2,525 | B 站开源动画视频生成模型，IJCAI'25。V3.2（2025-09）基于 Wan2.2，8 步推理；支持任意帧推理、角色 3D 视频生成、视频风格迁移、超低清超分；V3.1 有 12GB 显存版本；2025-10 发布 anymask（时空掩码图生视频）；官方在研 **AniMe** agent 研究（arXiv 2508.18781） | 动画垂类专用模型 + 掩码控制；与 Wan 生态兼容意味着 agent 可用同一套 ComfyUI/diffusers 调用 |
| [jianzongwu/DiffSensei](https://github.com/jianzongwu/DiffSensei) | 925 | CVPR 2025：多模态 LLM 做排版控制 + 扩散模型做定制漫画页生成（论文原型，仓库未标注许可证） | LLM 管"分格布局/对白框"，扩散管"画面"的分工架构 |
| [donahowe/AutoStudio](https://github.com/donahowe/AutoStudio) | 452 | 多轮交互中保持主体一致的多 agent 图像生成（原 wuw2019 仓库已迁移至此；**未核实** wuw2019 原仓库下架原因） | 多 agent 分工（主题/布局/绘画）保持一致性 |
| [muzishen/RCDMs](https://github.com/muzishen/RCDMs) | 62 | AAAI 2025：富上下文条件扩散提升故事可视化一致性 | 学术基线 |

**与短剧强相关的实践**（详见主题二）：火宝短剧（15.9k）、zenstory drama-skills（2.7k）、story-to-handdrawn-video（2.2k）、Anil-matcha/Open-AI-Micro-Drama-Generator（525）、yubowen123/AIYOU（135）、bestaidrama/awesome-ai-drama-generators（30，剧转分镜/小说转剧集工具清单）。

**小结**：学术线（StoryDiffusion/ToonCrafter/DiffSensei）2024-2025 年密集出现后大多停更；产业活跃度转移到了**工程化的短剧流水线**（角色资产库 + 分镜表 + 逐镜提示词 + 逐镜生成 + ffmpeg 剪辑成片），后者与 Agent Skills 形态天然契合。

---

## 1.3 通用图生视频/角色动画模型仓库

| 仓库 | Star* | 本地推理 | API 途径 | 要点 |
|---|---|---|---|---|
| [Wan-Video/Wan2.2](https://github.com/Wan-Video/Wan2.2) | 17,812 | diffusers + ComfyUI 官方集成；TI2V-5B 可跑 RTX 4090（720P@24fps） | wan.video 官方站、ModelScope/HF Space、阿里云百炼 | MoE 架构；**Wan2.2-Animate-14B**（角色动画/替换，动作表情整体复刻，已入 diffusers）与 **Wan2.2-S2V-14B**（音频驱动电影感视频，配 CosyVoice TTS）对短剧最有用 |
| [Wan-Video/Wan2.1](https://github.com/Wan-Video/Wan2.1) | 17,134 | 同上 | 同上 | VACE 视频编辑、FLF2V 首尾帧；生态插件最多 |
| [zai-org/CogVideo](https://github.com/zai-org/CogVideo) | 13,066 | diffusers 本地推理 | 智谱 open.bigplatform（bigmodel.cn）API | 原 THUDM/CogVideoX；Apache-2.0；2025-11 后更新放缓 |
| [Tencent-Hunyuan/HunyuanVideo](https://github.com/Tencent-Hunyuan/HunyuanVideo) | 12,606 | 本地推理（显存要求高） | 腾讯云 | 腾讯社区许可（非纯开源条款）；2026-10 仍在推送 |
| [Lightricks/LTX-Video](https://github.com/Lightricks/LTX-Video) | 11,058 | 本地（主打实时级速度） | fal.ai、Replicate | 仓库 Apache-2.0；其后续 LTX-2 已被 claude-code-video-toolkit 集成为"AI cameo"镜头来源 |
| [guoyww/AnimateDiff](https://github.com/guoyww/AnimateDiff) | 12,276 | ComfyUI 生态内使用 | 无官方 API | 官方仓已停更（2024-07），但作为运动先验模块仍广泛用于动画风格出图+动图 |
| [bilibili/Index-anisora](https://github.com/bilibili/Index-anisora) | 2,525 | Wan 兼容权重，V3.1 有 12GB 版 | ModelScope/HF | 动画垂类最强开源模型（见 1.2） |

**Agent 可用的四条调用路径**（由各 README 与技能仓库实践归纳）：
1. **本地权重**：diffusers / ComfyUI / GGUF 量化——免费但需 GPU；
2. **云 GPU 自部署**：Modal（$30/月免费额度）、RunPod——claude-code-video-toolkit 的默认路径，把开源 TTS/图像/音乐模型部署成 API；
3. **聚合 API**：fal.ai、Replicate、Atlas Cloud——OpenMontage、vox-director、super-video-maker-skill 等技能的标准做法（一行 curl 即可被 skill 包装）；
4. **厂商官方 API**：阿里百炼（Wan）、智谱（CogVideo）、MiniMax、火山引擎、HeyGen——读者仓库中 ark-video-gen / minimax-video-gen 属于此路径。

**小结**：模型层竞争集中在 Wan2.x（角色动画 + 音频驱动 + 显存友好）与 LTX（速度）；对 agent 技能作者而言，模型是"可替换的零件"，技能应按 drama-skills 的"不绑定供应商"原则把模型抽象成配置。

---

## 1.4 SVG/CSS/HTML 动画生成

此路线**没有生成模型参与，纯靠 LLM 写代码**，因此 skills 化程度反而最高：

| 项目 | Star* | 说明 | 可借鉴点 |
|---|---|---|---|
| [greensock/gsap-skills](https://github.com/greensock/gsap-skills) | 16,080 | **GSAP 官方 AI skills**（2026-03 创建）：core API、timelines、ScrollTrigger、MotionPath、Flip、React/Vue/Svelte 集成、性能优化；agentskills.io 标准格式，`npx skills add` 或 Claude Code `/plugin marketplace add` 安装 | 引擎厂商下场写官方 skill 的范本；README 内置"对 agent 的话"（未指明动画库时推荐 GSAP） |
| [iart-ai/motion-skills](https://github.com/iart-ai/motion-skills) | 753 | **54 个技能、17 个可安装包**（web-animation 9、motion-design 9、kinetic-typography、data-animation、map-animation、webgl、javascript-animation 逐帧 canvas、lower-thirds 透明字幕条、manim-skills…），是 iart.ai 商业产品的开源底座 | **deliver-and-verify 循环**：渲染一帧→截图→自查，配 `tools/verify/`（contact-sheet.sh、probe-mp4.sh、seek-shot.sh）；按受众拆包分发 |
| [csthink/dashmotion](https://github.com/csthink/dashmotion) | 176 | 自然语言或 Mermaid→自包含 HTML/SVG 动效技术图解（Claude skill） | "静态图+动效"的最小实现，与读者 jargon-anim 定位最接近 |
| [chingswy/Skill-Research-Figure](https://github.com/chingswy/Skill-Research-Figure) | 179 | 学术论文 TikZ 图与手绘风 SVG 图的 Claude Code skill | 论文可视化垂类 |
| [Cocoon-AI/architecture-diagram-generator](https://github.com/Cocoon-AI/architecture-diagram-generator) | 7,413 | 系统架构图→独立 HTML/SVG 文件（静态为主） | 自包含单文件输出的交付形态 |
| [robonuggets/marp-slides](https://github.com/robonuggets/marp-slides) | 323 | MARP 演示 skill，含 SVG 图表与暗色主题 | 演示文稿+SVG 组合 |

其他：OpenMontage 内含 `canvas-procedural-animation` 技能；小体量实践有 AnayGarodia/sketchling（26 stars，面向 LLM 的手绘插画语言）、aj47/prompt-to-animation（1 star，LLM 生成 SVG 动画）等。**未发现**高星的"LLM 生成 Lottie 动画"专门项目。

---

# 主题二：Agent Skills 生态中的视频/动画技能

## 对比总表

| 技能/仓库 | Star* | 类型 | 依赖 | 组织方式 | 许可证 |
|---|---|---|---|---|---|
| [anthropics/skills](https://github.com/anthropics/skills) | 180,131 | 官方示例（无专门视频技能） | Python/PIL 等 | skills/ + spec/ + template/ | Apache-2.0（文档类为源码可得） |
| [calesthio/OpenMontage](https://github.com/calesthio/OpenMontage) | 65,738 | agentic 视频制作系统（700+ 技能） | Remotion/Blender/ffmpeg/各家 API | .agents/skills/ 全量 skills 化 | AGPL-3.0 |
| [harry0703/MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) | 129,303 | AI 短视频一键生成（Web 应用，非 skill） | LLM API + edge-tts + MoviePy/ffmpeg | 传统应用架构 | MIT |
| [chatfire-AI/huobao-drama](https://github.com/chatfire-AI/huobao-drama) | 15,891 | 一站式 AI 短剧平台 | Nuxt3 + Hono + Mastra agents + SQLite | backend/workspace/skills/ 内嵌 SKILL.md（UI 可编辑） | CC BY-NC-SA 4.0 |
| [greensock/gsap-skills](https://github.com/greensock/gsap-skills) | 16,080 | Web 动画官方 skills | GSAP npm 包 | skills/ 多技能包 | MIT |
| [Vincentwei1021/video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft) | 11,009 | Remotion 电影感产品视频 skill | Remotion + 截图 + 音频资产 | SKILL.md + 157 镜头卡 + 资产库 | Apache-2.0 |
| [zenstory-ai/drama-skills](https://github.com/zenstory-ai/drama-skills) | 2,661 | 短剧/漫剧 11 技能全集 | Python 3.9+、ffmpeg、各家生图/视频 API | 11 个 skill，五份 Markdown 即工程事实 | MIT |
| [Agentchengfeng/chengfeng-videocut-skills](https://github.com/Agentchengfeng/chengfeng-videocut-skills) | 3,044 | 视频剪辑 Agent（驱动真实剪辑器） | Node、MCP server、配套 Runtime | Plugin + 7 技能 + references 合同 | Apache-2.0 |
| [gnipbao/story-to-handdrawn-video](https://github.com/gnipbao/story-to-handdrawn-video) | 2,177 | 中文故事→手绘翻书动画 | Remotion 渲染器 + agent 生图 + ffmpeg | skill-package/ 与渲染器仓库双形态 | MIT |
| [Alisa0808/vox-director](https://github.com/Alisa0808/vox-director) | 2,183 | Vox 风格拼贴讲解视频 | Atlas Cloud API + 本地 ffmpeg | agent skill | MIT |
| [Vincentwei1021/anything2explainer](https://github.com/Vincentwei1021/anything2explainer) | 2,367 | 主题→动态图形讲解视频 | Remotion + edge-tts/kokoro/火山 TTS | SKILL.md + 模板 + 风格/运动规范 + QC | PolyForm NC |
| [feitangyuan/onetake](https://github.com/feitangyuan/onetake) | 2,021 | 一镜到底连续动效 | 代码动画 + probe.py 验证 | skill + 量化 oracle 脚本 | PolyForm NC |
| [digitalsamba/claude-code-video-toolkit](https://github.com/digitalsamba/claude-code-video-toolkit) | 2,186 | Claude Code 视频制作工作区 | Modal/RunPod 云 GPU 开源模型 + ffmpeg | skills + 斜杠命令 + 模板 + 工具 | MIT |
| [0xsline/OpenChatCut](https://github.com/0xsline/OpenChatCut) | 2,221 | 本地对话式视频剪辑器 | 多轨时间线 + Agent Skills + MCP | 应用+skills 混合 | AGPL-3.0 |
| [Agents365-ai/video-podcast-maker](https://github.com/Agents365-ai/video-podcast-maker) | 1,668 | 主题→4K 旁白视频 | 本地 TTS（edge/azure）+ manifest 驱动 | skill + manifest 工作流 | MIT |
| [iart-ai/motion-skills](https://github.com/iart-ai/motion-skills) | 754 | 54 个动效技能/17 包 | Remotion/Manim/GSAP/Canvas | 每包独立仓库 | MIT |
| [shuyicc/MathLens](https://github.com/shuyicc/MathLens) | 364 | 数学题→讲解视频 | Manim + edge-tts | 8 步流水线 skill | 未标注 |
| [adithya-s-k/manim_skill](https://github.com/adithya-s-k/manim_skill) | 1,152 | Manim 动画技能 | ManimCE | SKILL.md+rules+templates+examples | MIT |
| [wshuyi/remotion-video-skill](https://github.com/wshuyi/remotion-video-skill) | 394 | Remotion 视频技能 | Remotion + MiniMax/Edge TTS | 单 skill | 未标注 |
| [haidrrrry/claude-remotion-skill](https://github.com/haidrrrry/claude-remotion-skill) | 317 | Remotion 创建/剪辑教学 | Remotion | 单 skill | MIT |

\* Star 数均为 2026-10-09 GitHub API 数据。

---

## 2.1 anthropics/skills 官方仓库

- 规模：**180,131 stars**（2026-10-09），README 明确"演示 Claude 技能系统可能性"，并指向 [agentskills.io](https://agentskills.io) 的 Agent Skills 标准。
- 目录：`skills/`（19 个技能）+ `spec/`（规范）+ `template/`（模板）；Claude Code 可 `/plugin marketplace add anthropics/skills` 一键安装。
- **没有专门的视频/动画技能**。与动画最接近的三个：
  - **slack-gif-creator**：PIL 逐帧绘制 + `GIFBuilder` 类库封装，SKILL.md 写死平台硬约束（emoji GIF 128×128、消息 GIF 480×480、10-30fps、48-128 色、emoji 3 秒内），description 用"Use when users request animated GIFs for Slack like..."句式精准触发；
  - **algorithmic-art**：p5.js 生成艺术，**两步创作法**（先产出"算法美学宣言".md，再据此写代码），强调避免临摹在世艺术家以规避版权；
  - **canvas-design / theme-factory / frontend-design / web-artifacts-builder**：视觉设计与前端产物相关。
- 借鉴点：官方技能演示了"**把平台约束写成可执行检查**"（GIF 尺寸/色数）与"**把创作过程拆成两个 prompt 阶段**"两个模式；`spec/` 与 `template/` 是写新技能时的对照基准。

## 2.2 社区视频/动画技能重点项目

### zenstory-ai/drama-skills —— 短剧工作流的方法论标杆（2,661 stars，MIT）

来自真实漫剧工作室产线（自称 2025 年以来上千个 AI 短剧项目，放弃近 8 万行代码的自建工具后"蒸馏"成技能）。**11 个技能**：`novel-analyze → write → assets → storyboard → image-prompts → video-prompts → produce → edit → review` 等。设计原则（README 原文归纳）：

- **五份 Markdown 就是创作事实**：每集只维护 `剧本.md`、`视觉设定.md`、`分镜.md`、`图片提示词.md`、`视频提示词.md`（成片阶段加 `剪辑单.md`），没有并行数据库；
- **连续性锁**：跨镜一致的角色造型写成"能原样贴进提示词的短语"，每镜关键帧注明依据了哪些条目，漏项由检查脚本报错；
- **先预览、确认，再生产**：所有生图/视频/配音任务先把数量、内容、参考、参数落到文件，用户明确确认后才调外部 API 花钱；**供应商凭据不进项目**；
- 单技能内部为标准五件套：`SKILL.md + agents/ + assets/ + references/ + scripts/`；
- `.agents/notes/` 记录全部设计决策（implemented/rejected 分类）——**工程决策日志进仓库**的做法很少见；
- 通过 ClawHub（`.clawhub/publish.json`）与 `npx skills add zenstory-ai/drama-skills` 双渠道分发；
- 成本公示：68 秒竖屏样片视频生成成本约 40 元。

单技能 SKILL.md（short-drama-write）质量极高：description 写明触发语与**明确的不负责边界**（"不负责资产、分镜、媒体提示词或终审"）；正文有 Quick Start（文件格式规约）、入口分流、编号工作流、写作要求，并内置**反过度设计条款**（"若自检让剧本长出输入没有要求的机关，撤掉机关而不是替它找理由"）。

### Vincentwei1021/video-shotcraft —— 镜头卡资产库模式（11,009 stars，Apache-2.0）

- 核心资产：**157 张镜头配方卡**（每张卡附 demo 实现源码与动态样片）+ 1 支已验收完整宣传片模板（Ink Press）+ 可复用组件 + **BGM/SFX 音频资产库**（assets/audio 下按 camera/data/film/impact/whoosh 等分类的 mp3）。
- SKILL.md 的**模式判断设计**：开始前先区分"直接用模板 / 自主自由创作 / 共同创作"三种互不合并的模式，未选模式时只做只读产品检查再推荐，已明确选择就不再询问——把"何时问用户"写成了规则（含两条例外条款）。
- 双端兼容：`agents/openai.yaml` 让同一技能同时服务 Claude Code 与 Codex。

### gnipbao/story-to-handdrawn-video —— 渲染器+技能双形态（2,177 stars，MIT）

中文故事或有序图片 → 3:4 竖屏手绘翻书动画（"文字→黑白画稿→彩色插画"逐层动画，或整页卷页翻书）。
- **327 项风格资产**：297 条画风配方（HS-001~HS-277）+ 30 种主题配色，JSON 风格库 + 每种风格的标准场景示例 PNG（全部用"老人小孩过石拱桥"统一对比场景）+ 离线 style-library.html；
- 仓库= Remotion 渲染器（npm 工程，负责实际处理与导出）+ `skill-package/`（可拷入 ~/.claude/skills 的技能壳），通过 `STORY_VIDEO_PROJECT` 环境变量在技能与渲染器间解耦；
- 支持参考图风格迁移（agent 解析参考图的线条/造型/配色/材质，用同一视觉语言生成新分镜）、内置手写中文字体与中文字检查。

### Agentchengfeng/chengfeng-videocut-skills —— 驱动真实剪辑器（3,044 stars，Apache-2.0）

Claude Code Skills 驱动的视频剪辑 agent：Plugin（7 个技能：剪口播、字幕、画面、导出、工作台操作等）+ **MCP server**（dist/server.mjs）+ 配套本地 Runtime（执行工程操作并提供工作台 UI）。亮点是**版本合同治理**：installer-manifest.json 固定 marketplaceRef/pluginRef 与提交 SHA，"缺能力时只报告并停止，不自动安装升级"；相关生态还有 OpenChatCut（2,221 stars，本地多轨时间线剪辑器 + Agent Skills + MCP）。

### 其他值得看的技能

- **Alisa0808/vox-director**（2,183 stars，MIT）：一句话主题→Vox 风格报纸拼贴讲解片，Atlas Cloud API + 本地 ffmpeg，全流程自动化。
- **feitangyuan/onetake**（2,021 stars，PolyForm NC）：主打"一镜到底"连贯动效（每个节拍从上一节拍"长出来"）；**连续性 oracle**：`probe.py` 逐帧记录画面内容、量化每个边界的 carry score（0.83 的成片通过，0.40 的"幻灯片式"版本被拒），同时拒绝均匀节奏、无静止、无运动模糊等反模式——**把"好不好看"变成可测量验收**。
- **digitalsamba/claude-code-video-toolkit**（2,186 stars，MIT）：完整工作区（`/setup`、`/video` 斜杠命令 + 模板 + 工具）；路线是**云 GPU 跑开源模型**（Qwen3-TTS 配音、FLUX.2 图像、ACE-Step 音乐部署到 Modal/RunPod），成本公示（配音 ~$0.01、AI 视频片段 ~$0.23、52 秒竖屏短片 ~$0.80）。
- **Agents365-ai/video-podcast-maker**（1,668 stars，MIT）：主题→4K 旁白视频，v5.3 起本地 TTS（edge 免费 + azure），manifest 驱动装配。
- **Bomx/super-video-maker-skill**（309 stars）：HeyGen 数字人 + Seedance b-roll（fal.ai）+ OpenAI 图像 + Remotion/HyperFrames + ffmpeg 的全管线技能，主打"Avatar Explainer"格式。
- **znyupup/ai-video-editing-skill**（150）：原始素材→成片的 vlog 自动剪辑 skill。**xianyu110/ecommerce-video-skills**（59）：12 个中文电商短视频技能（3 秒钩子、卖点分镜、图生视频提示词、edge-tts、字幕花字、ffmpeg 成片、抖音/TikTok Shop 导出）。

## 2.3 厂商官方 skills（与视频/动画相关）

来自 VoltAgent/awesome-agent-skills（35,423 stars，收录 1000+ 技能）等聚合仓库的收录信息：

- **remotion-dev**：官方技能（officialskills.sh 收录"Programmatic video creation with React"）；google-labs-code 亦有 remotion 技能（从 Stitch 设计稿生成走查视频）；
- **fal-ai-community**：fal-generate、fal-kling-o3（Kling 视频）、fal-lip-sync（对口型）、fal-video-edit、fal-upscale——生成模型 API 的标准 skill 包装；
- **openai/sora**：Sora API 生成/混剪/管理短视频的官方技能；
- **MiniMax-AI**：cli（文本/图像/视频/语音/音乐全模态）、gif-sticker-maker（照片→Funky Pop 风 GIF 贴纸）、frontend-dev；
- **greensock**：gsap-skills（见 1.4）；
- **video-db/skills**：实时与批量视频工作流（录屏采集、URL/YouTube/RTSP 摄取、转写、索引、搜索、字幕、时间线剪辑、HLS 流输出）；
- **SupercmoHQ/superCMO-skills**（Apache-2.0）：营销视频/图片生产（UGC 广告、AI 演员、竞品调研）；
- **taisly/agent**：把成片发布到 TikTok/Reels/Shorts 的 Codex 插件+skill+MCP；
- **flutter/flutter-animating-apps**、**microsoft/frontend-ui-dark-ts**：应用动画类官方技能。

（以上条目来自聚合仓库 README，除 remotion 文档与 gsap-skills 外未逐一验证技能源码，标注为"聚合仓库收录"。）

## 2.4 聚合与分发渠道

- **聚合清单**：ComposioHQ/awesome-claude-skills（76,747）、VoltAgent/awesome-agent-skills（35,423）、travisvn/awesome-claude-skills（15,333）、BehiSecc/awesome-claude-skills（10,227）、libukai/awesome-agent-skills（5,153，中文指南）、heilcheng/awesome-agent-skills（6,265）。
- **分发机制**：`npx skills add <owner>/<repo>`（vercel-labs/skills CLI，自动探测 40+ agent）、Claude Code `/plugin marketplace add`、ClawHub（skills.sh / officialskills.sh 收录页）、直接拷贝到 `~/.claude/skills/`、`~/.codex/skills/`、`~/.agents/skills/` 等约定目录。
- **官方规范**：agentskills.io + anthropics/skills 的 `spec/`；技能正迅速成为 Claude Code / Codex / Cursor / Gemini CLI 通用的"能力封装单位"。

## 2.5 SKILL.md 组织模式归纳（生态共性）

1. **分层标准件**：`SKILL.md`（<500 行：触发 description、Quick Start、入口分流、编号工作流、禁止事项）+ `references/`（按需加载的领域知识/风格库/镜头卡/合同文档）+ `scripts/`（确定性 Python/Node/ffmpeg 工具与验证器）+ `assets/`（BGM/SFX/字体/模板工程）+ `examples/`（金标准样片与过程存档）。典型：manim_skill 的 20+ rules 文件、video-shotcraft 的 shots/ 目录。
2. **成本与确认治理**：drama-skills 的"预览→确认→生产"三段式 + 供应商凭据不进项目；claude-code-video-toolkit / OpenMontage / drama-skills 都在 README 公示单条视频成本。
3. **验证闭环**：onetake 的连续性 oracle（量化 carry score）、motion-skills 的 deliver-and-verify（contact-sheet + probe-mp4）、MathLens 的渲染失败自动修复、Yusuke710 的字幕 lint——**技能不只教"怎么做"，还教"怎么自检"**。
4. **触发词与边界**：description 里写清"Use when…"与"不负责…"（drama-skills 每个技能都显式划界）。
5. **多端兼容**：`agents/openai.yaml`（Codex 端声明）、遵循 agentskills.io 规范、避免绑定单一宿主。
6. **产物隔离**：所有生成物写入会话/项目目录（Yusuke710 的 `~/.manim-skill/<slug>/`、story-to-handdrawn 的 `STORY_VIDEO_PROJECT`），绝不污染用户工作区。

---

# 信息缺口（未核实/未找到）

- **Motion Canvas 的专门 LLM 项目**：未找到头部项目，仅有零星个人仓库；"无专门项目"结论基于 GitHub 搜索，非权威统计。
- **wuw2019/AutoStudio 原仓库**：已 404，现存 donahowe/AutoStudio（452 stars）疑为迁移/复刻仓库，迁移原因未核实。
- **部分聚合仓库条目**（remotion 官方 skill、openai/sora、fal 系列、MiniMax 系列）来自 VoltAgent 聚合 README 收录，未逐一打开源仓库验证 SKILL.md 内容；ComposioHQ/awesome-claude-skills 的 README 未能通过 grep 检索到视频条目（文件结构原因），未深入。
- **用户提到的 "AI-Animator"、"eternal?"**：按名搜索未命中高相关高星仓库，可能为记忆偏差或非公开项目，未收录。
- **个别许可证细节**：huobao-drama 的 GitHub API 显示 NOASSERTION，README badge 为 CC BY-NC-SA 4.0（按 README 标注）；Remotion、HunyuanVideo 为自定义许可，商用条款请以仓库 LICENSE 原文为准。
- **star 数为动态值**：不同时间点查询存在 ±1 误差（如 video-shotcraft 11,008/11,009），本文统一取 2026-10-09 最后一次查询值。

---

# 对自建 Agent Skill 的启示

结合读者已有的 video-edit、video-tutorial-gen、ark-video-gen、minimax-video-gen、douyin-video-maker、jargon-anim 六个技能，提炼十条可直接落地的做法：

1. **给每个技能补齐"标准五件套"**：对照 drama-skills 的 `SKILL.md + agents/ + assets/ + references/ + scripts/`，把现有技能中的隐性经验显性化为 references 文档；SKILL.md 控制在入口+工作流+禁则，长知识全部下沉 references（adithya-s-k/manim_skill 拆 20+ rules 文件的做法可仿）。
2. **在 SKILL.md 里写死"确认点"**：ark/minimax 视频生成按次计费，应采用 drama-skills 的"提示词先落盘→展示本次任务的数量/参数/参考图→用户确认→才调 API"流程，并把"供应商凭据不进项目目录"写为规则。
3. **建一条通用的"交付-验证"脚本族**：参考 motion-skills 的 `verify/`（ffprobe 探测时长/分辨率/码率、关键帧 contact sheet、seek 抽帧核对）与 MathLens 的"渲染失败自动修复"，为 video-edit 和 jargon-anim 增加产物自检环节——技能的差异化竞争力在自检，不在生成。
4. **量化验收标准进技能**：借鉴 onetake 的连续性 oracle 思路，为 jargon-anim 定义可测指标（术语出现与配音对齐帧差、字幕 lint、构图安全区），让 agent 在交付前跑分。
5. **沉淀"镜头/手法卡"资产库**：video-shotcraft 的 157 张镜头卡（每张 = 效果描述 + 参考实现源码 + 样片）是 jargon-anim 最直接的模板——把常用术语动画手法（公式推导、流程展开、对比高亮、进度脉冲等）做成编号卡片库，description 里支持点名调用。
6. **风格库 JSON + 标准对比示例**：story-to-handdrawn-video 用"同一场景 327 种风格示例图"让用户按号选风格——jargon-anim 可建"同一术语的 N 种视觉风格"示例库（JSON 配方 + PNG 示例 + 离线浏览页）。
7. **TTS-动画同步机制**：MathLens 的 `wait_for_narration(keyword)`（配音说到关键词才触发动画）与"音频时长回写分镜表"两招，可直接搬进 video-tutorial-gen；字数/语速估算表（如 kokoro ≈2.5 words/s，中文 Yunxi ≈5.5 字/s）写成 references 速查表。
8. **引擎选型遵循"代码动画为主、生成模型为辅"**：讲解/术语类内容用 Remotion 或 Manim（可版本化、可 QC、渲染免费）；ark/minimax 等生成 API 留给"实拍感镜头"；最终用 ffmpeg 合成——这是 OpenMontage、火宝短剧、claude-code-video-toolkit、drama-skills 共同的混合管线。
9. **产物目录隔离 + 多端兼容**：仿 Yusuke710 的会话目录（`~/.<skill>-home>/<slug>/`）避免污染用户 cwd；加 `agents/openai.yaml` 与 agentskills.io 规范对齐，使技能可被 Codex/Cursor 等复用；分发上提供 `npx skills add <owner>/<repo>` 友好的仓库结构。
10. **把成本写进文档**：单条视频的生成成本（drama-skills ¥40/68s、toolkit $0.80/52s、OpenMontage $1.33/60s 的公示方式）应写进 SKILL.md 或 README，让 agent 能在方案选择阶段替用户算账。

---

## 附：本次调研直接核实的来源

- GitHub REST API（star/许可/推送时间，2026-10-09）；gh CLI 认证查询（文件树、内容目录）
- 仓库 README/SKILL.md 原文：zenstory-ai/drama-skills、Vincentwei1021/video-shotcraft、gnipbao/story-to-handdrawn-video、calesthio/OpenMontage、iart-ai/motion-skills、digitalsamba/claude-code-video-toolkit、Bomx/super-video-maker-skill、Agentchengfeng/chengfeng-videocut-skills、shuyicc/MathLens、chatfire-AI/huobao-drama、Vincentwei1021/anything2explainer、feitangyuan/onetake、Alisa0808/vox-director、marcelo-earth/generative-manim、Yusuke710/manim-skill、greensock/gsap-skills、wshuyi/remotion-video-skill、Wan-Video/Wan2.2、bilibili/Index-anisora、anthropics/skills（README + slack-gif-creator + algorithmic-art）
- 官方文档：[remotion.dev/docs/ai](https://www.remotion.dev/docs/ai)（AI 友好文档机制实测）
