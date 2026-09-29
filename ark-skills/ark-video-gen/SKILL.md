---
name: ark-video-gen
description: "直连火山引擎方舟（Ark）API 做文生视频 / 图生视频 / 参考生视频，默认模型 doubao-seedance-2-5-260628，内置省钱调用纪律与跨片段一致性方法论（统一素材包、尾帧接力）。Use whenever the user wants to 生成视频、文生视频、图生视频、参考生视频、生成一段视频/视频片段、让 AI 做视频、视频保持背景一致/画面连续、做短剧、口播数字人视频、提到 seedance/即梦/豆包视频 — even if they don't explicitly name a model or tool. Also triggered as /ark-video-gen."
---

# 火山方舟视频生成（doubao-seedance，直连 API）

用封装脚本直连方舟数据面 API（`https://ark.cn-beijing.volces.com/api/v3`）提交视频生成任务、轮询状态、下载 MP4，**不依赖 arkcli**。认证用 `ARK_API_KEY`（ark- 开头的方舟 API Key）——不要读取、传递或落盘任何 API key，脚本自己从环境变量或 `~/.zshrc` 解析。

> ark- 家族分工：视频用本技能；静态图用 `ark-image-gen`；朗读配音（TTS）用 `ark-tts`；情景音频创作用 `ark-audio-gen`；录音转文字用 `ark-asr`。

## 省钱调用纪律（生成前必读：视频按成功任务计费，每分钟几十秒就是几元到上百元）

1. **参数先过本地校验，不花钱**：脚本在提交前本地拦截时长越界、分辨率不支持、首帧/首尾帧/参考三种互斥模式混用、task-type 参数错等（这些送上去会被 400 拒绝或模型忽略素材，白跑一趟）。构造完请求先 `--dry-run` 看一眼参数 JSON 和成本预估，确认再提交。
2. **三档出片，先便宜后贵**：试提示词用 `--draft`（出片快、画质低，**不降单价**）或 `-R 480p` → 看片满意 → **同提示词同参数**出正式片（升 720p/1080p）。省钱机制是"低档试错、满意再出高档"，不是 draft 本身打折。禁止一上来就 1080p 押注未验证的提示词。
3. **提示词先自检再提交（翻车重试才是最大浪费）**：提交前对照「失败模式速查」检查——① 外观只靠 @参考图定义，文字不重复描述长相；② 光照/风格描述逐字复用（跨片段时）；③ 一个镜头只指定 1 种运镜；④ 手部动作简化或让手出画；⑤ 台词短句、单人、中近景（口型同步的前提）；⑥ 加"无字幕无水印"约束。改结果时每次只改一个变量。
4. **能剪辑解决的不重新生成**：延长接缝跳变→删帧（前段末 6 帧、后段首 1 帧）；片段间轻微色差→统一 LUT；个别镜头穿帮→B-roll/字卡遮切。重新抽一次卡 = 重新计费。
5. **结果立即下载**：video_url 是 TOS 签名地址 24 小时过期。可复用素材（角色图、场景图、基准片段、尾帧图）固定下来反复用——一致性靠固定素材集，不靠重新生成碰运气。
6. **时长上限不加价硬闯**：超出单段上限（2.5 为 30s）的内容用分段生成+拼接或 extend 延长，不要提交超限时长等报错。

## 模型选择与价格（在线推理，元/百万 tokens；不含视频输入/含视频输入）

| 别名 | 模型 | 单段时长 | 分辨率 | 单价 | 适用场景 |
|---|---|---|---|---|---|
| `25`（默认） | doubao-seedance-2-5-260628 | 4–30s | 480p/720p/1080p | 70/42；1080p 77/46 | **复杂场景/短剧/口播正式成片**（参考 30图+10视频+10音频、专用延长/编辑参数、draft 样片流程） |
| `2mini` | doubao-seedance-2-0-mini-260615 | 4–15s | 仅 480p/720p | 23/14 | 最便宜试提示词（约 0.5 元/s@720p） |
| `2fast` | doubao-seedance-2-0-fast-260128 | 4–15s | 仅 480p/720p | 37/22 | 2.0 系里快且强 |
| `2`/`2pro` | doubao-seedance-2-0-260128 | 4–15s | 至 4k | 46/28；1080p 51/31 | 2.0 效果优先（约 1 元/s@720p） |
| `1pro` | doubao-seedance-1-0-pro-250528 | 5–12s | 至 1080p | —（无声） | 简单视频；**唯一支持 `seed`/`--camera-fixed` 的系列** |

换算参考（不含视频输入）：2.5@720p ≈ 1.51 元/s、2.5@1080p ≈ 3.74 元/s、2.0@720p ≈ 1 元/s。脚本提交前会打印成本预估（以 usage 为准）。价格来自火山方舟价格文档 2026-09 口径，控制台实时价优先。

## 一致性方法论（背景不变、画面连续）

**核心认知**：2.0/2.5 没有跨请求记忆，`seed` 和 `camera_fixed` 仅 1.0 系支持——**跨片段一致性只来自"固定素材包 + 接续机制 + 剪辑兜底"**。首要参数开关不存在，别浪费时间找。

### 素材包纪律（一次备齐，全程冻结）

- **角色**：大头照（无表情）+ 全身照各一张；**不要**三视图/多视图（会被认成多个主体）。群演角色也要固定参考图，否则出"大众脸"。
- **场景**：用 ark-image-gen 生成一张场景空镜/设定图。**背景必须用参考图锁，不能只靠文字描述**——这是背景漂移的头号原因。
- **数量**：官方建议 4–5 个精选素材，不要用满上限（素材互相冲突时模型取平均，越加越漂）。重要素材放前面。
- **prompt 模板逐字复用**，跨片段只换本段动作/台词/情绪，光照与风格描述一个字都不改（"光照占视觉一致性的一半"）。

### 跨片段接续：三种机制按场景选

| 机制 | 用法 | 适用 |
|---|---|---|
| **尾帧接力** | `--return-last-frame` 拿到尾帧图 → 下一段 `--image` 首帧（或与场景图一起 `--ref-image`）循环 | 通用；同场景连续镜头 |
| **视频延长** | 上段成品 `--ref-video` + 提示词"将@视频1向后延长，……"，2.5 加 `--task-type extend`（ratio 须 adaptive） | 文戏/连续长镜头；**连续延长 ≤2 次**（3 次以上画质衰减），每 2 次用成品重启一轮 |
| **首尾帧** | `--image` 首帧 + `--last-frame` 尾帧（2.5 时 ratio 须 adaptive） | 已知镜头起止画面 |

**分段铁律**：场景或动作大转折的"武戏"（追逐、打斗、换景）→ 分段生成再剪辑，不要延长硬接。成片 30–45s 用延长接力；更长（60–90s 口播）→ 分段独立生成 + **先拼完整音轨再对画面** + 接缝 B-roll 遮切。

### prompt 模板（@引用句式，台词用 {} 包裹）

口播：`@图片1 为说话角色，@图片2 为场景背景，镜头固定不动、画面平稳，保持人物样貌、服装、背景、光线完全一致，面对镜头说{台词}，口型与@音频1同步，语速约每分钟260字，画面真实、无字幕无水印`

短剧分镜：`参考@图片1的分镜、景别、运镜，人物角色是@图片2，场景是@图片3，道具是@图片4，创作一段15s的……`

### 失败模式速查（翻车先查这里，改提示词比重抽卡便宜）

| 症状 | 原因 | 处置 |
|---|---|---|
| 背景/场景漂移 | 场景只靠文字；风格词每段改写 | 加场景参考图 @ 引用；风格锁逐字复用；改用延长/尾帧接力 |
| 换脸/身份漂移 | 参考图冲突或与文字打架 | 每角色头像+全身图（角度光线一致）；文字只管动作 |
| 口型不同步 | 长句、语速快、人脸太小、音频带 BGM | 短句拆分；单人中近景；干净干声；逐句生成再拼 |
| 接缝跳变 | 延长衔接的已知特性 | 剪辑删帧（前段末 6 帧、后段首 1 帧）；以切镜时刻收尾 |
| 画质越续越差 | 连续延长 >2 次 | 用成品重启新延长链；或官方"白模"中转 |
| 手部崩坏 | 手部交互复杂 | "双手自然放在桌面"或让手出画 |
| 一次生成塞太多 | >3 镜头/上限时长 | 单次最多 2–3 个衔接镜头，其余分段 |

## 标准流程：直接跑脚本

```bash
# 文生视频（默认 2.5）
bash <技能目录>/scripts/ark_video.sh "一只柴犬在樱花树下奔跑，电影感，浅景深" -o ./dog.mp4 -d 5 -r 16:9 -R 720p

# 试提示词：draft 便宜档，确认后同参数出正式片
bash <技能目录>/scripts/ark_video.sh "复杂分镜脚本提示词" --draft -R 480p -o /tmp/sample.mp4

# 口播（角色图+场景图+飞哥音色音频，音频时长决定生成时长下限）
bash <技能目录>/scripts/ark_video.sh "@图片1 为说话角色，@图片2 为场景背景，…口型与@音频1同步{台词}" \
  --ref-image face.jpg --ref-image scene.jpg --ref-audio voice.mp3 -d 15 -r 9:16 -o ./talk.mp4

# 视频延长（2.5 专用参数；ratio 必须 adaptive）
bash <技能目录>/scripts/ark_video.sh "将@视频1向后延长：人物继续同位置口播下一段台词，保持背景光线完全一致，镜头固定不动" \
  --ref-video prev.mp4 --task-type extend -r adaptive -d 15 -o ./ext.mp4

# 尾帧接力（跨段一致性标准做法；2.5 首帧任务 ratio 必须 adaptive）
bash <技能目录>/scripts/ark_video.sh "…下一段提示词" --image last_frame.jpg -r adaptive --return-last-frame -o ./seg2.mp4
```

成功时最后输出单行 JSON：`{"ok":true,"task_id":"cgt-...","model":"...","video_path":"/abs/path.mp4","last_frame_path":"...","duration":5,"ratio":"16:9","resolution":"720p","usage_total_tokens":...}`；失败 `{"ok":false,"stage":"args|submit|poll|download","error":"..."}` 非零退出。

常用选项：`-m` 模型别名 · `-d` 时长 · `-r` 画幅（16:9/9:16/1:1/adaptive——**2.5 的首帧/首尾帧/extend/edit 任务必须 adaptive**） · `-R` 分辨率 · `--draft` 草稿 · `--image` 首帧 · `--last-frame` 尾帧 · `--ref-image/--ref-video/--ref-audio` 参考（可重复；1.0 系不支持） · `--return-last-frame` 返回尾帧图 · `--task-type auto/reference/edit/extend`（仅 2.5；edit 须 `-d -1`，edit/extend 须 `-r adaptive`） · `--timeout` 轮询上限（默认 900s，1080p/30s 任务建议 1800） · `--keep-url` 保留 video_url · `--dry-run` 只校验不提交（输出对 base64 脱敏）。`-s`/`--camera-fixed` 仅 1.0 系有效，2.x 会忽略并提示。

## 手动等价请求（脚本不可用时参考）

```bash
# 1) 创建任务（返回 {"id":"cgt-..."}）
curl -s -X POST "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks" \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" -d '{
  "model": "doubao-seedance-2-5-260628",
  "content": [
    {"type": "text", "text": "提示词"},
    {"type": "image_url", "image_url": {"url": "https://..."}, "role": "reference_image"},
    {"type": "video_url", "video_url": {"url": "https://..."}, "role": "reference_video"},
    {"type": "audio_url", "audio_url": {"url": "https://..."}, "role": "reference_audio"}
  ],
  "duration": 5, "ratio": "16:9", "resolution": "720p", "generate_audio": true,
  "return_last_frame": true
}'
# 2) 轮询 GET /contents/generations/tasks/cgt-...（queued → running → succeeded/failed）
# 3) 从 content.video_url 下载；return_last_frame 时另有 content.last_frame_url（jpeg，无水印）
```

content 元素规则：图像不写 role = 首帧（图生视频）；首尾帧模式两个 image_url 的 role 必须分别 `first_frame`/`last_frame`；参考素材必须写 role。**首帧、首尾帧、全模态参考三种模式互斥，不可混用**。首帧图建议 <3MB（本地文件转 `data:image/jpeg;base64,...`），优先公网 URL 或方舟素材库 `asset://`。

## 注意事项

- **生成耗时 1–5 分钟起**（30s/1080p 更久），必须轮询；本机无 `timeout` 命令，不要用它包 curl。
- **参考素材上限**：2.5 为 30 图 + 10 视频（总 ≤30s）+ 10 音频（总 ≤30s，支持纯音频驱动）；2.0 系为 9 图 + 3 视频（总 ≤15s）+ 3 音频（总 ≤15s，不可单独输入，须至少搭配 1 图或 1 视频）；1.0 系仅支持首帧图，不支持参考素材。本地文件的总时长、单文件大小、请求体总量脚本会在提交前校验（ffprobe 存在时）。2.5 的首帧/首尾帧任务与 edit 任务 duration 必须为 -1（edit）且 ratio=adaptive。
- **音频驱动口播**：音频时长决定视频时长下限；台词口型由模型联合生成，`reference_audio` 是音色参考——飞哥复刻音色走 `ark-tts` 生成干声后再传入。
- **用量与计费**：token ≈ (输入视频时长+输出视频时长) × 宽 × 高 × 帧率 / 1024，精确以 `usage.total_tokens` 为准；失败/取消不计费，但成功即计费——这就是"draft 先行 + 本地校验"的原因。**实测校准（2026-09-27，2.5 已开通）**：4s/480p/1:1 实际输出 640×640@24fps，usage 38800 tokens（与公式精确吻合，≈2.72 元）；分辨率档本质是像素预算（480p=409600、720p=921600、1080p=2073600），1:1 画幅按开方取边（480p→640×640 而非 480×480）。draft 模式无单价折扣。
- 用量、额度、模型细节去火山方舟控制台查看，不要猜测。

## 报错速查

- 401 → `ARK_API_KEY` 缺失或无效（检查 `~/.zshrc`）。
- 400 InvalidParameter duration/resolution/ratio → 超出该模型取值范围（脚本本地校验应已拦截，若仍出现说明官方口径有更新，以报错信息为准调整）。
- 400 TaskTypeMismatch → `omni_reference_task_type` 指定值与实际内容不符（如 extend 任务没带参考视频）。
- 404 InvalidEndpointOrModel.NotFound → 模型 ID 写错或已下线。**已下线模型**：`1.0-lite` 系、`1.5pro`（251215）、`1.5pro draft`——别再尝试。
- 404 ModelNotOpen（"has not activated the model"）→ 模型真实存在但**本账号未开通**：去火山方舟控制台开通该模型服务后重试；未开通期间用 `-m 2fast`/`-m 2` 过渡。（2026-09-27 实测：2.5 已开通并通过真实任务验证，2.0/2fast/2mini/1pro/1fast 亦可用。）
- **免费探测模型是否开通**（不创建任务、不计费）：POST 该模型 + 必非法参数（`"duration":99999,"ratio":"invalid_ratio"`）——返回 400 InvalidParameter 说明模型门已过、可用；返回 404 说明未开通或无权限。模型探测与认证探测（GET 一个假任务 id，404=认证正常）都免费。
