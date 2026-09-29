#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AGENTS.md 生成器：为各业务 workspace 统一生成指令文件。

单一源头：全局纪律（GATE 降级、状态落盘、派发约定）与各家族链条都配置在本脚本，
改纪律后重新生成即可同步所有 workspace，避免五份手写文件各自漂移。

用法：
    py scripts/emit_agents_md.py           # 生成/更新各 workspace 的 AGENTS.md
    py scripts/emit_agents_md.py --check   # 只检查是否与生成结果一致（供 CI）
"""
import os
import sys
import argparse

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.dirname(REPO_ROOT)

# ── 全局纪律：注入每个会话，控制篇幅 ──────────────────────────────
DISCIPLINES = """## 全局纪律（所有技能工作流通用）

### GATE 无人值守降级
技能流程中的 GATE 默认用 AskUserQuestion 请用户批准。无法交互时（后台任务、自主运行、
用户不在场）：把待批产物落盘为 `<产物名>.pending-approval.md`（或在产物头部标注 `状态：待批准`），
**停在**该 GATE，交付说明中明确「等待用户批准什么、批准后从哪继续」；严禁自行放行 GATE。

### 状态落盘与断点续跑
多步流水线每完成一步，立即把进度写入项目状态文件（各家族路径见下）：已完成步骤与产物路径、
当前步骤、下一步、待用户决策项。用户说「继续」或会话重入时，**先读状态文件**再行动，
不重做已完成步骤；流程进行到哪一步以状态文件为准，不依赖对话记忆。

### 派发约定
- 单次 subagent 派发必须自包含：任务目标、输入文件路径、验收标准一次给全，不说「如前所述」。
- 并发派发 ≤ 3。
- 可用 subagent：executor（实现/写文件）、planner（规划）、researcher / tech-researcher（只读调研）、
  reviewer（只读审查）、vision（视觉判定）。派发目标改名或增删后，需同步更新
  `~/.zcode/agents/` 或 `.zcode/agents/` 下的定义，并跑 `py <repo>/scripts/scan_skills.py`。

### 技能维护
本目录技能安装自 `agent-skills` 源仓库；改技能请改源仓库后执行
`py <repo>/scripts/deploy.py --deploy` 同步，勿直接改安装侧（会被部署器判为冲突）。
"""

FAMILIES = {
    "papers": {
        "title": "论文工作区（paper-skills）",
        "chain": "链条：`/paper-proposal` 选题提案 → `/paper-litreview` 文献综述 → `/paper-experiment` 实验 → "
                 "`/paper-draft` 撰写 → `/paper-revise` 修改 → `/paper-rebuttal` 审稿答复 → `/paper-submit` 投稿。"
                 "用户要求「从头做研究/写论文」时按此顺序推进，每步产物是下一步的输入。",
        "artifact": "产物根：一篇论文一个 `paper<NNN>/` 目录，直接建在本工作区根下（NNN 为三位零填充流水号，"
                    "取现有 `paper*` 目录最大编号 +1，首篇 = `paper001`）。"
                    "状态文件：`paper<NNN>/progress.md`。数字与引用只能来自实验产物和已核验文献矩阵。",
        "skills": "本区已安装：proposal / litreview / experiment / draft / revise / rebuttal / submit（7 个）。",
    },
    "novels": {
        "title": "小说工作区（novel-skills）",
        "chain": "链条：`/novel-research` 题材调研 → `/novel-outline` 总大纲 → 设定三件套 "
                 "（`/novel-worldview` `/novel-characters` `/novel-style`）→ `/novel-volume` 卷纲 → "
                 "`/novel-opening` 黄金三章 → `/novel-chapter` 逐章正文（顺序循环，严禁并行写多章）→ "
                 "`/novel-cover` 封面。已有成书可随时 `/novel-deconstruct` 拆书逆向（六层拆解 + 跨书指令库）。"
                 "正文硬门槛：≥2000 纯汉字、每章爽点、章末钩子、AIGC 检测达标。",
        "artifact": "产物根：`books/<book>/`；状态文件：`books/<book>/progress.md`（伏笔台账 + 章节进度，"
                    "novel 系技能已内置维护，重入必读）。",
        "skills": "本区已安装：research / outline / worldview / characters / style / volume / opening / chapter / cover / deconstruct（10 个）。",
    },
    "patents": {
        "title": "专利工作区（patent-skills）",
        "chain": "链条：`/patent-disclosure` 技术交底 → `/patent-priorart` 现有技术检索 → "
                 "`/patent-claims` 权利要求 → `/patent-draft` 申请文件 → `/patent-oa` 审查意见答复。"
                 "一步一审查关卡，前一步产物是后一步输入。",
        "artifact": "产物根：一案一个 `patent<NNN>/` 目录，直接建在本工作区根下（NNN 为三位零填充流水号，"
                    "取现有 `patent*` 目录最大编号 +1，首案 = `patent001`）。"
                    "状态文件：`patent<NNN>/progress.md`。",
        "skills": "本区已安装：disclosure / priorart / claims / draft / oa（5 个）。",
    },
    "douyin": {
        "title": "抖音内容调研工作区（douyin-skills）",
        "chain": "分层触发：给视频链接 = `/douyin-video-analysis` 单视频深度剖析；"
                 "给账号名/主页 = `/douyin-account-analysis` 账号级分析（内部复用单视频流水线）。"
                 "转写依赖用户级 ark-asr 技能（已全局安装）。",
        "artifact": "产物：分析报告按主题落盘（如 `reports/<主题>/`），单视频剖析产物随视频目录组织。",
        "skills": "本区已安装：video-analysis / account-analysis（2 个）。",
    },
}

HEADER = "<!-- 本文件由 agent-skills/scripts/emit_agents_md.py 生成，勿手改；改纪律/链条请改脚本后重新生成。 -->\n"


def render_family(ws):
    cfg = FAMILIES[ws]
    return (f"# {cfg['title']}\n\n"
            f"本目录即 {ws} 业务的 ZCode 工作区：专属技能装在 `.zcode/skills/`，产物直接建在本目录下。\n\n"
            f"{cfg['chain']}\n\n{cfg['artifact']}\n\n{cfg['skills']}\n\n" + DISCIPLINES)


def render_root():
    idx = "\n".join(
        f"- **{ws}/** — {FAMILIES[ws]['title']}：{FAMILIES[ws]['skills']}"
        for ws in FAMILIES)
    return ("# ZCodeProject 工作区总览\n\n"
            "本目录按业务分 workspace（会话工作区请设在对应业务子目录），各自持有 `.zcode/skills/`（安装自 agent-skills 源仓库）：\n\n"
            f"{idx}\n\n"
            "- **agent-skills/** — 技能源仓库（勿直接使用其中的技能；部署、校验工具在 `agent-skills/scripts/`）。\n"
            "- **ai-model-report/** — 通用工作区（未配置专属技能）。\n\n"
            "在子目录开会话时以该子目录的 AGENTS.md 为准；其中「全局纪律」各处一致。\n\n" + DISCIPLINES)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只检查一致性，不写文件")
    args = ap.parse_args()

    outputs = {os.path.join(PROJECT, "AGENTS.md"): render_root()}
    for ws in FAMILIES:
        outputs[os.path.join(PROJECT, ws, "AGENTS.md")] = render_family(ws)

    drift = 0
    for path, content in outputs.items():
        if args.check:
            cur = open(path, encoding="utf-8").read() if os.path.exists(path) else None
            if cur != HEADER + content:
                print(f"[D] {path} 与生成结果不一致（重跑 emit_agents_md.py 更新）")
                drift += 1
            else:
                print(f"[=] {path}")
        else:
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(HEADER + content)
            print(f"[>] {path} 已生成")
    if args.check and drift:
        sys.exit(1)


if __name__ == "__main__":
    main()
