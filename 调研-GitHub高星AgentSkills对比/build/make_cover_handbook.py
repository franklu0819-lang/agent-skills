#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""借鉴手册封面渲染 + 合并"""
import os, sys

PDF_SKILL_DIR = "/Users/leo/.zcode/cli/plugins/cache/zcode-plugins-official/pdf/0.1.7/skills/pdf"
sys.path.insert(0, os.path.join(PDF_SKILL_DIR, "scripts"))

from cover_render import render_cover, detect_fonts
from pypdf import PdfReader, PdfWriter, Transformation

BUILD = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(BUILD), "AgentSkills技能完善借鉴手册.pdf")

content = {
    "kicker": "技能改进参考 · LEARNING FROM BENCHMARKS",
    "hero": "技能完善借鉴手册",
    "summary": "从七个高星对标项目（K-Dense、oh-story、addyosmani、anthropics、r14dd/patent、douyin 数据 API、ponytail）拆解 20 项可移植机制：契约测试、文件系统状态层、前置门禁、评估账本、诚实边界声明、MCP 化等，每项标注来源与落地位置，并给出 P0-P2 三级落地路线图。",
    "meta": "数据口径：GitHub API · 2026 年 9 月 29 日 · 服务于 franklu0819-lang/agent-skills 六家族改造",
    "footer": "AGENT-SKILLS HANDBOOK · DOC 2026-09-03",
    "year": "2026",
    "word": "LEARN",
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
    "/Title": "Agent Skills 技能完善借鉴手册",
    "/Author": "Z.ai",
    "/Creator": "Z.ai",
    "/Subject": "从高星对标项目拆解 20 项可移植机制并给出落地路线",
})
with open(OUT, "wb") as f:
    writer.write(f)
print("final:", OUT, len(writer.pages), "pages")
