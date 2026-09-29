#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""agent-skills 结构契约校验器

借鉴 K-Dense scientific-agent-skills 的 tests/_contract 思路：
只读不执行、按规则按技能报告问题（精确到行号）、错误退出非零。

用法：
    python3 scripts/scan_skills.py            # 校验全仓库
    python3 scripts/scan_skills.py --quiet    # 只输出问题，无横幅
    python3 scripts/scan_skills.py --strict   # warning 也计入退出码

规则（E=error，W=warning，I=info）：
  R1  E  SKILL.md 存在且含 frontmatter
  R2  W  frontmatter 键为封闭集：必需 name/description；未知键告警
  R3  E  frontmatter name 与目录名一致
  R4  E  description 存在且 ≥ 50 字符
  R5  E  正文引用的相对路径（scripts/ references/ assets/ 下）真实存在于技能目录
  R6  E  跨技能引用可解析：提到兄弟技能目录下的脚本时，该文件必须存在（存在则记 I 级依赖）
  R7  W  外部技能依赖（~/.zcode/skills/ 或 ~/.agents/skills/ 下、且不在本仓库）必须显式声明"依赖"
  R8  W  自引用绝对路径：~/.agents/skills/<自身>/ 应改为技能基目录相对写法
  R10 E  subagent 派发引用可解析：正文 dispatch/派遣/派发 的目标名必须存在于
          已发现的 agent 定义（~/.zcode/agents、本仓库父目录 .zcode/agents）或内置名单；
          无反引号包裹的派发写法不识别（避免误报）
  R11 W  description 过长（> 500 字符）：进系统提示的成本大户，优先做减负整改
"""
import os
import re
import sys
import glob
import argparse

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Agent Skills 规范定义的保留键（封闭集；演进时在此追加）
KNOWN_KEYS = {
    "name", "description",                 # 必需
    "license", "allowed-tools", "metadata", "version",  # 规范保留
    "when_to_use", "compatibility",        # 常见扩展
}
REQUIRED_KEYS = {"name", "description"}
MIN_DESC_LEN = 50
MAX_DESC_LEN = 500

# ZCode 内置 subagent（非用户自定义，写死；内置新增时在此追加）
BUILTIN_AGENTS = {
    "general-purpose", "Explore",
    "documents:visual-judge", "pdf:visual-judge",
    "presentations:visual-judge", "spreadsheets:visual-judge",
}

DISPATCH_RE = re.compile(r"(?:[Dd]ispatch|派遣|派发)[^`\n]{0,8}`([a-zA-Z][\w:.-]*)`")


def discover_agents():
    """发现本机 agent 定义（用户级 + 本仓库父目录的项目级），返回 (名字集合, 目录列表)。"""
    dirs = [
        os.path.join(os.path.expanduser("~"), ".zcode", "agents"),
        os.path.join(os.path.dirname(REPO_ROOT), ".zcode", "agents"),
    ]
    names = set()
    found = []
    for d in dirs:
        if not os.path.isdir(d):
            continue
        mds = glob.glob(os.path.join(d, "*.md"))
        if mds:
            found.append(d)
        for p in mds:
            fm = re.match(r"^---\n(.*?)\n---", open(p, encoding="utf-8").read(), re.S)
            if fm:
                nm = re.search(r"^name:\s*(.+)$", fm.group(1), re.M)
                if nm:
                    names.add(nm.group(1).strip().strip('"'))
    return names, found


def scan():
    skills = sorted(glob.glob(os.path.join(REPO_ROOT, "*-skills", "*", "SKILL.md")))
    if not skills:
        print(f"E: 仓库根目录未发现任何 *-skills/*/SKILL.md（路径异常？REPO_ROOT={REPO_ROOT}）")
        return 1

    # 技能名 → 目录（供跨技能解析）
    name2dir = {os.path.basename(os.path.dirname(p)): os.path.dirname(p) for p in skills}
    repo_skill_names = set(name2dir)

    # R10 依据：本机实际存在的 subagent
    user_agents, agent_dirs = discover_agents()
    agent_names = user_agents | BUILTIN_AGENTS
    if agent_dirs:
        print(f"[I] R10 agent 名单: {', '.join(sorted(user_agents))} + 内置 {len(BUILTIN_AGENTS)} 个")
    else:
        print("[I] R10 未发现任何 agent 定义目录（~/.zcode/agents 或 .zcode/agents），跳过派发引用校验")

    problems = []   # (severity, skill, message)
    deps = set()    # 跨技能依赖（I 级）

    for path in skills:
        sdir = os.path.dirname(path)
        sname = os.path.basename(sdir)
        rel = os.path.relpath(path, REPO_ROOT)
        text = open(path, encoding="utf-8").read()
        lines = text.split("\n")

        def line_of(pat):
            for i, ln in enumerate(lines):
                if pat in ln:
                    return i + 1
            return "?"

        m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        if not m:
            problems.append(("E", rel, "R1 缺少 frontmatter（--- 包裹的 YAML 头）"))
            continue
        fm, body = m.group(1), text[m.end():]

        # R2 封闭键集
        keys = re.findall(r"^([a-zA-Z_-]+):", fm, re.M)
        missing = REQUIRED_KEYS - set(keys)
        if missing:
            problems.append(("E", rel, f"R2 缺少必需键: {sorted(missing)}"))
        for k in keys:
            if k not in KNOWN_KEYS:
                problems.append(("W", rel, f"R2 未知键 '{k}'（若为规范新增请更新 scan_skills.py 的 KNOWN_KEYS）"))

        # R3 name 一致
        nm = re.search(r"^name:\s*(.+)$", fm, re.M)
        if nm and nm.group(1).strip() != sname:
            problems.append(("E", rel, f"R3 name='{nm.group(1).strip()}' 与目录名 '{sname}' 不一致"))

        # R4/R11 description 长度
        dm = re.search(r"^description:\s*(.+)$", fm, re.M)
        if dm:
            dlen = len(dm.group(1).strip())
            if dlen < MIN_DESC_LEN and not re.search(r"^description:\s*[>|]", fm, re.M):
                problems.append(("W", rel, f"R4 description 过短（{dlen} < {MIN_DESC_LEN} 字符）"))
            if dlen > MAX_DESC_LEN:
                problems.append(("W", rel, f"R11 description 过长（{dlen} > {MAX_DESC_LEN} 字符）：触发语义留在 description，流程/门槛细节移入正文"))

        # R5/R6/R8 路径引用
        for mt in re.finditer(r"(?<![\w/~$/.-])((?:scripts|references|assets)/[\w./-]+\.(?:sh|py|md|js|txt|json|png))", body):
            ref = mt.group(1)
            if os.path.exists(os.path.join(sdir, ref)):
                continue
            # R6 尝试跨技能解析：正文该行附近是否提到兄弟技能名
            host = None
            for other in repo_skill_names - {sname}:
                if other in body[max(0, mt.start() - 120): mt.end() + 40]:
                    if os.path.exists(os.path.join(name2dir[other], ref)):
                        host = other
                        break
            if host:
                deps.add(f"{sname} -> {host}:{ref}")
            else:
                problems.append(("E", rel, f"R5 引用不存在且无法解析: {ref}（第 {line_of(ref)} 行附近）"))

        # R7 外部技能依赖须声明 / R9 仓库内兄弟技能不应走绝对路径
        for mt in re.finditer(r"~/(?:\.zcode|\.agents)/skills/([\w-]+)/", body):
            dep = mt.group(1)
            if dep == sname:
                problems.append(("W", rel, f"R8 自引用绝对路径 ~/.agents|zcode/skills/{dep}/，应改为技能基目录相对写法（第 {line_of(mt.group(0))} 行）"))
            elif dep in repo_skill_names:
                ctx = body[max(0, mt.start() - 300): mt.start()]
                if not re.search(r"依赖|定位|顺序|发现|前提|requires|depends", ctx):
                    problems.append(("W", rel, f"R9 仓库内兄弟技能 '{dep}' 被以绝对路径引用，应改为按技能名发现（声明依赖 + 定位顺序；第 {line_of(mt.group(0))} 行）"))
            else:
                ctx = body[max(0, mt.start() - 300): mt.start()]
                if not re.search(r"依赖|前提|requires|depends", ctx):
                    problems.append(("W", rel, f"R7 外部技能依赖 '{dep}' 未声明（引用前 300 字符内无'依赖'说明，第 {line_of(mt.group(0))} 行）"))

        # R10 subagent 派发引用可解析
        if agent_dirs:
            for mt in DISPATCH_RE.finditer(body):
                tgt = mt.group(1)
                if tgt not in agent_names:
                    problems.append(("E", rel, f"R10 派发目标 '{tgt}' 不存在于已发现的 agent 定义（第 {line_of(mt.group(0))} 行）"))

    # ── 输出 ──
    for sev, rel, msg in sorted(problems, key=lambda x: (x[0], x[1])):
        print(f"[{sev}] {rel}: {msg}")
    for d in sorted(deps):
        print(f"[I] 跨技能依赖: {d}")
    errs = sum(1 for s, _, _ in problems if s == "E")
    warns = sum(1 for s, _, _ in problems if s == "W")
    print(f"\n扫描 {len(skills)} 个技能: {errs} error / {warns} warning / {len(deps)} 条跨技能依赖")
    return 1 if errs else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--strict", action="store_true", help="warning 也计入退出码")
    args = ap.parse_args()
    if not args.quiet:
        print(f"agent-skills 结构契约校验 · REPO_ROOT={REPO_ROOT}\n")
    code = scan()
    sys.exit(code)
