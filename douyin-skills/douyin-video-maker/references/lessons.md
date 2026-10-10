# douyin-video-maker 事故记录与实测回写

维护纪律：每次真实翻车或实测发现的事实，修复后回写到这里（现象 → 根因 → 修复），SKILL.md 硬坑清单同步收录。竖屏/抖音化部分为空白地带，首期实测（2026-10）重点回填。

## 继承自 jargon-anim 的已验证事故（六轮迭代，同源管线）

1. JS `transform` 覆盖 CSS transform 居中 → 居中一律流式（margin auto/text-align/flex），JS 只写 translateY/scale
2. 收尾场景无 flex 居中 → outro 卡停左上角；审片必须抽片尾最后一帧
3. `opacity:0` 仍占 flex 空间 → 挤偏邻居，动态内容独立绝对定位层
4. timeline.json 缓存旧文本 → 改词必重跑 gen_timeline
5. 「音频存在即跳过」→ 改词必删旧 mp3
6. heredoc 中文标点字面量不可靠 → 脚本内替换标点用 `chr(0xFF0C)` 码点写法
7. 场景重编号连锁：beat 引用/section id/元素 id/CSS 选择器要同步；veil 黑场只由收尾场景函数设置
8. 打字机/逐字动画用 `SENT.length` 驱动，不写死字数

## 竖屏/抖音化实测记录

### 首期全链路验收（2026-10-09，示例合集「AI 冷知识」第 01 期《天空为什么是蓝的》）

成片 49.0s/2.6MB，12 句 203 字符，渲染 1471 帧用时 59s，vision 四轮审查通过。事故全记录：

1. **`npm init -y` 中文目录名报 Invalid name**（`第01期-天空为什么是蓝的` 不是合法 package name）→ 手写 `{"name":"ep-01-slug","private":true}` 再 `npm i`。已写进 SKILL.md 环境依赖。
2. **动画模板 `#s2-card` 漏 `position:absolute`** → 卡片掉文档流贴顶、压角标；两轮 vision 一致报告「卡片在 y0-21%」定位根因。封面模板 `#ep-badge` 同型问题（徽章掉流顶部、被当成缺失）。**判读经验：vision 报「元素缺失」先分两种——锚点延迟入场（抽帧时刻早于 B() 锚点，正常）vs 真缺失/掉流（连续多帧位置异常）**；本期 3 个 P1「缺失」里 2 个是前者、1 个是后者。
3. **SRT+force_style 字幕整片不可见**：libass 对 SRT 用 384x288 默认坐标系，MarginV=300>288 字幕推出画面，ffmpeg 零报错（libass 正常加载字体、SRT 时间轴正确，唯一线索是抽帧底部无字）。jargon-anim 横屏 MarginV=40<288 所以从未暴露。修复：assemble.py 直接生成 final.ass（PlayRes=1080x1920，样式坐标即像素）。**教训：竖屏大 MarginV 必须走 ASS**。
4. **verify_splice 尾缝 16.7% 超 15% 阈值**：click 复判（缝 ±30ms 相邻样本最大跳变）仅 524=1.6% 全幅，平滑淡出非爆音。根因：TTS 输出电平偏低（全片峰值 32% 全幅），缝峰值/全片峰值的比例被放大。**判读纪律：>15% 先做跳变复判再定爆音**。
5. **make_cover 持续用旧模版**：改了仓库源 templates/cover.template.html 但没 deploy——make_cover 的技能模版探测指向安装侧 `.zcode/skills/`。修复探测逻辑（向上逐级找）+ deploy 后生效。**教训：技能源→deploy→重复制 tools 三步一个不能少**。

### whole 整段合成模式（2026-10-10 实测，解决「语速忽快忽慢」）

用户反馈小帅（BV411）成片语速忽快忽慢。定位与修复全记录：

1. **根因**：v1 逐句合成时模型每句自定韵律，实测逐句语速 5.86~8.29 字/s（极差 41%）；而整段合成（如试听样带）模型统筹全篇语速均匀。**逐句时间轴精确 vs 整段韵律均匀**是两种模式的本质权衡。
2. **实现**：整段一次合成（≤1024 字节）→ silencedetect(-45dB/0.15s) 解析停顿 → **DP 把停顿分配给句子**（代价=每句实际语音长与 字数×平均字率 之差平方，句边界与句内逗号停顿时长重叠 0.32~0.50s 不能按时长硬分，必须按字数对齐）→ 从 whole.wav 样本级裁句。
3. **坑 A：mp3 裁切爆音**——mp3 帧对齐 ±48ms，切口落进语音导致句首硬切（拼接缝 click 达 75% 全片峰值）；必须先解码 whole.wav 再裁（ffmpeg 对 wav 是样本精确）。
4. **坑 B：whole 模式高头缝是自然起音非爆音**——解说腔起音爆发力强（缝峰值可达 75% 全片峰值），但 12ms afade 后相邻样本跳变仅 8% 全幅；verify_splice 已升级为超阈自动 click 复判（跳变 >3000 才判爆音）。逐句合成模式头缝 ~1% 是 TTS 单句自带轻起音，两种模式基线不同。
5. **坑 C：ffmpeg 进度行 time=00:00:36.12 形态**——用 `time=([\d.]+)` 正则解析会截成 `00`，总时长必须 ffprobe 取。
6. 末句区间的结束点=音频尾（DP 允许最后一句用「音频尾」作边界）；停顿数 < 句数-1 时 DP 报错回退 per-beat。

实测口径回写：磁性解说男声 + speed=10 口播自然；49 秒成片 203 字符 TTS 费用按火山刊例 <0.05 元；竖屏字幕 44px/底边 y1620 视觉审查通过（与画面元素最低点 y1380 有 200px 余量）；封面期号徽章 y300/标题 y490/钩子 y1160 全在九宫格 3:4 裁切线内。

### 剪映「小帅/小美」对应与 v1 引擎接入（2026-10-10 调研+实测）

需求：用户点名要剪映「小帅」音色。调研与实测全记录：

1. **对应关系最终版**：剪映同款音色 = 火山「豆包语音」BV 系（官方音色总表「视频配音」场景）：影视解说小帅 `BV411_streaming`、影视解说小美 `BV412_streaming`、活力解说男 `BV410_streaming`、解说小帅-多情感 `BV437_streaming`。BV 系走 **v1 HTTP API**（`/api/v1/tts`，`Authorization: Bearer;{token}`，cluster=volcano_tts，appid+token 鉴权，token 用豆包语音控制台 Access Token，body 内 app.token 是无实义 Fake 字段）。
2. **三路实测排除**：① VC_BV411 是音色转换服务的写法（声转声），TTS 侧直接用 BV411_streaming；② v3 unidirectional API 不认 BV 系与 1.0 短 ID（55000000）；③ 老「精品发音人」短 ID（影视解说 zh_male_xiaoming 等，6489/93478 表）在 v1 网关报 `Invalid workflow synthesize_with_sami` —— sami 引擎已不对外路由，该表是历史文档，勿再按它选音色。
3. **v1 参数**：speed_ratio [0.5,2.0]（技能统一用百分比 --speed，内部换算 1+speed/100）；text ≤1024 字节；reqid 每次必须唯一（uuid）；返回 JSON code=3000 + data(base64)；网络抖动重试 3 次间隔 5s（SSL EOF 与 v3 同款毛病）。
4. **凭证**：v1 需要「语音技术→应用管理」的数字 AppID（`ARK_SPEECH_V1_APPID`）+ Access Token（`ARK_SPEECH_V1_TOKEN`，缺失回退 v3 的 ARK_SPEECH_API_KEY——同一控制台账号两套凭证，用户 2026-10-10 已配置）。
5. 已固化为 `scripts/tts_v1.py`（`--list-voices` 看内置 BV 系高频表），gen_timeline 按 speaker 前缀自动分派双引擎。
