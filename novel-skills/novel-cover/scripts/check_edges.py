#!/usr/bin/env python3
"""check_edges.py — 检测封面四边是否存在纯色边条（黑边/白边letterbox）

用法: check_edges.py <图片> [--tol 1.5] [--depth 8]
--tol    边条宽度超过画幅对应边长的百分比即判失败（默认 1.5%）
--depth  从每条边向内逐列/行扫描的最大深度，取画幅短边的百分比（默认 8%）

原理: 逐列/行计算亮度均值与标准差；均值<8 或 >247 且标准差<3 的连续行列视为纯色条。
输出: 每边一行 `边  条宽px(百分比)  判定`；任一边超阈值则退出码 1。
"""
import argparse
import statistics
import sys

from PIL import Image


def edge_bar_width(get_line, length, limit):
    """从边缘向内逐线扫描，返回纯色条的宽度（像素）。"""
    width = 0
    for i in range(limit):
        vals = get_line(i)
        mean = statistics.mean(vals)
        std = statistics.pstdev(vals)
        if (mean < 8 or mean > 247) and std < 3:
            width = i + 1
        elif width and width >= 3 and std < 6 and (mean < 16 or mean > 240):
            width = i + 1  # 允许条内侧少量过渡噪声
        else:
            break
    return width


def has_signature_above(img_l, W, H, bar_top):
    """底边纯色条上方是否紧邻居中亮色文字簇（署名）——是则该黑带为设计边距，豁免。"""
    px = img_l.load()
    zone_top = max(0, bar_top - int(H * 0.06))
    xs = [x for y in range(zone_top, bar_top) for x in range(0, W, 2) if px[x, y] > 120]
    if len(xs) < 20:
        return False
    lo, hi = min(xs), max(xs)
    center_dev = abs((lo + hi) / 2 - W / 2) / W
    return center_dev < 0.12  # 文字簇须大致居中


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--tol", type=float, default=1.5)
    ap.add_argument("--depth", type=float, default=8)
    args = ap.parse_args()

    img = Image.open(args.image)
    img_l = img.convert("L")
    W, H = img_l.size
    px = img_l.load()
    step = max(1, min(W, H) // 400)  # 采样步长，加速大图

    limit = int(min(W, H) * args.depth / 100)
    edges = {
        "左": (lambda i: [px[i, y] for y in range(0, H, step)], H),
        "右": (lambda i: [px[W - 1 - i, y] for y in range(0, H, step)], H),
        "上": (lambda i: [px[x, i] for x in range(0, W, step)], W),
        "下": (lambda i: [px[x, H - 1 - i] for x in range(0, W, step)], W),
    }

    failed = False
    for name, (get_line, full_len) in edges.items():
        w = edge_bar_width(get_line, full_len, limit)
        pct = w / full_len * 100
        ok = pct <= args.tol
        note = ""
        # 底部署名边距豁免：条上方紧邻居中文字簇的黑带是设计，不是 letterbox
        if not ok and name == "下" and pct <= 6:
            bar_top = full_len - w
            if has_signature_above(img_l, W, full_len, bar_top):
                ok, note = True, "（署名底边距·设计，豁免）"
        if not ok:
            failed = True
        print(f"{name}边\t{w}px\t{pct:.1f}%\t{'通过' if ok else '超标-纯色边条'}{note}")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
