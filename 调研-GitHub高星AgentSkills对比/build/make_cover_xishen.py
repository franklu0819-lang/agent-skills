#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""拆书报告封面 + 合并"""
import os, sys

PDF_SKILL_DIR = "/Users/leo/.zcode/cli/plugins/cache/zcode-plugins-official/pdf/0.1.7/skills/pdf"
sys.path.insert(0, os.path.join(PDF_SKILL_DIR, "scripts"))

from cover_render import render_cover, detect_fonts
from pypdf import PdfReader, PdfWriter, Transformation

BUILD = os.path.dirname(os.path.abspath(__file__))
OUT = "/Users/leo/ZCodeProject/Games/Games1/books/deconstruct-lab/deconstruct/我不是戏神/拆书报告-我不是戏神.pdf"

content = {
    "kicker": "拆书报告 · NOVEL DECONSTRUCT",
    "hero": "我不是戏神",
    "summary": "三九音域著，番茄小说，2023-2026 年连载 900 余天，400 万字，完结时 531.6 万人在读、评分 9.9、蝉联巅峰榜第一。浅拆模式（L1/L3/L5）：戏子=神道载体的容器公式、机制化诗意（期待值命数/落幕晋阶）、界域笔墨经济学、降爽卷呼吸法，附十条模块库指令。",
    "meta": "novel-deconstruct 技能生成 · 数据来源为公开信息 · 2026 年 9 月 29 日",
    "footer": "DECONSTRUCT LAB · DOC 2026-09-05",
    "year": "2026",
    "word": "拆书",
}

palette = {"primary": "#4b5e68", "text": "#1d1f20", "muted": "#878d90", "bg": "#ffffff", "accent": "#d65c34"}
fonts = detect_fonts()
render_cover("01", content, os.path.join(BUILD, "cover.pdf"), palette=palette, fonts=fonts)

A4_W, A4_H = 595.28, 841.89
def normalize(page):
    w, h = float(page.mediabox.width), float(page.mediabox.height)
    if abs(w - A4_W) > 2 or abs(h - A4_H) > 2:
        page.add_transformation(Transformation().scale(sx=A4_W / w, sy=A4_H / h))
        page.mediabox.lower_left = (0, 0)
        page.mediabox.upper_right = (A4_W, A4_H)
    return page

writer = PdfWriter()
writer.add_page(normalize(PdfReader(os.path.join(BUILD, "cover.pdf")).pages[0]))
for p in PdfReader(os.path.join(BUILD, "body.pdf")).pages:
    writer.add_page(normalize(p))
writer.add_metadata({
    "/Title": "《我在精神病院学斩神》拆书报告",
    "/Author": "Z.ai",
    "/Creator": "Z.ai",
    "/Subject": "novel-deconstruct 浅拆模式拆书报告（L1/L3/L5）",
})
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "wb") as f:
    writer.write(f)
print("final:", OUT, len(writer.pages), "pages")
