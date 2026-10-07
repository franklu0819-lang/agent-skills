# EP.01/EP.02 制作事故记录(完整复盘)

技能纪律都从这里来。按时间序,每条:现象 → 根因 → 修复 → 固化的纪律。

## 1. transform 居中被 JS 覆盖(EP.01 首版,4 处元素偏移)
- 现象:聊天卡、标题、示例行整体偏右 440px,S3 注释被挤出屏幕
- 根因:`fadeUp()`/`pop()` 每帧重写 `style.transform`,把 CSS `translate(-50%,-50%)` 居中抹掉
- 修复:全部元素改 `left:0;right:0;margin:0 auto` / `text-align:center` / flex 容器居中
- 纪律:CSS 一律不做 transform 居中;**新写场景仍会复发**(EP.01 的 #s3-box/#s5-box 在 v2 版又中招),写完逐元素自查

## 2. 动画时序错乱(EP.01 首版)
- 现象:10 秒时切块动画已发生(应在 14.5s)
- 根因:B() 函数"相对时间又减了一次场景起点"
- 修复:锚点统一为跟句引用 `B('s2b2')`(render.js 注入 beatsMap),彻底消灭手写秒数

## 3. 全角化标点(EP.02,vision 审片挑出)
- 现象:字幕/标题混用半角标点
- 根因:script.json 与 anim/index.html 两处文案,只改了一处;heredoc 里中文标点字面量半角全角肉眼不可辨,连续三次替换"成功"实未生效
- 纪律:两处都改;脚本替换一律 `chr(0xFF0C)` 码点写法;完成后用 `ord()` 打印码点验证

## 4. 句间停顿长 + 咔哒杂音(EP.02 v2 前)
- 现象:句间 0.5~0.7s 停顿;拼接点咔哒声
- 根因:TTS 每句自带 0.2~0.3s 头尾静音 + 0.35s 拼接间隙;拼接点波形非零跳变
- 修复:管线 v2 —— silenceremove(-50dB,两端留 15ms,areverse 技巧裁尾)→ audio/clean/;拼接时每句 12ms afade(尾部 areverse 技巧);gap 0.35→0.18
- 验证标准:拼接点 ±20ms 窗口峰值必须为 0(verify_splice.py)

## 5. 新文案配旧音频(EP.02 s5b1)
- 现象:口播仍是"为什么人人都在说这个词"
- 根因:场景重编号时旧音频文件跟着 mv 到新编号,gen_timeline 检测到文件存在跳过重录
- 修复:删除强制重录;asr_check.py 终验
- 纪律:**改词必删旧 mp3;重编号/迁移后逐句核对词是否变更**

## 6. 字幕用了旧文案(EP.01 v3)
- 现象:script.json 已全角化,SRT 里仍输出半角
- 根因:assemble.py 读的是 timeline.json(缓存了首次 gen_timeline 时的 text),不是 script.json
- 纪律:**改词/标点后必须重跑 gen_timeline**(音频在则只刷文本),再 assemble

## 7. 英文词口音(EP.02 hello)
- 现象:飞哥听 hello 发音不对;词级/整句 ASR 都能转出 hello(说明读的是这个词),问题在口音
- 处置:该句用 crosslingual 语种模式重录;asr_check.py 保底验证"没读成别的词",口音终判只能用户人耳
- 纪律:英文词多的句子先默认合成+asr_check,不合格再 crosslingual;重要英文例词先请用户听样

## 8. 画面与字幕重叠(EP.02)
- 现象:S1 提示行、S3 脚注、S6 点题句都压在字幕带
- 修复:底部 y≥850 划为字幕带;与旁白重复的画面文字直接删;必要脚注上移
- 纪律:画面元素底边 ≤830;vision 审片必带"字幕是否压画面"检查项

## 9. Token 片口径自洽(EP.02 v3)
- 现象:初版"1 token ≈ 0.7 汉字"与实测/飞哥口径矛盾
- 修复:飞哥口径 1 token ≈ 1.3~1.6 汉字落地后,联动修了换算注释、128K 换算、中文切分示例三处
- 纪律:改任何事实数字,全文(口播+画面)自洽排查

## 10. EP.01 片尾预告卡在左上角(v4→v5)
- 现象:outro 卡停在左上角
- 根因:新写 EP.01 时漏了 `#sc7{display:flex;...}` 居中规则,outro(absolute 无坐标)停在流起点
- 教训:抽帧必须抽到**片尾最后一帧**——之前 9 帧全在 outro 入场前,漏检
- 同场加映:EP.02 片尾黑场失效——renderFrame 里 veil 判断写死 `s7`,重编号后收尾是 s8,每帧被覆盖成 0
- 纪律:veil 由收尾场景函数全权负责;新场景 section 必配居中规则;审片含最后一帧

## 11. 期数/命名(EP.02 迁移)
- 系列 v2 调整(GPT/LLM 前置)时:目录 mv + 角标/进度点/episode 同步 + assemble 输出名按 `AI黑话图鉴-EP{NN}-{slug}.mp4` 自动生成(script.json 加 slug)
- 纪律:改期数时全局搜索 "EP.0" 与 episode 字段,画面(角标/outro)与元数据(script.json)一致

## 12. 技能固化首轮审查发现的缺陷(2026-10-06,reviewer 对抗审查)
- **assemble.py ffprobe 探测 final.mp4 但产物已改名 OUT_NAME** → 每次运行末尾 KeyError 崩溃、退出码非 0(此前在 EP.01 上出现过一次,被误判为"统计步骤瞬时失败")。修:探测 OUT_NAME + 检查 returncode。
- **verify_splice 检查窗落在 apad 纯静音区(结构性永远 0)** → 检查点必须是真实缝:句尾缝 end-gap 与下句头缝 end 各开窗。修后经反证试验验证:响亮处硬切检出 25.9%>15% 报警;正常产物缝值 131~1235(≈0.6-6%)通过。
- **模板提取时把场景 CSS 整段切除** → outro/.ot 等样式与 #sc2 flex 居中全部丢失,且构件库规则被包进注释不生效——"示例自己就渲染错"。教训:**固化模板后必须用真实渲染冒烟(截图人看)+ 反证测试(故意破坏应报警)**,不能只 grep id 引用。
- **SKILL.md 把新增未验证产物包装进"已跑通"承诺** → 诚实分层:三件套与两期逐字节同源;新增脚本/模板注明验证状态。
- **占位符无守卫** → 模板占位文案直送 TTS 会烧钱;gen_timeline 加 assert_no_placeholder(退出码 1)。
- **环境依赖漏报 ark-tts/ark-asr 技能路径** → 补 TTS_SH/ASR_SH 环境变量覆盖。
- **tutorials 工作区未纳入 AGENTS.md 生成体系** → emit_agents_md.py FAMILIES 注册后重新生成。
