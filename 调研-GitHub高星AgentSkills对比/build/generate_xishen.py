#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""《我不是戏神》拆书报告 PDF — 正文生成"""
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
    canvas.drawString(LM, A4[1] - 1.35 * cm, "拆书报告 ·《我不是戏神》")
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

h1(story, '一、结论速览与基本盘')
body(story, '本报告由 novel-deconstruct 技能以<b>浅拆模式</b>生成（无原文，基于番茄作品页、百度百科、实体书目录、正文引用片段、作者卷末总结与媒体报道完成 L1/L3/L5；L2/L4/L6 需原文，待补）。硬事实附来源，推断已标注。')
bullets(story, [
    '<b>它凭什么登顶</b>：把"表演"做成世界规则——戏子在废土上以表演维系"观众期待值"，期待值就是命数；晋阶条件是"在无人问津的舞台上完成一次掌声鸣动的落幕"这种机制化诗意。容器之上还有元小说层：读者也是"观众"，追更行为被写进世界观。',
    '<b>最值得抄的三件事</b>：① 升级机制与世界规则一体化（期待值=复活币、落幕=晋阶，非外挂式金手指）；② 界域制换地图+笔墨经济学（前期一个界域慢写小角色群像、后期提速转主线）；③ 主动降爽的结构呼吸（第四卷故意让主角碰壁，作者：所向披靡的主角会让其他人的牺牲显得弱小愚蠢）。',
    '<b>最大的坑（作者自认）</b>：第四卷压抑期"肯定成为一部分读者弃书的理由"；且作者坦白此书没有细致大纲（对比斩神期"按最初规划坚持"）——悲壮史诗路线对大纲纪律的要求其实更高，这是它最惊险的走钢丝。',
])
table_block(story, '表 1-1 基本盘（来源：番茄作品页、百度百科、橙瓜、69 短剧资讯、中国作家网、新浪）',
    ['项', '事实'],
    [
        ['作者', '三九音域（番茄殿堂作家；代表作三部曲第三本）'],
        ['平台与状态', '番茄小说；2023-09-28 至 2026-04-30 完结，连载 900+ 天'],
        ['体量', '400.4 万字；作者预想六卷完结、可能五六合并'],
        ['成绩', '上线 8 天阅读破百万；完结时 531.6 万人在读、116 万人点评、评分 9.9、蝉联番茄巅峰榜第一'],
        ['荣誉', '澳门国际科幻奖最佳科幻网络文学；中国作协网络文学重点作品扶持项目（中华优秀文化主题）'],
        ['衍生', '实体书出版（豆瓣可见第 3 册）；完结日作者于苏州同里古镇直播'],
    ],
    [0.16, 0.84])

h1(story, '二、核心设定与金手指（L1）')
bullets(story, [
    '<b>世界观</b>：赤色流星致人类文明停滞（再造不出火箭、核弹、汽车），文明金字塔坍塌；灰界随流星降临，如镜面后的鬼魅倒影侵蚀现实。九大界域各自为政，界域外是灰雾与灾厄。',
    '<b>金手指（机制化的诗意）</b>：主角陈伶（京城剧院实习编导）穿越后体内寄宿"观众"，须以表演维系期待值求生（第 313 章：期待值 68% 时再努努力就能多出一条命）；觉醒遗落的"戏神道"。晋阶条件与世界规则绑定：在无人问津的舞台上完成一次掌声鸣动的落幕。',
    '<b>组织与代称</b>：黄昏社（收殓队，入殓将死的界域君）、通天塔、时代存档与九位博士之谜；扑克代号体系（陈伶=红心6、师姐=梅花K、白也=红心Q），红王世系（陈伶为六代红王）。',
    '<b>文化工程</b>：戏曲唱段除自创《安魂谣》外全部取自真实传统曲目；戏曲程式（生旦净末丑、唱念做打）转译为能力体系。"观众"设定源于作者对"被注视"的真实体验——双重视看打破第四面墙。',
])
table_block(story, '表 2-1 卷结构：界域篇章制（证据：实体书目录、正文引用、卷末总结四）',
    ['卷', '主场', '功能'],
    [
        ['第一卷', '第三区', '穿越、"观众"觉醒、弟弟陈宴之死、入黄昏社'],
        ['第二卷 绘朱颜', '红尘界域系', '四篇章（滚滚红尘/柳镇织命/戏道古藏/红尘拍卖）：拜师学艺+界域故事'],
        ['极光界域卷', '极光城', '界域完整慢写：风筝意象、极光君献祭、陈伶独留晋升战'],
        ['红尘界域卷', '红尘', '解放红尘、苏知微重建线（柳树告别）'],
        ['第四卷（漂泊卷）', '融合派、南海、鬼嘲深渊', '主动降爽：居无定所、被误解，蜕变为六代红王'],
        ['后续卷', '天枢等界域', '侧重点从界域转故事线，界域覆灭提速'],
    ],
    [0.20, 0.26, 0.54])

h1(story, '三、节奏与爽点频谱（L3）')
table_block(story, '表 3-1 四条情绪引擎',
    ['引擎', '供给什么', '证据'],
    [
        ['机制爽', '期待值=命数；晋阶条件机制化（无人问津的舞台+掌声落幕）', '第 313 章原文'],
        ['中式怪诞', '红衣戏子立于灰暗废土的视觉反差；戏鬼、灰界、古藏的东方怪谈氛围', '番茄简介、读者长评'],
        ['文明哀悼', '界域覆灭的离别美学（风筝、柳树、入殓仪式）；人命渺如尘埃，人类灿若星辰', '第 145/1033 章原文、环球人物采访'],
        ['反转发条', '环环相扣的反转推进', '读者长评'],
    ],
    [0.13, 0.47, 0.40])
h2(story, '3.1 更新节奏：日更一章为何还能蝉联巅峰')
bullets(story, [
    '对比同作者《斩神》爆点日五更：本书每天仅更一章，卡文即停更整理大纲（世界日报采访）。',
    '单章钩子密度从章节标题即可见：审判 / 你也是个灾厄 / 杀戮舞曲 / 他下班了 / 你们谁能惩戒我——标题全部是悬念句或反问句，单章即钩子。',
    '章法样本：第 532 章三根手指三条信息（信息章法，一次喂三条钩子）；第 145 章风筝章（意象章法，大事件前纯意象蓄力，把界域覆灭的伦理两难放进孩子们的风筝）。',
    '（推断）低频高密策略的适用前提：机制爽可累积——期待值是明示数值，读者带着进度条追更，数值化进度感补偿了更新量。',
])
h2(story, '3.2 界域笔墨经济学与降爽卷（作者一手方法论）')
bullets(story, [
    '<b>笔墨经济学</b>（卷末总结四）：前期界域（极光、红尘）花大量笔墨构建界域、写接地气的小角色的精神世界与爱恨情仇，让界域立体；后期若每个界域覆灭都这样写，写一千万字也写不完、一定被说太水，故界域覆灭提速、视角从城中人转故事线本身。指令：长篇的地图笔墨预算必须前置进大纲。',
    '<b>降爽卷</b>：第四卷陈伶离开黄昏社、融合派覆灭、被南海界域扫地出门、回归鬼嘲深渊——居无定所、受屈无人出头。作者逻辑：戏神从一开始就是宏大而悲壮的故事，一个所向匹敌的主角会让其他人的牺牲显得弱小愚蠢、打碎主基调。风险自认：肯定成为一部分读者弃书的理由。',
    '<b>对冲手段（推断）</b>：蜕变预告（成为六代红王的目标感）+ 红王世系与时代存档的长线悬念 + 卷末明示"第五卷不会这么压抑"。指令：压抑卷限一卷，卷首配预告性钩子与数值进度感。',
])
table_block(story, '表 3-2 雷点与风险清单',
    ['风险', '证据', '对我们的指令'],
    [
        ['降爽卷弃书', '作者自认第四卷弃书风险', '压抑卷限一卷，卷首给蜕变预告'],
        ['无细致大纲', '卷末总结自白没有细致大纲', '悲壮史诗更需台账纪律（progress.md 伏笔登记）'],
        ['感情戏短板', '斩神期作者自嘲感情戏是弱项', '情感线走克制留白（伞下回眸式）'],
        ['群像过载', '九大界域+黄昏社+扑克全员', '群像按功能位轮转，每卷主推 2-3 人'],
    ],
    [0.18, 0.38, 0.44])

h1(story, '四、人物公式（L5）')
table_block(story, '表 4-1 主角公式：陈伶',
    ['维度', '内容'],
    [
        ['身份', '表：京城剧院实习编导（穿越者）、黄昏社红心6；里：六代红王'],
        ['欲望链', '求生（维系期待值）→ 找回时代真相 → 改写注定的悲剧 → 扛起黄昏社（三层升格：机制生存、真相、使命）'],
        ['障碍', '文明停滞的世道 + 灰界灾厄 + 浮生绘追踪 + 自身灭世力量失控 + 注定悲剧的命运结构'],
        ['反差', '冷静与疯魔并存；台上万人瞩目的主角、台下挣扎求生的凡人；被双重视看（台内观众+台外读者）'],
        ['金手指耦合', '表演既是战斗系统又是生命线：期待值即命数，升级条件与世界规则一体'],
    ],
    [0.18, 0.82])
h2(story, '4.1 容器公式：戏子=神道载体（对照斩神的病人=神明）')
body(story, '<b>公式：行当原型（生旦净末丑、唱念做打）+ 世界规则化（程式即能力、落幕即晋阶）+ 元层（观众=读者）。</b>与斩神容器的三点进化：其一，照护关系进化为表演机制（可数值化）；其二，神话拼盘深挖为单一文化深井（戏曲真实曲目+自创一首安魂谣）；其三，读者从门外被写进世界观。移植度高：任何行将消亡的传统技艺皆可套此公式（非遗×怪谈×废土），关键纪律同斩神——程式必须来自真实戏曲逻辑，真九假一，真实文化给怪谈供血。')
table_block(story, '表 4-2 群像工程与功能位',
    ['机制/功能位', '代表', '作用'],
    [
        ['扑克代号体系', '红心6陈伶、梅花K师姐、红心Q白也', '身份面具+记忆锚点，大编制群像可追踪'],
        ['界域君制（节气角色）', '极光君、红尘君、无极君楼羽、苏知微', '每卷自带倒计时与悲壮底色；后期切君视角承担群像叙事'],
        ['亲情牺牲位', '陈宴（弟弟）', '第一卷立刀子基调：为让哥哥活下去而牺牲'],
        ['立场对手', '韩蒙（兵神道）、孤渊', '承载文明级两难（彩鸢章：你的正确与我何干），冲突由立场差而非善恶驱动'],
        ['师门线', '梅花K、宁如玉、丑角（叛徒）', '温情与追杀双供给'],
        ['理性见证位', '楚牧云', '见证主角暴走史，降爽卷的担忧视角'],
        ['献祭/告别者', '极光君、苏知微（柳树告别姚清）', '文明哀悼的人身化：变成你画中的模样'],
        ['反派美学位', '楼羽（贤者之石、碳基转硅基屠界）', '神明下凡式的压迫感'],
    ],
    [0.20, 0.28, 0.52])

h1(story, '五、对我们写作的直接指令')
table_block(story, '表 5-1 模块库转化指令（供 novel-worldview / novel-outline / novel-characters 使用）',
    ['编号', '指令', '去向'],
    [
        ['X1', '机制设计先于金手指：升级条件必须从世界观规则里长出来（落幕晋阶、期待值命数），不挂系统外挂', 'novel-worldview'],
        ['X2', '元层借用要克制：读者即观众只作底色不点破，打破第四面墙的收益在共时不在说破', 'novel-worldview / style'],
        ['X3', '长篇成本账前置：前两个地图慢写立口碑，其后地图降笔墨转主线，防写一千万字写不完', 'novel-outline'],
        ['X4', '降爽卷预埋钩子对冲：压抑卷限一卷，配蜕变预告+数值进度感', 'novel-volume'],
        ['X5', '意象章法：大事件前安排一章纯意象蓄力（风筝章之于极光城覆灭），情绪章是爆点章的放大器', 'novel-chapter'],
        ['X6', '主角欲望链首层必须是机制性生存（数值化进度条），第一章就让读者拿到', 'novel-characters / opening'],
        ['X7', '大编制群像先建代号体系（牌面/职级/辈分），登记表按功能位+主推卷位两列管理', 'novel-characters'],
        ['X8', '每个地图配一个节气角色（界域君式倒计时人物），其状态变化即卷的推进刻度', 'novel-volume'],
        ['X9', '立场对手至少一个：写卷纲时先写他为什么是对的，再写冲突', 'novel-outline'],
        ['X10', '非遗/技艺容器真九假一：程式取真实传统，自创部分显性标注', 'novel-worldview'],
    ],
    [0.08, 0.72, 0.20], align_center_cols=[0])

h1(story, '六、口径与待补项')
bullets(story, [
    '信息来源：番茄小说作品页与目录、百度百科、豆瓣/读书网实体书目录（第 3 册）、正文引用片段（第 145/313/532/1033 章）、作者卷末总结（四）、新浪完结报道（2026-04-30）、世界日报/环球人物（2026-05）、中国作家网（2025-01）、橙瓜、69 短剧资讯、Bangumi、番茄页读者长评。',
    '浅拆局限：L2 黄金三章细拆、L4 桥段库、L6 文风画像需原文；补原文后按技能 Pipeline 从 L2 起跑，拆书进度.md 已留断点。',
    '产物清单：拆书进度.md（状态层）、拆书报告.md（本报告源）、节奏与爽点.md（L3）、人物拆解.md（L5）。',
])

doc = TocDocTemplate(OUT_BODY, pagesize=A4,
                     leftMargin=LM, rightMargin=RM, topMargin=TM, bottomMargin=BM,
                     title='《我不是戏神》拆书报告',
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
