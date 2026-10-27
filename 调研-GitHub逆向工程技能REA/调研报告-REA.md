# REA（Reverse Engineer Anything）深度调研

> 调研日期：2026-10-12 ｜ 仓库：https://github.com/morluto/rea ｜ 本地克隆：`调研-GitHub逆向工程技能REA/rea`（完整历史，.git 51MB）

## TL;DR

REA 是一个让 AI 编码代理（Claude Code / Codex / Cursor / Gemini CLI 等）代为执行逆向工程的开源工具（MIT，TypeScript），形态为 **MCP server + CLI + Agent Skill 三位一体**。口号 "See a feature you like. Understand how it works, down to the binary level."——看到别人 App 里的功能，让 Agent 逆到二进制层搞懂原理，再带证据链重建一个自己的版本。2026-10-09 前后爆火出圈。

## 一、爆火数据（2026-10-12 gh api 实测）

| 指标 | 数值 |
| --- | --- |
| Stars | **112,696** |
| Forks | 25,183 |
| Open issues | 177 |
| 创建时间 | 2026-04-14 |
| npm 版本 | rea-agents v6.4.0（305KB CHANGELOG，高速迭代） |
| 提交总数 | 2,450 |

增长曲线：4 月创建时名叫 `betterBinaryMCP`（只是一个 Hopper 反汇编器 MCP 增强）；7-12 移除 Python 实现重写为 Node.js；**10-09 爆火后单日涌入 366 commits、10-11 仍有 304 commits**。社区流传"5 小时 30K+ star、一天 Trending #1"（Facebook 帖 / Trendshift 徽章佐证）。舆论场：Matthew Berman "Software is done."、Replit CEO "Pretty much all software will soon be open source."；也有人泼冷水（见第五节）。

## 二、它是什么（三位一体）

```
npx rea-agents setup   ← 一步注册：MCP server + 匹配的工作流指令（skill），带备份
```

- **MCP server**（`io.github.morluto/rea`）：24 个工具注册模块（src/server/register*Tools.ts），100+ 工具。同类客户端也可只用 CLI。
- **CLI**：`rea` 命令，与 MCP 走同一套 workflow，JSON 输出可流式。
- **Agent Skill**（`.agents/skills/reverse-engineer-anything/`）：1 个 SKILL.md（237 行，v39）+ 6 篇 references，教代理"怎么查、怎么问、怎么收尾"。skills.sh 可单独安装。
- 另有 2 个仓库自维护 skill：`rea-tool-design`（改工具契约时读 docs/tool-design.md）、`rea-changelog-update`。

**REA 不是反汇编器**，而是代理与真实分析引擎之间的编排层。深度原生分析靠 provider：Hopper（主力，商业，demo 可用）/ Ghidra（自带安装，只读）/ IDA（复用 mrexodia/ida-pro-mcp）。静态 JS/.NET 分析零引擎依赖。全本地运行。

## 三、能力矩阵（17 类目标）

原生二进制（伪代码/汇编/字符串/符号/交叉引用）、ELF 离线布局（pwntools）、Go 二进制（内嵌编译器元数据，零依赖）、WASM（WABT）、EVM 字节码（选择器/参数推断）、Linux crash 记录、JS/Electron（模块/imports/sourcemap/IPC/原生插件关系）、网站（CDP 被动观测+截图）、HAR/mitmproxy 抓包、.NET 程序集（CIL）、Android APK（headless JADX）、Android 设备（adb）、JEB 项目、Apktool 资源、固件（Binwalk/Unblob）、包与资源清单（plist/Apple bundle）、进程行为捕获（PTY）。

平台：macOS 12+ / 主流 Linux；Node 22.19+/24.11+；Windows Ghidra 支持实验性。

## 四、Skill 设计分析（对我们 agent-skills 最有参考价值）

### 4.1 结构：薄入口 + 按需加载

```
.agents/skills/reverse-engineer-anything/
├── SKILL.md (237 行)          ← 路由与纪律，不堆细节
└── references/
    ├── native-and-artifacts.md      (194 行)
    ├── javascript-applications.md   (175 行)
    ├── connection-and-recovery.md   (127 行)
    ├── evidence-workflows.md        (54 行)
    ├── android-applications.md      (34 行)
    └── runtime-observation.md       (28 行)
```

SKILL.md 明确写 "Read only the relevant guide"——references 不是全读，是按目标类型路由读。全 skill 总量约 1,064 行，但单次调查只触达入口+1~2 篇。

### 4.2 五个值得抄的设计模式

1. **按目标路由（Route the target first）**：SKILL.md 主体是一张"目标 → 第一个工具"决策表（ASAR→`analyze_javascript_application`、APK→`inspect_android_package`、固件→`inspect_firmware_regions`…），代理不用猜入口。
2. **summary-first 分页下钻**：未知大小/大目标先 `detail: "summary"`，再用 `inspect_analysis_view` 按 Evidence ID 取局部视图；禁止为读已返回的数据而重跑生产者；MCP 传输超限（`resource_constraint: transport`）时降级取摘要而非重复分析。这套"大结果分页协议"是给 token 经济性设计的。
3. **Evidence 证据链语义**：每个结论必须区分 observation / inference / unknown，引用 evidence_id，保留 limitations 与 coverage；`record_unknown`/`update_unknown` 把"没查到"也登记为带修订号的一等公民。"静态分析不得声称观察到了执行"写成硬纪律。
4. **Connect only when needed（反诊断滥用）**：工具可用就直接干活，"不要每次调查前跑 readiness/诊断"；工具缺失时才读 connection-and-recovery，且要求"先诊断观察到的具体 blocker，别对所有问题重复 setup"——这是对 agent 常见坏习惯（上来就跑 doctor）的针对性防御。
5. **版本漂移防御**：skill 提示"从 main 安装的 skill 可能描述了旧 npm release 没有的能力，以服务器实际 advertise 的工具列表和 schema 为准"——skill 与 MCP server 分发节奏不同步的现实问题，写进了 skill 本身。

### 4.3 工程纪律（AGENTS.md 里的样板）

- 依赖向内分层：domain/contracts → provider adapters → application workflows → CLI/MCP adapters；引擎协议不得漏进领域层。
- 安装器红线：变更必须**可加、幂等、有备份**；绝不顺手装/升级无关软件（Node/Homebrew/Java/Ghidra 一律 bring-your-own）；`setup` 先展示计划再动手。
- 凭证脱敏但不靠名字猜："不得从命名或文本模式推断敏感性"。
- skill 本身是构建产物的一部分：`build:cached` 会打包 runtime+skill；`docs/public/product-catalog.json` 等为生成物，改源头再重新生成。

## 五、争议与冷思考

- **法律/伦理**：README 有免责声明（" lawful reverse-engineering research… 你自负合规责任"）；dev.to 评测强调"复刻思想与行为，别抄版权代码/素材"。技能本身中性，用法合规看用户。
- **token 成本**：深度调查消耗大量 agent token（dev.to 明确列为缺点）。
- **舆论泡沫**：一个热门 YouTube 评测的观点——"互联网跑在了自己前面"：核心原理只是"把现成逆向工具包一层统一 MCP 接口"，Apple TV 遥控器 45 分钟复刻、Photoshop 全家桶复刻等 demo 传播中存在放大。
- **作者是谁**：morluto（个人开发者），6 个月内从 Hopper 小工具长成 11 万星项目；社区贡献涌入极快（近一周日均 200+ commits）。
- 防钓鱼声明：项目特意注明"未发行任何加密货币/代币"——爆火项目的标准自保动作。

## 六、对我们仓库的可借鉴点

1. **"目标→入口工具"决策表**可直接移植到我们的多引擎技能（如视频/语音家族）：SKILL.md 首屏给路由表，细节下沉 references 按需读。
2. **大结果分页协议**（summary → Evidence ID 局部视图 → 超限降级）适合我们所有"产物大、agent 只需要局部"的场景（长视频时间线、长音频转写）。
3. **observation/inference/unknown 三态 + 证据 ID 纪律**，正是我们在 OpenMontage 调研里记的"质量门工具化"的同款思想，可进触发案例。
4. **skill 与运行时版本漂移提示**：我们部署到 ~/.agents/skills 的技能同样存在"技能文档超前/落后于脚本"问题，值得在 SKILL.md 加同款防御句式。
5. **安装器三原则**（幂等、备份、绝不顺手装无关软件）可作为我们 deploy.py 的对照检查单。

## 七、复现入口（本地）

```bash
cd 调研-GitHub逆向工程技能REA/rea
cat README.md                                    # 主文档
cat .agents/skills/reverse-engineer-anything/SKILL.md   # skill 本体（v39）
ls docs/ | head -60                              # 57 篇契约/指南文档
open https://rea.tools/showcase/                 # 官方案例（DX-Ball/Notion/TH04）
```

— 报告完 —
