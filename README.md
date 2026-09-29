# agent-skills

个人 Agent 技能仓库，托管面向 ZCode 等 Agent CLI 的技能（SKILL.md + 配套脚本），按技能家族分目录组织，安装到 `~/.agents/skills/`（用户级）或 `<工作区>/.zcode/skills/`（项目级）即可使用。

## 目录说明

| 目录 | 家族 | 内容 |
|------|------|------|
| [ark-skills/](ark-skills/) | 火山引擎方舟（Ark）/ 豆包系 | 语音、音频、图片、视频生成共 5 个技能 |
| [patent-skills/](patent-skills/) | 专利全流程 | 交底、检索、权利要求、申请文件、OA 答复共 5 个技能 |
| [novel-skills/](novel-skills/) | 网文创作全流程 | 调研、大纲、设定、卷纲、章节、拆书、封面共 10 个技能 |
| [paper-skills/](paper-skills/) | 学术论文全流程 | 提案、综述、实验、撰写、修改、rebuttal、投稿共 7 个技能 |
| [nex-skills/](nex-skills/) | 产品研发全生命周期 | 规格、设计、开发、架构、发布、运维、增长、路线图等共 12 个技能 |
| [douyin-skills/](douyin-skills/) | 抖音内容调研 | 单视频下载剖析、账号级深度分析共 2 个技能 |

后续其他技能家族会以各自目录加入。

## ark-skills：方舟系技能

| 技能 | 用途 | 默认模型/服务 |
|------|------|---------------|
| [ark-tts](ark-skills/ark-tts/) | 语音合成（TTS），支持复刻音色朗读任意中文文本，内置 289 个音色库 | 豆包大模型 TTS |
| [ark-asr](ark-skills/ark-asr/) | 语音识别（ASR），本地音频文件或 URL 转写为带标点的文字，支持说话人分离 | Seed-ASR 录音文件识别 |
| [ark-audio-gen](ark-skills/ark-audio-gen/) | 音频创作：一条提示词直出含多角色对白、情绪、BGM、音效的成片音轨（约 2 分钟内） | Seed-Audio 1.0 |
| [ark-image-gen](ark-skills/ark-image-gen/) | 文生图 / 图生图 / 组图 / 多图层拆分，支持指定比例与分辨率档位 | Seedream 全系（5.0 lite/flash/pro、4.5、4.0） |
| [ark-video-gen](ark-skills/ark-video-gen/) | 文生视频 / 图生视频 / 参考生视频，内置本地参数校验、draft 先行、成本预估等省钱纪律，支持尾帧接力保持画面连续 | doubao-seedance-2-5 |

## patent-skills：专利系技能

覆盖发明专利从立意到授权的全流程，技能间按交底 → 检索 → 权利要求 → 申请文件 → OA 答复的顺序衔接，每步都有审阅关卡。

| 技能 | 用途 |
|------|------|
| [patent-disclosure](patent-skills/patent-disclosure/) | 技术交底书：从粗想法/代码库/设计文档挖掘发明点，撰写交底书并审查充分公开 |
| [patent-priorart](patent-skills/patent-priorart/) | 现有技术检索：分类号+关键词多查询系统检索，输出特征对比表与新颖性/创造性评估 |
| [patent-claims](patent-skills/patent-claims/) | 权利要求撰写：布局独权/从权层次与退守位置，审查清楚性、引用基础与支持 |
| [patent-draft](patent-skills/patent-draft/) | 申请文件撰写：围绕已批权利要求组装说明书、摘要、附图说明（CN/US/PCT） |
| [patent-oa](patent-skills/patent-oa/) | 审查意见答复：逐条映射审查意见到答复策略（争辩/修改/删除/分案），起草意见陈述书 |

## novel-skills：小说系技能

网文创作全流程技能链，按调研 → 大纲 → 设定三件套 → 卷纲 → 黄金三章 → 逐章正文 → 封面的顺序衔接。正文类技能带硬门槛：≥2000 纯汉字、每章爽点、章末钩子、朱雀 AIGC 检测双线达标（疑似 AI 片段字数占比 <40%）。

| 技能 | 用途 |
|------|------|
| [novel-research](novel-skills/novel-research/) | 题材调研：市场热度、读者画像、3-5 部竞品拆解、差异化方向（横向选赛道） |
| [novel-deconstruct](novel-skills/novel-deconstruct/) | 拆书：单本爆款工程级逆向——黄金三章细拆、爽点频谱、桥段库、人物公式、文风画像，产出可复用模块库（纵向学写法，断点续跑） |
| [novel-outline](novel-skills/novel-outline/) | 三幕式总大纲：一句话故事、三幕九节点骨架、分卷框架、爽点节奏 |
| [novel-worldview](novel-skills/novel-worldview/) | 世界观设定：修炼/力量体系、地图动线、势力组织、资源经济 |
| [novel-characters](novel-skills/novel-characters/) | 人物设定：主角档案、感情线、反派梯队、关系网、出场登记 |
| [novel-style](novel-skills/novel-style/) | 风格指南：叙事视角、文风基调、对白规则、钩子风格与禁用清单 |
| [novel-volume](novel-skills/novel-volume/) | 卷纲：卷内三幕切分、章级事件/爽点/钩子排布表、伏笔埋收登记 |
| [novel-opening](novel-skills/novel-opening/) | 黄金三章精写：开局策略设计 + 三章蓝图，留存生死线专用流程 |
| [novel-chapter](novel-skills/novel-chapter/) | 章节编写：按卷纲逐章撰写，字数/爽点/钩子/AIGC 检测四重验证 |
| [novel-cover](novel-skills/novel-cover/) | 封面生成：Seedream 竖版 3:4 封面 + 排字，双门质检（客观 + 主观） |

## paper-skills：论文系技能

学术论文全流程技能链：选题提案 → 文献综述 → 实验 → 撰写 → 修改 → rebuttal → 投稿，每步均有审阅关卡，引用一律逐条核验真实性。

| 技能 | 用途 |
|------|------|
| [paper-proposal](paper-skills/paper-proposal/) | 选题提案：领域侦察与缺口分析 → 研究提案（问题、假设、方法、贡献、工作计划）→ 新颖性/可行性对抗评审 |
| [paper-litreview](paper-skills/paper-litreview/) | 文献综述：多查询系统检索+滚雪球 → 主题聚类叙事综述、引用矩阵、缺口分析，逐条核验引用真实可达 |
| [paper-experiment](paper-skills/paper-experiment/) | 实验：假设/变量/基线/数据集/指标/消融/统计计划设计 → 可复现配置驱动实验代码 → 结果分析 |
| [paper-draft](paper-skills/paper-draft/) | 撰写：章节大纲与论点-证据映射（用户批准）→ 逐节起草，只用实验产出与已核验文献作为证据池 |
| [paper-revise](paper-skills/paper-revise/) | 修改：模拟同行评审（新颖性、方法、清晰度、呈现）→ 用户选题修复 → 逐项验证解决 |
| [paper-rebuttal](paper-skills/paper-rebuttal/) | Rebuttal：逐条映射审稿意见到回应策略（补充实验/礼貌反驳需用户确认）→ 逐点回应信与承诺修改 |
| [paper-submit](paper-skills/paper-submit/) | 投稿：抓取期刊/会议作者指南 → 会议模板成稿、统一引用、图表整合、cover letter → 投稿前检查 |

## nex-skills：产品研发系技能

覆盖产品从想法到运营的全生命周期，均为多角色子智能体工作流（researcher / planner / executor / reviewer 等），关键决策点设用户审阅关卡。

| 技能 | 用途 |
|------|------|
| [nex-specs](nex-skills/nex-specs/) | 产品规格：把想法/功能请求变成评审过的 PRD 式规格（用户故事、验收标准、里程碑） |
| [nex-design](nex-skills/nex-design/) | 视觉设计：三个方向风格板并行探索 → 用户选向 → 高保真交互原型 |
| [nex-dev](nex-skills/nex-dev/) | 双向开发：规格+已确认设计 → 可测试验收标准 → 先红后绿的 TDD 实现 |
| [nex-arch](nex-skills/nex-arch/) | 技术架构：现状勘察 → 架构提案（组件、选型、数据流、数据模型）→ 用户定向 |
| [nex-reverse](nex-skills/nex-reverse/) | 逆向工程：重建 as-built 架构与数据库设计 → 逐模块行为规格 → 一致性对抗审查 |
| [nex-release](nex-skills/nex-release/) | 发布：版本号、changelog、绿色构建+测试+E2E → 发布门审查（不部署） |
| [nex-ops](nex-skills/nex-ops/) | 运维/事故：根因诊断（证据链）→ 用户选定修复 → 最小修复 → 事故报告 |
| [nex-growth](nex-skills/nex-growth/) | 增长运营：指标基线 → 活动/内容计划 → 文案物料生产 → 事实性对抗审查 |
| [nex-business-plan](nex-skills/nex-business-plan/) | 商业计划：并行市场调研+数据基线 → 计划综合 → 事实核查 → 终稿 |
| [nex-roadmap](nex-skills/nex-roadmap/) | 路线图建议：只读项目文档与调研报告，提出优先级排序的 top 5 待建功能 |
| [nex-docs-tidy](nex-skills/nex-docs-tidy/) | 文档审计：docs/ 树体检（结构合规、陈旧、孤儿/重复）→ 用户定处置 → 执行 |
| [nex-slide](nex-skills/nex-slide/) | 幻灯片：素材汇集 → 大纲规划 → 固定品牌风格成片 → 质检 |

## douyin-skills：抖音系技能

抖音内容调研流水线，2026-09 实战沉淀：短链解析 → chrome-devtools 真浏览器提取（纯 curl 拿不到，抖音页面纯前端渲染）→ 分轨下载合成 → ark-asr 转写 → 结构化剖析。两技能分层触发：给视频链接 = 单视频剖析；给账号名/主页 = 账号级分析（内部复用单视频流水线）。

| 技能 | 用途 |
|------|------|
| [douyin-video-analysis](douyin-skills/douyin-video-analysis/) | 单视频深度剖析：短链/链接 → 元数据（赞/藏/评/章节要点/热评）→ 视频流提取（含 blob MSE 分轨）→ 下载 → ark-asr 转写 → 三层评判（站得住/说过头/盲区）+ 核查清单 |
| [douyin-account-analysis](douyin-skills/douyin-account-analysis/) | 账号级分析：外部搜索定位 sec_uid（勿走站内搜索）→ 选 ≥3 个代表性视频 → **作者归属验证**（sec_uid 比对防粉丝仿写混淆）→ 背景与争议调研 → 内容支柱/变现结构/观点体系归纳 + 结合用户情境的建议 |

## 安装与部署

不再手动 `cp`——`scripts/deploy.py` 按部署清单（`scripts/deploy.json`）同步各家族到安装目录，并用内容 hash 防止静默覆盖安装侧热修：

```bash
py scripts/deploy.py --status    # 看漂移：源/安装侧/基线三方对比
py scripts/deploy.py --init      # 首次对现有安装记录基线（不覆盖任何文件）
py scripts/deploy.py --deploy    # 同步：已同步跳过 / 源更新安全覆盖 / 安装侧热修报冲突
py scripts/deploy.py --deploy --force  # 冲突时备份热修为 <技能>.bak.<hash8> 后覆盖
```

当前部署布局：ark 系 → 用户级 `~/.agents/skills/`（全局）；novel / paper / patent / douyin 系 → 项目级，装到各自写作/业务工作区（如 novels、papers）的 `.zcode/skills/`，产物目录直接建在工作区根下（paper/patent 用 `paper<NNN>` / `patent<NNN>` 三位零填充编号）；nex 系 → 用户级 `~/.zcode/skills/`（全局，任意工作区可触发 /nex-*）。

改技能一律改本源仓库再 `--deploy` 同步，不要直接改安装侧。各工作区的 AGENTS.md 由 `scripts/emit_agents_md.py` 统一生成（全局纪律 + 家族链条），改纪律改脚本重新生成。

## 质量校验

三个校验/维护工具，提交前都建议跑：

```bash
py scripts/scan_skills.py            # 技能结构契约（error 计入退出码）
py scripts/scan_agents.py            # agent 定义契约（tools 白名单、MCP 工具风险提醒）
py scripts/emit_agents_md.py --check # AGENTS.md 与生成源是否一致
```

`scan_skills.py` 规则：frontmatter 封闭键集（未知键告警）、`name` 与目录名一致、description 长度（过短/过长双审计，>500 字符列为减负候选）、正文引用的脚本/文档真实存在、跨技能依赖显式声明、**subagent 派发引用可解析**（dispatch/派遣 的目标必须存在于 `~/.zcode/agents`、项目 `.zcode/agents` 或内置名单——历史上 oracle / data-analyst / looker 三个不存在的派发目标就是这样抓出来的）。接入 pre-commit：`repos: [{repo: local, hooks: [{id: scan-skills, name: scan skills, entry: py scripts/scan_skills.py --strict, language: system, pass_filenames: false}]}]`。

`scan_agents.py` 规则：frontmatter/name 一致性、tools 白名单（未知工具报错；`mcp__*` 依赖会话 MCP 可用性，仅提醒——agent .md 列了不可用工具会阻断派发，此脚本用于提前拦截）。

`scripts/trigger_cases.md` 是触发回归用例集（典型话术 → 期望技能，含歧义与跨家族抑制用例）：**改任何 description 前后各核对一遍**，防触发漂移。

`llms.txt` 是给 Agent 看的仓库说明书（六家族 40 技能一行式索引、依赖关系、边界），安装或检索本仓库的 Agent 优先读它。

## 密钥配置

技能与脚本**不读取、不存储、不落盘任何 API key**，认证统一从环境变量解析：

| 环境变量 | 用途 | 获取方式 |
|----------|------|----------|
| `ARK_API_KEY` | 方舟数据面 API（图片/视频生成） | [火山方舟控制台](https://console.volcengine.com/ark)，`ark-` 开头 |
| `SPEECH_API_KEY` | 豆包语音服务（TTS/ASR/音频创作），**方舟 ark- Key 本服务不认** | 豆包语音控制台 API Key 管理页，UUID 格式 |

写入 shell 配置即可（Windows Git Bash 为 `~/.bashrc`，zsh 为 `~/.zshrc`），脚本会自动解析：

```bash
export ARK_API_KEY=ark-xxxxxxxx
export SPEECH_API_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

## 目录结构

```
agent-skills/
├── ark-skills/
│   ├── ark-asr/          # 语音识别
│   │   ├── SKILL.md
│   │   └── scripts/transcribe.sh
│   ├── ark-audio-gen/    # 音频创作
│   │   ├── SKILL.md
│   │   └── scripts/audio_gen.sh
│   ├── ark-image-gen/    # 图片生成
│   │   ├── SKILL.md
│   │   └── scripts/image_gen.sh
│   ├── ark-tts/          # 语音合成
│   │   ├── SKILL.md
│   │   ├── references/voices.md
│   │   └── scripts/tts.py
│   └── ark-video-gen/    # 视频生成
│       ├── SKILL.md
│       └── scripts/ark_video.sh
├── patent-skills/
│   ├── patent-disclosure/  # 技术交底书
│   ├── patent-priorart/    # 现有技术检索
│   ├── patent-claims/      # 权利要求撰写
│   ├── patent-draft/       # 申请文件撰写
│   └── patent-oa/          # 审查意见答复
├── paper-skills/
│   ├── paper-proposal/     # 选题提案
│   ├── paper-litreview/    # 文献综述
│   ├── paper-experiment/   # 实验
│   ├── paper-draft/        # 撰写
│   ├── paper-revise/       # 模拟评审与修改
│   ├── paper-rebuttal/     # 审稿意见回应
│   └── paper-submit/       # 投稿准备
├── nex-skills/
│   ├── nex-specs/          # 产品规格
│   ├── nex-design/         # 视觉设计
│   ├── nex-dev/            # 双向开发
│   ├── nex-arch/           # 技术架构
│   ├── nex-reverse/        # 逆向工程
│   ├── nex-release/        # 发布
│   ├── nex-ops/            # 运维/事故
│   ├── nex-growth/         # 增长运营
│   ├── nex-business-plan/  # 商业计划
│   ├── nex-roadmap/        # 路线图建议
│   ├── nex-docs-tidy/      # 文档审计
│   └── nex-slide/          # 幻灯片
├── novel-skills/
    ├── novel-research/     # 题材调研
    ├── novel-deconstruct/  # 拆书（模块库逆向）
    ├── novel-outline/      # 三幕式总大纲
    ├── novel-worldview/    # 世界观设定
    ├── novel-characters/   # 人物设定
    ├── novel-style/        # 风格指南
    ├── novel-volume/       # 卷纲
    ├── novel-opening/      # 黄金三章
    ├── novel-chapter/      # 章节编写
    │   └── scripts/count_han.sh
    └── novel-cover/        # 封面生成
        └── scripts/（gen_cover.sh / overlay_text.py / check_edges.py）
└── douyin-skills/
    ├── douyin-video-analysis/     # 单视频下载与深度剖析
    │   ├── SKILL.md
    │   └── scripts/fetch.sh       # 短链解析 / 带校验下载 / 抽音轨
    └── douyin-account-analysis/   # 账号级深度分析
        └── SKILL.md
```
