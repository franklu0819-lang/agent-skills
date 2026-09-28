#!/usr/bin/env python3
"""overlay_text.py — 封面无字底图上叠加书名与署名（排字兜底，B 模式）

用法:
  overlay_text.py <底图> --title "书名" [--author "墨夜寒"] [--title-size 230]
                  [--author-size 70] [--out 输出.jpg] [--title-font 路径] [--author-font 路径]

书名顶部居中大字带描边；署名底部居中「<author> 著」。输出 JPEG（质量 92）。
字体自动回退链: 华文黑体(Medium) → 冬青黑体 → 宋体 → Arial Unicode。
"""
import argparse
import sys
from PIL import Image, ImageDraw, ImageFont

FONT_CHAIN = [
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
]


def load_font(preferred: str | None, size: int):
    candidates = ([preferred] if preferred else []) + FONT_CHAIN
    for path in candidates:
        if not path:
            continue
        try:
            return ImageFont.truetype(path, size, index=0)
        except OSError:
            continue
    sys.exit(f"错误: 找不到可用中文字体（尝试过: {candidates}）")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--title", required=True)
    ap.add_argument("--author", default="墨夜寒")
    ap.add_argument("--title-size", type=int, default=0, help="0=按图宽自适应（约 15%）")
    ap.add_argument("--author-size", type=int, default=0, help="0=按图宽自适应（约 4.5%）")
    ap.add_argument("--out", default="")
    ap.add_argument("--title-font", default="")
    ap.add_argument("--author-font", default="")
    args = ap.parse_args()

    img = Image.open(args.image).convert("RGBA")
    W, H = img.size
    ts = args.title_size or max(80, int(W * 0.15))
    asz = args.author_size or max(40, int(W * 0.045))
    f_title = load_font(args.title_font, ts)
    f_author = load_font(args.author_font, asz)
    d = ImageDraw.Draw(img)

    # 书名：顶部居中，米白字+深褐描边（网文封面通用做法，深浅底图都可读）
    tw = d.textlength(args.title, font=f_title)
    d.text(((W - tw) / 2, H * 0.04), args.title, font=f_title,
           fill=(255, 246, 228, 255), stroke_width=max(6, ts // 18),
           stroke_fill=(70, 25, 15, 225))

    # 署名：底部居中「墨夜寒 著」
    author = f"{args.author} 著"
    aw = d.textlength(author, font=f_author)
    d.text(((W - aw) / 2, H - asz * 2.4), author, font=f_author,
           fill=(242, 238, 230, 238), stroke_width=max(3, asz // 16),
           stroke_fill=(25, 25, 25, 210))

    out = args.out
    if not out:
        stem = args.image.rsplit(".", 1)[0]
        out = f"{stem}-叠字版.jpg"
    img.convert("RGB").save(out, quality=92)
    print(f"{out}\t{W}x{H}")


if __name__ == "__main__":
    main()
