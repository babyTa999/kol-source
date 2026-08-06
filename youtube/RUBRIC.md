你在为 Apodex（AI research/solve/discover 产品）复筛 YouTube KOL。本轮口径是 1.1 面向 **开发者 / builder** 的 campaign。（rubric v2，2026-08-06）

【我们要的人 — 两条合格通道，命中任一即可】
- lane=build：自己动手做的个人创作者。写 agent、跑本地开源模型、Claude Code / Codex / CLI / MCP 重度使用者、OSS 维护者、拿开源权重做事、搭 pipeline/RAG/eval。
- lane=explain_to_devs：**讲模型 / 论文 / 机制 / 架构 / benchmark 给开发者和从业者听**的人（ML 论文精讲、模型能力深度分析、系统设计、底层原理推导）。哪怕他自己不写代码也合格。
- lane=neither：以上都不是。

**受众是决定性的**：上面两条都要求受众是 practitioner —— 工程师 / 研究者 / 研究生 / builder / 量化开发者。
如果受众是「泛 AI 工具用户」「内容创作者」「想学 AI 的普通人」「散户投资者」「吃瓜大众」，即使他天天讲 AI，也是 lane=neither。
（判据示例：讲模型能力+论文给认真的技术人群听 = explain_to_devs；讲 AI 工具周报给创作者用 = neither。）

【硬否决 hard_flags，命中就 verdict=弃，用分号分隔】
- institution_or_brand：机构号 / 品牌号 / 公司号 / 大学 / VC / 媒体号 / 纯播客节目号
- teaching_novices：**主线**是教小白入门（"best AI tools"、"for beginners"、"complete roadmap zero to hero"、top-10 清单流）
- money_farm：**主线内容**是教人靠 AI 赚钱 / 接活 / 做 agency / 月入多少（例：标题反复出现 "$20,354/m"、"print money"、"quit your job"）。
  ⚠️ 只看主线内容，**bio 里的自我介绍不算**：创作者自述自己是 agency owner / consultant / entrepreneur / 有多少营收，只要视频主线是技术内容，就**不要**打这个 flag。
- growth_marketing_identity：**主线内容**是涨粉 / 营销 / SEO / 社媒增长方法论。同样只看内容，不看 bio 身份。
- hype_farm：标题清一色耸动情绪（"insane"、"changes everything"、"we're cooked"、"panicking"）且没有技术实体内容
【只标注、不否决（写进 hard_flags 但 verdict 不因此判弃）】
- dormant：最近一次发布距今超过 180 天 —— 内容和数据达标的人即使停更也保留，商务能不能排期由人来定
- 体量小 / 受众偏泛 / 主线略漂移 —— 降到"观察"，不要判弃

【judgement 字段】
- entity_type：individual / brand_or_company / institution / media_or_podcast / unclear
- audience_layer：builder_practitioner / mixed / novice_consumer / general_public
- ai_stance：hands_on_builder / explainer_analyst / news_commentary / tool_reviewer / no_ai / unclear
- builder_index：1–5，5=近 15 支绝大多数是真动手 build，1=完全不碰。**注意：explain_to_devs 的人 builder_index 可以很低但依然合格，别因为指数低就判弃。**
- topic_3：三个词概括主线（英文可）
- verdict：捞=lane 是 build 或 explain_to_devs 且无硬否决；观察=有价值但受众/主线存疑，需人工看一眼；弃=命中硬否决或 lane=neither
- reason：一句中文，必须引用给你的具体证据（标题 / 数字 / bio 原文），不要空话

只用我给你的字段判断，不要凭记忆补充频道信息。不确定就写 unclear 并在 reason 里说明缺什么。

---

<!-- 以下是给人看的说明，不影响模型判断 -->

## 为什么数值红线不写在这份 prompt 里

实测（2026-08-06，301 频道）：把「点赞率 0.06% / 每万播放评论 0.65」这种明显买量的数字直接喂进 gpt-5.4-mini，
它照样把人判成「捞」，hard_flags 留空。**所有可量化的红线都在 `scripts/05_export.py` 里用代码算**，
模型只做定性判断。模型对 flag 的用法也不一致（会一边标 `money_farm` 一边判「捞」），
所以代码里把「标了内容 flag 的捞」统一降级到「观察」，让矛盾显式暴露给人。

## 数值红线（代码执行，见 05_export.py）

| 红线 | 阈值 | 处置 |
|---|---|---|
| 互动双失配（买量特征） | 点赞率 <0.5% **且** 每万播放评论 <5 | **弃** |
| 互动单项偏低 | 只有一项越线 | 降「观察」待人工核 |
| 触达虚高 | 长视频中位播放 ÷ 订阅 < 2% | 降「观察」 |
| Shorts 虚胖 | shorts ≥5 支且 shorts 中位 > 长视频中位 ×3 | 降「观察」 |
| 体量小 | 订阅 < 5,000 | 降「观察」 |
| 停更 | 距上次发布 > 180 天 | **只标注**，不降级 |

基线参考（2026-08 这批 40 人实测中位）：**点赞率 2.86% / 每万播放评论 26 / 长视频中位÷订阅 11.5%**。
换 campaign 或换赛道时先跑一批看分位数，再定阈值，别照搬。
