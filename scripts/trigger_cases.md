# 触发回归用例集

改技能 description 前后各核对一遍：把「用户话术」逐条丢给新会话（或让主 agent 模拟触发判断），
实际触发的技能必须与「期望」一致。任何一条变了，先判断是 wording 改坏了还是预期本该更新，
再改 description——触发漂移是技能仓库最常见的静默退化。

覆盖已部署家族（ark、social 用户级 + paper/novel/patent/douyin 项目级）。nex 未部署，不在触发面内。

## paper 系（papers 工作区）

| # | 用户话术 | 期望 |
|---|---------|------|
| P1 | 我想写一篇关于 LLM 稀疏注意力的论文，从选题开始 | paper-proposal |
| P2 | 帮我做这个题目的文献综述 | paper-litreview |
| P3 | 设计并跑一下对比实验 | paper-experiment |
| P4 | 开始写初稿 / 写第四章实验分析部分 | paper-draft |
| P5 | 模拟审稿人给我提意见，然后改稿 | paper-revise |
| P6 | 审稿意见回来了，帮我写 rebuttal | paper-rebuttal |
| P7 | 投 CVPR 前帮我按模板整理投稿材料 | paper-submit |
| P8 | （歧义）「写论文」不带阶段信息 | 应问清阶段或从 proposal 引导，不得直接开写正文 |

## novel 系（novels 工作区）

| # | 用户话术 | 期望 |
|---|---------|------|
| N1 | 我想写一本都市修仙小说，先调研下市场 | novel-research |
| N2 | 定总大纲 / 故事主线 | novel-outline |
| N3 | 搭力量体系和地图设定 | novel-worldview |
| N4 | 设计主角和女主 人物档案 | novel-characters |
| N5 | 写第一章到第三章（开篇） | novel-opening（不是 novel-chapter） |
| N6 | 继续写第 47 章 / 批量写到 50 章 | novel-chapter（且顺序执行不并行） |
| N7 | 给这本书做个封面 | novel-cover |
| N8 | （歧义）「继续写」无章节号 | 路由到 novel-chapter（中置信可接受），其正文前置检查发现缺已确认卷纲时必须引导先 /novel-volume，不得裸写正文（路由层 + 技能内前置检查两层防线） |

## patent 系（patents 工作区）

| # | 用户话术 | 期望 |
|---|---------|------|
| T1 | 我有个技术想法，帮我挖发明点写交底书 | patent-disclosure |
| T2 | 检索一下这个方案的新颖性 / 现有技术 | patent-priorart |
| T3 | 写权利要求书 | patent-claims |
| T4 | 根据已批权要写说明书和摘要 | patent-draft |
| T5 | 审查意见下来了，帮我答复 OA | patent-oa |

## douyin 系（douyin 工作区）

| # | 用户话术 | 期望 |
|---|---------|------|
| D1 | 剖析这个视频 https://v.douyin.com/xxx | douyin-video-analysis |
| D2 | 分析「张三说财」这个账号 | douyin-account-analysis（含作者归属验证） |
| D3 | （分界）同一句话里既有链接又有账号名 | 链接优先单视频，账号分析需用户明确 |

## ark 系（用户级，全局）

| # | 用户话术 | 期望 |
|---|---------|------|
| A1 | 把这段文字用我的声音读出来 | ark-tts（复刻音色） |
| A2 | 转写这段录音 / 会议录音转文字 | ark-asr |
| A3 | 生成一张 16:9 的海报配图 | ark-image-gen |
| A4 | 做一段 15 秒的文生视频 | ark-video-gen |
| A5 | 做一段带 BGM 和多角色对白的广播剧片段 | ark-audio-gen（不是 ark-tts） |

## social 系（用户级，全局）

| # | 用户话术 | 期望 |
|---|---------|------|
| S1 | 把这些要点做成一套 3:4 小红书贴图 + 文案 | social-cards |
| S2 | 内容都在这份文件里（给定路径），出一组公众号图文卡片和发布文案 | social-cards（直接用给定内容，不重新调研） |
| S3 | （缺内容）「做一套 XX 发布的贴图」但对话里没有任何要点/数据 | social-cards 触发后先停下要素材或先调研，不得编造数据产图 |
| S4 | （分界）「生成一张 16:9 海报图」「画一只猫」 | ark-image-gen（无卡组 + 文案交付诉求，不触发 social-cards） |
| S5 | 帮我写一篇公众号文章，讲讲 XX | social-article |
| S6 | 给这篇内容出 3 个公众号标题（标注当量）+ 摘要 | social-article |
| S7 | 写一篇头条号文章 / 头条文章 | social-article |
| S8 | 把这篇文章排版好，提交到公众号草稿箱 | wechat-mp-draft |
| S9 | 给公众号文章做个封面图 | wechat-mp-draft（封面在其职责内；只要图不提交时走其 cover 流程） |
| S10 | （分界）「公众号文章配图」 | 按形态路由：3:4 卡组 → social-cards；正文横幅/金句卡 → social-article |
| S11 | （分界）「把文章直接发出去 / 群发」 | wechat-mp-draft 只到草稿箱，须说明发布需后台手动操作 |

## 跨家族抑制（不该触发的）

| # | 用户话术 | 期望 |
|---|---------|------|
| X1 | （papers 工作区）写一章网文 | 不触发 novel-chapter（未安装），提示去 novels 工作区 |
| X2 | 帮我把这个 PPT 改成 16:9 | 走内置 presentations:pptx 技能，不触发 ark-image-gen |
| X3 | 翻译这段话 | 无技能匹配，主 agent 直接做，不得误触任何家族 |
| X4 | 帮我写个小红书文案，不用配图 | 主 agent 直接写；social-cards 以「卡组 + 文案包」为交付，纯文字请求不触发 |
