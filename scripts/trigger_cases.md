# 触发回归用例集

改技能 description 前后各核对一遍：把「用户话术」逐条丢给新会话（或让主 agent 模拟触发判断），
实际触发的技能必须与「期望」一致。任何一条变了，先判断是 wording 改坏了还是预期本该更新，
再改 description——触发漂移是技能仓库最常见的静默退化。

覆盖已部署家族（ark 用户级 + paper/novel/patent/douyin 项目级）。nex 未部署，不在触发面内。

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
| N8 | （歧义）「继续写」无卷纲时 | 应引导先 /novel-volume，不得裸写正文 |

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

## 跨家族抑制（不该触发的）

| # | 用户话术 | 期望 |
|---|---------|------|
| X1 | （papers 工作区）写一章网文 | 不触发 novel-chapter（未安装），提示去 novels 工作区 |
| X2 | 帮我把这个 PPT 改成 16:9 | 走内置 presentations:pptx 技能，不触发 ark-image-gen |
| X3 | 翻译这段话 | 无技能匹配，主 agent 直接做，不得误触任何家族 |
