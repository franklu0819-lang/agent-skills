#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""agent-skills 部署器：把源仓库的技能家族同步到各安装目录。

与 scan_skills.py 配套：scan 保证源仓库结构合法，deploy 保证"源是唯一事实"
且同步过程不会静默覆盖安装侧的本地热修。

部署记录（baseline）写在每个安装目录下的 .deploy-manifest.json，
记录每个技能部署时的内容 hash。再次部署时据此判断安装侧是否被热修：
  源 == 安装            → 跳过（已同步）
  源 != 安装 == 基线    → 安全更新（安装侧没动过，只是源更新了）
  源 != 安装 != 基线    → 冲突（安装侧被热修过）：默认报告并跳过，
                          --force 时先备份为 <技能>.bak.<hash8> 再覆盖

用法：
    py scripts/deploy.py --status          # 只报告漂移状态，不改任何文件
    py scripts/deploy.py --init            # 为现有安装记录基线（不覆盖任何文件）
    py scripts/deploy.py --deploy          # 同步（新增/安全更新；冲突跳过并报告）
    py scripts/deploy.py --deploy --force  # 冲突也覆盖（热修内容先备份）
    py scripts/deploy.py --deploy --family social-skills  # 只处理指定家族（可多次给）
"""
import os
import sys
import json
import shutil
import hashlib
import argparse

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST_NAME = ".deploy-manifest.json"


def load_targets():
    cfg = json.load(open(os.path.join(REPO_ROOT, "scripts", "deploy.json"), encoding="utf-8"))
    out = []
    for t in cfg["targets"]:
        dest = t["dest"].replace("{HOME}", os.path.expanduser("~")).replace(
            "{PROJECT}", os.path.dirname(REPO_ROOT))
        out.append((t["family"], os.path.normpath(dest)))
    return out


def dir_hash(path):
    """目录内容 hash：排序遍历相对路径 + 文件内容。"""
    if not os.path.isdir(path):
        return None
    h = hashlib.sha256()
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in sorted(dirs) if not d.startswith(".")]
        for f in sorted(files):
            fp = os.path.join(root, f)
            h.update(os.path.relpath(fp, path).replace("\\", "/").encode())
            h.update(open(fp, "rb").read())
    return h.hexdigest()


def read_manifest(dest):
    p = os.path.join(dest, MANIFEST_NAME)
    if not os.path.exists(p):
        return {}
    return json.load(open(p, encoding="utf-8")).get("skills", {})


def write_manifest(dest, skills):
    os.makedirs(dest, exist_ok=True)
    p = os.path.join(dest, MANIFEST_NAME)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"skills": skills}, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def copy_skill(src, dst):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--status", action="store_true", help="只报告漂移，不改文件")
    g.add_argument("--init", action="store_true", help="记录安装基线，不覆盖文件")
    g.add_argument("--deploy", action="store_true", help="同步源到安装目录")
    ap.add_argument("--force", action="store_true", help="冲突时备份后覆盖")
    ap.add_argument("--family", action="append", help="只处理指定家族（可多次给）")
    args = ap.parse_args()

    conflicts, updated, inited, extra_report = 0, 0, 0, 0

    for family, dest in load_targets():
        if args.family and family not in args.family:
            continue
        fam_dir = os.path.join(REPO_ROOT, family)
        src_skills = sorted(d for d in os.listdir(fam_dir)
                            if os.path.isdir(os.path.join(fam_dir, d))
                            and os.path.exists(os.path.join(fam_dir, d, "SKILL.md")))
        if not src_skills:
            print(f"[!] 家族 {family} 下没有技能（清单配错？），跳过")
            continue

        base = read_manifest(dest)
        print(f"\n== {family} -> {dest}")

        for sname in src_skills:
            src = os.path.join(fam_dir, sname)
            dst = os.path.join(dest, sname)
            sh, dh, bh = dir_hash(src), dir_hash(dst), base.get(sname)

            if sh == dh:
                print(f"  [=] {sname} 已同步")
                if args.init:
                    if sname not in base:
                        base[sname] = sh
                        inited += 1
                elif args.deploy and base.get(sname) != sh:
                    base[sname] = sh  # 已同步时把基线刷新为当前源 hash
                continue

            if dh is None:
                tag = "新增"
                act = True
            elif bh is None:
                if args.init:
                    # 首次纳管：安装侧现状即基线（随后 --deploy 判定为安全更新）
                    base[sname] = dh
                    inited += 1
                    print(f"  [+] {sname} 记录基线（安装侧现状，与源不同）")
                    continue
                print(f"  [?] {sname} 安装侧无基线且内容与源不同：--init 记录现状，或 --force 覆盖")
                conflicts += 1
                continue
            elif dh == bh:
                tag = "更新"
                act = True
            else:
                if not args.force:
                    print(f"  [X] {sname} 冲突：安装侧被热修（{bh[:8]}→{dh[:8]}），默认跳过；--force 可备份后覆盖")
                    conflicts += 1
                    continue
                bak = dst + ".bak." + dh[:8]
                if os.path.exists(bak):
                    shutil.rmtree(bak)
                shutil.move(dst, bak)
                print(f"  [B] {sname} 热修内容已备份到 {os.path.basename(bak)}")
                tag, act = "强制覆盖", True

            if args.status:
                print(f"  [D] {sname} 漂移（{'安装侧缺文件' if dh is None else tag}），未改动")
                continue
            if args.init:
                # init 只记录现状，不覆盖：漂移技能记录安装侧 hash 并提示
                base[sname] = dh if dh else sh
                inited += 1
                print(f"  [+] {sname} 记录基线{'（注意：与源不同，init 记录的是安装侧现状）' if dh != sh else ''}")
                continue
            if act:
                copy_skill(src, dst)
                base[sname] = sh
                updated += 1
                print(f"  [>] {sname} {tag}（{sh[:8]}）")

        # 安装侧不属于该家族的多余技能：只报告不碰
        if os.path.isdir(dest):
            known = set(src_skills)
            for d in sorted(os.listdir(dest)):
                if d in known or d == MANIFEST_NAME or d.startswith("."):
                    continue
                if os.path.isdir(os.path.join(dest, d)) and \
                        os.path.exists(os.path.join(dest, d, "SKILL.md")):
                    print(f"  [I] 安装侧额外技能 {d}（不在 {family}，不管理）")
                    extra_report += 1

        if args.init or args.deploy:
            write_manifest(dest, base)

    mode = "status" if args.status else ("init" if args.init else "deploy")
    print(f"\n{mode} 完成: {updated} 更新 / {inited} 记基线 / {conflicts} 冲突")
    if conflicts:
        print("存在冲突：先决定保留哪一侧（热修请回传源仓库），再 --force 或重新部署")
        sys.exit(2)


if __name__ == "__main__":
    main()
