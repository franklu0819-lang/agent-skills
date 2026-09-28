---
name: ark-image-gen
description: 直连火山方舟 API 用豆包 Seedream 全系模型（5.0 lite / 5.0 flash / 5.0 pro / 4.5 / 4.0）做文生图 / 图生图 / 组图 / 多图层拆分，支持指定画面比例（16:9、9:16 等）与分辨率档位。Use whenever the user wants 生成图片、文生图、画一张图、画个Logo/插画/海报、配图、产品图、图生图、参考图生成、横版/竖版/指定比例的图、一次生成一组图、拆图层/分层/把图里的元素拆出来（PSD 式透明图层）—— 即使没有明说"生成图片"三个字，只要是要一张/一组全新图片或拆层就用本技能。Also triggered as /ark-image-gen。
---

# 火山方舟图片生成（Seedream 全系，直连 API）

用封装脚本直连方舟数据面 API（`https://ark.cn-beijing.volces.com/api/v3/images/generations`）生成图片，**同步返回**。认证用 `ARK_API_KEY`（ark- 开头）——不要读取、传递或落盘任何 API key，脚本自己从环境变量或 `~/.zshrc` 解析。

> ark- 家族分工：静态图用本技能；视频用 `ark-video-gen`；朗读配音（TTS）用 `ark-tts`；情景音频创作用 `ark-audio-gen`；录音转文字用 `ark-asr`。

## 模型选择（`-m`，别名或完整模型名）

Seedream 5.0 官方分三档：**lite**（组图）/ **flash**（多图层，快速）/ **pro**（多图层，旗舰）；4.5 / 4.0 支持组图。

| 别名 | 模型 | 总像素范围 | 能力 | 特点 |
|---|---|---|---|---|
| `5`（默认，= `5lite`） | doubao-seedream-5-0-260128 | 3,686,400 ~ 16,777,216 | 组图 | 官方名 Seedream 5.0 lite；最小 1920x1920 |
| `5flash` | doubao-seedream-5-0-flash-260915 | 921,600 ~ 4,624,220 | 多图层 | 快速版；支持 1024x1024 小图，计费与 5pro 同低档 |
| `5pro` | doubao-seedream-5-0-pro-260628 | 921,600 ~ 4,624,220 | 多图层 | 交互编辑；上限低（≈2150²），计费 token 少 |
| `4.5` | doubao-seedream-4-5-251128 | 3,686,400 ~ 16,777,216 | 组图 | 支持流式 |
| `4` | doubao-seedream-4-0-250828 | 921,600 ~ 16,777,216 | 组图 | 可 1024x1024 小图 |

**能力互斥**（2026-09-28 实测）：`--layers` 多图层仅 5flash/5pro；`-g` 组图仅 5/5lite/4.5/4。lite 收到 layer_decomposition 会**静默按普通单图生成并计费**，flash/pro 收到组图参数直接 400——脚本按注册表能力在本地拦截，不要绕过。

像素范围实测：5/4.5/4/5pro 于 2026-09-17、5flash 于 2026-09-28（非法尺寸直接 400 不计费，服务端报错会明示上下限）；`-m 4` 不传 size 时走服务端默认（自适应 2048x2048），5flash 不传 size 实测自适应 2K 档（1664x2496）。

## 标准流程：直接跑脚本

```bash
# 横版 16:9，2K 档总像素
bash <技能目录>/scripts/image_gen.sh "清晨海面的白色帆船，电影感" -m 5 --ratio 16:9 -s 2K -o ./output/sea.jpg

# 竖版 9:16（默认基准像素）
bash <技能目录>/scripts/image_gen.sh "夏日便利店，黄昏胶片感" -m 4.5 --ratio 9:16 -o ./output/shop.jpg

# 小图（4.0 支持 1024x1024；5.0/4.5 最低 1920x1920）
bash <技能目录>/scripts/image_gen.sh "柴犬追蝴蝶" -m 4 -s 1024x1024 -o ./output/dog.jpg

# 组图（仅 5/5lite/4.5/4）：同一主题内容关联的一组
bash <技能目录>/scripts/image_gen.sh "一组4张柴犬四季插画，风格统一" -m 5lite -g 4 -s 2K -o ./output/shiba

# 多图层拆分（仅 5flash/5pro）：把一张图拆成底图 + 各元素透明 PNG
bash <技能目录>/scripts/image_gen.sh --layers --ref ./poster.jpg -m 5flash -o ./output/poster
# 提示词可省略（自动全量拆分），也可点名元素控制拆什么、省钱提速：
bash <技能目录>/scripts/image_gen.sh "只拆出主标题文字" --layers --ref ./poster.jpg -m 5flash -o ./output/poster
```

多图层成功时最后输出（含元数据 JSON 路径）：

```json
{"ok":true,"images":["…/poster_z00_base.jpg","…/poster_z01_主标题文字.png"],"model":"doubao-seedream-5-0-flash-260915","size":"adaptive","usage_total_tokens":8568,"generated_images":2,"layers_json":"/abs/poster_layers.json"}
```

图层文件按 `_z<叠放序号>_<图层名>` 命名（`_z00_` 恒为底图，jpeg；其余为带透明通道的 PNG）；`<前缀>_layers.json` 记录每层的 `z_index` / `name` / `description` / `bounding_box`（absolute 像素坐标 + normalized 0~1000），按 z_index 把各层贴回 bounding_box 位置即可还原原图。

成功时最后输出：

```json
{"ok":true,"images":["/abs/path/sea.jpg"],"model":"doubao-seedream-5-0-260128","size":"2731x1536","usage_total_tokens":16386,"generated_images":1}
```

常用参数：

| 选项 | 说明 | 默认 |
|---|---|---|
| `-m` | 别名 `5` / `5lite` / `5flash` / `5pro` / `4.5` / `4` 或完整模型名 | `5` |
| `-s` | 分辨率：`宽x高` 或 `1K/2K/4K`（快捷名透传服务端自适应比例）；`--layers` 模式只接受 `1K/1.5K/2K/auto` 档位或不传 | 不传走服务端默认 |
| `-r` | 画面比例 `宽:高`（16:9 / 9:16 / 4:3 / 3:2 / 21:9…），按 `-s` 的像素基准换算宽高，越界自动钳制并提示；`--layers` 模式不支持 | 不传则按 `-s` 或服务端默认 |
| `-o` | 输出路径（多图自动加 -1/-2 后缀；多图层加 `_z<序号>_<图层名>` 后缀并写 `_layers.json`；格式按实际返回自动纠正） | `./ark_image_<时间戳>.jpg` |
| `-g` | 组图张数（内容关联的一组，1-14；**仅 5/5lite/4.5/4**，flash/pro 会拦截） | 单图 |
| `--layers` | 多图层拆分（**仅 5flash/5pro**）：`--ref` 恰好 1 张输入图；提示词可省略=自动全量拆分，或点名元素；约 1 分钟，按图层张数计费 | 关 |
| `--ref` | 参考图（可重复多次，做图生图/多图生图；本地文件自动 base64 入 `images` 数组，大文件可用——请求体走临时文件） | 无 |
| `--seed` | 固定种子复现 | 随机 |
| `--watermark` | 加 AI 水印 | 不加 |
| `--dry-run` | 只打印参数 JSON 不实际生成（换算结果先看这个） | 关 |

比例换算规则：`--ratio 16:9 -s 2K` → 基准 4194304 像素 → 2731x1536；只传 `--ratio` 用模型默认基准；换算结果超出模型像素范围时自动钳制并打 stderr 提示。

## 实测确认的坑（2026-09-17 / 09-28）

- **Seedream 5.0(lite) / 4.5 最小 3686400 像素**（1920x1920）：传 1024x1024 报 "image size must be at least 3686400 pixels"。要小图用 `5flash` / `5pro` / `4`（最低 921600，960x960）。脚本会自动钳制（`-s 512x512 -m 5` → 1920x1920）。
- **5flash / 5pro 上限 4624220 像素**：`-s 4K -m 5flash` 会被自动压到上限附近，要大图用 `5` / `4.5` / `4`。
- 计费按张按像素：5.0 1920² ≈ 14400 tokens、2731x1536 ≈ 16386；5flash / 5pro 1024² ≈ 4096 tokens（总像素/256，低单价档）。日常配图/草稿优先 `5flash`（快、便宜、支持小图），要 4K 大图或最强画质再换 `5`。
- 组图（`-g N`，仅 5/5lite/4.5/4）适合同一主题多张插画/分镜；参考图数 + 生成数 ≤ 15，按实际返回张数计费（实测 lite 2 张 2560x1440 = 28800 tokens）。
- 响应 URL 是 TOS 签名地址有时效，脚本已自动下载到本地，把本地路径交给用户。
- **普通生成的参考图字段是顶层 `images` 数组（2026-09-18 实测）**：本地文件转裸 base64 放入 `images:[b64]` 是唯一被接受的形态——单数 `image` 字段 / `image:[...]` 均 400；http/data URL 可原样放同一数组。请求体与响应用的 JSON 经临时文件传给 curl/python（命令行参数有 ~1MB 上限，大参考图曾触发 Argument list too long）。
- **多图层模式的参考图字段恰好相反：单数 `image` + data URL 前缀（2026-09-28 实测）**：`image:"data:image/jpeg;base64,…"` 是本地文件唯一被接受的形态——`images` 数组报 "layer_decomposition requires exactly one input image"，裸 b64 被当 URL 解析报错。脚本按模式自动切换两种形态。
- **多图层 size 只接受档位**：像素形式报 "explicit WIDTHxHEIGHT size is not supported with layer_decomposition"（脚本已拦截，只放行 1K/1.5K/2K/auto）。
- **多图层不发 prompt 键 = 自动全量拆分**：传空字符串会破坏自动识别语义，脚本在 `--layers` 且无提示词时整个省略该字段；点名元素（如"只拆出主标题"）能显著省线提速（实测全量拆 1024² 海报出 16 张 ≈ 65k tokens，限定拆 1 元素 ≈ 8.5k）。
- **能力不支持时的服务端行为不一致（2026-09-28 实测）**：lite 收 `layer_decomposition` **静默忽略**（按普通单图生成并计费，最坑）；flash/pro 收组图参数直接 400。脚本在客户端按模型能力拦截，报错信息会给出可用模型。
- 多图层耗时约 1 分钟（flash 实测 58~74 秒），超时默认 300 秒够用；输出张数由拆分结果决定（1 底图 + 最多 16 层）。
- **服务端默认会给图片加「AI 生成」角标水印（2026-09-18 实测）**——脚本已显式传 `watermark:false`；需要水印时 `--watermark` 打开。

## 报错速查

- 401 → `ARK_API_KEY` 缺失或无效（检查 `~/.zshrc`）。
- 400 InvalidParameter size → 像素超出该模型范围（脚本一般已自动钳制；手写参数时对照上表）；`--layers` 模式传了像素形式 size。
- "requires exactly one input image" → 多图层模式参考图数量/字段形态不对（脚本已处理：恰好 1 张、单数 image + data URL）。
- "not supported by the current model" → 组图参数发给了 flash/pro，或多图层参数发给了不支持的模型（脚本已按能力拦截）。
- 404/ModelNotOpen → 该模型未在方舟控制台开通，换 `-m` 其他版本。
