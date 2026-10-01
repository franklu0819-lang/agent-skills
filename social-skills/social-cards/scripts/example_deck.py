# -*- coding: utf-8 -*-
"""示例卡组：封面 / 看点列表 / 多系列对比条形 / 定价+时间线（源自真实任务「Gemini 4 发布」）

用法：    py -3 example_deck.py [bg_dir] [out_dir]     # 默认 bg/ final/
复用：    复制改名为 compose.py → 替换数据与文案 → 按需增删卡片；排版工具在 cardkit.py，勿重写。
背景：    先用 ark-image-gen 生成 3:4 无文字背景（--ratio 3:4 -s 2K → 1774x2365）。
硬规则：  见 SKILL.md（墨迹盒居中 / 断词原子 / 浅底深字 / 行距 / 色相分离 / 译法）。
"""
import os
import sys

sys.dont_write_bytecode = True  # 不在技能目录留 __pycache__（会污染部署器的目录 hash）
from cardkit import *   # noqa: F401,F403

BG = sys.argv[1] if len(sys.argv) > 1 else "bg"
OUT = sys.argv[2] if len(sys.argv) > 2 else "final"


def bg(name):
    return os.path.join(BG, name)


# ---------------------------------------------------------------- 1 封面
img = canvas(bg("bg_cover.jpg"))
d = ImageDraw.Draw(img)
pill(img, W / 2, 230, "AI 前沿速递 · 2026.09.30", cn_bold(52),
     fill=(66, 133, 244, 90), line=(140, 185, 255, 130))
glow_text(img, (W / 2, 560), "Gemini 4", en_black(320), WHITE, (90, 140, 255, 160))
google_bar(img, W / 2, 790)
d.text((W / 2, 950), "Argon 正式发布", font=cn_bold(168), fill=WHITE, anchor="mm")
d.text((W / 2, 1105), "谷歌开启「前沿智能」新纪元", font=cn(80), fill=SOFT, anchor="mm")

chips = [
    ("编程新 SOTA", "DeepSWE 77.9%", GOOGLE[0]),
    ("输出上限扩至 100 万 token", "从 6.4 万 → 100 万 · 业界领先", GOOGLE[2]),
    ("首发优惠价 $2 / $10 每百万 tokens", "缓存输入为输入价的 5%", GOOGLE[3]),
]
cy = 1430
for title, sub, color in chips:
    d.rounded_rectangle([M, cy, W - M, cy + 220], radius=40, fill=PANEL, outline=PANEL_LINE, width=2)
    d.rounded_rectangle([M, cy, M + 16, cy + 220], radius=8, fill=color)
    d.text((M + 70, cy + 78), title, font=cn_bold(66), fill=WHITE, anchor="lm")
    d.text((M + 70, cy + 162), sub, font=cn(50), fill=MUTED, anchor="lm")
    cy += 258

d.text((W / 2, H - 165), "首发通道：Fairwind 计划 · 可信网络防御者", font=cn(52), fill=SOFT, anchor="mm")
page_no(img, 1, "信息来源：Google 官方博客")
save(img, OUT, "deck_01_cover")

# ---------------------------------------------------------------- 2 看点列表
img = canvas(bg("bg_points.jpg"))
y = header(img, "5 大核心看点", "一文看懂")
items = [
    ("定位跃迁", "专攻「长时程复杂工作流」：软件工程、法律与金融知识工作、网络安全防御三大主战场", GOOGLE[0]),
    ("编程新 SOTA", "DeepSWE v1.1 达 77.9%；Fuchsia 内核 80 万+ 行 C/C++ 代码自主迁移 Rust", GOOGLE[1]),
    ("百万 token 输出", "输出上限从 6.4 万 token 扩至 100 万，业界领先，支撑多步骤深度求解", GOOGLE[2]),
    ("安全攻防一体", "自主发现、验证并修补关键漏洞；Wiz「Scan for Good」已借其发现全球性医疗软件漏洞", GOOGLE[3]),
    ("谷歌全员内用", "量子算法优化超已发表基线 40%，智能体集群释放 300+ TiB 内存", GOOGLE[0]),
]
row_h = 356
for i, (t, desc, color) in enumerate(items):
    top = y + i * row_h
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([M, top, W - M, top + row_h - 40], radius=36, fill=PANEL, outline=PANEL_LINE, width=2)
    cx, cyc, r = M + 96, top + (row_h - 40) / 2, 62
    d.ellipse([cx - r, cyc - r, cx + r, cyc + r], fill=color)
    d.text((cx, cyc - 6), str(i + 1), font=en_black(84), fill=WHITE, anchor="mm")
    d.text((M + 210, top + 86), t, font=cn_bold(72), fill=WHITE, anchor="lm")
    ly = top + 180
    for ln in wrap(desc, cn(52), W - M * 2 - 260)[:2]:
        d.text((M + 210, ly), ln, font=cn(52), fill=SOFT, anchor="lm")
        ly += 76
page_no(img, 2, "信息来源：Google 官方博客")
save(img, OUT, "deck_02_points")

# ---------------------------------------------------------------- 3 多系列对比条形
img = canvas(bg("bg_bench.jpg"))
d = ImageDraw.Draw(img)
header(img, "跑分对比", "对比 GPT-6 与 Claude 旗舰")

models = [
    ("Gemini 4 Argon", GOOGLE[0]),
    ("GPT-6 Astra", (16, 163, 127)),
    ("Claude Opus 5.5", (217, 119, 87)),
    ("Claude Fable 5.1", (154, 106, 255)),
]
namef = en_bold(44)
widths = [60 + d.textlength(nm, font=namef) for nm, _ in models]
total = sum(widths) + 64 * (len(models) - 1)
lx = (W - total) / 2
for (nm, c), wd in zip(models, widths):
    dot(img, lx + 15, 428, 14, c)
    d.text((lx + 46, 428), nm, font=namef, fill=SOFT, anchor="lm")
    lx += wd + 64

groups = [
    ("DeepSWE v1.1 · 真实软件工程", [77.9, 74.1, 74.2, 67.4], "Argon 第一", GOOGLE[0]),
    ("Vals Index · 知识工作", [68.9, 63.1, 67.0, 65.8], "Argon 第一", GOOGLE[0]),
    ("CWE-bench v1 · 漏洞攻防", [68.0, 68.0, 67.0, 58.0], "并列第一", GOOGLE[2]),
    ("FrontierSWE v2 · 前沿软件工程", [55.0, 65.5, 62.3, 56.3], "Astra 第一", (16, 163, 127)),
    ("Terminal-Bench 4.0 · 终端任务", [57.4, 58.2, 66.4, 57.9], "Opus 第一", (217, 119, 87)),
]
gy = 512
bar_h, bar_gap = 36, 9
group_h = 94 + 4 * (bar_h + bar_gap) + 30
for title, vals, tag, tagc in groups:
    top = gy
    d.rounded_rectangle([M - 16, top - 6, W - M + 16, top + group_h - 30], radius=36,
                        fill=PANEL, outline=PANEL_LINE, width=2)
    d.text((M + 24, top + 36), title, font=cn_bold(56), fill=WHITE, anchor="lm")
    pill(img, right=W - M - 30, cy=top + 34, text=tag, fnt=cn_bold(42), fill=tagc + (70,),
         pad_x=26, pad_y=12)
    by = top + 94
    track_w = (W - 2 * M) - 158
    for (nm, c), v in zip(models, vals):
        d.rounded_rectangle([M, by, M + track_w, by + bar_h], radius=bar_h / 2,
                            fill=(255, 255, 255, 30))
        fw = track_w * v / 100.0
        d.rounded_rectangle([M, by, M + fw, by + bar_h], radius=bar_h / 2, fill=c)
        d.text((W - M, by + bar_h / 2), "%.1f%%" % v, font=en_bold(44), fill=c, anchor="rm")
        by += bar_h + bar_gap
    gy += group_h

fy = gy + 16
d.rounded_rectangle([M, fy, W - M, fy + 158], radius=36, fill=(10, 12, 26, 175),
                    outline=PANEL_LINE, width=2)
d.text((M + 56, fy + 52), "注：LVBench 91.7%、AutomationBench 51.3% 为官方口径单项第一",
       font=cn(46), fill=SOFT, anchor="lm")
d.text((M + 56, fy + 112), "Argon 并非全场领先，FrontierSWE 与 Terminal-Bench 仍落后于竞品",
       font=cn(46), fill=SOFT, anchor="lm")
page_no(img, 3, "信息来源：Google 官方博客 · MarkTechPost 汇总")
save(img, OUT, "deck_03_bars")

# ---------------------------------------------------------------- 4 定价 + 时间线
img = canvas(bg("bg_price.jpg"))
y = header(img, "价格与获取", "怎么用上") + 20

d = ImageDraw.Draw(img)
ph = 500
d.rounded_rectangle([M, y, W - M, y + ph], radius=44, fill=PANEL, outline=PANEL_LINE, width=2)
d.text((W / 2, y + 90), "首发优惠期 · 每百万 tokens", font=cn(54), fill=MUTED, anchor="mm")
d.text((W / 2 - 300, y + 235), "$2", font=en_black(150), fill=GOOGLE[0], anchor="mm")
d.text((W / 2, y + 235), "/", font=en_black(110), fill=MUTED, anchor="mm")
d.text((W / 2 + 300, y + 235), "$10", font=en_black(150), fill=GOOGLE[3], anchor="mm")
d.text((W / 2 - 300, y + 360), "输入", font=cn_bold(52), fill=SOFT, anchor="mm")
d.text((W / 2 + 300, y + 360), "输出", font=cn_bold(52), fill=SOFT, anchor="mm")
d.text((W / 2, y + 445), "缓存输入为输入价的 5% · 优惠期后恢复 $4 / $20", font=cn(50), fill=MUTED, anchor="mm")

ty = y + ph + 110
tl = [
    ("2026.07.21", "官宣启动「史上最大规模」预训练", GOOGLE[0]),
    ("2026.09.24", "DeepMind 确认进入后训练阶段", GOOGLE[2]),
    ("2026.09.30", "Gemini 4 Argon 正式发布", GOOGLE[3]),
    ("即将开始", "付费 API 客户与 Google AI Ultra 订阅者优先", GOOGLE[1]),
]
d.line([M + 44, ty + 15, M + 44, ty + 3 * 230 + 15], fill=(255, 255, 255, 60), width=4)
for i, (date, desc, color) in enumerate(tl):
    cyc = ty + i * 230 + 15
    dot(img, M + 44, cyc, 22, color)
    d.text((M + 120, cyc - 45), date, font=date_font(date, 56), fill=color, anchor="lm")
    d.text((M + 120, cyc + 55), desc, font=cn_bold(56), fill=WHITE, anchor="lm")

fy = ty + 3 * 230 + 15 + 130
d.rounded_rectangle([M, fy, W - M, fy + 190], radius=36, fill=(10, 12, 26, 205),
                    outline=(251, 188, 5, 120), width=3)
d.text((W / 2, fy + 60), "注意", font=cn_bold(50), fill=(251, 188, 5), anchor="mm")
d.text((W / 2, fy + 135), "Argon 分阶段开放，目前 API 模型目录暂无 gemini-4 条目",
       font=cn(48), fill=WHITE, anchor="mm")
page_no(img, 4, "信息来源：Google 官方博客")
save(img, OUT, "deck_04_price")

print("done:", sorted(os.listdir(OUT)))
