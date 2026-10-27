# OpenMontage 深度分析报告（含实测验证）

> 调研日期：2026-10-11 · 仓库：calesthio/OpenMontage @ main（浅克隆，170MB）
> 本地路径：`调研-GitHub视频制作开源项目/OpenMontage/`
> 验证环境：macOS arm64 (darwin 25.6.0) · Node v22.23.2 · FFmpeg · 无任何付费 API key

## 一、项目定位

66.2k 星（GitHub Trending 日榜第一出身），AGPLv3。官方定位：**"首个开源 agentic 视频生产系统"——把 AI 编程助手（Claude Code/Cursor/Codex/Windsurf）变成视频制作工作室**。

它不是一个"视频生成 WebUI"，而是：**一套写给 agent 看的生产指令体系 + 一组可被调用的工具 + 一个 Remotion 渲染器**。你把仓库打开在 Claude Code 里说"做一个 60 秒神经网络科普动画"，agent 按 AGENT_GUIDE.md 的合同读产线定义、逐阶段调用工具、过检查点、渲染成片。

## 二、核心架构

### 2.1 设计哲学：智能在指令里，Python 只做工具和持久化

AGENT_GUIDE.md 原文：**"Python = tools + persistence. No orchestration logic, creative decisions, review logic, or checkpoint policy in Python code."**

```
Agent 读产线清单(YAML) → 读阶段导演技能(MD) → 调工具(Python BaseTool)
→ 自审(meta skill) → checkpoint(Python 工具) → 呈报人类批准
```

与我们 agent-skills 的"技能即智能"完全同源，但它把这套哲学推到了极致：**Python 代码里没有一行编排逻辑**。

### 2.2 三层知识架构

| 层 | 位置 | 内容 | 实测数量 |
|---|---|---|---|
| Layer 1 | `tools/tool_registry.py` + `base_tool.py` | 工具注册表：每个工具声明 capability/tier/status/cost/**agent_skills[]**，运行时自发现，`support_envelope()` 供 agent 查询"我能干什么" | 126 个工具类 |
| Layer 2 | `skills/{core,creative,meta,pipelines}/` | OpenMontage 特定约定：产线导演技能、质量清单、增强链顺序 | 157 个 .md |
| Layer 3 | `.agents/skills/` | 通用 API 知识（来自 skills.sh）：供应商参数、提示技巧、代码模式 | 91 个技能 |

README 宣传的 "700+ agent skills" 是把三层引用关系展开后的口径；物理技能文档约 248 个，但**引用链设计**（工具 → 技能 → 供应商知识）是真功夫。

### 2.3 产线系统（Rule Zero：一切生产必须走产线）

`pipeline_defs/*.yaml` 是可执行契约，每条产线定义：stages（阶段）→ 每阶段一个 director 技能 → `review_focus`（人审看什么）→ `success_criteria`（机器可验的成功标准）→ checkpoint 策略 → 预算。

13 条产线：animated-explainer、animation、avatar-spokesperson、character-animation、cinematic、clip-factory、documentary-montage、hybrid、localization-dub、podcast-repurpose、screen-demo、talking-head、framework-smoke。

以 documentary-montage（检索优先的真实素材混剪）为例，6 个阶段各配一个导演技能：idea-director（一句话主题问题+基调+音乐计划）→ scene-director（槽位描述+每槽 2-3 条搜索词）→ asset-director（素材语料库）→ edit-director（节奏/并置/音乐同步/基调连续性四维决策）→ compose-director（渲染）→ executive-producer（整体编排）。素材源：Pexels、**Archive.org (Prelinger)、NASA、Wikimedia Commons**、Unsplash，配 **CLIP 语义检索**（lib/clip_embedder）。

### 2.4 导演技能的写作质量（关键差异点）

`edit-director.md` 教的是**真正的剪辑心智模型**而非 API 用法：
- "纪录片混剪活在四个维度：节奏、并置、音乐同步、基调连续性"
- **"敌人是幻灯片感——等长停留+无声音设计的片段连播。感觉像幻灯片，无论素材多好，剪辑就是失败的"**（配套 `lib/slideshow_risk.py` 把这个标准工具化）
- 护栏："静默重大变更"：旁白增删、换音乐、时长拉伸 90s→2m30s 都必须停下来问用户，"修剪辑，不要糊墙"

meta 层还有 taste-direction（审美定向）、bespoke-composition（定制构图）、atelier 模式（英雄作品禁用模板组件防同质化，收尾必过"独特性审查：这会不会是任何其他产品的视频？"）。

### 2.5 工具与供应商治理

- **Selector/Provider 模式**：`tts_selector`/`video_selector`/`image_selector` 按"需求+可用 key+成本"自动路由到最佳供应商，agent 默认走 selector
- `.env.example` 列了 **20+ 家供应商**：fal.ai/MiniMax/Replicate/Higgsfield/Kling 官方/Google(Imagen+Veo+TTS)/ElevenLabs/OpenAI/xAI/豆包语音/fish.audio/通义 DashScope/腾讯混元 TokenHub/Suno/火山 Ark Seedance/HeyGen/LTX/Runway/即梦 Jimeng/ComfyUI 本地/Ideogram/Cartesia/Inworld——基本把市面 API 一网打尽
- **全免费本地链路存在**：Piper 本地 TTS、faster-whisper 本地 ASR、公共档案素材（Archive.org/NASA/Wikimedia 无需 key）、`llm.provider: ollama` 本地 LLM、Remotion 本地渲染
- **预算治理**：config.yaml 内置 budget（observe/warn/cap 三模式、单动作超 0.5 美元需批准、新付费工具首次调用需批准）+ `tools/cost_tracker.py`

### 2.6 渲染器

`remotion-composer/`（Remotion/React）：
- 多主题系统（clean-professional / flat-motion-graphics 等，注释明言"防止每个视频都长得像暗色金融科技风"）
- 组件库：Explainer、CinematicRenderer、TalkingHead、CollageBurst、CaptionOverlay（词级字幕）、图表组件等
- 另有 HyperFrames（HTML+GSAP）备用运行时
- `render_demo.py`：**零 key 演示渲染**——3 个预编排 JSON props 直接渲染成片，用于环境自检（这个设计本身值得学）

## 三、实测验证

### 3.1 渲染链路（✅ 全部通过，零 API key）

| 演示 | 时长 | 分辨率/帧率 | 大小 | 内容 |
|---|---|---|---|---|
| world-in-numbers | 23.1s | 1080p/30fps h264 | 4.2MB | 全球数据故事：标题卡→"8.1B" 数字滚动→超大城市柱状图→结尾标语 |
| code-to-screen | 25.0s | 1080p | 3.6MB | 开发者工作流讲解（对比+KPI 卡） |
| focusflow-pitch | 22.5s | 1080p | 4.1MB | 创业路演（品牌页+仪表盘动画） |

安装：npm 199 包 34 秒；每支渲染约 1-2 分钟（含首次 headless Chrome 下载）。

**抽帧验证结论**（4+2+2 帧逐帧视觉分析）：
- 动画真实存在：开场副标题处于**淡入中间态**（第 30 帧）、数字滚动定格、仪表盘转动——不是静态图轮播
- 排版层级清晰：品红+深蓝紫主题贯穿、数字/正文/注释三级字阶、图表带网格线与数据标签
- 叙事结构完整：起（标题卡）-承（数据页）-转（图表）-合（"Big systems. Human-scale decisions." 结尾卡）

质量评价：作为**纯组件动画**（无生成式内容），达到可发布的 motion graphics 水准，明显优于 MoneyPrinterTurbo 系的"素材片段拼接"审美下限。但注意：这三支是**人工预编排的 props**（curated demos），验证的是渲染器与组件库质量，**不是 agent 现场生成能力**。

### 3.2 完整产线（未实测，原因如下）

跑真实产线（如 documentary-montage）需要：① agent 运行时（Claude Code 打开该仓库按 AGENT_GUIDE 驱动）② LLM key（config 支持 anthropic/openai/gemini/openrouter/ollama/minimax）③ 素材源（Pexels/Unsplash 免费 key，或公共档案免 key）④ 可选音乐/TTS。本次未配置上述 key，属"可跑但需要用户决定用哪家供应商"的状态——其 onboarding 技能（skills/meta/onboarding.md）设计的就是先做能力发现再让用户选。

## 四、对我们 agent-skills 生态的启示

1. **可借鉴的思想**（不涉及代码，AGPLv3 无传染）：
   - **产线 YAML 契约**：把"阶段→导演技能→review_focus→success_criteria"做成机器可验的合同——我们的技能目前偏"单技能作战"，多阶段长链路（如 douyin-video-maker 的文案→配音→字幕→合成）可以借这种阶段化合同写法
   - **零 key demo 自检**：每个技能内置一条"无 key 可跑的验证命令"，部署验收从"人读文档"变成"机器渲染出片"——与我们"全链路实测部署"的习惯完美互补
   - **三层分离**：项目特定约定（怎么用）与通用 API 知识（怎么调）分层，避免每个技能重复抄供应商文档
   - **Selector 模式 + 预算门**：多供应商技能（我们 glm/minimax/ark 三家 TTS 并存）可做"需求→可用 key→成本"的自动路由，并在技能层内置费用上限与首次付费确认
   - **质量门工具化**：slideshow_risk、verify_scene_pacing 这类"把导演经验变成可执行校验"的思路，可直接用于抖音竖屏视频的"节奏/静帧/同质化"检查
2. **它的空隙（我们的差异化空间）**：
   - 素材与审美完全英语生态；中文场景（抖音竖屏、剪映草稿、中文 TTS 断句/字幕规范）未覆盖
   - 无发布链路（MoneyPrinterPlus 的一键发抖音反而更强）
   - 重桌面/长视频审美，短视频网感（钩子/爆点节奏）非其所长
3. **合规提醒**：AGPLv3——**借鉴架构思想与文档写法安全；直接复制其代码进我们的仓库会触发传染**，需整段避让。

## 五、结论

OpenMontage 是"指令驱动生产系统"路线目前最完整的实现：把编排智能全部外置为 Markdown 指令层，Python 退化为工具与持久化，渲染确定性交给 Remotion。零 key 演示渲染实测三支全部成功且质量合格，证明其渲染链路工程成熟度很高；完整 agentic 产线的上限取决于驱动 agent 的能力和所配供应商。对我们而言，它验证了"技能生态做视频"这条路线的天花板远高于单点工具，其**产线合同、零 key 自检、质量门工具化**三个设计最值得吸收。
