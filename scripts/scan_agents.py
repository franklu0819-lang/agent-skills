#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""agent 定义（.zcode/agents/*.md）契约校验器。

背景：agent .md 的 tools 里列出当前会话不可用的工具（尤其 MCP 工具）会直接
阻断该 subagent 的派发，且报错不指向原因。本脚本在静态侧提前拦住两类问题：
未知工具名、依赖会话 MCP 可用性的工具名。

用法：
    py scripts/scan_agents.py              # 自动扫 ~/.zcode/agents 和 <repo父>/.zcode/agents
    py scripts/scan_agents.py --dir PATH   # 追加一个 agents 目录

规则（E=error，W=warning，I=info）：
  A1  E  frontmatter 存在，且含 name、description
  A2  E  frontmatter name 与文件名一致（不含 .md）
  A3  E  tools 中出现未知工具（不在 KNOWN_TOOLS 内、也不是 mcp__ 前缀）
  A4  W  tools 中的 mcp__* 工具：静态侧无法确认会话可用性，改配置后首次派发
          失败时优先排查此处（历史上 MCP 工具失效导致派发被阻断）
  A5  W  description 过短（< 30 字符），不利于主 agent 路由
  A6  I  报告 model/thoughtLevel 等可选键，便于盘点各 agent 的模型分布
"""
import os
import re
import sys
import glob
import argparse

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ZCode 已知工具（内置；平台新增工具时在此追加）
KNOWN_TOOLS = {
    "Read", "Write", "Edit", "Bash", "Glob", "Grep",
    "WebFetch", "WebSearch", "TodoWrite",
    "Agent", "Skill", "TaskOutput", "TaskStop",
    "AskUserQuestion", "EnterPlanMode", "ExitPlanMode",
    "SendMessage", "ReadSessionContext", "ListModels",
    "CreateWorkflow", "AmendWorkflow", "ListWorkflowRuns", "GetWorkflowRun",
    "ResumeWorkflowRun", "ListSavedWorkflows", "SaveWorkflow",
    "EvalWorkflowSnippet", "ResolveWorkflowQuestion",
    "CronCreate", "CronUpdate", "CronDelete", "CronList",
    "OffPeakCreate", "OffPeakList",
}


def parse_tools(fm):
    """解析 tools 字段：行内 [A, B] 或多行 '- A' 两种写法。"""
    m = re.search(r"^tools:\s*\[(.*)\]\s*$", fm, re.M)
    if m:
        return [t.strip().strip("'\"") for t in m.group(1).split(",") if t.strip()]
    tools = []
    block = re.search(r"^tools:\s*\n((?:\s+- .+\n?)+)", fm, re.M)
    if block:
        tools = [ln.strip().lstrip("- ").strip("'\"") for ln in block.group(1).splitlines()]
    return tools


def scan(dirs):
    files = []
    for d in dirs:
        files += glob.glob(os.path.join(d, "*.md"))
    if not files:
        print(f"未发现任何 agent 定义（目录: {', '.join(dirs)}）")
        return 1

    problems, infos = [], []
    for path in sorted(files):
        fname = os.path.splitext(os.path.basename(path))[0]
        try:
            rel = os.path.relpath(path, os.path.dirname(REPO_ROOT))
            if rel.startswith(".."):
                rel = path  # 不在仓库父目录下（如用户级 C: 盘），显示绝对路径
        except ValueError:
            rel = path  # 跨盘符，relpath 不可用
        text = open(path, encoding="utf-8").read()

        m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        if not m:
            problems.append(("E", rel, "A1 缺少 frontmatter"))
            continue
        fm = m.group(1)

        nm = re.search(r"^name:\s*(.+)$", fm, re.M)
        if not nm:
            problems.append(("E", rel, "A1 缺少 name"))
        elif nm.group(1).strip().strip('"') != fname:
            problems.append(("E", rel, f"A2 name='{nm.group(1).strip()}' 与文件名 '{fname}' 不一致"))

        dm = re.search(r"^description:\s*(.+)$", fm, re.M)
        if not dm:
            problems.append(("E", rel, "A1 缺少 description"))
        elif len(dm.group(1).strip()) < 30:
            problems.append(("W", rel, f"A5 description 过短（{len(dm.group(1).strip())} 字符）"))

        for t in parse_tools(fm):
            if t.startswith("mcp__"):
                problems.append(("W", rel, f"A4 MCP 工具 '{t}' 依赖会话 MCP 可用性；该 agent 派发失败时优先排查此处"))
            elif t not in KNOWN_TOOLS:
                problems.append(("E", rel, f"A3 未知工具 '{t}'（内置新工具请更新 scan_agents.py 的 KNOWN_TOOLS）"))

        for key in ("model", "thoughtLevel"):
            km = re.search(rf"^{key}:\s*(.+)$", fm, re.M)
            if km:
                infos.append(f"{fname}: {key}={km.group(1).strip()}")

    for sev, rel, msg in sorted(problems, key=lambda x: (x[0], x[1])):
        print(f"[{sev}] {rel}: {msg}")
    for i in infos:
        print(f"[I] {i}")
    errs = sum(1 for s, _, _ in problems if s == "E")
    warns = sum(1 for s, _, _ in problems if s == "W")
    print(f"\n扫描 {len(files)} 个 agent 定义: {errs} error / {warns} warning")
    return 1 if errs else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", action="append", default=[], help="追加 agents 目录（可多次）")
    args = ap.parse_args()
    dirs = args.dir + [
        os.path.join(os.path.expanduser("~"), ".zcode", "agents"),
        os.path.join(os.path.dirname(REPO_ROOT), ".zcode", "agents"),
    ]
    sys.exit(scan(dirs))
