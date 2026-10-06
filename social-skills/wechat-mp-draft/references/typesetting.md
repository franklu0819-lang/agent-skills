# 公众号正文排版规范（微信编辑器适配）

## 编辑器硬约束（违反必翻车）

- **只认内联样式**：`<style>` 标签、`class`、`id`、外链 CSS 全部被过滤——每个元素必须带 `style="…"` 属性。
- 用 `section` 代替 `div`（官方推荐，兼容最好）；放心用的标签：section / p / span / strong / em / b / i / u / blockquote / ul / ol / li / h2 / h3 / h4 / img / a / hr / br。
- **正文图片必须用微信域 URL**（uploadimg 返回的 `mmbiz.qpic.cn`）：外链图在部分客户端显示为「此图片来自微信公众平台」占位。本地路径交给 mp_submit.py 自动上传替换。
- 不要表格（手机端挤压不可读）；代码块样式被削得只剩底色，多行代码建议改用截图。
- 视频/小程序卡片等富媒体接口不支持，别写进 content。

## 样式基线（浅色正文底，品牌深蓝系）

正文底是白/浅灰。brand.md 的青蓝 `#82DEF5` 是给深底用的——浅底上对比只有约 1.9:1，**正文强调一律用深青蓝**；金色太浅不能作浅底文字色，只作装饰线。

| 元素 | 内联样式 |
|---|---|
| 根 section | `font-size:15px;color:#333333;line-height:1.75;letter-spacing:0.5px;text-align:justify;` |
| p | `margin:0 0 20px;` |
| h2 小标题 | `margin:36px 0 18px;font-size:17px;font-weight:700;color:#0B3355;border-left:4px solid #F2D183;padding-left:12px;line-height:1.5;` |
| h3 | `margin:28px 0 14px;font-size:16px;font-weight:700;color:#17547D;line-height:1.5;` |
| h4 | `margin:24px 0 12px;font-size:15px;font-weight:700;color:#17547D;` |
| strong | `color:#17547D;font-weight:700;` |
| em | `font-style:normal;color:#17547D;`（微信斜体中文发虚，用色代斜） |
| 行内 code | `background:#F2F4F7;color:#C7254E;font-size:13px;padding:2px 6px;border-radius:3px;font-family:Menlo,Consolas,monospace;` |
| a | `color:#576B95;text-decoration:none;`（微信标准链色） |
| ul / ol | `margin:0 0 20px;padding-left:22px;`（ol 26px） |
| li | `margin:0 0 10px;` |
| 引用 section | `margin:0 0 20px;padding:14px 16px;background:#F7F9FB;border-left:3px solid #F2D183;border-radius:0 4px 4px 0;` |
| 引用内 p | `margin:0;font-size:14px;color:#666666;line-height:1.7;` |
| figure | `margin:0 0 20px;text-align:center;` |
| img | `width:100%;height:auto;display:block;border-radius:4px;` |
| 图注 | `margin:8px 0 0;font-size:13px;color:#888888;` |
| hr | `border:none;border-top:1px dashed #E0E0E0;margin:28px 0;` |

小标题编号优先用「01 / 02」式样写进标题文本（呼应品牌横幅）；typeset.py 产出的 HTML 已按本基线注入内联样式，手动微调保持同一口径。

## 受限 Markdown 子集（typeset.py 的输入）

只用以下语法，其余（表格、嵌套列表、脚注、H1）不支持——写了会按普通段落渲染并告警：

```markdown
## 二级标题（小标题）
### 三级标题
普通段落，**加粗**、*强调*、`行内代码`、[链接文字](https://…)。
> 引用行（连续多行合并为一个引用块）
- 列表项
1. 有序列表项
![图注文字](本地图片路径或URL)
---
```

- 一段写一行（段内换行会被拼接）；图片行独立成行，alt 非空时自动生成居中图注。
- `# H1` 不要写——文章标题走草稿表单的 title 字段，不进正文。
- 本地图路径原样保留在 `src` 里，mp_submit.py 提交时自动上传替换为微信域 URL。

## 排版流程与自检

1. 从 copy.md 抽正文（去掉标题候选/摘要/头条候选等非正文区），按受限子集写 `正文.md`；
2. 跑 `scripts/typeset.py 正文.md -o 正文.html`，脚本报告字符数（>19000 预警，上限 2 万）；
3. 浏览器打开 HTML 目检：样式生效（内联）、图片路径正确、无 md 语法残留（`**`、`> ` 等字面量）；
4. 手动微调直接改 HTML，保持内联样式形态，再组装 draft.json 提交。
