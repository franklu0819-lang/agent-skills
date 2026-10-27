#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""disk-cleanup 白名单清理执行器：只认 common.py 注册表里的类别，绝不接受任意路径。

用法：
    python3 clean.py --list                          # 列出全部类别与说明
    python3 clean.py --category ID [--category ID…]  # 预演（不删除）
    python3 clean.py --category ID… --yes            # 真执行（前提：会话内已获用户确认）
    python3 clean.py --node-modules /abs/path … [--yes]

安全设计：
  - 不带 --yes 或带 --dry-run 一律只预演；
  - 拒绝 sudo 运行；
  - 只清理注册表类别的固定目录；node_modules 需通过路径校验（绝对路径、
    名为 node_modules、落在 PROJECT_ROOTS 之下）；
  - 清空目录只删其子项（目录本身保留），protect 集合内的顶层条目跳过。
"""
import argparse
import os
import shutil
import stat
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (CATEGORIES, PROJECT_ROOTS, bin_available, category_by_id,
                    category_size, du_bytes, expand, human, probe_paths, run)


def disk_free():
    return shutil.disk_usage("/").free


def clear_children(path, protect=()):
    """删除 path 的全部子项（保留 path 本身）。返回 (删除数, 失败数)。"""
    removed = failed = 0
    try:
        entries = os.listdir(path)
    except OSError:
        return 0, 0
    for name in entries:
        if name in protect:
            continue
        p = os.path.join(path, name)
        try:
            st = os.lstat(p)
            if stat.S_ISLNK(st.st_mode):
                os.unlink(p)
            elif os.path.isdir(p):
                shutil.rmtree(p)
            else:
                os.unlink(p)
            removed += 1
        except OSError:
            failed += 1
    return removed, failed


def node_modules_ok(path):
    """校验 node_modules 路径：绝对路径、目录、名为 node_modules、在 PROJECT_ROOTS 下。"""
    if not os.path.isabs(path):
        return False, "必须是绝对路径"
    if os.path.basename(path.rstrip("/")) != "node_modules":
        return False, "目录名必须是 node_modules"
    if not os.path.isdir(path):
        return False, "目录不存在"
    rp = os.path.realpath(path)
    for root in PROJECT_ROOTS:
        r = os.path.realpath(os.path.expanduser(root))
        if rp.startswith(r + os.sep):
            return True, ""
    return False, "不在项目根（{}）之内".format("、".join(PROJECT_ROOTS))


def clean_category(c, do_it):
    """清理单个类别。返回 (状态行, 释放字节数)。do_it=False 只预演。"""
    cid = c["id"]
    before, _, _ = category_size(c)
    existing = [p for p in probe_paths(c) if os.path.exists(p)]
    has_bin = bin_available(c)
    cmd = c.get("cmd")

    if not has_bin and not existing:
        return f"SKIP  {cid}：未安装 {c.get('bin')}，且无可回退目录", 0

    # 组装动作：有官方命令用命令（声明回退的目录记为候选）；否则直接清目录；
    # always_clear_dirs 为命令成功也要顺带清空的可再生残留（如 npm 的 _npx）
    acts, use_cmd, dirs_to_clear = [], False, []
    always_dirs = [expand(p) for p in c.get("always_clear_dirs", [])
                   if os.path.isdir(expand(p))]
    if cmd and has_bin:
        use_cmd = True
        act = "执行 " + " ".join(cmd)
        if c.get("cmd_fallback_dirs") and existing:
            act += f"（失败则回退清空 {'、'.join(existing)}）"
        acts.append(act)
    if not use_cmd and existing:
        dirs_to_clear = list(existing)
        acts.append(f"清空 {'、'.join(existing)}")
    if always_dirs:
        acts.append(f"清空 {'、'.join(always_dirs)}")
    if not acts:
        return f"SKIP  {cid}：无可执行动作（目录不存在）", 0

    if not do_it:
        for a in acts:
            print(f"  [预演] {a}")
        return f"DRY   {cid}：预演，未删除", 0

    failed = 0
    if use_cmd:
        ok, _ = run(cmd, timeout=c.get("cmd_timeout", 900))
        if not ok:
            if c.get("cmd_fallback_dirs") and existing:
                print(f"  [warn] {cid}：命令失败，回退清空缓存目录")
                dirs_to_clear = list(existing)
            else:
                return f"FAIL  {cid}：清理命令执行失败（保持现状，不做回退）", 0

    protect = c.get("protect", ())
    for p in dirs_to_clear + always_dirs:
        _, f = clear_children(p, protect)
        failed += f

    after, _, _ = category_size(c)
    if before is None or after is None:
        return ("PARTIAL " if failed else "OK      ") + f"{cid}：已执行（前后大小不可度量，失败 {failed} 项）", 0
    freed = max(before - after, 0)
    st = "OK" if failed == 0 else f"PARTIAL({failed} 项失败)"
    return f"{st:<8} {cid}：释放约 {human(freed)}（原 {human(before)}）", freed


def clean_node_modules(path, do_it):
    ok, why = node_modules_ok(path)
    if not ok:
        return f"SKIP  {path}：{why}", 0
    before = du_bytes(path, timeout=240)
    if not do_it:
        print(f"  [预演] 删除目录 {path}（{human(before)}）")
        return f"DRY     {path}：预演，未删除", 0
    try:
        shutil.rmtree(path)
    except OSError as e:
        return f"FAIL    {path}：{e}", 0
    return f"OK      {path}：释放约 {human(before)}", before or 0


def main():
    ap = argparse.ArgumentParser(description="磁盘清理白名单执行器")
    ap.add_argument("--list", action="store_true", help="列出全部类别")
    ap.add_argument("--category", action="append", default=[], metavar="ID")
    ap.add_argument("--node-modules", action="append", default=[], metavar="PATH")
    ap.add_argument("--yes", action="store_true",
                    help="真执行（默认预演；执行前提是会话内已获用户确认）")
    ap.add_argument("--dry-run", action="store_true", help="等价于不带 --yes")
    args = ap.parse_args()

    if os.geteuid() == 0:
        sys.exit("拒绝以 root/sudo 运行：本技能只清理当前用户可再生的缓存。")
    do_it = args.yes and not args.dry_run

    if args.list:
        for c in CATEGORIES:
            tier = "安全" if c["tier"] == "safe" else "谨慎"
            print(f"[{tier}]  {c['id']:<22} {c['label']}：{c['note']}")
        return

    if not args.category and not args.node_modules:
        ap.error("请给 --category ID 或 --node-modules PATH（或 --list）")

    for cid in args.category:
        if category_by_id(cid) is None:
            sys.exit(f"未知类别 {cid}（白名单见 --list；不接受任意路径）")

    print("== 清理执行（--yes，已确认）==" if do_it else "== 预演模式（未带 --yes，不删除任何文件）==")
    free0 = disk_free()
    total = 0
    for cid in args.category:
        line, freed = clean_category(category_by_id(cid), do_it)
        print(line)
        total += freed
    for p in args.node_modules:
        line, freed = clean_node_modules(p, do_it)
        print(line)
        total += freed
    free1 = disk_free()

    if do_it:
        print(f"合计：类别口径释放约 {human(total)}；"
              f"卷可用空间 {human(free0)} → {human(free1)}（净增 {human(free1 - free0)}，含系统并发写入误差）")
    else:
        print("预演结束：未删除任何文件。确认后带 --yes 重新执行。")


if __name__ == "__main__":
    main()
