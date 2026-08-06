# kol-source — KOL Sourcing 管线（X + YouTube）

从画像定义到落地 Google Sheet 的完整 KOL sourcing SOP + 可执行脚本。X（Twitter）线见下；**YouTube 线见 [youtube/PIPELINE_YT.md](youtube/PIPELINE_YT.md)**。给用 Claude Code / Codex 的同事：clone 下来、填好 `.env`、在 repo 里开 agent 就能跑。

## 这个 repo 里有什么

| 文件 | 内容 |
|---|---|
| [PIPELINE.md](PIPELINE.md) | 完整管线 6 阶段：画像定义 → 搜寻 → 硬门槛筛选 → 画像验证 → 去重 → 落表；工具选型与成本速查 |
| [SCHEMA.md](SCHEMA.md) | 表维度（10 基础列 + 备注格式约定）、10 类·3 方向分类体系、归类规则 |
| [LESSONS.md](LESSONS.md) | 经验教训（画像列 40% 错误率事故、中文圈识别规则、成本与协作纪律） |
| [AGENTS.md](AGENTS.md) / CLAUDE.md | agent 操作手册：判定标准、一票否决清单、改表纪律、产出格式 |
| `scripts/` | X 线 Stage 3（画像验证）可执行脚本，其余阶段由 agent 按 PIPELINE.md 驱动工具完成 |
| [youtube/PIPELINE_YT.md](youtube/PIPELINE_YT.md) | **YouTube 线完整管线**：6 步全脚本化，验证层 0 credits（yt-dlp + RSS），Deepline 只买判断，301 频道全量 ≈ $0.3 |
| [youtube/RUBRIC.md](youtube/RUBRIC.md) | YouTube 判据（rubric v2，dev/builder 口径）+ 数值红线阈值表；这份文件同时是喂给模型的 prompt |
| [youtube/DISCARD.md](youtube/DISCARD.md) | YouTube 弃选口径：每类为什么弃、反例、以及哪些东西不作为弃选依据 |
| `youtube/scripts/` | 01 免费抓取 → 02 去重算指标 → 03 互动质检 → 04 定性判断 → 05 代码红线合判 → 06 建联优先级 |

> 起因：2026-07 中文区 KOL 池复核发现批量建表的画像列错误率 ~40%——农场号被写成科研博主、负债学量化的奶爸被写成 LegalTech 分析师。**核心铁律：画像列必须逐人回读时间线验证。** 详见 LESSONS.md。

## 依赖

- [Deepline CLI](https://deepline.ai)（`deepline` 已登录；twitterapi provider，~$0.001/条）
- Python 3.10+（仅标准库）
- Claude Code 或 Codex CLI（判断由 agent 完成）
- 目标 Sheet 开「知道链接可查看」（读走 gviz）；写回凭据问表格 owner 要（走 `.env`，不进 git）

## 快速开始（agent 驱动，推荐）

```bash
cp .env.example .env   # 填 SPREADSHEET_ID / GID / TAB
claude                 # 或 codex
> 帮我核实这张 KOL 表的标签，跑完整管线      # 验证已有池
> 按 PIPELINE.md 给 <画像> 搜一批新 KOL      # 从零 sourcing
```

## 手动分步（Stage 3 验证）

```bash
python3 scripts/fetch_sheet.py            # 1. 读回表格现状 -> data/sheet_current.csv
python3 scripts/extract_handles.py        # 2. 提取账号+行号 -> data/handles.tsv
bash scripts/pull_timelines.sh            # 3. 拉时间线（断点续传）-> data/tl_*.json
python3 scripts/digest.py > data/digests.txt   # 4. 标签 vs 实际 对照摘要
# 5. agent/人工读 digests.txt 逐人判断 -> data/edits.json（格式见下）
python3 scripts/apply_edits.py data/edits.json          # 6. 预览
python3 scripts/apply_edits.py data/edits.json --write  #    写回（定点单元格）
```

### edits.json 格式

```json
[
  {"row": 9, "cells": {"E": "娜美知识库·情感话题/资源搬运引流号", "F": "弱"},
   "note_prepend": "🔴删除候选：农场号（空bio·情感引流+资源搬运）"}
]
```

`cells`＝列字母→新值直接覆盖；`note_prepend`＝前置追加到备注列（默认 J），**原备注自动保留**（`｜` 分隔）。

## 改表纪律（不可违反，详见 PIPELINE.md Stage 5）

Sheet 是唯一真相源（写前必读回现状）；只做定点增量；删除候选只标不删；备注只追加；写完汇报明细。

## 成本参考

93 账号全量验证 ≈ $2、几分钟。**建表后立即跑一轮验证**，别等投放前才发现标签是编的。
