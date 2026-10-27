#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""《我在精神病院学斩神》拆书报告 PDF — 正文生成"""
import os, sys, hashlib

PDF_SKILL_DIR = "/Users/leo/.zcode/cli/plugins/cache/zcode-plugins-official/pdf/0.1.7/skills/pdf"
sys.path.insert(0, os.path.join(PDF_SKILL_DIR, "scripts"))

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                PageBreak, KeepTogether, CondPageBreak, HRFlowable)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

pdfmetrics.registerFont(TTFont('SimHei', '/System/Library/Fonts/STHeiti Medium.ttc', subfontIndex=1))
pdfmetrics.registerFont(TTFont('Microsoft YaHei', '/System/Library/Fonts/STHeiti Medium.ttc', subfontIndex=1))
pdfmetrics.registerFont(TTFont('Times New Roman', '/System/Library/Fonts/Supplemental/Times New Roman.ttf'))
registerFontFamily('SimHei', normal='SimHei', bold='SimHei')
registerFontFamily('Microsoft YaHei', normal='Microsoft YaHei', bold='Microsoft YaHei')
registerFontFamily('Times New Roman', normal='Times New Roman', bold='Times New Roman')
from pdf import install_font_fallback
install_font_fallback()

CARD_BG      = colors.HexColor('#eaedee')
TABLE_STRIPE = colors.HexColor('#f1f3f4')
HEADER_FILL  = colors.HexColor('#4b5e68')
BORDER       = colors.HexColor('#c5d0d5')
ACCENT       = colors.HexColor('#d65c34')
TEXT_PRIMARY = colors.HexColor('#1d1f20')
TEXT_MUTED   = colors.HexColor('#878d90')

BUILD = os.path.dirname(os.path.abspath(__file__))
OUT_BODY = os.path.join(BUILD, "body.pdf")
LM = RM = 2.0 * cm
TM, BM = 2.2 * cm, 2.0 * cm
AVAIL_W = A4[0] - LM - RM
AVAIL_H = A4[1] - TM - BM

S = {}
S['h1'] = ParagraphStyle('H1', fontName='Microsoft YaHei', fontSize=18, leading=26,
                         textColor=TEXT_PRIMARY, spaceBefore=16, spaceAfter=8, wordWrap='CJK')
S['h2'] = ParagraphStyle('H2', fontName='Microsoft YaHei', fontSize=13, leading=19,
                         textColor=HEADER_FILL, spaceBefore=12, spaceAfter=6, wordWrap='CJK')
S['body'] = ParagraphStyle('Body', fontName='SimHei', fontSize=10.5, leading=17.5,
                           textColor=TEXT_PRIMARY, alignment=TA_LEFT, spaceAfter=8, wordWrap='CJK')
S['bullet'] = ParagraphStyle('Bullet', parent=S['body'], leftIndent=14, spaceAfter=5)
S['caption'] = ParagraphStyle('Caption', fontName='SimHei', fontSize=8.5, leading=12,
                              textColor=TEXT_MUTED, alignment=TA_CENTER, spaceBefore=3, spaceAfter=6)
S['th'] = ParagraphStyle('TH', fontName='Microsoft YaHei', fontSize=9.5, leading=13,
                         textColor=colors.white, alignment=TA_CENTER, wordWrap='CJK')
S['td'] = ParagraphStyle('TD', fontName='SimHei', fontSize=9, leading=13,
                         textColor=TEXT_PRIMARY, alignment=TA_LEFT, wordWrap='CJK')
S['tdc'] = ParagraphStyle('TDC', parent=S['td'], alignment=TA_CENTER)
S['note'] = ParagraphStyle('Note', fontName='SimHei', fontSize=9.5, leading=15,
                           textColor=HEADER_FILL, leftIndent=10, spaceAfter=8, wordWrap='CJK')
S['toc0'] = ParagraphStyle('TOC0', fontName='Microsoft YaHei', fontSize=12, leading=20, leftIndent=6, wordWrap='CJK')

class TocDocTemplate(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if hasattr(flowable, 'bookmark_name'):
            self.notify('TOCEntry', (getattr(flowable, 'bookmark_level', 0),
                                     getattr(flowable, 'bookmark_text', ''),
                                     self.page, getattr(flowable, 'bookmark_key', '')))

def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont('SimHei', 7.5); canvas.setFillColor(TEXT_MUTED)
    canvas.drawString(LM, A4[1] - 1.35 * cm, "拆书报告 ·《我在精神病院学斩神》")
    canvas.setStrokeColor(ACCENT); canvas.setLineWidth(1.2)
    canvas.line(LM, A4[1] - 1.55 * cm, A4[0] - RM, A4[1] - 1.55 * cm)
    canvas.setStrokeColor(BORDER); canvas.setLineWidth(0.5)
    canvas.line(LM, 1.35 * cm, A4[0] - RM, 1.35 * cm)
    canvas.drawString(LM, 1.0 * cm, "novel-deconstruct 浅拆模式（L1/L3/L5）")
    canvas.drawRightString(A4[0] - RM, 1.0 * cm, "第 %d 页" % doc.page)
    canvas.restoreState()

def add_heading(text, style, level=0):
    key = 'h_%s' % hashlib.md5(text.encode()).hexdigest()[:8]
    p = Paragraph('<a name="%s"/><b>%s</b>' % (key, text), style)
    p.bookmark_name = text; p.bookmark_level = level
    p.bookmark_text = text; p.bookmark_key = key
    return p

def h1(story, text):
    story.append(CondPageBreak(AVAIL_H * 0.15))
    story.append(KeepTogether([add_heading(text, S['h1'], 0),
        HRFlowable(width='100%', thickness=1.5, color=ACCENT, spaceBefore=0, spaceAfter=10)]))

def h2(story, text):
    story.append(CondPageBreak(AVAIL_H * 0.22))
    story.append(add_heading(text, S['h2'], 1))

def body(story, text):
    story.append(Paragraph(text, S['body']))

def bullets(story, items):
    for it in items:
        story.append(Paragraph('• ' + it, S['bullet']))
    story.append(Spacer(1, 4))

def make_table(headers, rows, ratios, align_center_cols=None):
    align_center_cols = align_center_cols or []
    data = [[Paragraph('<b>%s</b>' % h, S['th']) for h in headers]]
    for r in rows:
        data.append([Paragraph(c, S['tdc'] if ci in align_center_cols else S['td'])
                     for ci, c in enumerate(r)])
    t = Table(data, colWidths=[x * AVAIL_W for x in ratios], hAlign='CENTER', repeatRows=1)
    st = [('BACKGROUND', (0, 0), (-1, 0), HEADER_FILL),
          ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
          ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
          ('LEFTPADDING', (0, 0), (-1, -1), 6), ('RIGHTPADDING', (0, 0), (-1, -1), 6),
          ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]
    for i in range(1, len(data)):
        st.append(('BACKGROUND', (0, i), (-1, i), colors.white if i % 2 == 1 else TABLE_STRIPE))
    t.setStyle(TableStyle(st))
    return t

def table_block(story, title, headers, rows, ratios, **kw):
    t = make_table(headers, rows, ratios, **kw)
    cap = Paragraph(title, S['caption'])
    story.append(Spacer(1, 8))
    if len(rows) <= 8:
        story.append(KeepTogether([t, cap]))
    else:
        story.append(t); story.append(cap)
    story.append(Spacer(1, 8))

# ══════════════ 正文 ══════════════
story = []
story.append(Paragraph('<b>目 录</b>', ParagraphStyle('TOCT', parent=S['h1'], spaceBefore=6)))
story.append(HRFlowable(width='100%', thickness=1.5, color=ACCENT, spaceBefore=0, spaceAfter=12))
toc = TableOfContents(); toc.levelStyles = [S['toc0']]
story.append(toc); story.append(PageBreak())

# ── 第一部分 ──
h1(story, '一、结论速览与基本盘')
body(story, '本报告由 novel-deconstruct 技能以<b>浅拆模式</b>生成（无原文，基于公开书评、章节目录、完本感言、作者访谈与读者评论完成 L1/L3/L5 三层；L2 黄金三章、L4 桥段库、L6 文风画像需原文，待补）。所有硬事实附来源，推断已标注。')
bullets(story, [
    '<b>它凭什么留住读者</b>：把"超凡组织"写成"精神病院"——神明是病人、主角是学斩神的人。反差设定供给悬念，病人与神明的温情关系供给情绪，家国叙事供给燃点，三条情绪引擎并行。',
    '<b>最值得抄的三件事</b>：① 病人=神明的反差容器（任何"强者弱化形态"题材可复用）；② 守夜人的家国情绪引擎（口号"大夏境内，神明禁行"出圈到抖音变装挑战）；③ 长线伏笔的仪式化回收（读者专门称赞"几百章后被作者告知这是我埋的伏笔"）。',
    '<b>最大的坑</b>：第三卷换地图并加入思想深度时口碑下滑，作者靠删减提速、旧地图联动、新地图快速给爆点挽回。换地图期是四百万字长篇的死亡谷。',
])
table_block(story, '表 1-1 基本盘（来源：番茄作品页、完本感言、DC 娱乐网人物稿、热点观察访谈）',
    ['项', '事实'],
    [
        ['作者', '三九音域（王怀誉，1999 年生，金融学硕士，江苏镇江）'],
        ['平台与状态', '番茄小说；2021-07-09 至 2023-06-09 完结，连载近两年'],
        ['体量', '2033 章 / 426 万字 / 六卷（第六卷近 50 万字收尾）'],
        ['成绩', '番茄端内收藏 2100 万、阅读人数超 3000 万（完本感言自述）'],
        ['荣誉', '2023 年度中国好小说；中国网络文学影响力榜 IP 影响力；第二届网文青春榜年榜'],
        ['衍生', '动画 2024 现象级；实体书《夜幕之下》；官方完结同人曲'],
    ],
    [0.16, 0.84])

h1(story, '二、核心设定与金手指（L1）')
bullets(story, [
    '<b>世界观</b>：迷雾吞噬全球 98%，仅大夏幸存——迷雾被挡在国境线旁百年。"大夏神明在哪"是贯穿全书的悬念（第 16 章借赵空城之口抛出"他们一直在"）。神明从圣经、希腊、北欧、克苏鲁等体系随机出现。',
    '<b>金手指</b>：迷雾作用于人体产生"禁墟"（超凡能力体系）；主角林七夜持有精神世界【凡尘神域】，特性"奇迹"（后期用于重构被抹杀的沧南市）。',
    '<b>升级通道</b>：精神病院里的"病人"实为神明（黑夜女神、梅林、米迦勒等），赐予主角神力——书名双关"（跟神）学（如何）斩神"。升级通道与情感关系是同一条线，学力即羁绊。',
    '<b>组织</b>：守夜人（136 小队、镇妖关、镇国神碑）。作者自述灵感来自抗洪武警与戍边军人。',
])
table_block(story, '表 2-1 卷结构（证据：番茄目录、作者访谈、完本感言）',
    ['卷', '主题与功能'],
    [
        ['第一卷 凡尘神域', '热血+守护；入院、世界观揭示、鬼面王单元、入守夜人（沧南主场）'],
        ['第二卷', '守护主题深化，口碑高峰期'],
        ['第三卷 极恶都市', '换地图，加入"思想觉醒、先驱、反抗"底色；口碑下滑后反转'],
        ['第四至五卷', '多地图扩张，队伍成型，群像高光集中期（剑圣斩神、沈青竹灭信徒）'],
        ['第六卷', '爆点、反转、伏笔密度最高的收官，近 50 万字'],
    ],
    [0.22, 0.78])

h1(story, '三、节奏与爽点频谱（L3）')
body(story, '无原文模式：频谱基于读者评价、章节目录与作者访谈归纳，未做逐章统计（补原文后按技能标准抽样 30 章以上）。')
table_block(story, '表 3-1 四条情绪引擎',
    ['引擎', '供给什么', '证据'],
    [
        ['反差悬念', '病人=神明的持续揭示；每个新病人是一次世界观抽奖', '设定本体；读者"精神病院是可爱温情的地方"评价'],
        ['温情', '神明把主角当孩子、主角照护神明', '高赞长评对主角"把病人当工具人"的批评，反证此关系是核心期待'],
        ['家国燃点', '守夜人牺牲、刻碑、神明禁行口号', '读者"为七夜守护镇国神碑与外神死战而落泪"；口号登抖音热榜'],
        ['长线悬念', '大夏神明在哪，贯穿 2033 章', '第 16 章"他们一直在"；完本感言称第六卷伏笔密集回收'],
    ],
    [0.14, 0.42, 0.44])
h2(story, '3.1 开篇节奏（第一卷前 50 章目录证据）')
bullets(story, [
    '第 1 章"黑缎缠目"直接进入病院异象，无日常铺垫；第 2 章"月亮上的天使"即上世界观最大奇观——奇观前置。',
    '1 至 30 章：沧南主场单元闭环（鬼面人、祂的眼、月下直刀、黑夜女神、鬼面王）；第 32 至 35 章"守夜人、刻碑、正规军"完成入队仪式群；第 40 章"凡尘神域"金手指点题。',
    '第 46 章"校园杀机"作者自注"新书首秀第一把火，今天五更"——第一卷中段第一个爆点高峰，作者以五更配合（爆点+更新量组合拳）。',
    '（推断）单元对手约 30 章一循环，爆点高峰间隔约 40 至 50 章，符合都市异能长线节奏。',
])
h2(story, '3.2 群像高光与换地图死亡谷')
bullets(story, [
    '<b>群像高光</b>：读者记住的名场面几乎全是配角高光——赵空城"最帅的一刀"、冷轩对战洛基、拽哥融合地狱本源、剑圣斩神、沈青竹灭信徒、迦蓝的枪。（推断）中后期每卷 2 至 3 次配角名场面，主角负责串联而非独占爽点。',
    '<b>换地图死亡谷</b>（作者访谈一手陈述）：第三卷换地图加思想深度，读者质疑灌水、节奏变慢、弃坑。挽回组合三件事：适当删减、加快节奏、与上一地图联动。作者大纲观："大部分读者预期跟大纲偏差不大时会改大纲，尊重合理意见，原则性的不改。"',
])
table_block(story, '表 3-2 雷点清单（读者用脚投票的坑）',
    ['雷点', '读者反馈（节选）', '对我们的指令'],
    [
        ['后期乏力/元素过载', '第三卷开始乏力，元素太多，没有前两卷精彩', '神话体系数量设上限，每卷只开一个新体系'],
        ['主角情感回应单薄', '黑夜女神给了成神的资本，男主说了个谢谢？？？', '赐予与回报对称，感情债要还'],
        ['配角入队理由弱', '江洱不明不白进小队，特殊小队不是圣母队', '每个入队事件给硬理由（能力、代价、契约）'],
        ['煽情刻意', '煽情有点刻意，矫揉造作', '燃点靠事件不靠形容词，删抒情段'],
        ['大 boss 动机弱', '最后剧情有点无聊（boss 设定原因）', '终局 boss 的动机在第二至三卷埋实'],
    ],
    [0.20, 0.40, 0.40])

h1(story, '四、人物公式（L5）')
table_block(story, '表 4-1 主角公式：林七夜',
    ['维度', '内容'],
    [
        ['身份', '表：精神病院"病人"；里：136 小队队员、守夜人、队长'],
        ['欲望链', '守护姨妈和老弟 → 守护小队 → 守护大夏（三层欲望升格链）'],
        ['障碍', '神明入侵体系 + 自身禁墟之谜 + 大夏神明缺席之谜'],
        ['反差', '冷面寡言 × 被一院神明当孩子宠'],
        ['金手指耦合', '能力来自病人（神明）的赐予——升级通道与情感关系同线，学力即羁绊'],
    ],
    [0.18, 0.82])
h2(story, '4.1 病人=神明：可复用的容器公式')
body(story, '<b>公式：神话原型 + 人的困境（"病症"）+ 与主角的单线羁绊。</b>例证：患创伤后应激障碍的"孙悟空"；黑夜女神、梅林、米迦勒以病人形态居院。移植度高：任何"强者弱化形态"题材可用（退休神明、落难巨佬、失忆大能入住主角的照护机构），换皮后仍成立。关键纪律：每个病人的"病症"必须是其神话逻辑的产物（孙悟空的应激障碍源于其经历），不能随机设定——神话逻辑给温情供血，随机设定只给猎奇。')
table_block(story, '表 4-2 配角功能位清单',
    ['功能位', '角色', '节奏作用'],
    [
        ['引路人/牺牲位', '赵空城', '第 16 章世界观解说人；"最帅的一刀"是第一卷情绪锚点'],
        ['萌系战力', '百里胖胖', '释压+奇观（万物缴械）；第三卷遗迹单元主角之一'],
        ['冷面强手', '沈青竹', '高光名场面（灭信徒）供给者'],
        ['神秘强援/遗憾位', '迦蓝', '长线牵挂（沉睡令读者遗憾；其枪在第三卷遗迹重现）'],
        ['对手镜像', '冷轩、拽哥等', '敌转友的燃点供给（冷轩战洛基、拽哥融合地狱本源）'],
    ],
    [0.22, 0.18, 0.60])
h2(story, '4.2 关系动态模式')
bullets(story, [
    '新关系引入借任务或收容事件（新病人入院、新队员入队）；旧关系打破用牺牲与沉睡——用"缺席"而非"死亡"保留情感资产，迦蓝的枪重现即是资产激活。',
    '批评样本教训：江洱入队被批"不明不白"——关系引入的硬度不足会直接损伤群像可信度。',
])

h1(story, '五、对我们写作的直接指令')
table_block(story, '表 5-1 模块库转化指令（供 novel-outline / novel-opening / novel-characters 使用）',
    ['编号', '指令', '去向'],
    [
        ['D1', '反差容器放开篇第一章第一个画面（本书第 1 章直接进入病院异象，第 2 章上天使级奇观——世界观奇观前置，不铺垫日常）', 'novel-opening'],
        ['D2', '家国情绪引擎不喊口号：用刻碑、正规军等具体仪式承载，口号留到情绪积累后自然引爆', 'novel-outline / 卷纲'],
        ['D3', '伏笔台账给每条伏笔标"回收仪式感强度"，回收时明示"这是我埋的"本身就是爽点', 'novel-volume / progress.md'],
        ['D4', '换地图预案三件事写进大纲：删支线提速、旧地图角色联动、新地图快速给第一个爆点', 'novel-outline'],
        ['D5', '主角档案必写三层欲望升格链（每层对应一个卷段），不写单层动机', 'novel-characters'],
        ['D6', '重要配角登记时强制填"功能位 + 高光章位预留"；入队事件必须给硬理由', 'novel-characters'],
        ['D7', '情感资产表：记录每段关系的"缺席可能"（牺牲、沉睡、离别），供后期激活复用', 'novel-characters / progress.md'],
        ['D8', '若用"强者弱化"容器：病症=原型逻辑产物（神话逻辑给温情供血，随机设定只剩猎奇）', 'novel-worldview'],
    ],
    [0.08, 0.72, 0.20], align_center_cols=[0])

h1(story, '六、口径与待补项')
bullets(story, [
    '信息来源：番茄小说作品页与目录、完本感言（三叶屋、燃文、墨墨等多源一致）、热点观察作者访谈（2023-06）、DC 娱乐网作者人物稿（2026-05）、Bangumi 词条与短评、和图书第三卷章节页、maigoo 词条。盗文站评分样本失真，未采用。',
    '浅拆局限：L2 黄金三章细拆、L4 桥段库、L6 文风画像需原文；补原文（txt 或章节文件）后按技能 Pipeline 从 L2 起跑，拆书进度.md 已预留断点。',
    '产物清单：拆书进度.md（状态层）、拆书报告.md（本报告源）、节奏与爽点.md（L3）、人物拆解.md（L5）。',
])

doc = TocDocTemplate(OUT_BODY, pagesize=A4,
                     leftMargin=LM, rightMargin=RM, topMargin=TM, bottomMargin=BM,
                     title='《我在精神病院学斩神》拆书报告',
                     author='Z.ai', creator='Z.ai',
                     subject='novel-deconstruct 浅拆模式拆书报告（L1/L3/L5）')
# ── 章标题与首个内容块结构化捆绑（防孤行）──
from reportlab.platypus import Image as _Img

def _h(fl):
    try:
        return fl.wrap(AVAIL_W, AVAIL_H)[1]
    except Exception:
        return 0

bound, i = [], 0
MAX_GROUP = AVAIL_H * 0.42
while i < len(story):
    el = story[i]
    if isinstance(el, KeepTogether):
        inner = list(getattr(el, '_content', []))
        if any(getattr(f, 'bookmark_level', None) == 0 for f in inner):
            grp, j, used = list(inner), i + 1, sum(_h(f) for f in inner)
            while j < len(story) and len(grp) < len(inner) + 4:
                nxt = story[j]
                if isinstance(nxt, CondPageBreak):
                    if j + 1 < len(story) and getattr(story[j + 1], 'bookmark_level', None) == 1:
                        nh2 = _h(story[j + 1])
                        if used + nh2 <= MAX_GROUP:
                            grp.append(story[j + 1]); used += nh2; j += 2; continue
                    break
                if isinstance(nxt, PageBreak):
                    break
                nh = _h(nxt)
                if used + nh > MAX_GROUP:
                    break
                if isinstance(nxt, KeepTogether):
                    grp.extend(list(getattr(nxt, '_content', [])))
                    used += nh; j += 1
                elif isinstance(nxt, (Paragraph, Spacer, _Img, Table, HRFlowable)):
                    grp.append(nxt); used += nh; j += 1
                else:
                    break
            if len(grp) <= len(inner) + 1:
                bound.append(CondPageBreak(AVAIL_H * 0.30))
            el = KeepTogether(grp); i = j
            bound.append(el); continue
    bound.append(el); i += 1
story = bound
while story and isinstance(story[-1], Spacer):
    story.pop()

doc.multiBuild(story, onFirstPage=on_page, onLaterPages=on_page)
print("body ok:", OUT_BODY)
