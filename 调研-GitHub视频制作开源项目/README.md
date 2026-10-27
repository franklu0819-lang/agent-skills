# GitHub 视频制作开源项目全面调研

> 调研日期：2026-10-11。Star 数来自 GitHub API 实时数据，会持续变化，仅作量级参考。
> 延伸调研：[OpenMontage 深度分析报告（含零 key 渲染实测）](OpenMontage-深度分析报告.md) · 仓库已浅克隆至本目录 `OpenMontage/`
> 方法：GitHub Search API 按 topic/关键词分 5 轮扫描（video-generation、video-editing、text-to-video、MoneyPrinter 系、剪映生态、数字人/对口型、字幕/翻译、动画引擎、底层模型）+ Tavily 交叉验证 + 重点项目 README 精读。

## 总览：五个梯队

| 梯队 | 定位 | 代表项目 |
|---|---|---|
| 一键短视频生成 | 主题→成片流水线（素材库拼接范式） | MoneyPrinterTurbo 129k、Pixelle-Video 29k |
| Agentic 生产系统 | Agent 全程编排（2026 主流范式） | OpenMontage 66k、hypit 21k、ViMax 13k |
| 垂直内容平台 | 短剧/漫剧/解说/翻译等场景成品 | Toonflow 17k、huobao-drama 16k、NarratoAI 11k |
| 单点能力工具 | 剪映自动化/字幕/数字人/对口型 | pyJianYingDraft 4.5k、SmartSub 5.6k、SadTalker 14k |
| 底座 | 渲染引擎/生成模型/素材获取 | Remotion 63k、manim 95k、Wan2.2 18k、yt-dlp 197k |

**2026 年最重要的范式转移**：从 2024 年的"素材库拼接 + MoviePy 合成"（MoneyPrinterTurbo 范式）转向 **"Agent 编排 + 程序化渲染（Remotion）+ 可编辑中间产物（剪映草稿）"**。同时 **Agent Skill 形态**（Claude Code / Codex 技能）在 2026 年下半年爆发，出现了多个万星级视频技能。

---

## 一、一键短视频生成（MoneyPrinter 系）

| 项目 | Star | 状态 | 说明 |
|---|---|---|---|
| [harry0703/MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) | 129.5k | 活跃 | 品类霸主。主题→文案→素材检索→配音→字幕→成片；WebUI/API/CLI/Agent 四入口；Pexels/Pixabay 素材；MIT |
| [FujiwaraChoki/MoneyPrinterV2](https://github.com/FujiwaraChoki/MoneyPrinterV2) | 32.1k | 活跃 | 从短视频扩展到"在线赚钱自动化"全家桶 |
| [FujiwaraChoki/MoneyPrinter](https://github.com/FujiwaraChoki/MoneyPrinter) | 14k | 存续 | 品类鼻祖（2023），MoviePy 自动化 YouTube Shorts |
| [ATH-MaaS/Pixelle-Video](https://github.com/ATH-MaaS/Pixelle-Video) | 28.8k | 存续 | AI 全自动短视频引擎（2026-06 后放缓） |
| [ddean2009/MoneyPrinterPlus](https://github.com/ddean2009/MoneyPrinterPlus) | 7.2k | 停更 | 批量生成+混剪+**一键发布抖音/快手/小红书/视频号**（国内分发链路独有） |
| [RayVentura/ShortGPT](https://github.com/RayVentura/ShortGPT) | 8k | 停更 | 早期"AI 视频框架"概念，已被超越 |

## 二、Agentic 视频生产系统（2026 新物种，最值得关注）

| 项目 | Star | 说明 |
|---|---|---|
| [calesthio/OpenMontage](https://github.com/calesthio/OpenMontage) | 66.2k | **自称首个开源 agentic 视频生产系统**：12 条产线、100+ 工具、**700+ agent skills**；把 AI coding assistant 变成视频工作室；强调"真视频"（从免费素材库检索运动镜头剪辑成片，而非静态图轮播）；AGPLv3，曾登 GitHub Trending 日榜第一 |
| [hypit-ai/hypit](https://github.com/hypit-ai/hypit) | 20.8k | **克隆爆款视频全工作流**：换脸、换台词、换 B-roll，一条命令出片 |
| [latent-spaces/brag](https://github.com/latent-spaces/brag) | 15k | 把刚写完的项目一键变成发布宣传短片（开发者自宣传场景切口极准） |
| [waooAI/waoowaoo](https://github.com/waooAI/waoowaoo) | 14.5k | 工业级全流程 AI 影视生产平台，可控制片 |
| [krillinai/OpenCreator](https://github.com/krillinai/OpenCreator) | 12.7k | 原 KrillinAI，视频翻译起家转型创作者工作台（powered by Codex） |
| [HKUDS/ViMax](https://github.com/HKUDS/ViMax) | 12.6k | 港大出品：导演/编剧/制片/生成 Agent 一体 |
| [dramaclaw/dramaclaw](https://github.com/dramaclaw/dramaclaw) | 6.8k | 通用 AIGC 视频引擎：剧本→成片一条管线（短剧/广告/带货/乙女游戏） |
| [Anil-matcha/Open-Generative-AI](https://github.com/Anil-matcha/Open-Generative-AI) | 30k | 免费 AI 图像/视频生成 studio（600+ 模型聚合） |

## 三、短剧 / 漫剧 / 小说推文（中文特色赛道）

| 项目 | Star | 说明 |
|---|---|---|
| [HBAI-Ltd/Toonflow-app](https://github.com/HBAI-Ltd/Toonflow-app) | 17.1k | 短剧/漫剧制作平台：剧本→智能分镜→角色场景资产管理→图/视频生成；无限画布 + Agent 工作流 + **MCP 与插件扩展**、本地部署、自选模型 |
| [chatfire-AI/huobao-drama](https://github.com/chatfire-AI/huobao-drama) | 16k | 火宝短剧：一句话生成完整短剧，剧本到成片全自动 |
| [ArcReel/ArcReel](https://github.com/ArcReel/ArcReel) | 5.4k | 小说/剧本→角色/场景/道具资产→分镜→视频 + **剪映草稿**；主打跨镜头一致性、多供应商、费用追踪 |
| [TypeTale/TypeTale](https://github.com/TypeTale/TypeTale) | 861 | 字字动画：AI 短剧/电影/小说推文，免费桌面软件 |
| [zzy7517/novel2video](https://github.com/zzy7517/novel2video) | 412 | 小说/漫画推文，支持 SD & ComfyUI |
| [Anil-matcha/Open-AI-Micro-Drama-Generator](https://github.com/Anil-matcha/Open-AI-Micro-Drama-Generator) | 527 | 多 Agent 短剧生成 |

## 四、剪映 / CapCut 自动化（工具层）

| 项目 | Star | 说明 |
|---|---|---|
| [GuanYixuan/pyJianYingDraft](https://github.com/GuanYixuan/pyJianYingDraft) | 4.5k | Python 剪映草稿生成/导出事实标准，构建自动化混剪流水线；CapCut 版 pyCapCut 开发中 |
| [luoluoluo22/jianying-editor-skill](https://github.com/luoluoluo22/jianying-editor-skill) | 3.9k | **Agent 技能形态**：自动化剪映视频剪辑 |
| [mcncarl/jianying-headless](https://github.com/mcncarl/jianying-headless) | 3k | 无头剪映：原生草稿 + 隔离剪辑/导出 + 独立 Agent Skill |
| [jub0t/concat](https://github.com/jub0t/concat) | 4.7k | 开源 CapCut 替代品（跨平台，支持 MCP） |
| [Hommy-master/capcut-mate](https://github.com/Hommy-master/capcut-mate) | 1.9k | 剪映 API + 扣子插件：生成并下载草稿文件，带 skills |
| [renezander030/capcut-cli](https://github.com/renezander030/capcut-cli) | 860 | 非官方 CLI 直接编辑剪映/CapCut 工程（字幕/变速/音量） |
| [JimLiu/baocut](https://github.com/JimLiu/baocut) | 634 | AI video agent + 可编辑时间线：转写/字幕/翻译/配音/剪辑/动效 |
| [GuanYixuan/pyCapCut](https://github.com/GuanYixuan/pyCapCut) | — | pyJianYingDraft 的国际版分支，开发中 |

## 五、Agent Skill 形态视频工具（与 agent-skills 生态直接同赛道）

| 项目 | Star | 说明 |
|---|---|---|
| [Vincentwei1021/video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft) | 11.2k | **Claude Code/Codex 技能**：Remotion 渲染电影感产品视频；157 张镜头配方卡 + 214 风格 + 214 运动预览 + 生产级模板；2026-09 新增浏览器端 Motion Workbench（CapCut 式精修，帧级一致导出）；Trendshift 日/周榜 |
| [Vincentwei1021/video-talkcraft](https://github.com/Vincentwei1021/video-talkcraft) | 新 | shotcraft 姊妹篇（2026-08）：解说视频；**词级时间戳本地对齐（中位 20–40ms）**、78 张运动配方卡、7 层反幻灯片系统、三重 QA 门 |
| [luoluoluo22/jianying-editor-skill](https://github.com/luoluoluo22/jianying-editor-skill) | 3.9k | 见上，剪映自动化技能 |
| [mcncarl/jianying-headless](https://github.com/mcncarl/jianying-headless) | 3k | 见上，含独立 Agent Skill |
| [shang-zhu/violin](https://github.com/shang-zhu/violin) | 1.1k | 开源视频翻译技能 |
| [InsiderX-Pro/video-translator](https://github.com/InsiderX-Pro/video-translator) | 928 | 实时视频翻译/配音技能 |
| [zenstory-ai/video-recap-skills](https://github.com/zenstory-ai/video-recap-skills) | 561 | Claude Code/Codex 技能：视频→中文解说（场景检测 + ASR + VLM） |
| OpenMontage skills 体系 | — | 700+ 技能内嵌于其 agentic 系统，技能组织方式值得研究 |

## 六、视频翻译 / 配音 / 字幕

| 项目 | Star | 说明 |
|---|---|---|
| [jianchang512/pyvideotrans](https://github.com/jianchang512/pyvideotrans) | 19.3k | 视频翻译+内嵌配音+字幕老牌工具 |
| [Huanshere/VideoLingo](https://github.com/Huanshere/VideoLingo) | 18.7k | Netflix 级字幕切割/翻译/对齐/配音一键全自动 |
| [modelscope/FunClip](https://github.com/modelscope/FunClip) | 6.4k | 阿里：FunASR 转写 + LLM 辅助剪辑，本地 Gradio |
| [buxuku/SmartSub](https://github.com/buxuku/SmartSub) | 5.6k | 转字幕/翻译/AI 配音/声音克隆/烧录一站式桌面端，Whisper/FunASR 本地离线 |
| [liuzhao1225/YouDub-webui](https://github.com/liuzhao1225/YouDub-webui) | 5.6k | YouTube/B 站视频本地化配音（中文视角） |
| [jhj0517/Whisper-WebUI](https://github.com/jhj0517/Whisper-WebUI) | 2.9k | Whisper 字幕 WebUI |
| [R3gm/SoniTranslate](https://github.com/R3gm/SoniTranslate) | 1.4k | 视频同步翻译配音 |

## 七、解说 / 二创 / 长转短

| 项目 | Star | 说明 |
|---|---|---|
| [linyqh/NarratoAI](https://github.com/linyqh/NarratoAI) | 11.4k | AI 一键解说+剪辑（中文解说视频头部项目） |
| [WyattBlue/auto-editor](https://github.com/WyattBlue/auto-editor) | 5.5k | 自动剪静音/快剪，命令行效率工具 |
| [Anil-matcha/AI-Youtube-Shorts-Generator](https://github.com/Anil-matcha/AI-Youtube-Shorts-Generator) | 5.3k | Opus Clip/Vidyo.ai 开源替代：长视频→爆款 9:16 切片 |
| [xixihhhh/clipforge](https://github.com/xixihhhh/clipforge) | 967 | 带货短视频：商品图→卖点提炼→种草脚本→锁图不变形→配音字幕成片 |
| [YeJe-cpu/SeeCut](https://github.com/YeJe-cpu/SeeCut) | 264 | 数字人/口播视频网感精剪 |

## 八、数字人 / 对口型

| 项目 | Star | 说明 |
|---|---|---|
| [KlingAIResearch/LivePortrait](https://github.com/KlingAIResearch/LivePortrait) | 19.2k | 快手：肖像驱动动画（图→动） |
| [duixcom/Duix-Avatar](https://github.com/duixcom/Duix-Avatar) | 15.8k | **真开源**离线数字人：视频生成+数字人克隆工具包 |
| [OpenTalker/SadTalker](https://github.com/OpenTalker/SadTalker) | 14.1k | 单图说话经典（CVPR 2023） |
| [xszyou/Fay](https://github.com/xszyou/Fay) | 13.6k | 数字人 agent 框架（2.5D/3D/多端 + LLM 连通业务） |
| [Rudrabha/Wav2Lip](https://github.com/Rudrabha/Wav2Lip) | 13.2k | 对口型奠基工作，仍在被大量 fork |
| [OpenTalker/video-retalking](https://github.com/OpenTalker/video-retalking) | 7.3k | 说话头视频唇形替换编辑 |
| [TMElyralab/MuseTalk](https://github.com/TMElyralab/MuseTalk) | 6.7k | 腾讯音乐：实时高质量隐空间 inpainting 对口型 |
| [modstart-lib/aigcpanel](https://github.com/modstart-lib/aigcpanel) | 5.6k | 一站式数字人系统：视频合成+声音合成+克隆，本地模型管理 |
| [antgroup/echomimic_v2](https://github.com/antgroup/echomimic_v2) | 4.7k | 蚂蚁：半身动作驱动（CVPR 2025） |
| [lipku/LiveTalking](https://github.com/lipku/LiveTalking) | 9.8k | 实时交互流式数字人 |
| [Kedreamix/Linly-Talker](https://github.com/Kedreamix/Linly-Talker) | 3.5k | 数字人对话系统全家桶 |

## 九、底层视频生成模型（权重开源，本地部署可用）

| 项目 | Star | 说明 |
|---|---|---|
| [hpcaitech/Open-Sora](https://github.com/hpcaitech/Open-Sora) | 29.9k | 视频生成训练框架（Democratizing Video Production） |
| [Wan-Video/Wan2.2](https://github.com/Wan-Video/Wan2.2) | 17.8k | 阿里万相：当前开源视频生成第一梯队 |
| [Open-Sora-Plan](https://github.com/PKU-YuanGroup/Open-Sora-Plan) | 12.2k | 北大系 Sora 复现计划 |
| [zai-org/CogVideo](https://github.com/zai-org/CogVideo) | 13.1k | 智谱 CogVideoX（文/图生视频） |
| [Tencent-Hunyuan/HunyuanVideo](https://github.com/Tencent-Hunyuan/HunyuanVideo) | 12.6k | 腾讯混元视频生成系统框架（另有 HunyuanVideo-1.5 轻量版 4.6k） |
| [Lightricks/LTX-Video](https://github.com/Lightricks/LTX-Video) | 11.1k | 实时向 DiT 视频模型 |
| [AILab-CVC/VideoCrafter](https://github.com/AILab-CVC/VideoCrafter) | 5.1k | 早期开源视频扩散模型 |
| [showlab/Awesome-Video-Diffusion](https://github.com/showlab/Awesome-Video-Diffusion) | 5.8k | 视频扩散模型论文/项目清单（追新用） |

## 十、程序化视频 / 动画引擎（开发者底座）

| 项目 | Star | 说明 |
|---|---|---|
| [yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp) | 196.7k | 素材获取链路事实标准（含 B 站/抖音） |
| [FFmpeg/FFmpeg](https://github.com/FFmpeg/FFmpeg) | 65k | 一切的底座 |
| [remotion-dev/remotion](https://github.com/remotion-dev/remotion) | 63.1k | **React 程序化视频**，已成 AI 视频技能首选渲染底座（shotcraft/talkcraft/brag 均基于它） |
| [mifi/lossless-cut](https://github.com/mifi/lossless-cut) | 44.4k | 无损剪辑瑞士军刀 |
| [ManimCommunity/manim](https://github.com/ManimCommunity/manim) | 41.4k | 社区版数学动画（3b1b 原版 94.9k） |
| [motion-canvas/motion-canvas](https://github.com/motion-canvas/motion-canvas) | 19.3k | TS 代码动画，解说视频向 |
| [Zulko/moviepy](https://github.com/Zulko/moviepy) | 15k | Python 剪辑库，MoneyPrinter 系底座 |
| [webadderallorg/Recordly](https://github.com/webadderallorg/Recordly) | 33.1k | 录屏→成品 demo 视频免剪辑 |

## 十一、通用编辑器（参考）

- [storytold/filmcraft](https://github.com/storytold/filmcraft) 8.7k — Rust 纯净室重写 Premiere Pro
- [OpenShot/openshot-qt](https://github.com/OpenShot/openshot-qt) 6.6k — 老牌跨平台编辑器
- [nadermx/backgroundremover](https://github.com/nadermx/backgroundremover) 8.1k — CLI 视频/图片去背景
- [hacksider/Deep-Live-Cam](https://github.com/hacksider/Deep-Live-Cam) 97k — 实时换脸（合规风险高，仅列存）

---

## 关键趋势判断

1. **范式转移已完成**：2024「素材拼接 + MoviePy」→ 2026「Agent 编排 + Remotion 程序化渲染 + 结构化中间产物（草稿/时间线）」。新品不再做"又一个 MoneyPrinter"，而是做可编辑、可干预的 agentic 产线。
2. **Agent Skill 形态是 2026 下半年最大增量**：video-shotcraft（11.2k）证明"技能即产品"可以拿万星；该赛道单品爆发速度远超传统 WebUI 项目。技能分发渠道（Claude Code / Codex / MCP / 扣子插件）本身成为竞争维度（capcut-mate 同时做 API+扣子+skills）。
3. **Remotion 取代 MoviePy 成为新一代渲染底座**：帧级确定性、React 组件化、浏览器预览与导出一致——这解决了 AI 生成视频"不可复现/不可精修"的痛点。shotcraft 的 Motion Workbench（浏览器精修 + 帧一致导出）是当前最佳实践。
4. **剪映草稿是中国市场特色落地路径**："AI 生成剪映草稿 → 人工在剪映里微调"兼顾自动化与可控性，pyJianYingDraft → capcut-mate → jianying-headless 已形成完整工具梯队，且全部在做 Agent 集成。
5. **垂直场景单品机会**：带货（clipforge）、项目宣传（brag）、解说（NarratoAI/talkcraft）、短剧（huobao/Toonflow）、本地化（VideoLingo）——"窄场景深做"比"通用平台"更容易起量。
6. **共性短板**（也是机会）：跨镜头角色/风格一致性（ArcReel 主打但未彻底解决）、版权与平台合规（素材库+AI 生成内容归属）、成片质量控制（多数项目缺少 QA 门，talkcraft 的三重 QA 是例外）。

## 对本仓库（agent-skills）的启示

- **直接对标品**：video-shotcraft / video-talkcraft（Remotion + 配方卡模式）、jianying-editor-skill、violin、video-recap-skills。其中 shotcraft 的「镜头配方卡 + 运动预览 Gallery + 生产级模板」三件套，与我们的技能组织思路高度同构，值得逐项拆解。
- **可借鉴技术点**：talkcraft 的词级时间戳本地对齐（中位 20–40ms/字）对 douyin-video-maker 的字幕同步（当前 ASS 方案）是直接补充；baocut 的"可编辑时间线"中间产物设计也适配我们的剪映链路。
- **赛道空隙**：剪映技能玩家都停留在"草稿生成/导出"，"素材→成片→发布"全链路 + 实测验收的技能仍稀缺（与我们 douyin-video-maker 的定位互补而非冲突）。
- **OpenMontage 的 700+ skills** 是目前最大的视频技能集合，其技能间编排协议（AGENT_GUIDE.md）值得专门研究。
