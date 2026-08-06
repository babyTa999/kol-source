# YouTube KOL 复筛管线

给一批 YouTube 频道链接，输出「捞 / 观察 / 弃」+ 建联优先级。
和 X 线（[PIPELINE.md](../PIPELINE.md)）的关键差别：**YouTube 的验证层完全免费**，
Deepline 只用来做定性判断，所以全量几百个频道的成本在 $1 以内。

```
channels.csv → 01 免费抓取 → 02 算指标+去重 → 04 定性判断 → 03 互动质检 → 05 合判 → 06 排优先级 → 落表
                （yt-dlp/RSS）                  （deeplineagent）  （yt-dlp）    （代码红线）
```

## 成本速查

| 层 | 工具 | 成本 | 耗时（301 频道实测） |
|---|---|---|---|
| 频道元数据 + 近 15 支标题/播放/时长 | `yt-dlp --flat-playlist -J` | **0** | ~13 分钟（4 并发） |
| 发布节奏 / 停更天数 | 频道 RSS `feeds/videos.xml?channel_id=` | **0** | 同上（并在一起） |
| 评论数 / 点赞数 / Shorts 页 | `yt-dlp --no-playlist -J` 单视频 | **0** | ~12 分钟（5 并发，只跑存活者 101 人） |
| 定性判断 | `deepline tools execute deeplineagent`（gpt-5.4-mini，20 人/批） | **~$0.02/批**，301 人 ≈ $0.3 | ~40 分钟 |

**⛔ 不要用**：apify YouTube channel scraper（历史上占掉 Deepline 78% 花费，见 [LESSONS.md](../LESSONS.md)）、
scrapecreators youtube_search（只能搜，拿不到频道级数据）、任何 advanced search / people search。
免费层已经覆盖所有可量化红线，付费层只买"判断"。

## 分步跑

```bash
cd <repo>
# 0. 准备输入：表头 url,handle,src,note（url 必填；src 写来源池，note 写原记录/进度）
#    src 或 note 里出现「确认合作」的人会被自动标为「已签·豁免」，不进 rubric 重审
vi youtube/data/channels.csv

python3 youtube/scripts/01_fetch_free.py                 # 0 credits，断点续传
python3 youtube/scripts/02_metrics.py --today 2026-08-06  # 去重 + 指标 + 打印分位数

# 先看分位数再定阈值（换赛道别照搬旧阈值）
python3 -c "import json;print(len(json.load(open('youtube/data/metrics.json'))))"
python3 -c "import json;[print(m['key']) for m in json.load(open('youtube/data/metrics.json'))]" > youtube/data/all_keys.txt

python3 youtube/scripts/04_classify.py youtube/data/all_keys.txt youtube/data/classified.ndjson   # 花钱的一步
# 只给活下来的人跑互动质检（互动双失配是唯一硬杀项，捞出来的人必须都有这个数）
python3 -c "
import json;rows=[json.loads(l) for l in open('youtube/data/classified.ndjson')]
open('youtube/data/survivors.txt','w').write('\n'.join(r['key'] for r in rows if r['verdict'] in ('捞','观察')))"
python3 youtube/scripts/03_engage.py youtube/data/survivors.txt

python3 youtube/scripts/05_export.py youtube/data/classified.ndjson   # 代码红线合判 -> sheet_rows.json
python3 youtube/scripts/06_priority.py                                 # 捞的人排 T1–T4 + 动作
```

## Pilot 纪律（第一次跑新赛道必须做）

别直接全量。先抽 40 人的探针批，三段抽样，目的是**看清分布而不是出名单**：

1. **20 人**目标池（比如上一轮被筛掉的人里疑似合格的）
2. **10 人 golden set** —— 已有人工画像的人，用来算「机器判断 vs 人工判断一致率」。这是唯一的准确性指标
3. **10 人**当前池里停滞的，看是判断偏了还是商务卡住

跑完先在对话里给分布简报（分位数、机构号残留比例、和人工画像的分歧点），拿到纠偏再上全量。

**2026-08 实测的 golden set 结论**：表面一致率 75%，但 4 个分歧全指向同一件事 ——
「AI 相关强弱」和「动手 build 度」是两个**正交维度**（Matt Wolfe 人工标 AI=强但动手度 2；
Coding Jesus 人工标 AI=弱但动手度 5）。**旧 rubric 的标签不能直接迁到新 campaign。**

## 模型判定会抖动（已实测）

同一个频道在不同批次里可能翻结论：How I AI 在 301 人全量跑里是「捞」（builder_index 5），
在 4 人的 smoke test 里被判「弃」。批内上下文不同 → 判定漂移，这是 LLM 的固有抖动，不是 bug。

因此：
- **单次跑出来的「弃」不要当定论**，尤其是数据面（触达/互动/更新频率）没问题的人
- 可量化的东西全部交给 `05_export.py` 的代码红线，那部分是确定性的
- 每次换 rubric 或换模型，重跑一遍 golden set 看一致率，别只看总数变化

## 落表

`data/sheet_rows.json` 第一行是表头，直接写 Google Sheet 新 tab。
两条已验证的坑：
- 本地 google-sheets MCP（localhost:3000）的 `tools/call` 需要 Bearer token，**脚本直连会 401**，只能走 MCP 工具；
  几百行要分批写（40 行/批），并先 `appendDimension` 扩够行数和列数，否则报 "exceeds grid limits"
- 复活标记用一个字：**「捞」**写在 A 列；另有「观察 / 弃 / 已签·豁免」

判据与弃选口径见 [RUBRIC.md](RUBRIC.md) 与 [DISCARD.md](DISCARD.md)。
