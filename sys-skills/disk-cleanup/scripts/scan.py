#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""disk-cleanup 只读扫描器：枚举本机可清理类别与大小。绝不删除任何东西。

用法：
    python3 scan.py            # 人读表格（stdout）；进度信息走 stderr
    python3 scan.py --json     # 机器可读 JSON

随时可跑，无需确认。大目录 du 可能要一两分钟。
"""
import argparse
import datetime
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (CATEGORIES, PROJECT_ROOTS, bin_available, category_size,
                    docker_reclaimable, du_bytes, human)


def log(msg):
    print(msg, file=sys.stderr)


def scan_node_modules():
    """扫描 PROJECT_ROOTS 下的 node_modules（只记录最外层，不深入其内部）。

    深度上限 5 层、跳过隐藏目录，返回 [{path, size}]，按大小降序。
    """
    found = []
    for root in PROJECT_ROOTS:
        r = os.path.expanduser(root)
        if not os.path.isdir(r):
            continue
        log(f"扫描项目根 {r} …")
        base = r.rstrip("/").count(os.sep)
        for dirpath, dirnames, _ in os.walk(r):
            for d in dirnames:
                if d == "node_modules":
                    found.append(os.path.join(dirpath, d))
            # 不深入隐藏目录与 node_modules 内部；深度上限 5
            dirnames[:] = [d for d in dirnames
                           if not d.startswith(".") and d != "node_modules"]
            if dirpath.count(os.sep) - base >= 5:
                dirnames[:] = []
    out = []
    for p in sorted(set(found)):
        b = du_bytes(p, timeout=240)
        if b:
            out.append({"path": p, "size": b})
    out.sort(key=lambda x: -x["size"])
    return out


def main():
    ap = argparse.ArgumentParser(description="磁盘清理只读扫描")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    log("只读扫描开始（不删除任何文件）……")
    disk = shutil.disk_usage("/")
    items, skipped = [], []
    for c in CATEGORIES:
        if not bin_available(c):
            skipped.append(f"{c['id']}（未安装 {c['bin']}）")
            continue
        log(f"度量 {c['label']} …")
        size, detail, note = category_size(c)
        if c["id"] == "docker-prune" and size is None:
            skipped.append(f"docker-prune（{note}）")
            continue
        if size is None or size <= 0:
            skipped.append(f"{c['id']}（{note or '当前无可清理内容'}）")
            continue
        items.append({
            "id": c["id"], "tier": c["tier"], "label": c["label"],
            "size": size, "size_h": human(size), "detail": detail,
            "note": c["note"], "probe_note": note,
        })

    log("扫描项目 node_modules …")
    node_modules = scan_node_modules()

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    safe = [i for i in items if i["tier"] == "safe"]
    cautious = [i for i in items if i["tier"] == "cautious"]
    for group in (safe, cautious):
        group.sort(key=lambda x: -x["size"])
    nm_total = sum(n["size"] for n in node_modules)
    safe_total = sum(i["size"] for i in safe)
    cautious_total = sum(i["size"] for i in cautious)

    if args.json:
        print(json.dumps({
            "scanned_at": now,
            "disk_free": disk.free, "disk_total": disk.total,
            "safe": safe, "cautious": cautious,
            "node_modules": node_modules,
            "safe_total": safe_total, "cautious_total": cautious_total,
            "node_modules_total": nm_total,
            "skipped": skipped,
        }, ensure_ascii=False, indent=2))
        return

    W = 78
    print(f"磁盘清理扫描报告  {now}")
    print(f"卷可用空间：{human(disk.free)} / {human(disk.total)}")
    print("=" * W)
    print("【安全类 · 纯缓存，可再生，无数据丢失】")
    if safe:
        for i in safe:
            print(f"  {i['id']:<22} {i['size_h']:>9}   {i['label']}")
            print(f"  {'':<22} {'':>9}   ↳ {i['note']}")
    else:
        print("  （无）")
    print("-" * W)
    print("【谨慎类 · 有代价或副作用，默认不清理，需点名】")
    if cautious:
        for i in cautious:
            print(f"  {i['id']:<22} {i['size_h']:>9}   {i['label']}")
            print(f"  {'':<22} {'':>9}   ↳ {i['note']}")
            if i["probe_note"]:
                print(f"  {'':<22} {'':>9}   ↳ {i['probe_note']}")
    else:
        print("  （无）")
    print("-" * W)
    print(f"【项目构建产物 · node_modules，清后需重新 install】共 {len(node_modules)} 处 / {human(nm_total)}")
    for n in node_modules:
        print(f"  {n['path']}  {human(n['size'])}")
    print("=" * W)
    print(f"安全类合计 {human(safe_total)}；谨慎类合计 {human(cautious_total)}；"
          f"node_modules 合计 {human(nm_total)}")
    if skipped:
        print(f"未计入（不存在/未安装/不可用）：{'；'.join(skipped)}")
    print("（以上为只读扫描结果。执行任何清理前需经用户确认，见 SKILL.md 确认门。）")


if __name__ == "__main__":
    main()
