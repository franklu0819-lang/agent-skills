---
name: jargon-anim
description: 制作「AI 黑话图鉴」系列科普动画视频(每期 90 秒左右,讲一个 AI 术语):文案分镜 → 飞哥复刻音色逐句配音(ark-tts,裁静音)→ 确定性 HTML/JS 动画 → puppeteer 逐帧渲染 → ffmpeg 合成烧录字幕成片。Use whenever the user wants 制作黑话动画/黑话系列新一期/术语科普动画/AI黑话图鉴 EP.N/上下文窗口这期/继续做黑话系列 —— 系列已出 EP.01《GPT与LLM》、EP.02《Token》。硬边界:软件操作录屏教程走 video-tutorial-gen;AI 生成实拍视频走 ark-video-gen;纯配音走 ark-tts。未明确指令不烧钱调云端视频模型,本技能全程本地渲染。
---

# AI 黑话图鉴 · 动画课程制作

把一个 AI 术语做成 90 秒左右的科普动画:深色科技风、彩色词块、飞哥复刻音色、逐句声画同步。**核心管线(gen_timeline / render / assemble)与 EP.01/EP.02 两期成片逐字节同源,历经 6 轮迭代;verify_splice / asr_check 两个验证脚本与 templates 为技能侧固化产物,已修复并在真实项目上验证。严格照本流程走,所有坑都已写成纪律,不要即兴。**

## 系列档案(权威,新期必须延续)

- **结构**:EP.01《GPT与LLM》✅ → EP.02《Token》✅ → EP.03《上下文窗口》(待做)→ 后续待定
- **视觉**:1920x1080@30fps,深蓝黑背景 `#0d1017`,主蓝 `#5B8CFF`,块色板循环 `#5B8CFF/#8B7CFF/#FF9F5A/#43C9A3/#FFD166`;左上角标「AI 黑话图鉴」右上角标「EP.NN · SLUG」;片尾进度点第 N 个亮
- **事实口径(飞哥定,不得违背)**:**1 token ≈ 1.3~1.6 个汉字**;128K 上下文 ≈ 二十来万字;中文常见词一两块。所有换算数字引用前先查证(tiktoken/官方文档),并全片自洽
- **内容纪律**:讲黑话必须讲到工作本质(如 Token 必讲"大模型本质是预测下一个 Token");结尾金句 + 下期预告钩子要严丝合缝
- 已交付成片在 `tutorials/AI黑话/第NN期-主题/`,做新期前先看最近一期的 script.json 与 anim/ 找延续感

## 环境依赖(一次性)

- node ≥18、ffmpeg、python3(均已在 PATH);本机 Chrome(`/Applications/Google Chrome.app/...`)
- **用户级技能**:ark-tts(`~/.agents/skills/ark-tts/scripts/tts.py`,配音)、ark-asr(`~/.agents/skills/ark-asr/scripts/transcribe.sh`,ASR 终验);两者可用环境变量 `TTS_SH`/`ASR_SH` 覆盖路径
- 火山语音 Key(ARK_SPEECH_API_KEY,zshrc;旧名 SPEECH_API_KEY 兼容;注意是语音控制台 UUID Key,非方舟 ark- Key)
- puppeteer-core —— **每期目录** `npm init -y && npm i puppeteer-core --registry=https://registry.npmmirror.com`(约 2s,勿走 npmjs 代理)

## 制作流程(每期端到端)

期目录:`tutorials/AI黑话/第NN期-主题/`,含 `script.json`(文案分镜唯一人工编辑源)、`audio/beats|clean/`、`anim/index.html`、`tools/`、`build/`、`STATUS.md`。

### 1. 初始化期目录
```bash
mkdir -p 第NN期-主题/{audio/beats,anim,build,tools}
cp <技能目录>/scripts/{gen_timeline.py,render.js,assemble.py,verify_splice.py,asr_check.py} 第NN期-主题/tools/
cp -R 上一期/node_modules 第NN期-主题/node_modules
```
### 2. 文案 script.json(复制 `templates/script.template.json`)
- 每句 ≤25 字、**标点一律全角**(半角会被 ASR/vision 挑)、口播少读英文全词(画面显示英文、嘴里说中文)
- 7 段式:钩子→揭示→机制→数量级→tip→金句→预告;每句 = 一个动画节拍
- **模板占位文案（"（第一句…""XXX"）必须全部替换**——gen_timeline 有占位符守卫会直接拒绝,防止废音频烧钱
- **GATE:文案定稿后给用户过目**(交互在场用 AskUserQuestion;无人值守落 `script.pending-approval.md` 停下等批,严禁自行放行)
### 3. 配音 + 时间轴
```bash
python3 tools/gen_timeline.py   # 逐句 TTS→裁头尾静音→timeline.json(权威时间轴,断点续跑)
```
- 改词后**必须删对应 `audio/beats/XX.mp3`** 再跑(文件在即跳过,漏删=新文案配旧音)
- 英文词口音差:该 beat 加 `"language": "crosslingual"` 重录
### 4. 动画 anim/index.html(复制 `templates/index.template.html`)
- 场景函数里动画锚点一律 `B('s2b2')` 跟句引用,**不写死秒数**(重录后自动跟拍)
- 收尾场景:s7 问句退场 → outro 入场 → `o($("veil"), E(t,dur-0.9,dur-0.1))` 黑场;**veil 只在收尾函数设置,renderFrame 不得覆盖**
- 改角标 `EP.NN · SLUG`、进度点第 N 个亮
### 5. 渲染 + 组装
```bash
node tools/render.js            # Chrome 无头逐帧 → build/silent.mp4(~2300 帧 90s)
python3 tools/assemble.py       # 拼音频(fade 防爆音)+ final.srt + 烧录 → AI黑话图鉴-EP{NN}-{slug}.mp4
```
- 抽帧检查:`node tools/render.js sample 300,600,900`(存 build/preview/)

### 6. 验证链(全过才算完)
1. **拼接点**:`python3 tools/verify_splice.py` —— 拼接点峰值必须 ≈0(>15% 全片峰值=爆音)
2. **抽帧自查**:每场景至少 1 帧,**必须含片尾最后一帧**(预告卡居中?黑场生效?)——历史上的 bug 全藏在最后一帧
3. **英文词**:`python3 tools/asr_check.py` —— 全部命中才算读对;口音标准与否请用户复听终判
4. **vision 终审**:抽 8-10 帧(各场景+片尾)派 vision agent,字幕不得与画面重叠(底部 y≥850 归字幕,元素底边 ≤830)
5. 修复后重渲:改画面 `render.js`+`assemble.py`;只改字幕 `assemble.py`;改词 `gen_timeline.py`→`render.js`→`assemble.py`

### 7. 交付
- 报文件名+时长+体积;**按刊例报 TTS 费用**(以火山控制台刊例为准;每期约数百字符,费用极低,历史各期折算均 <0.05 元;本地渲染 0 元)
- `STATUS.md` 落盘:场景结构、文案定稿、验证结果、本期新坑
- 更新系列记忆(`ai-jargon-series-pipeline`)

## 硬坑清单(每条都真翻过车)

1. **JS 动画 transform 覆盖 CSS transform 居中** → 元素居中一律 `left:0;right:0;margin:0 auto`、text-align 或 flex;JS 只写 translateY/scale。新写场景代码仍会复发,写完自查
2. **收尾场景 section 必须带 flex 居中**(`display:flex;align-items:center;justify-content:center`)→ 否则无坐标的 outro 卡停左上角(EP.01 翻过车);审片必须抽到片尾最后一帧才能发现
3. **opacity:0 仍占 flex 空间** → 会挤偏同行邻居;动态内容用独立绝对定位层(EP.01 生成块、S1 胶囊都中过)
4. **timeline.json 缓存 script.json 的 text** → 改词/标点后必须重跑 gen_timeline,否则字幕用旧文本(assemble 读 timeline 不读 script)
5. **gen_timeline 按"音频存在即跳过"续跑** → 改词必删旧 mp3;重编号迁移音频后逐个核对"词变了没删"的情况
6. **heredoc 里写中文标点字面量不可靠**(半角全角肉眼难辨,已三次踩坑)→ 脚本里替换标点一律 `chr(0xFF0C)` 码点写法
7. **场景重编号连锁**:beat id 引用(B('s4b2'))、section id、元素 id、CSS 选择器要同步;veil 黑场只由收尾场景函数设置,renderFrame 不得覆盖(写死场景 id 是重灾区)
8. **期数/命名全局同步**:改期数时全局搜 "EP.0" 与 episode 字段,画面角标、outro、进度点、script.json、成片文件名(assemble 按 episode/slug 自动命名)一致
9. **字幕安全区**:底部 y≥850 归字幕;说明性文字不与旁白复述重复(重复内容删画面文字)
10. **打字机/逐字动画**用 `SENT.length` 驱动,改文案自动适配,不要写死字数

## 参考

- `scripts/`:gen_timeline.py(TTS+清洗+时间轴)/ render.js(逐帧渲染)/ assemble.py(合成+命名)/ verify_splice.py(拼接点)/ asr_check.py(英文词)
- `templates/`:script.template.json(分镜模板)/ index.template.html(引擎+构件库+示例场景)
- `references/lessons.md`:EP.01/02 的完整事故记录与修复 diff 要点
- ark-tts 技能:tts.py 参数细节(语速、语种、错误码)
