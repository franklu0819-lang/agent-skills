#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""标题/摘要长度校验（汉字当量口径，与 social-cards 技能一致）。

当量口径：east_asian_width 为 F/W（汉字、全角标点）记 1，其余（字母/数字/半角
符号）记 0.5。公众号文章标题上限 32 当量——微信按汉字 2 字符/英文 1 字符计、
上限 64 字符，当量 ×2 恰好对齐；20 当量是贴图标题（social-cards）的版面限制，
不适用于文章标题（2026-10-08 勘误）。

用法：
    python3 len_check.py title "标题一" "标题二"        # 公众号标题，默认 ≤32 当量
    python3 len_check.py title --limit 30 "头条标题"    # 自定义上限（头条标题 5–30 字）
    python3 len_check.py digest "摘要文字"              # 摘要，默认 ≤120 当量
    python3 len_check.py file 文案.md                   # 自动抽取 标题候选/摘要 段校验

file 模式约定（文案.md 既定结构，旧名 copy.md 同样适用）：`## 标题候选` 段每行
`1. （手法）标题` 按 32 当量；`## 头条标题候选` 段按 30 当量；`## 摘要` 段整段按
120 当量。标题行的行尾当量注记（`—— 17.0 当量` / `（17.0 当量）`）自动剥离，
不计入长度。
退出码：0 全部通过；1 有超限或什么都没校验到。结果走 stdout，错误走 stderr。
"""
import re
import sys
import unicodedata


def han_eq(s):
    return sum(1.0 if unicodedata.east_asian_width(c) in ("F", "W") else 0.5 for c in s)


def check(kind, text, limit):
    text = text.strip()
    eq = han_eq(text)
    ok = eq <= limit
    print("[%s] %s：当量 %.1f / %.0f（字符 %d）「%s」"
          % ("OK" if ok else "OVER", kind, eq, limit, len(text), text))
    return ok


def section(md, keyword, exclude=None, require=None):
    """取包含 keyword 的 ## 小节正文（到下一个 ## 级标题为止）。

    只认恰好二级（## ）：### 子标题属于本节内容，不截断。
    """
    lines = md.splitlines()
    for i, ln in enumerate(lines):
        s = ln.strip()
        if re.match(r"^##(?!#)", s) and keyword in s:
            if exclude and exclude in s:
                continue
            if require and require not in s:
                continue
            body = []
            for ln2 in lines[i + 1:]:
                if re.match(r"^##(?!#)", ln2.strip()):
                    break
                body.append(ln2)
            return "\n".join(body)
    return None


def title_lines(sec_text):
    out = []
    for ln in sec_text.splitlines():
        m = re.match(r"^\s*\d+\s*[.、)）]\s*(.+)$", ln)
        if not m:
            continue
        t = re.sub(r"^[（(][^（）()]*[)）]\s*", "", m.group(1).strip())
        # 行尾当量注记（「—— 17.0 当量」「（17.0 当量）」）是给人看的，剥离后再校验
        t = re.sub(r"[ \t]*[——-]+[ \t]*\d+(?:\.\d+)?\s*当量$", "", t)
        t = re.sub(r"[ \t]*[（(]\d+(?:\.\d+)?\s*当量[)）]$", "", t)
        t = t.replace("**", "").strip()
        if t:
            out.append(t)
    return out


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1
    mode = args[0]
    results = []

    if mode == "title":
        rest = args[1:]
        limit = 32.0
        if "--limit" in rest:
            k = rest.index("--limit")
            if k + 1 >= len(rest):
                print("title 模式 --limit 需要一个数值参数", file=sys.stderr)
                return 1
            limit = float(rest[k + 1])
            rest = rest[:k] + rest[k + 2:]
        if not rest:
            print("title 模式需要至少一个标题", file=sys.stderr)
            return 1
        results = [check("标题 %d" % (k + 1), t, limit) for k, t in enumerate(rest)]

    elif mode == "digest":
        text = " ".join(args[1:]).strip()
        if not text:
            print("digest 模式需要摘要文字", file=sys.stderr)
            return 1
        results = [check("摘要", text.replace("**", "").replace("`", ""), 120.0)]

    elif mode == "file":
        if len(args) < 2:
            print("file 模式需要文章 md 路径（文案.md / copy.md）", file=sys.stderr)
            return 1
        with open(args[1], encoding="utf-8") as f:
            md = f.read()
        found = False
        sec = section(md, "标题候选", exclude="头条")
        if sec is not None:
            ts = title_lines(sec)
            if ts:
                found = True
                results += [check("公众号标题 %d" % (k + 1), t, 32.0) for k, t in enumerate(ts)]
        sec = section(md, "标题候选", require="头条")
        if sec is not None:
            ts = title_lines(sec)
            if ts:
                found = True
                results += [check("头条标题 %d" % (k + 1), t, 30.0) for k, t in enumerate(ts)]
        sec = section(md, "摘要")
        if sec is not None:
            text = re.sub(r"[*`>]", "", sec)
            text = re.sub(r"^\s*\d+\s*[.、)）]\s*", "", text, flags=re.M)  # 列表式摘要的序号
            text = re.sub(r"\s+", "", text)  # 换行/空格不计当量
            if text:
                found = True
                results.append(check("摘要", text, 120.0))
        if not found:
            print("file 模式：文章 md 里没有找到 标题候选/头条标题候选/摘要 任一段（## 级标题）",
                  file=sys.stderr)
            return 1

    else:
        print("未知模式：%s（可用 title / digest / file）" % mode, file=sys.stderr)
        return 1

    over = [r for r in results if not r]
    print("== %d 项校验，%d 项超限 ==" % (len(results), len(over)))
    return 1 if over else 0


if __name__ == "__main__":
    sys.exit(main())
