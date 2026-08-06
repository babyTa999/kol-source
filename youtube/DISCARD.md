# 弃选口径（YouTube 线）

筛选类产出必须带弃选口径，否则「捞出来的人」没法复核。本文记录 2026-08-06 全量 301 频道复筛中
202 个「弃」是按什么剔的，以及每一类的反例（长得像但不该弃 / 看着能要但要弃）。

## 一、结构性否决（不随 campaign 变，永久弃）

| 类别 | 判据 | 本批案例 |
|---|---|---|
| 机构号 / 品牌号 / 公司号 | 频道名或 bio 自述是机构、公司、平台、培训品牌 | Ninja Nerd（"Official Ninja Nerd Website"）· AsapSCIENCE（"ASAPSCIENCE INC."）· DataExpert · Maven Analytics · JetBrains Academy · Clio · SAIR · Website Learners · Teacher's Tech |
| 纯播客 / 访谈节目号 | 双主持、每周固定档期、内容全是嘉宾访谈 | Syntax（Wes Bos & Scott Tolinski）· OMGenomics · Limitless Podcast · Everything AI and Law · Hidden Brain |
| 媒体化频道 | 主线是新闻/案件/时事评论，受众是大众 | LegalEagle · How Money Works · Law By Mike · BlackBeltBarrister · Two Minute Papers |
| 涨粉 / 营销 / 变现方法论 | **主线内容**是 YouTube 涨粉、SEO、投流、接活、月入多少 | Mike and Matty · Roberto Blake · SocialtyPro · Danny Why · Automation Xpert · Thinkverse AI · Income stream surfers |
| 教小白入门 | 主线是 "best AI tools" / "for beginners" / "zero to hero roadmap" / top-N 清单 | Skill Leap AI · Alex The Analyst · Luke Barousse · Parker Prompts · AI by Aly · digitalSamaritan |

**反例（别误伤）**：bio 里写自己是 agency owner / consultant / 有多少营收，但视频主线是技术内容 → **不弃**
（Bart Slodyczka、Coding Jesus、AI Jason 在 v1 都因此被误杀）。判定只看主线内容。

## 二、受众错位（随 campaign 口径变，1.1 弃 / 别的 campaign 可能能用）

- 受众是**泛 AI 工具用户 / 内容创作者**：Matt Wolfe · MattVidPro · AI Zayan · Tina Huang · Jeff Su
- 受众是**散户投资者 / 交易者**：Ticker Symbol: YOU · The Moving Average · James Shack · Brian Feroldi · 一整批 quant/trading 频道
- 受众是**大众科普 / 吃瓜**：Angela Collier · SciencePetr · Robert Miles · Looking Glass Universe · BrainCraft
- 受众是**医疗/法律从业者但零 AI**：Doc Schmidt · Attorney Ryan · The Law Simplified · the bumbling biochemist

> 这一类务必标清「因受众错位而弃」，因为换 campaign（如医疗 AI 线、AFP 科研线）时这批要重新捞回来，
> 不是永久黑名单。

## 三、数据否决（代码算，见 RUBRIC.md 阈值表）

- **互动双失配（买量嫌疑）**：点赞率 <0.5% 且 每万播放评论 <5。本批 5 人：Atef Ataya（120 万播放 9 个赞）·
  CodingEntrepreneurs（2025 年 2–3% → 2026 年 0.05–0.18% 的双峰，典型中途开始买量）· CodeWithMuh · SolomonChristAI · beau
- **触达虚高**：长视频中位 ÷ 订阅 < 2%。本批案例 Website Learners（289 万订阅 / 中位 8,100）·
  Teacher's Tech（118 万 / 5,100）· The Law Simplified（11.6 万 / 95）
- **停更**：只标注不弃（Selene 2026-08-06 定）。但停更 >180 天的人**不进建联排期**，单列 T4-存档：
  Karpathy（525 天）· Reducible（740 天）· Umar Jamil（557 天）· connor-shorten（724 天）· James Briggs（308 天）· AI Coffee Break（270 天）

## 四、不作为弃选依据的东西

- **订阅数**：本批捞回的人订阅中位数只有 10.6 万，最小 6,880；而 100 万+ 的大号里没有一个通过 1.1 口径
- **国籍**：不按国籍卡（会误伤，如 CodeTradingCafe 频道地黎巴嫩但内容是正经算法交易）。按「受众地域 + 内容原创性」判
- **单条视频**：搜索/推荐命中的那条可能是旧库存单发，必须看近 15 支标题定主线（见 LESSONS.md 同类事故）
- **模型的 hard_flags**：模型标 flag 不一致，只当提示，不当判决
