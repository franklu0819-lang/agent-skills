---
name: douyin-video-maker
description: 抖音竖屏科普动画视频制作：文案分镜 → ark-tts 公版解说音色逐句配音（裁静音）→ 竖屏 1080x1920 确定性 HTML 动画（知识科普风）→ puppeteer 逐帧渲染 → ffmpeg 合成烧字幕（可选 BGM 闪避），按「视频合集」封面模版自动出高辨识度封面，产出可直接发布抖音的成片+封面+发布文案。Use whenever the user wants 做抖音视频/把这篇文案做成抖音视频/抖音视频制作/新合集做一期/给视频合集设封面模版/做竖屏口播动画视频 —— 输入是文案、产出是视频就用本技能。硬边界：剖析已有抖音视频走 douyin-video-analysis；账号调研走 douyin-account-analysis；AI 生成实拍视频走 ark-video-gen；纯配音走 ark-tts。全程本地渲染，不烧云端视频模型。Also triggered as /douyin-video-maker.
---

# 抖音视频制作（竖屏科普动画）

把一篇文案做成可直接发布抖音的成片包：竖屏成片（解说+动画+烧录字幕）、合集模版封面、发布文案。核心管线与 jargon-anim（AI 黑话图鉴，6 轮迭代验证）同源，本技能将其抖音化：1080x1920 竖屏、每句 ≤18 字短节奏、公版解说音色、合集封面模版系统。**严格照本流程走，所有坑都写成了纪律，不要即兴。**

> 引擎分工：本技能管「文案 → 竖屏动画成片」全链路；剖析已有抖音视频 → `douyin-video-analysis`；账号调研 → `douyin-account-analysis`；AI 生成实拍视频 → `ark-video-gen`；纯配音不出片 → `ark-tts`；横屏课程动画 → tut 家族 `jargon-anim`。

## 规格与安全区（1080x1920 竖屏，硬纪律）

- 30fps、CRF 18、faststart；目标时长 40~90s；每句 ≤18 字、标点一律全角
- **安全区**：顶部 y<160 归角标；主内容 y 200~1400；**字幕区 y1400~1650（画面元素底边 ≤1380 防重叠）**；底部 y>1700 留白避让抖音 UI（文案/头像/进度条）；右侧 x>940 不放关键元素（点赞按钮列）
- 字幕烧录：assemble.py 自动生成 `final.ass`（PlayRes=视频分辨率，坐标即像素：Hiragino Sans GB 44px、底边距底 300px→y1620 避让抖音 UI）——**不要改回 SRT+force_style**：libass 对 SRT 用 384x288 默认坐标系，MarginV>288 会把字幕推出画面（2026-10 实测踩坑）
- 封面 1080x1920 全幅；**核心信息（期号/标题/钩子）必须落在 y<1400**——抖音主页九宫格会把封面裁成约 3:4

## 环境依赖（一次性）

- node ≥18、ffmpeg、python3、本机 Chrome（`/Applications/Google Chrome.app/...`）
- 用户级 ark-tts 技能（`~/.agents/skills/ark-tts/scripts/tts.py`，可用环境变量 `TTS_SH` 覆盖路径）——配音走**双引擎自动分派**（gen_timeline 内置）：音色 `BV` 开头（剪映同款 1.0 大模型库）→ 本技能 `tts_v1.py`（v1 HTTP API）；其余（2.0 库/复刻）→ ark-tts `tts.py`（v3）
- 火山语音 Key 两套：`ARK_SPEECH_API_KEY`（v3 用，zshrc；UUID）＋ v1 用 `ARK_SPEECH_V1_APPID`（数字 AppID）与 `ARK_SPEECH_V1_TOKEN`（缺省回退 ARK_SPEECH_API_KEY）——控制台「语音技术→应用管理」获取
- puppeteer-core —— **每期目录**先手写 `package.json`（`{"name":"ep-01-slug","private":true}`，name 用英文；中文期目录 `npm init -y` 会报 Invalid name，2026-10 实测）再 `npm i puppeteer-core --registry=https://registry.npmmirror.com`（或从上一期 `cp -R node_modules`）
- 技能脚本/模板有更新时：改仓库源 → `deploy.py --deploy --family douyin-skills` → 再把 scripts 重新复制到期目录 tools/（期目录工具是副本，技能模板 make_cover 读的是**安装侧**）

## 目录组织（合集制，产物在 douyin 工作区）

```
douyin/videos/<合集slug>/
├── collection.json        # 合集配置:显示名/音色/语速/封面主题色 —— 建一次长期用
├── cover.template.html    # 可选:合集自定义封面模版(没有则用技能自带默认模版)
└── 第NN期-标题/           # 期目录(两位零填充期号,--all 排序依赖)
    ├── script.json        # 文案分镜(唯一人工编辑源)
    ├── audio/beats|clean/
    ├── anim/index.html
    ├── tools/             # 从技能 scripts/ 复制的工具
    ├── build/             # silent.mp4、narration.wav、preview/
    ├── <合集名>-第NN期-<slug>.mp4   # 成片(assemble 自动命名)
    ├── cover.jpg          # 封面
    └── report.md          # 交付纪要
```

**新建合集**（首个技能动作之一）：

```bash
mkdir -p douyin/videos/<合集slug>
cat > douyin/videos/<合集slug>/collection.json <<'EOF'
{
  "name": "合集显示名",
  "speaker": "BV411_streaming",
  "speed": 10,
  "cover": {
    "subtitle": "硬核科普",
    "palette": {"c-main": "#5B8CFF", "c-accent": "#FF9F5A", "c-bg": "#0d1017"}
  }
}
EOF
```

- `speaker`：解说音色，**默认影视解说小帅 `BV411_streaming`**（剪映同款，用户 2026-10-10 定），**按前缀自动选引擎**（BV 开头走 v1，其余走 v3）。常用款：
  - **剪映同款 BV 系（v1）**：影视解说小帅 `BV411_streaming`（抖音影视解说标配）、活力解说男 `BV410_streaming`（活力向解说首选）、影视解说小美 `BV412_streaming`、解说小帅-多情感 `BV437_streaming`、沉稳解说男 `BV142_streaming`、知性女声 `BV009_streaming`——完整表 `python3 tools/tts_v1.py --list-voices` 或官方文档「豆包语音-音色列表」
  - **2.0 库（v3，ark-tts）**：磁性解说男声 `zh_male_cixingjieshuonan_uranus_bigtts`、解说小明 `zh_male_jieshuoxiaoming_uranus_bigtts`、流畅女声 `zh_female_liuchangnv_uranus_bigtts` 等，全部清单见 ark-tts 技能 references/voices.md
- `speed`：语速百分比 [-50,100]，抖音口播推荐 8~12 轻加速
- `cover.palette`：封面主题色（注入封面模版 CSS 变量 `--c-main/--c-accent/--c-bg`），换色不改版式

## 制作流程（每期端到端）

### 1. 初始化期目录
```bash
mkdir -p 第NN期-标题/{audio/beats,anim,build,tools}
cp <技能目录>/scripts/{gen_timeline.py,tts_v1.py,render.js,assemble.py,make_cover.js,verify_splice.py,asr_check.py} 第NN期-标题/tools/
cp -R 上一期/node_modules 第NN期-标题/node_modules   # 或 npm i puppeteer-core
```
### 2. 文案 → script.json（复制 `templates/script.template.json`）
- 用户给的文案**改写为分镜**：7 段式钩子→概念→要点×3→数字/例子→金句→引导关注；每句 ≤18 字、口播化（书面语砍短）
- 替换 `title`（封面大标题 ≤12 字）、`hook`（封面钩子词 3~6 字）、`episode`、`slug`
- **模板占位文案必须全部替换**——gen_timeline 有占位符守卫直接拒绝，防废音频烧钱
- **GATE-1 文案定稿给用户过目**（在场用 AskUserQuestion；无人值守落 `script.pending-approval.md` 停等，严禁自行放行）
### 3. 配音 + 时间轴
```bash
python3 tools/gen_timeline.py   # TTS→裁静音→timeline.json(权威时间轴)
```
- **合成模式自动分派**（`--tts-mode` 可强制 whole/per-beat）：BV 剪映同款系（解说腔韵律起伏大）默认 **whole 整段合成**——一次合成全篇再按停顿 DP 对齐切句，语速由模型统筹（逐句合成各句自定快慢，实测小帅逐句语速极差 41%，整段消除）；v3 的 2.0 库默认逐句（时间轴精确、可断点续跑）
- 改词后删除缓存再跑：**per-beat 删对应 `audio/beats/XX.mp3`；whole 删 `audio/whole.mp3`**（文件在即跳过，漏删=新文案配旧音）
- 英文词口音差（仅 per-beat+v3）：该 beat 加 `"language": "crosslingual"` 重录
### 4. 动画 anim/index.html（复制 `templates/anim.template.html`）
- 改角标（合集名/第NN期·主题）、各场景画面文字、收尾进度点第 N 个亮
- 动画锚点一律 `B('s3b2')` 跟句引用，**不写死秒数**（重录后自动跟拍）
- 画面文字与旁白不复述同一句（旁白说的，画面只写关键词）
### 5. 渲染
```bash
node tools/render.js sample 150,450,750,1050   # 抽帧预览存 build/preview/
```
- **GATE-2 抽帧给用户过目**（重点：首帧钩子、要点卡三张、金句、**必须含片尾最后一帧**——历史 bug 全藏在最后一帧）
- 确认后全量渲染：
```bash
node tools/render.js            # → build/silent.mp4(约 1500~2700 帧)
```
### 6. 合成
```bash
python3 tools/assemble.py                    # 拼音轨+final.srt+烧录 → <合集名>-第NN期-<slug>.mp4
python3 tools/assemble.py --bgm <bgm.mp3>    # 可选:BGM 循环+解说闪避(--bgm-vol 0.25 可调)
```
### 7. 封面
```bash
node tools/make_cover.js                     # 在期目录内:模版+合集配置 → cover.jpg
# 改了封面模版/主题色后,在合集目录: node <任一期>/tools/make_cover.js --all 重出全部封面
```
### 8. 验证链（全过才算完）
1. **拼接点**：`python3 tools/verify_splice.py` —— 超阈值自动 click 复判（相邻样本跳变 >3000 才是真爆音）；whole 模式解说腔的自然起音电平可达全片峰值 75%，属正常非爆音
2. **抽帧自查**：每场景至少 1 帧 + 最后一帧（金句卡居中？outro 正常？黑场生效？）；**元素未出现先查是不是锚点延迟入场**（B() 跟句设计，元素随解说句入场，抽帧时刻早于锚点就是空的——抽该句入场后的帧再判）
3. **英文词**（有则跑）：`python3 tools/asr_check.py`；口音标准与否请用户复听终判
4. **vision 终审**：抽 6~10 帧派 vision agent，检查字幕与画面元素重叠、安全区越界、**id 定位元素是否贴顶掉文档流**（见硬坑 12）
5. 修复后重跑：改画面 `render.js`+`assemble.py`；只改字幕 `assemble.py`；改词 `gen_timeline.py`→`render.js`→`assemble.py`；改封面 `make_cover.js`

### 9. 交付
- 成片+封面报文件名/时长/体积；**按火山刊例报 TTS 费用**（每期几百字符，历史 <0.05 元；本地渲染 0 元）
- 写发布文案（标题+简介+话题标签）与 `report.md`（场景结构、文案定稿、验证结果、本期新坑）
- 期号递增信息在下一期 script.json 的 `episode` 字段体现（唯一事实源）

## 硬坑清单（每条都真翻过车，前 6 条继承自 jargon-anim 六轮迭代）

1. **JS 动画 transform 覆盖 CSS transform 居中** → 元素居中一律 `left:0;right:0;margin:0 auto`/text-align/flex；JS 只写 translateY/scale。新写场景代码写完自查
2. **收尾场景 section 必须带 flex 居中** → 否则无坐标的 outro 卡停左上角；审片必须抽到片尾最后一帧才能发现
3. **opacity:0 仍占 flex 空间** → 动态内容用独立绝对定位层
4. **timeline.json 缓存 script.json 的 text** → 改词/标点后必须重跑 gen_timeline（assemble 读 timeline 不读 script）
5. **gen_timeline 按「缓存存在即跳过」续跑** → 改词必删旧音频：per-beat 删 `audio/beats/XX.mp3`，whole 模式删 `audio/whole.mp3`
6. **占位符守卫**：script.json 里残留「（钩子…」等模板占位文案会被直接拒绝——这是防烧钱设计，别绕过
7. **竖屏安全区**（本技能新增）：字幕区 y1400~1650，画面元素底边 ≤1380；底部 y>1700 与右侧 x>940 不放关键内容——抖音 UI 会盖住
8. **字幕字体**：烧录样式用 `Hiragino Sans GB`（本机无 PingFang.ttc，不赌 fontconfig 回退）
9. **封面九宫格裁切**：期号/标题/钩子必须 y<1400，否则主页列表里被裁掉
10. **期号全局同步**：改期数时全局搜「第NN期/EP」，角标、outro、进度点、script.json、封面、成片文件名（assemble 按 collection+episode+slug 自动命名）一致
11. **make_cover 模版查找顺序**：合集目录 `cover.template.html` > 期目录 > 技能自带（安装侧）；改合集模版后用 `--all` 重出历史封面保持版式统一
12. **id 定位元素必须显式 position**（2026-10 实测：模板 `#s2-card`、`#ep-badge` 双双漏 `position:absolute` 掉文档流贴顶）：id 选择器里写 left/top 而没写 position 就是无效样式——改版式时自查，或一律加 `.abs` 类
13. **字幕烧录走 final.ass**（assemble 自动生成，PlayRes=视频分辨率）：SRT+force_style 的 MarginV/字号都按 libass 的 384x288 默认坐标系解释，MarginV>288 字幕直接出画（成片无字幕但 ffmpeg 不报错，极隐蔽——抽帧看底部才能发现）
14. **技能源改动三步链**：改仓库源 → deploy 同步安装侧 → 重新复制 scripts 到期目录 tools/——期目录工具与安装侧模板都是副本，漏一步就是跑旧代码（2026-10 实测：make_cover 一直用旧模版）

## 与其他工作流的集成

- 解说音色换个人风格：改合集 collection.json 的 speaker（ark-tts 公版库 289 个，`--list-voices 解说` 可筛）
- 成片再剪辑/去口癖：video-edit 技能（whisper 转写+cutlist 精剪）
- 发布：抖音创作者本地上传成片+封面（本技能不自动发布）；发布文案见交付物
- 剖析对标账号内容再制作：douyin-account-analysis 调研 → 本技能出片

## 参考

- `scripts/`：gen_timeline.py（TTS+清洗+时间轴）/ render.js（逐帧渲染）/ assemble.py（合成+字幕+BGM）/ make_cover.js（封面模版出图）/ verify_splice.py（爆音检查）/ asr_check.py（英文词 ASR 终验）
- `templates/`：script.template.json（分镜模板）/ anim.template.html（竖屏动画引擎+示例场景）/ cover.template.html（封面模版）
- `references/lessons.md`：事故记录与竖屏适配实测回写
- ark-tts 技能：tts.py 参数细节（语速、语种、错误码）、公版音色全表
