#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""微信公众号草稿提交 CLI（纯标准库，无第三方依赖）。

凭据：环境变量 WECHAT_MP_APPID / WECHAT_MP_SECRET（公众号后台 → 设置与开发 →
基本配置 → 公众号开发信息）。密钥只走环境变量，本脚本不落盘、不打日志、
报错不回显完整密钥。实际配置在 ~/.zshrc（仅交互式 zsh 加载）——ZCode 工具
shell 非交互读不到，统一用 zsh -ic 'python3 …/mp_submit.py …' 调用。
另需在后台「基本配置 → IP 白名单」加入本机出口 IP。

网络：默认直连（IP 白名单按出口 IP 校验，走代理会失配）；特殊网络用 --proxy。

子命令：
    add draft.json [--output result.json] [--dry-run]
        一键提交：正文内本地图片 uploadimg → 封面 add_material（永久素材）
        → 硬上限校验 → draft/add 新建草稿。draft.json 格式见 SKILL.md；
        本地图片路径相对 draft.json 所在目录解析。
    uploadimg 图片...          正文图 → mmbiz.qpic.cn URL（打印 JSON 映射）
    material 图片              封面 → 永久素材 media_id
    list [--limit 10]          草稿箱列表（media_id + 标题）
    get <draft_media_id>       查看单篇草稿（打印 JSON）
    delete <draft_media_id>    删除草稿（需 --yes）
    token                      连通性自检（打印掩码 token）

退出码：0 成功；1 失败；2 需确认。结果走 stdout，错误与警告走 stderr。
"""
import argparse
import json
import mimetypes
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request
import uuid

API_BASE = "https://api.weixin.qq.com"
WX_IMG_HOST = "mmbiz.qpic.cn"

# 常见 errcode → 处置提示
HINTS = {
    40013: "AppID 无效：核对 WECHAT_MP_APPID（后台-设置与开发-基本配置）",
    40125: "AppSecret 无效或已重置：后台重新生成后更新 ~/.zshrc 里的 WECHAT_MP_SECRET",
    40164: "IP 不在白名单：把报错信息里的出口 IP 加到 后台-基本配置-IP白名单",
    42001: "access_token 失效：脚本每次现取，重跑即可",
    45009: "接口调用频率超限：稍等再试",
    48001: "账号无此接口权限：草稿 API 需要已认证的公众号",
    40007: "media_id 无效：核对草稿 media_id 或重新上传素材",
    45001: "媒体文件超过大小限制（正文图/封面 ≤10MB）",
}


class WxError(Exception):
    def __init__(self, errcode, errmsg, ctx=""):
        self.errcode = errcode
        msg = "微信接口错误 [%s] %s" % (errcode, errmsg)
        if ctx:
            msg += "（%s）" % ctx
        hint = HINTS.get(errcode)
        if hint:
            msg += "\n  → %s" % hint
        super().__init__(msg)


def warn(msg):
    print("[警告] %s" % msg, file=sys.stderr)


def die(msg, code=1):
    print("[mp_submit] %s" % msg, file=sys.stderr)
    sys.exit(code)


def han_eq(s):
    """汉字当量：全角（F/W）=1，半角=0.5（与 len_check.py / social-cards 同口径）。"""
    return sum(1.0 if unicodedata.east_asian_width(c) in ("F", "W") else 0.5 for c in s)


def http_json(url, data=None, headers=None, proxy=None, timeout=60, retries=2):
    """带网络层重试的 JSON 请求（URLError/超时重试 2 次，间隔 3 秒）。

    默认显式直连（空 ProxyHandler）：不读 http_proxy 等环境变量——IP 白名单
    按出口 IP 校验，静默走环境代理会导致 40164 失配；要代理就用 --proxy 明给。
    """
    if proxy:
        handlers = [urllib.request.ProxyHandler({"http": proxy, "https": proxy})]
    else:
        handlers = [urllib.request.ProxyHandler({})]
    opener = urllib.request.build_opener(*handlers)
    last = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, data=data, headers=headers or {})
            with opener.open(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8", "replace")
                try:
                    return json.loads(raw)
                except ValueError:
                    die("响应不是 JSON（疑似网关/代理错误页）：%s" % raw[:120].replace("\n", " "))
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last = e
            if attempt < retries:
                time.sleep(3)
    die("网络错误（已重试 %d 次）：%s" % (retries, last))


def check_wx(resp, ctx=""):
    err = resp.get("errcode", 0)
    if err:
        raise WxError(err, resp.get("errmsg", ""), ctx)
    return resp


def call_wx(fn, ctx, retries=1):
    """API 层重试：仅 errcode==-1（系统繁忙）重试一次。"""
    for attempt in range(retries + 1):
        try:
            return fn()
        except WxError as e:
            if e.errcode == -1 and attempt < retries:
                time.sleep(3)
                continue
            raise


def credentials():
    appid = os.environ.get("WECHAT_MP_APPID", "")
    secret = os.environ.get("WECHAT_MP_SECRET", "")
    if not appid or not secret:
        die(
            "缺少凭据：环境变量 WECHAT_MP_APPID / WECHAT_MP_SECRET 未配置。\n"
            "  1. 公众号后台 → 设置与开发 → 基本配置 → 公众号开发信息，拿 AppID / AppSecret；\n"
            "  2. 写入 ~/.zshrc：export WECHAT_MP_APPID=… 与 export WECHAT_MP_SECRET=…"
            "（本脚本不落盘任何密钥）；\n"
            "  3. 同页「IP 白名单」加入本机出口 IP；\n"
            "  4. 用 zsh -ic 'python3 …/mp_submit.py …' 调用（非交互 shell 读不到 ~/.zshrc）。"
        )
    return appid, secret


def get_token(appid, secret, proxy):
    """stable_token：不使旧 token 失效，避免多次提交互相顶掉。"""
    body = json.dumps({
        "grant_type": "client_credential",
        "appid": appid,
        "secret": secret,
        "force_refresh": False,
    }).encode("utf-8")
    resp = http_json(
        API_BASE + "/cgi-bin/stable_token", data=body,
        headers={"Content-Type": "application/json"}, proxy=proxy)
    if "access_token" not in resp:
        if resp.get("errcode"):
            check_wx(resp, "获取 access_token")
        die("stable_token 响应异常（无 access_token）：%s"
            % json.dumps(resp, ensure_ascii=False)[:200])
    return resp["access_token"]


def multipart_body(field, filename, data):
    boundary = "wx" + uuid.uuid4().hex
    ctype = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    head = (
        "--%s\r\n"
        'Content-Disposition: form-data; name="%s"; filename="%s"\r\n'
        "Content-Type: %s\r\n\r\n" % (boundary, field, os.path.basename(filename), ctype)
    ).encode("utf-8")
    tail = ("\r\n--%s--\r\n" % boundary).encode("utf-8")
    return head + data + tail, "multipart/form-data; boundary=%s" % boundary


def upload_image(token, path, kind, proxy):
    """kind: img=正文图（uploadimg→url）/ material=永久素材（add_material→media_id）"""
    if not os.path.isfile(path):
        die("找不到图片文件：%s" % path)
    with open(path, "rb") as f:
        data = f.read()
    if len(data) > 10 * 1024 * 1024:
        die("图片超过 10MB 上限：%s（%.1f MB）" % (path, len(data) / 1048576.0))
    if kind == "img":
        url = API_BASE + "/cgi-bin/media/uploadimg?access_token=" + token
    else:
        url = API_BASE + "/cgi-bin/material/add_material?access_token=" + token + "&type=image"
    body, ctype = multipart_body("media", os.path.basename(path), data)

    def _do():
        return http_json(url, data=body, headers={"Content-Type": ctype}, proxy=proxy)

    resp = call_wx(_do, "上传 %s" % os.path.basename(path))
    return check_wx(resp, "上传 %s" % os.path.basename(path))


def post_wx(token, path, payload, proxy, ctx):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    def _do():
        return http_json(
            "%s%s?access_token=%s" % (API_BASE, path, token), data=body,
            headers={"Content-Type": "application/json"}, proxy=proxy)

    resp = call_wx(_do, ctx)
    return check_wx(resp, ctx)


# 单引号/双引号 src 都要抓（手动改 HTML 两种写法都合法）
IMG_SRC_RE = re.compile(r"<img[^>]+?src=([\"'])(.+?)\1", re.I)


def collect_local_images(content_html):
    """按出现顺序去重收集正文图片 src（含单/双引号形态）。"""
    seen, ordered = set(), []
    for _, src in IMG_SRC_RE.findall(content_html):
        if src not in seen:
            seen.add(src)
            ordered.append(src)
    return ordered


def replace_src(content, src, url):
    """带 img 标签上下文替换 src，返回 (新 content, 替换次数)。"""
    pat = re.compile(r"(<img[^>]+?src=([\"']))%s(\2)" % re.escape(src), re.I)
    return pat.subn(lambda m: m.group(1) + url + m.group(2), content)


def validate_article(idx, art, content):
    problems = []
    title = art.get("title", "")
    if not title:
        problems.append("articles[%d] 缺 title" % idx)
    if len(title) > 64 or han_eq(title) > 64:
        problems.append("articles[%d] title 超上限：%d 字符 / %.1f 当量（上限 64）"
                        % (idx, len(title), han_eq(title)))
    if len(art.get("author", "")) > 8:
        problems.append("articles[%d] author 超 8 字符" % idx)
    digest = art.get("digest", "")
    if len(digest) > 120 or han_eq(digest) > 120:
        problems.append("articles[%d] digest 超上限：%d 字符 / %.1f 当量（上限 120）"
                        % (idx, len(digest), han_eq(digest)))
    if len(content) > 20000:
        problems.append("articles[%d] content 超 20000 字符（当前 %d）" % (idx, len(content)))
    return problems


def resolve(base, p):
    return p if os.path.isabs(p) else os.path.join(base, p)


def prepare_articles(spec, base_dir):
    """校验 + 干跑信息收集。返回 (articles_payload, problems, plan)。不联网。"""
    articles = spec.get("articles")
    if not isinstance(articles, list) or not articles:
        die("draft.json 缺少非空 articles 数组")
    problems, plan, payload = [], [], []
    for idx, a in enumerate(articles):
        if a.get("content_html_file"):
            path = resolve(base_dir, a["content_html_file"])
            if not os.path.isfile(path):
                problems.append("articles[%d] content_html_file 不存在：%s" % (idx, path))
                continue
            with open(path, encoding="utf-8") as f:
                content = f.read()
        elif "content_html" in a:
            content = a["content_html"]
        else:
            problems.append("articles[%d] 缺 content_html_file 或 content_html" % idx)
            continue
        m = re.search(r"<body[^>]*>(.*)</body>", content, re.S | re.I)
        if m:
            content = m.group(1)  # 容忍整页 HTML，只取 body 内部

        problems += validate_article(idx, a, content)

        uploads = []
        for src in collect_local_images(content):
            if re.match(r"^https?://", src, re.I):
                if WX_IMG_HOST not in src:
                    warn("articles[%d] 正文含非微信域外链图 %s（部分客户端不显示，建议本地化）"
                         % (idx, src))
                continue
            path = resolve(base_dir, src)
            if not os.path.isfile(path):
                problems.append("articles[%d] 正文图不存在：%s" % (idx, path))
            else:
                uploads.append((src, path))

        thumb = a.get("thumb_media_id", "")
        cover = a.get("cover_image", "")
        cover_path = None
        if not thumb:
            if not cover:
                problems.append("articles[%d] 缺封面：thumb_media_id 或 cover_image 至少一项" % idx)
            else:
                cover_path = resolve(base_dir, cover)
                if not os.path.isfile(cover_path):
                    problems.append("articles[%d] 封面文件不存在：%s" % (idx, cover_path))
                elif os.path.getsize(cover_path) > 10 * 1024 * 1024:
                    problems.append("articles[%d] 封面超 10MB" % idx)

        plan.append({
            "index": idx, "title": a.get("title", ""),
            "images": [p for _, p in uploads], "cover": cover_path,
        })
        payload.append({
            "title": a.get("title", ""),
            "author": a.get("author", ""),
            "digest": a.get("digest", ""),
            "content": content,
            "content_source_url": a.get("content_source_url", ""),
            "need_open_comment": int(a.get("need_open_comment", 1)),
            "only_fans_can_comment": int(a.get("only_fans_can_comment", 0)),
            "_uploads": uploads,
            "_cover_path": cover_path,
            "_thumb": thumb,
        })
    return payload, problems, plan


def cmd_add(args):
    draft_path = os.path.abspath(args.draft)
    base_dir = os.path.dirname(draft_path)
    with open(draft_path, encoding="utf-8") as f:
        spec = json.load(f)
    payload, problems, plan = prepare_articles(spec, base_dir)

    print("== 提交计划 ==")
    for p in plan:
        print("  文章[%d]《%s》：正文图 %d 张，封面 %s"
              % (p["index"], p["title"] or "（无标题）", len(p["images"]),
                 p["cover"] or "（已有 thumb_media_id）"))
    if problems:
        for msg in problems:
            print("  [X] %s" % msg, file=sys.stderr)
        die("校验未通过（%d 项），未联网" % len(problems))

    if args.dry_run:
        print("--dry-run 校验通过，未联网。")
        return

    appid, secret = credentials()
    token = get_token(appid, secret, args.proxy)
    print("access_token 获取成功（%s…）" % token[:8])

    articles_out = []
    for a in payload:
        content = a["content"]
        for src, path in a["_uploads"]:
            resp = upload_image(token, path, "img", args.proxy)
            content, cnt = replace_src(content, src, resp["url"])
            if cnt == 0:
                die("正文图 %s 已上传但 src 替换 0 次（HTML 与校验时不一致？），中止提交" % src)
            print("  正文图已上传：%s → %s" % (path, resp["url"]))
        # 兜底复查：替换后不得残留任何本地路径 src，防止带病提交
        for src in collect_local_images(content):
            if not re.match(r"^https?://", src, re.I):
                die("替换后正文仍残留本地图片 src：%s（中止，未提交）" % src)
        thumb = a["_thumb"]
        if not thumb:
            resp = upload_image(token, a["_cover_path"], "material", args.proxy)
            thumb = resp["media_id"]
            print("  封面已传为永久素材：%s → media_id=%s" % (a["_cover_path"], thumb))
        articles_out.append({
            "title": a["title"], "author": a["author"], "digest": a["digest"],
            "content": content, "content_source_url": a["content_source_url"],
            "thumb_media_id": thumb,
            "need_open_comment": a["need_open_comment"],
            "only_fans_can_comment": a["only_fans_can_comment"],
        })

    resp = post_wx(token, "/cgi-bin/draft/add", {"articles": articles_out},
                   args.proxy, "新建草稿")
    media_id = resp.get("media_id", "")
    result = {"media_id": media_id,
              "view": "mp.weixin.qq.com → 内容与互动 → 草稿箱（建议先预览到手机再发布）"}
    print("草稿创建成功：media_id=%s" % media_id)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print("结果已写入 %s" % args.output)


def cmd_uploadimg(args):
    appid, secret = credentials()
    token = get_token(appid, secret, args.proxy)
    mapping = {}
    for p in args.images:
        resp = upload_image(token, p, "img", args.proxy)
        mapping[p] = resp["url"]
        print("%s → %s" % (p, resp["url"]))
    print(json.dumps(mapping, ensure_ascii=False, indent=2))


def cmd_material(args):
    appid, secret = credentials()
    token = get_token(appid, secret, args.proxy)
    resp = upload_image(token, args.image, "material", args.proxy)
    print(json.dumps({"media_id": resp.get("media_id", ""), "url": resp.get("url", "")},
                     ensure_ascii=False, indent=2))


def cmd_list(args):
    appid, secret = credentials()
    token = get_token(appid, secret, args.proxy)
    resp = post_wx(token, "/cgi-bin/draft/batchget",
                   {"offset": 0, "count": max(1, min(args.limit, 20)), "no_content": 1},
                   args.proxy, "拉取草稿列表")
    items = resp.get("item", []) or []
    print("草稿总数 %s，本页 %d 篇" % (resp.get("total_count", "?"), len(items)))
    for it in items:
        news = (it.get("content") or {}).get("news_item") or []
        titles = " | ".join(n.get("title", "") for n in news)
        print("  %s  %s" % (it.get("media_id", ""), titles))


def cmd_get(args):
    appid, secret = credentials()
    token = get_token(appid, secret, args.proxy)
    resp = post_wx(token, "/cgi-bin/draft/get", {"media_id": args.media_id},
                   args.proxy, "读取草稿")
    print(json.dumps(resp, ensure_ascii=False, indent=2))


def cmd_delete(args):
    if not args.yes:
        print("删除草稿 %s 需要显式确认：加 --yes 重跑。" % args.media_id, file=sys.stderr)
        sys.exit(2)
    appid, secret = credentials()
    token = get_token(appid, secret, args.proxy)
    post_wx(token, "/cgi-bin/draft/delete", {"media_id": args.media_id},
            args.proxy, "删除草稿")
    print("已删除草稿 %s" % args.media_id)


def cmd_token(args):
    appid, secret = credentials()
    token = get_token(appid, secret, args.proxy)
    print("连通正常，access_token=%s…（掩码显示，完整 token 不落盘）" % token[:8])


def main():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--proxy", default=None,
                        help="HTTP 代理（默认直连：IP 白名单按出口 IP 校验，走代理会失配）")
    ap = argparse.ArgumentParser(description="微信公众号草稿提交 CLI（详见文件头注释）",
                                 parents=[common])
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("add", parents=[common], help="一键提交草稿（上传图 + 封面素材 + draft/add）")
    p.add_argument("draft", help="draft.json 路径（本地图片相对该文件所在目录解析）")
    p.add_argument("--output", help="结果 JSON 落盘路径（含 media_id）")
    p.add_argument("--dry-run", action="store_true", help="只校验并列计划，不联网")
    p.set_defaults(fn=cmd_add)

    p = sub.add_parser("uploadimg", parents=[common], help="正文图上传 → mmbiz URL")
    p.add_argument("images", nargs="+")
    p.set_defaults(fn=cmd_uploadimg)

    p = sub.add_parser("material", parents=[common], help="封面上传为永久素材 → media_id")
    p.add_argument("image")
    p.set_defaults(fn=cmd_material)

    p = sub.add_parser("list", parents=[common], help="草稿箱列表")
    p.add_argument("--limit", type=int, default=10)
    p.set_defaults(fn=cmd_list)

    p = sub.add_parser("get", parents=[common], help="查看单篇草稿")
    p.add_argument("media_id")
    p.set_defaults(fn=cmd_get)

    p = sub.add_parser("delete", parents=[common], help="删除草稿（需 --yes）")
    p.add_argument("media_id")
    p.add_argument("--yes", action="store_true")
    p.set_defaults(fn=cmd_delete)

    p = sub.add_parser("token", parents=[common], help="连通性自检")
    p.set_defaults(fn=cmd_token)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
