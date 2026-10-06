---
name: wechat-mp-draft
description: 把公众号文章提交到微信公众号草稿箱：正文排版成微信编辑器可用的内联样式 HTML、生成文章封面（2.35:1 首图 / 1:1 次图）、调用公众号 API 上传正文图与封面素材并新建草稿。Use whenever the user wants 提交草稿、传到公众号、发到草稿箱、公众号排版、公众号封面图、把文章发到公众号后台 —— 提到草稿箱、公众号后台提交也触发。硬边界：只到草稿箱，不群发不发布；需要已认证公众号的 AppID/AppSecret（环境变量）与 IP 白名单。
---

# 公众号草稿提交（排版 → 封面 → 草稿箱）

把一篇已成稿的文章（通常是 social-article 技能产出的 `copy.md`）送进公众号草稿箱。四步：拿文章包 → 排版 → 封面 → 提交。

## 前置检查（首次使用必做）

- **凭据**：环境变量 `WECHAT_MP_APPID` / `WECHAT_MP_SECRET`（公众号后台 → 设置与开发 → 基本配置 → 公众号开发信息）。实际配置在 `~/.zshrc`，ZCode 工具 shell 非交互读不到，统一用 `zsh -ic '…'` 调脚本。缺失时如实告知用户配置路径，**绝不代填、绝不把密钥写进任何落盘产物**。
- **IP 白名单**：基本配置 → IP 白名单须包含本机出口 IP（报错 40164 会附上当前出口 IP，加进去即可）。API 默认**直连不走代理**——白名单按出口 IP 校验，走代理必然失配；特殊网络才用 `--proxy` 显式指定。
- **账号权限**：草稿 API 需**已认证**的公众号（未认证报 48001）。

## 第一步：拿文章包

输入是含标题/正文/摘要的文章 md（如 `docs/marketing/<slug>/copy.md`）。没有现成文章时先引导用户走 social-article 技能成稿，不要在本技能里从零写文章。

## 第二步：排版

读 `references/typesetting.md`（微信编辑器硬约束 + 内联样式基线 + 受限 Markdown 子集），然后：

```bash
python3 <本技能目录>/scripts/typeset.py 正文.md -o 正文.html
```

正文 md 只用受限子集；排版产物浏览目检一遍（无 md 语法残留、样式内联、图片路径正确）再进下一步。手动微调直接改 HTML，保持内联样式形态。

## 第三步：封面

读 `references/cover.md`：首图 2.35:1（≥900×383）、次图 1:1 500×500。两条路径——HTML 模板（`assets/templates/`，含中文大字的封面默认走这条，chrome-devtools 截图渲染）或 ark-image-gen AI 生图（纯视觉无字封面，首选 47:20 直出 2.35:1，兜底 21:9 后 PIL 裁切）。

## 第四步：提交

组装 `draft.json`（格式见下），跑一键提交：

```bash
zsh -ic 'python3 <本技能目录>/scripts/mp_submit.py add draft.json --output draft_result.json'
```

```json
{
  "articles": [
    {
      "title": "文章标题（≤20 汉字当量）",
      "author": "飞哥",
      "digest": "≤120 字摘要",
      "content_html_file": "正文.html",
      "cover_image": "cover.png",
      "need_open_comment": 1,
      "only_fans_can_comment": 0,
      "content_source_url": ""
    }
  ]
}
```

脚本自动完成：上传正文里的本地图片（uploadimg，src 替换为微信域 URL）→ 封面上传为永久素材（add_material）→ 硬上限校验（标题 64 / 摘要 120 / 正文 2 万字符）→ draft/add 新建草稿，输出草稿 media_id。本地图片路径相对 draft.json 所在目录解析；已有素材 media_id 时直接填 `"thumb_media_id"` 跳过封面上传。`--dry-run` 只校验并列计划，不联网。

**提交前过目一次**：把标题、摘要、封面路径、长度校验结果列给用户确认（用户说过「直接提交」或该文章包已被用户确认过时跳过）。无人值守且无确认记录时，把待提交要素落盘 `draft.pending-approval.json` 并停在提交步，交付说明写明等待确认什么——草稿箱提交可逆（可删除重提），但首次推送未经确认的内容仍应停一停。

## 交付

- 报告草稿 media_id 与查看路径：mp.weixin.qq.com → 内容与互动 → 草稿箱；建议先「预览」到手机再手动发布/群发。
- 常见报错速查（脚本报错也带提示）：40164 IP 不在白名单（按报错里的 IP 加白）｜40013 AppID 错｜40125 AppSecret 错或已重置｜48001 未认证无权限｜正文图片不显示 = 用了外链图，必须走 uploadimg 本地化。

## 边界与依赖

- **只到草稿箱**：不群发、不发布、不改已发布内容；发布由用户在后台手动完成（需要 API 发布时用户明示再加 freepublish）。
- 密钥纪律：AppSecret 只走环境变量，不写入任何产物/日志/代码；token 每次现取不缓存落盘。
- 依赖：ark-image-gen（AI 封面）、chrome-devtools MCP（模板封面渲染）；上游成稿依赖 social-article 技能。
