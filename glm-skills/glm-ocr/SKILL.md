---
name: glm-ocr
description: "智谱 GLM-OCR 文档解析：图片/PDF/URL 转 Markdown，中英日韩等多语言，手写体、印章、代码、复杂表格（直出 HTML）、公式均可，可返回布局明细与坐标，单图≤10MB、PDF≤50MB/100页。Use whenever the user wants OCR、文字识别、图片转文字、识别图里的字、截图上的字读出来、PDF转文字/Markdown、表格识别、手写体识别、发票/票据/证件识别、扫描件转文字、文档数字化、RAG 文档解析 —— 对本地图片、PDF 或图片 URL 做精确文字提取就用本技能。Also triggered as /glm-ocr。"
---

# GLM-OCR 文档解析（智谱 layout_parsing）

一句话：跑本技能 `scripts/ocr.py`（相对本 SKILL.md 目录）调智谱 `POST /api/paas/v4/layout_parsing`（模型 `glm-ocr`，0.9B 参数 OmniDocBench V1.5 SOTA），把图片/PDF 精确转写为 Markdown——表格直出 HTML、公式原样、印章手写都认。

接口文档：https://docs.bigmodel.cn/api-reference/模型-api/文档解析 （模型介绍：https://docs.bigmodel.cn/cn/guide/models/vlm/glm-ocr ）

## 什么时候用本技能 vs 直接视觉看图

- **用本技能**：整页/整篇文档转写、多页 PDF、需要精确排版（表格→HTML、阅读顺序、公式）、扫描件/照片/手写/印章、结果要落盘成 .md 入库（RAG、论文、归档）。
- **直接视觉看图**：单张图上问一两个信息（"这图里价格是多少"），不需要逐字转写。两者可组合：先视觉定位，再对本技能的输出做检索。

## 前置

- API Key：`ZHIPU_API_KEY`（[bigmodel.cn](https://bigmodel.cn/usercenter/proj-mgmt/apikeys) 右上角个人中心「API Keys」页，形如 `<32位hex>.<16位hex>`；glm- 家族统一只认此变量）。解析顺序：`--api-key` → `ZHIPU_API_KEY` 环境变量 → `~/.zshrc` 同名 export 行（与 glm-tts / glm-asr 同链）。缺失时如实提示，**绝不代填、绝不把 key 写入任何落盘产物**；**GLM Coding Plan 订阅 Key 不含本接口**，需开放平台常规 API Key。
- 本地文件按 magic bytes 自动判型（PNG/JPG/PDF），URL 直传免上传；open.bigmodel.cn 国内节点直连，不走本地代理。

## 标准流程：直接跑脚本

```bash
# 单图：stdout 直接出 Markdown（进度/用量走 stderr）
python3 scripts/ocr.py scan.png

# 存成 .md；PDF 只识别第 3-10 页
python3 scripts/ocr.py doc.pdf -o doc.md --pages 3-10

# 批量：目录下每张图生成同名 .md（-o 为已存在目录；URL 目标取 basename，同名自动加 -2 序号防覆盖）
python3 scripts/ocr.py *.png -o outdir/

# 完整响应 JSON（含布局明细/坐标/可视化图 URL）+ 元素截图信息
python3 scripts/ocr.py table.png --json raw.json --crop --visualize

# 图片或 PDF 的 URL 直传（官方提速建议：URL 优于 base64 上传）
python3 scripts/ocr.py https://example.com/paper.pdf
```

常用参数：

| 选项 | 说明 | 默认 |
|---|---|---|
| `-o PATH` | 单文件=输出 md 路径；多文件=输出目录（缺省则存源文件旁 `<名>.md`；URL 目标取 basename 落当前目录；同名自动加 `-2` 序号防覆盖；写盘失败时单文件结果改道 stdout 保住已计费内容） | stdout（单文件） |
| `--json PATH` | 完整响应 JSON 另存（仅单文件） | 无 |
| `--pages N` / `N-M` | PDF 起止页，从 1 起、含端点；作用于所有目标，图片目标自动忽略并 stderr 提示 | 全部 |
| `--crop` | `return_crop_images`：返回每元素截图信息 | 关 |
| `--visualize` | `need_layout_visualization`：返回布局可视化图 URL | 关 |
| `--timeout N` | 单次请求超时秒数 | 300 |
| `--api-key KEY` | API Key（默认自动解析，见前置） | 自动 |
| `--dry-run` | 只打印请求元信息不发送 | — |

退出码：0 成功；1 有失败项（缺 key、文件不存在/超限、网络失败、API 报错）。错误全走 stderr，stdout 只有识别结果。

## 输出解读

- `md_results`：识别出的 Markdown 正文（脚本 stdout / `-o` 落盘的就是它）——表格已是 HTML `<table>`，可直接入网页或数据处理。
- `usage`：token 统计，stderr 展示；`data_info.num_pages` 为 PDF 页数。
- `--json` 里的 `layout_details`（按页分组）：每元素含 `label`（`text`/`table`/`formula`/`image`）、归一化坐标 `bbox_2d` `[x1,y1,x2,y2]`（0-1，乘图片宽高得像素）、`content`（文本/表格 HTML/图片 URL）。要按坐标取元素、或只抽表格/公式时用它，不要正则解析 md_results。
- `--visualize` 的 `layout_visualization`：每页一张框线标注图 URL，核对版式切分对不对时看它。

## 限制与提速（官方口径）

- 单图 ≤10MB（PNG/JPG），PDF ≤50MB、≤100 页；超出先拆分。官方吞吐参考：PDF 约 1.86 页/秒、图片约 0.67 张/秒（单并发）。
- 大 PDF 提速：`--pages` 拆段并行调用（每段独立请求）；URL 传入比 base64 上传快。
- 百页级任务把 `--timeout` 调大（同步接口，100 页约 1 分钟量级）。

## 报错速查

- 缺 key / `HTTP 401` → Key 未配置或无效（**GLM Coding Plan 订阅 Key 调不了本接口**）；误用火山 `ARK_API_KEY`/`ARK_SPEECH_API_KEY`（旧名 `SPEECH_API_KEY`）也会 401，本接口只认智谱开放平台 Key。
- `HTTP 429` → 并发/频率超限，批量时降低并行度或串行重试。
- 响应 `error.code` 为参数类错误 → 检查文件是否损坏、是否超大小限制、PDF 是否超 100 页；脚本对本地文件已内置「data URI 被拒→纯 base64」自动降级重试（大小类错误不触发降级），仍失败则上报错误原文。
- 连接层错误与 HTTP 5xx → 脚本共自动尝试 3 次（间隔 3 秒）；4xx 业务错误立即报出不重试。

## 实测记录（2026-10-07）

- **base64 data URI 格式实测可用**（`data:image/png;base64,...`），本地文件主路径直接工作；「data URI 被拒→纯 base64」降级为兜底（monkeypatch 模拟 4xx file 格式错误验证可达）。
- 中文样张（PIL 渲染 Hiragino 36px）全文识别无误；表格图直出 `<table>` HTML，`layout_details` 的 label 序列 `['text','table']` 与版式对应。
- 真实发票 PDF（Cloudflare，1 页）字段识别准确；21 页中文报告全量 tokens=73281、`--pages 2-3` 只取 2 页 tokens=7986——**成本参照：约 3500 tokens/页，全量 21 页约 0.015 元**，批量可按此估算。
- URL 直传（官方示例图）免上传可用；批量不同目录同名文件生成 `x.png.md` / `x.png-2.md` 不覆盖，结束打汇总行。
- 空 md_results（纯图像页）不报错，stderr 提示后正常退出。

## 纪律

- 计费 0.2 元/百万 tokens（输入输出同价，1 元 ≈ 2000 张 A4 扫描图）。批量前先估量：拿 1-2 个样本试跑确认效果与耗时，再放全量。
- 识别结果是模型输出：关键数字、日期、金额等入正式产物前抽查核对，不确定处标注而非猜测。
- 不为"完美转写"对同一文件反复重试烧额度；效果不满意时优先换更清晰的扫描件。
