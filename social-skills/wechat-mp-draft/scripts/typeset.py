#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""受限 Markdown → 公众号正文 HTML（内联样式基线见 references/typesetting.md）。

用法：
    python3 typeset.py 正文.md -o 正文.html   # 写文件（HTML 片段，无 <html> 外壳）
    python3 typeset.py 正文.md                # 打到 stdout

支持子集：## ### #### 标题、段落、**加粗**、*强调*、`行内代码`、[链接](url)、
独立成行的 ![图注](图片路径)、> 引用（连续行合并一块）、- 与 1. 列表、--- 分隔线。
其余语法（表格、H1、缩进块）按普通段落渲染并告警。一段请写一行（段内换行被拼接）。
本地图片路径原样保留在 src 里，交给 mp_submit.py 上传替换为微信域 URL。
"""
import re
import sys

S = {
    "root": "font-size:15px;color:#333333;line-height:1.75;letter-spacing:0.5px;text-align:justify;",
    "h2": "margin:36px 0 18px;font-size:17px;font-weight:700;color:#0B3355;border-left:4px solid #F2D183;padding-left:12px;line-height:1.5;",
    "h3": "margin:28px 0 14px;font-size:16px;font-weight:700;color:#17547D;line-height:1.5;",
    "h4": "margin:24px 0 12px;font-size:15px;font-weight:700;color:#17547D;",
    "p": "margin:0 0 20px;",
    "strong": "color:#17547D;font-weight:700;",
    "em": "font-style:normal;color:#17547D;",
    "code": "background:#F2F4F7;color:#C7254E;font-size:13px;padding:2px 6px;border-radius:3px;font-family:Menlo,Consolas,monospace;",
    "a": "color:#576B95;text-decoration:none;",
    "ul": "margin:0 0 20px;padding-left:22px;",
    "ol": "margin:0 0 20px;padding-left:26px;",
    "li": "margin:0 0 10px;",
    "quote": "margin:0 0 20px;padding:14px 16px;background:#F7F9FB;border-left:3px solid #F2D183;border-radius:0 4px 4px 0;",
    "quote_p": "margin:0;font-size:14px;color:#666666;line-height:1.7;",
    "figure": "margin:0 0 20px;text-align:center;",
    "img": "width:100%;height:auto;display:block;border-radius:4px;",
    "figcaption": "margin:8px 0 0;font-size:13px;color:#888888;",
    "hr": "border:none;border-top:1px dashed #E0E0E0;margin:28px 0;",
}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def inline(s):
    s = esc(s)
    # 行内代码先摘出为占位符，避免内容里的 * [ 被 加粗/强调/链接 正则二次匹配
    codes = []

    def _stash(m):
        codes.append(m.group(1))
        return "\x00%d\x00" % (len(codes) - 1)

    s = re.sub(r"`([^`]+)`", _stash, s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)",
               lambda m: '<a href="%s" style="%s">%s</a>' % (m.group(2), S["a"], m.group(1)), s)
    s = re.sub(r"\*\*([^*]+)\*\*",
               lambda m: '<strong style="%s">%s</strong>' % (S["strong"], m.group(1)), s)
    # 强调内容首尾须非空白：*强调* ✓；数学乘号「2 * 3 * 4」的内容是「 3 」（首尾空白）不吞
    s = re.sub(r"\*(\S(?:[^*\n]*\S)?)\*",
               lambda m: '<em style="%s">%s</em>' % (S["em"], m.group(1)), s)
    s = re.sub(r"\x00(\d+)\x00",
               lambda m: '<code style="%s">%s</code>' % (S["code"], codes[int(m.group(1))]), s)
    return s


def render(md_text):
    lines = md_text.splitlines()
    out, para, warned = [], [], set()

    def warn_once(msg):
        if msg not in warned:
            warned.add(msg)
            print("[typeset] %s" % msg, file=sys.stderr)

    def flush_para():
        if para:
            text = inline("".join(para).strip())
            if text:
                out.append('<p style="%s">%s</p>' % (S["p"], text))
            para.clear()

    i, n = 0, len(lines)
    while i < n:
        t = lines[i].strip()

        if not t:
            flush_para()
            i += 1
            continue

        m = re.match(r"^(#{2,4})\s+(.*)$", t)
        if m:
            flush_para()
            lvl = len(m.group(1))
            out.append('<h%d style="%s">%s</h%d>' % (lvl, S["h%d" % lvl], inline(m.group(2)), lvl))
            i += 1
            continue

        if re.match(r"^-{3,}$", t):
            flush_para()
            out.append('<hr style="%s"/>' % S["hr"])
            i += 1
            continue

        m = re.match(r"^!\[([^\]]*)\]\(([^)\s]+)\)\s*$", t)
        if m:
            flush_para()
            alt, src = m.group(1).strip(), m.group(2)
            fig = '<figure style="%s"><img src="%s" style="%s"/>' % (S["figure"], src, S["img"])
            if alt:
                fig += '<figcaption style="%s">%s</figcaption>' % (S["figcaption"], inline(alt))
            fig += "</figure>"
            out.append(fig)
            i += 1
            continue

        if t.startswith("!["):
            flush_para()
            warn_once("图片行格式不对（应为 ![图注](路径) 独立成行，路径暂不支持空格），按普通段落渲染")
            para.append(t + " ")
            i += 1
            continue

        if t.startswith(">"):
            flush_para()
            quotes = []
            while i < n and lines[i].strip().startswith(">"):
                q = lines[i].strip().lstrip(">").strip()
                if q:
                    quotes.append(inline(q))
                i += 1
            if quotes:  # 全空 > 行不产出空引用盒
                body = "".join('<p style="%s">%s</p>' % (S["quote_p"], q) for q in quotes)
                out.append('<section style="%s">%s</section>' % (S["quote"], body))
            continue

        if re.match(r"^[-*]\s+\S", t):
            flush_para()
            items = []
            while i < n:
                s2 = lines[i].strip()
                if not s2:
                    # 松散列表：空行后若仍是同类列表项则并入同一列表，避免编号重置
                    j = i + 1
                    while j < n and not lines[j].strip():
                        j += 1
                    if j < n and re.match(r"^[-*]\s+\S", lines[j].strip()):
                        i = j
                        continue
                    break
                m2 = re.match(r"^[-*]\s+(.*)$", s2)
                if not m2:
                    break
                items.append('<li style="%s">%s</li>' % (S["li"], inline(m2.group(1))))
                i += 1
            out.append('<ul style="%s">%s</ul>' % (S["ul"], "".join(items)))
            continue

        if re.match(r"^\d+[.、]\s+\S", t):
            flush_para()
            items = []
            while i < n:
                s2 = lines[i].strip()
                if not s2:
                    j = i + 1
                    while j < n and not lines[j].strip():
                        j += 1
                    if j < n and re.match(r"^\d+[.、]\s+\S", lines[j].strip()):
                        i = j
                        continue
                    break
                m2 = re.match(r"^\d+[.、]\s+(.*)$", s2)
                if not m2:
                    break
                items.append('<li style="%s">%s</li>' % (S["li"], inline(m2.group(1))))
                i += 1
            out.append('<ol style="%s">%s</ol>' % (S["ol"], "".join(items)))
            continue

        if "|" in t and t.count("|") >= 2:
            flush_para()
            warn_once("疑似表格语法——公众号手机端不可读，已按普通段落渲染，建议改写为列表")
            para.append(t + " ")
            i += 1
            continue

        if t.startswith("# "):
            warn_once("H1 不进正文（标题走草稿表单 title 字段），已按普通段落渲染")
            para.append(t[2:] + " ")
            i += 1
            continue

        if t.startswith("    ") or t.startswith("\t"):
            warn_once("缩进块不支持，按普通段落渲染")

        para.append(t + " ")
        i += 1

    flush_para()
    return '<section style="%s">\n%s\n</section>' % (S["root"], "\n".join(out))


def main():
    args = sys.argv[1:]
    out_path = None
    if "-o" in args:
        k = args.index("-o")
        if k + 1 >= len(args):
            print("[typeset] -o 需要输出路径", file=sys.stderr)
            return 1
        out_path = args[k + 1]
        args = args[:k] + args[k + 2:]
    if len(args) != 1:
        print(__doc__)
        return 1
    with open(args[0], encoding="utf-8") as f:
        md = f.read()
    html = render(md)
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html + "\n")
        print("已写出 %s（%d 字符）" % (out_path, len(html)))
    else:
        sys.stdout.write(html + "\n")
    if len(html) > 19000:
        print("[typeset] HTML %d 字符，逼近公众号正文 2 万字符上限，建议精简" % len(html),
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
