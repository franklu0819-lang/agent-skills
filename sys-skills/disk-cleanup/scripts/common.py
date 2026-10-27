#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""disk-cleanup 共享库：类别注册表 + 工具函数。

scan.py 与 clean.py 共同 import 本文件，保证"扫描看到的"与"清理执行的"
永远是同一份路径事实。本文件只放数据与纯函数，不做任何删除。
"""
import os
import re
import shutil
import subprocess

HOME = os.path.expanduser("~")

# node_modules 扫描根（存在才扫）；清理 node_modules 时路径必须落在这些根下
PROJECT_ROOTS = [
    "~/ZCodeProject", "~/dev", "~/Projects", "~/code",
    "~/work", "~/workspace", "~/workspaces", "~/src",
]

# tier 语义：
#   safe     纯缓存/可再生，删除无数据丢失，只是重新下载或重新编译
#   cautious 有代价或副作用（数据可能还想留），默认不勾选，必须用户点名
#
# 字段：
#   id / tier / label / note   展示用
#   dirs     度量并（在无 cmd 时）清空内容的目录列表；支持 ~
#   bin      依赖的外部命令（不存在时：有 dirs 则回退清目录，否则跳过）
#   cmd      清理命令（官方工具优先）；cmd_fallback_dirs=True 时命令失败回退清 dirs
#   probe    特殊度量方式：brew / pnpm / docker / simctl
#   protect  清空 dirs 时跳过的顶层条目名（如 huggingface 登录 token）
CATEGORIES = [
    # ---------------- 安全类：纯缓存，可再生 ----------------
    {
        "id": "brew-cache", "tier": "safe", "label": "Homebrew 缓存",
        "note": "下载包与旧版本；下次安装重新下载（命令失败回退清下载缓存，"
                "可顺带清掉损坏的半截下载包）",
        "dirs": [], "bin": "brew", "probe": "brew",
        "cmd": ["brew", "cleanup", "--prune=all", "-s"], "cmd_timeout": 1800,
        "cmd_fallback_dirs": True,
    },
    {
        "id": "npm-cache", "tier": "safe", "label": "npm 缓存",
        "note": "~/.npm：npm cache clean --force 清 _cacache，另清 _npx（npx 包缓存，"
                "npm 官方命令不覆盖的可再生残留）",
        "dirs": ["~/.npm"], "bin": "npm", "probe": None,
        "cmd": ["npm", "cache", "clean", "--force"], "cmd_timeout": 600,
        "cmd_fallback_dirs": True, "always_clear_dirs": ["~/.npm/_npx"],
    },
    {
        "id": "pnpm-store", "tier": "safe", "label": "pnpm store",
        "note": "内容寻址存储；pnpm store prune 只删未引用块",
        "dirs": [], "bin": "pnpm", "probe": "pnpm",
        "cmd": ["pnpm", "store", "prune"], "cmd_timeout": 1200,
        "cmd_fallback_dirs": False,
    },
    {
        "id": "yarn-cache", "tier": "safe", "label": "yarn 缓存",
        "note": "yarn v1 全局缓存目录",
        "dirs": ["~/Library/Caches/Yarn", "~/.cache/yarn"], "bin": None, "probe": None,
        "cmd": None, "cmd_fallback_dirs": False,
    },
    {
        "id": "pip-cache", "tier": "safe", "label": "pip 缓存",
        "note": "wheel/http 缓存；pip cache purge",
        "dirs": ["~/Library/Caches/pip"], "bin": "python3", "probe": None,
        "cmd": ["python3", "-m", "pip", "cache", "purge"], "cmd_timeout": 600,
        "cmd_fallback_dirs": True,
    },
    {
        "id": "uv-cache", "tier": "safe", "label": "uv 缓存",
        "note": "uv 的 wheel 与源码缓存；uv cache clean",
        "dirs": ["~/Library/Caches/uv"], "bin": "uv", "probe": None,
        "cmd": ["uv", "cache", "clean"], "cmd_timeout": 600,
        "cmd_fallback_dirs": True,
    },
    {
        "id": "gradle-cache", "tier": "safe", "label": "Gradle 缓存",
        "note": "~/.gradle/caches；清后首次构建重新下载全部依赖",
        "dirs": ["~/.gradle/caches"], "bin": None, "probe": None,
        "cmd": None, "cmd_fallback_dirs": False,
    },
    {
        "id": "cocoapods-cache", "tier": "safe", "label": "CocoaPods 缓存",
        "note": "_specs / 项目 pod 缓存；pod install 重新下载",
        "dirs": ["~/Library/Caches/CocoaPods"], "bin": None, "probe": None,
        "cmd": None, "cmd_fallback_dirs": False,
    },
    {
        "id": "cargo-cache", "tier": "safe", "label": "Cargo 注册表缓存",
        "note": "~/.cargo/registry 的 cache 与 src；不影响已装二进制",
        "dirs": ["~/.cargo/registry/cache", "~/.cargo/registry/src"], "bin": None, "probe": None,
        "cmd": None, "cmd_fallback_dirs": False,
    },
    {
        "id": "huggingface-cache", "tier": "safe", "label": "HuggingFace 模型缓存",
        "note": "~/.cache/huggingface；模型需重新下载（跳过登录 token 文件）",
        "dirs": ["~/.cache/huggingface"], "bin": None, "probe": None,
        "cmd": None, "cmd_fallback_dirs": False,
        "protect": {"token", "stored_tokens"},
    },
    {
        "id": "playwright-cache", "tier": "safe", "label": "Playwright/Puppeteer 浏览器",
        "note": "测试浏览器二进制；npx playwright install 重装",
        "dirs": ["~/Library/Caches/ms-playwright", "~/Library/Caches/puppeteer"],
        "bin": None, "probe": None, "cmd": None, "cmd_fallback_dirs": False,
    },
    {
        "id": "xcode-deriveddata", "tier": "safe", "label": "Xcode DerivedData",
        "note": "构建产物与索引；下次打开项目全量重建（首次编译变慢）",
        "dirs": ["~/Library/Developer/Xcode/DerivedData"], "bin": None, "probe": None,
        "cmd": None, "cmd_fallback_dirs": False,
    },
    {
        "id": "core-sim-caches", "tier": "safe", "label": "CoreSimulator 缓存",
        "note": "模拟器临时缓存与日志",
        "dirs": ["~/Library/Developer/CoreSimulator/Caches"], "bin": None, "probe": None,
        "cmd": None, "cmd_fallback_dirs": False,
    },
    {
        "id": "ios-devicesupport", "tier": "safe", "label": "设备支持符号 (DeviceSupport)",
        "note": "iOS/watchOS/tvOS DeviceSupport；连真机调试时重新生成（几分钟）",
        "dirs": [
            "~/Library/Developer/Xcode/iOS DeviceSupport",
            "~/Library/Developer/Xcode/watchOS DeviceSupport",
            "~/Library/Developer/Xcode/tvOS DeviceSupport",
        ],
        "bin": None, "probe": None, "cmd": None, "cmd_fallback_dirs": False,
    },
    {
        "id": "sim-unavailable", "tier": "safe", "label": "失效模拟器设备",
        "note": "运行时已不存在的模拟器设备；simctl delete unavailable",
        "dirs": [], "bin": "xcrun", "probe": "simctl",
        "cmd": ["xcrun", "simctl", "delete", "unavailable"], "cmd_timeout": 300,
        "cmd_fallback_dirs": False,
    },

    # ---------------- 谨慎类：默认不勾选，必须用户点名 ----------------
    {
        "id": "docker-prune", "tier": "cautious", "label": "Docker 悬空资源",
        "note": "悬空镜像+停止的容器+构建缓存；停止容器内的数据会一并丢失。"
                "不动 volume 与在用镜像；-a 需用户点名才加",
        "dirs": [], "bin": "docker", "probe": "docker",
        "cmd": ["docker", "system", "prune", "-f"], "cmd_timeout": 1800,
        "cmd_fallback_dirs": False,
    },
    {
        "id": "xcode-archives", "tier": "cautious", "label": "Xcode 发布归档",
        "note": "Archives 含 dSYM；删除后历史版本无法符号化追查崩溃",
        "dirs": ["~/Library/Developer/Xcode/Archives"], "bin": None, "probe": None,
        "cmd": None, "cmd_fallback_dirs": False,
    },
    {
        "id": "user-logs", "tier": "cautious", "label": "用户日志与诊断报告",
        "note": "~/Library/Logs 含崩溃诊断报告；删后无法回查历史故障",
        "dirs": ["~/Library/Logs"], "bin": None, "probe": None,
        "cmd": None, "cmd_fallback_dirs": False,
    },
    {
        "id": "trash", "tier": "cautious", "label": "废纸篓",
        "note": "~/.Trash；清空后无法再恢复",
        "dirs": ["~/.Trash"], "bin": None, "probe": None,
        "cmd": None, "cmd_fallback_dirs": False,
    },
]


def expand(p):
    return os.path.expanduser(p)


def category_by_id(cid):
    for c in CATEGORIES:
        if c["id"] == cid:
            return c
    return None


def bin_available(c):
    b = c.get("bin")
    return b is None or shutil.which(b) is not None


def run(argv, timeout=120):
    """跑外部命令，返回 (ok, stdout)。异常/超时/非零都算失败。"""
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, r.stdout or ""
    except Exception:
        return False, ""


def du_bytes(path, timeout=300):
    """原生 du -sk（实际磁盘占用），返回 bytes；失败/超时返回 None。"""
    ok, out = run(["du", "-sk", path], timeout=timeout)
    if ok and out.strip():
        try:
            return int(out.split()[0]) * 1024
        except (ValueError, IndexError):
            return None
    return None


def human(n):
    if n is None:
        return "?"
    for u in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024 or u == "TB":
            return f"{int(n)} B" if u == "B" else f"{n:.1f} {u}"
        n /= 1024.0
    return f"{n:.1f} TB"


_UDID_RE = re.compile(
    r"\(([0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12})\)")
_DOCKER_SIZE_RE = re.compile(r"([0-9.]+)\s*(B|kB|MB|GB|TB)")


def parse_decimal_size(s):
    """解析 docker 的十进制尺寸（10.1GB → bytes）。"""
    m = _DOCKER_SIZE_RE.search(s)
    if not m:
        return None
    val, unit = float(m.group(1)), m.group(2)
    mult = {"B": 1, "kB": 10**3, "MB": 10**6, "GB": 10**9, "TB": 10**12}[unit]
    return int(val * mult)


# ---------------- 特殊度量（probe） ----------------

def probe_paths(c):
    """probe 类别返回参与度量的目录列表；普通类别返回 dirs。"""
    kind = c.get("probe")
    if kind == "brew":
        ok, out = run(["brew", "--cache"], timeout=60)
        return [out.strip()] if ok and out.strip() else []
    if kind == "pnpm":
        ok, out = run(["pnpm", "store", "path"], timeout=60)
        return [out.strip()] if ok and out.strip() else []
    if kind == "simctl":
        ok, out = run(["xcrun", "simctl", "list", "devices", "unavailable"], timeout=120)
        if not ok:
            return []
        base = os.path.join(HOME, "Library/Developer/CoreSimulator/Devices")
        return [os.path.join(base, u) for u in _UDID_RE.findall(out)]
    return [expand(p) for p in c["dirs"]]


def docker_reclaimable():
    """docker system df 的 RECLAIMABLE 合计（Images+Containers+Build Cache）。

    返回 (bytes|None, note)。Docker 未运行 → (None, 原因)。估计数：
    prune -f 实际只删悬空层，可能低于该值。
    """
    ok, out = run(["docker", "system", "df"], timeout=120)
    if not ok:
        return None, "Docker 未运行或不可用"
    total = 0
    seen = False
    for line in out.splitlines():
        if line.strip().startswith("TYPE"):
            continue
        for t in ("Images", "Containers", "Build Cache"):
            if line.strip().startswith(t + " "):
                # RECLAIMABLE 是最后一个"数值+单位"样式字段（可能带百分比）
                m = re.search(r"([0-9.]+(?:B|kB|MB|GB|TB))(?:\s+\(\d+%\))?\s*$", line.strip())
                if m:
                    b = parse_decimal_size(m.group(1))
                    if b is not None:
                        total += b
                        seen = True
    if not seen:
        return None, "docker system df 输出无法解析"
    return total, "估算值；prune 实际只删悬空层，可能少于此数"


def category_size(c):
    """类别当前占用：返回 (bytes|None, detail, note)。

    detail 给人看的路径/逐项大小；note 为度量附带说明（如 Docker 未运行）。
    """
    if c.get("probe") == "docker":
        b, note = docker_reclaimable()
        return b, c["label"], note or ""

    paths = probe_paths(c)
    items, total, missing = [], 0, 0
    for p in paths:
        if not os.path.exists(p):
            missing += 1
            continue
        b = du_bytes(p)
        if b is not None:
            total += b
            items.append((p, b))
    if not items:
        return None, "", "当前无可清理内容" if not paths else "目录不存在或为空"
    detail = "；".join(f"{p} {human(b)}" for p, b in sorted(items, key=lambda x: -x[1]))
    return total, detail, ""
