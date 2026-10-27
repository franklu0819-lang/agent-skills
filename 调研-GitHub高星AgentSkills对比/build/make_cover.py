#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""封面渲染 + 合并 + 元数据（六领域对标版）"""
import os, sys

PDF_SKILL_DIR = "/Users/leo/.zcode/cli/plugins/cache/zcode-plugins-official/pdf/0.1.7/skills/pdf"
sys.path.insert(0, os.path.join(PDF_SKILL_DIR, "scripts"))

from cover_render import render_cover, detect_fonts
from pypdf import PdfReader, PdfWriter, Transformation

BUILD = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(BUILD), "AgentSkills六领域高星对标分析报告.pdf")

content = {
    "kicker": "AGENT SKILLS 竞品调研 · SIX DOMAINS",
    "hero": "六领域高星对标分析",
    "summary": "按自有仓库六个技能家族（小说、论文、专利、方舟、抖音、产品研发），逐领域检索 GitHub 高星对标项目并深挖第一名：小说领域现 7,156 星直接竞品，专利与论文领域近乎空白，抖音下载红海而分析层无人。附六领域竞争地图与推广优先级建议。",
    "meta": "数据口径：GitHub API · 2026 年 9 月 29 日 · 调研对象为 franklu0819-lang/agent-skills 六家族",
    "footer": "AGENT-SKILLS BENCHMARK · DOC 2026-09-02",
    "year": "2026",
    "word": "DOMAINS",
}

palette = {
    "primary": "#4b5e68",
    "text": "#1d1f20",
    "muted": "#878d90",
    "bg": "#ffffff",
    "accent": "#d65c34",
}

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
    "/Title": "Agent Skills 六领域高星对标分析报告",
    "/Author": "Z.ai",
    "/Creator": "Z.ai",
    "/Subject": "按自有 agent-skills 六家族分领域检索 GitHub 高星对标项目并深度剖析",
})
with open(OUT, "wb") as f:
    writer.write(f)
print("final:", OUT, len(writer.pages), "pages")
