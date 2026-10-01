# -*- coding: utf-8 -*-
"""cardkit —— 3:4 社交贴图排版基座（social-cards 技能）

native 坐标系 1774x2365（3:4），save() 统一缩放输出 1080x1440 PNG+JPG。
规则：容器内文字一律按墨迹包围盒（textbbox）居中，禁止用字体度量推导（会整体偏下）；
浅底自动配深字；中文逐字断行、西文/数字串原子不可拆。
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

W, H = 1774, 2365           # native 画布（3:4）
M = 90                      # 版心边距
OUT_SIZE = (1080, 1440)     # 交付尺寸
FONT_DIR = "C:/Windows/Fonts/"

GOOGLE = [(66, 133, 244), (234, 67, 53), (251, 188, 5), (52, 168, 83)]
WHITE = (255, 255, 255)
SOFT = (228, 233, 243)
MUTED = (168, 178, 198)
PANEL = (8, 12, 28, 140)          # 半透明深色面板底
PANEL_LINE = (255, 255, 255, 30)

_fonts = {}


def font(name, size):
    key = (name, size)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(FONT_DIR + name, size)
    return _fonts[key]


def cn_bold(s):  return font("msyhbd.ttc", s)
def cn(s):       return font("msyh.ttc", s)
def en_black(s): return font("ariblk.ttf", s)
def en_bold(s):  return font("arialbd.ttf", s)


def has_cjk(s):
    return any(ord(c) > 0x2E80 for c in s)


def date_font(s, size):
    """日期/标签混排：含中文用中文字体；纯西文用 Arial（Arial 缺中文字形，用错会出豆腐块）"""
    return cn_bold(size) if has_cjk(s) else en_bold(size)


def luminance(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def canvas(bg_path, overlay_alpha=92, overlay_color=(5, 8, 22)):
    """加载背景（自动缩放到 native），叠一层深色保证文字对比度"""
    img = Image.open(bg_path).convert("RGBA")
    if img.size != (W, H):
        img = img.resize((W, H), Image.LANCZOS)
    img.alpha_composite(Image.new("RGBA", (W, H), overlay_color + (overlay_alpha,)))
    return img


def units(text):
    """排版单元：连续西文/数字串不可拆（C/C++、100 万+、gemini-4），CJK 与全角标点逐字"""
    out, buf = [], ""
    for ch in text:
        if ch == "\n":
            if buf:
                out.append(buf)
                buf = ""
            out.append(ch)
        elif ord(ch) > 0x2E80 or ch in "，。：；、！？「」（）·…—":
            if buf:
                out.append(buf)
                buf = ""
            out.append(ch)
        else:
            buf += ch
    if buf:
        out.append(buf)
    return out


def wrap(text, fnt, maxw):
    """按 units 断行，返回行列表"""
    d = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    lines, cur = [], ""
    for u in units(text):
        if u == "\n" or (cur + u).strip() and d.textlength(cur + u, font=fnt) > maxw:
            lines.append(cur.rstrip())
            cur = "" if u == "\n" else u.lstrip()
        else:
            cur += u
    if cur.strip():
        lines.append(cur.rstrip())
    return lines


def glow_text(img, xy, text, fnt, fill, glow_color, radius=22, anchor="mm"):
    """带辉光的大标题"""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text(xy, text, font=fnt, fill=glow_color, anchor=anchor)
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(radius)))
    ImageDraw.Draw(img).text(xy, text, font=fnt, fill=fill, anchor=anchor)


def pill(img, cx=0, cy=0, text="", fnt=None, fill=None, line=None,
         pad_x=46, pad_y=22, tcolor=None, right=None):
    """胶囊标签。文字按墨迹盒在胶囊内水平垂直居中；tcolor 缺省按底色亮度自动（浅底深字）。
    right=右对齐锚点（右缘 x 坐标）。返回胶囊下缘 y。"""
    d = ImageDraw.Draw(img)
    bbox = d.textbbox((0, 0), text, font=fnt)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    if right is not None:
        cx = right - (tw / 2 + pad_x)
    x0, y0 = cx - tw / 2 - pad_x, cy - th / 2 - pad_y
    x1, y1 = cx + tw / 2 + pad_x, cy + th / 2 + pad_y
    d.rounded_rectangle([x0, y0, x1, y1], radius=(y1 - y0) / 2, fill=fill,
                        outline=line, width=2 if line else 0)
    if tcolor is None:
        base = fill[:3] if fill else (255, 255, 255)
        tcolor = WHITE if luminance(base) < 140 else (16, 20, 30)
    d.text((cx - (bbox[0] + bbox[2]) / 2, cy - (bbox[1] + bbox[3]) / 2), text,
           font=fnt, fill=tcolor)
    return y1


def google_bar(img, cx, y, seg_w=130, h=14, gap=18):
    """四色装饰条"""
    d = ImageDraw.Draw(img)
    x = cx - (4 * seg_w + 3 * gap) / 2
    for c in GOOGLE:
        d.rounded_rectangle([x, y, x + seg_w, y + h], radius=h / 2, fill=c)
        x += seg_w + gap


def dot(img, cx, cy, r, color):
    ImageDraw.Draw(img).ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)


def header(img, title, sub, y=150):
    """页眉：四色竖条 + 标题，右侧副题，下方分隔线。返回内容起始 y。"""
    d = ImageDraw.Draw(img)
    x = M
    for c in GOOGLE:
        d.rounded_rectangle([x, y + 34, x + 26, y + 118], radius=13, fill=c)
        x += 44
    d.text((x + 24, y + 76), title, font=cn_bold(96), fill=WHITE, anchor="lm")
    d.text((W - M, y + 80), sub, font=cn(54), fill=MUTED, anchor="rm")
    d.line([M, y + 168, W - M, y + 168], fill=(255, 255, 255, 46), width=3)
    return y + 240


def page_no(img, n, source, total=4):
    """页脚：左侧信息来源，右侧页码 0X/0N（total ≤ 9）"""
    d = ImageDraw.Draw(img)
    d.text((M, H - 78), source, font=cn(42), fill=MUTED, anchor="lm")
    d.text((W - M, H - 78), "0%d / 0%d" % (n, total), font=en_bold(52), fill=MUTED, anchor="rm")


def save(img, out_dir, name):
    """输出 1080x1440 PNG + JPG"""
    os.makedirs(out_dir, exist_ok=True)
    out = img.convert("RGB").resize(OUT_SIZE, Image.LANCZOS)
    out.save(os.path.join(out_dir, name + ".png"))
    out.save(os.path.join(out_dir, name + ".jpg"), quality=93)
