#!/usr/bin/env python3
"""Stage 5｜合判 + 拼表：数值红线用代码算，覆盖模型判定，输出可写 Sheet 的行。

判定优先级（2026-08-06 Selene 定，见 youtube/RUBRIC.md 与 DISCARD.md）：
1. 已签/确认合作 → 「已签·豁免」，不进 rubric 重审
2. 互动双失配（点赞率<0.5% 且 每万播放评论<5）→ 弃（买量特征）
3. 机构/品牌号 → 弃
4. 模型判「捞」但标了内容 flag，或触达/体量偏弱 → 降「观察」（不是放弃，等人复核）
5. 停更只标注，不降级

输入 data/metrics.json + data/engage.ndjson + 分类结果
输出 data/sheet_rows.json（第一行是表头）

用法: python3 youtube/scripts/05_export.py data/classified.ndjson [--signed 确认合作]
"""
import argparse, collections, json, os

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
ap = argparse.ArgumentParser()
ap.add_argument("classified")
ap.add_argument("--signed", default="确认合作", help="metrics 的 src/note 里出现该词即视为已签，豁免重审")
args = ap.parse_args()

M = {m["key"]: m for m in json.load(open(os.path.join(DATA, "metrics.json")))}
ENG = {}
p = os.path.join(DATA, "engage.ndjson")
if os.path.exists(p):
    for l in open(p):
        d = json.loads(l)
        ENG[d["key"]] = d
CLS = {}
for l in open(args.classified):
    d = json.loads(l)
    CLS[d["key"]] = d

HEADER = ["捞", "Handle", "频道名", "主页链接", "来源", "订阅", "长视频中位播放", "中位÷订阅",
          "每万播放评论数", "点赞率%", "Shorts支数", "Shorts中位播放", "距上次发布(天)", "近30天更新",
          "builder指数", "合格通道", "受众层", "AI姿态", "主线3词", "数值红线(代码算)",
          "内容提示(模型标注·非判决)", "模型原判", "判定理由", "原记录", "证据·近5支标题"]

KILL = ("互动双失配",)
SOFT_CONTENT = ("teaching_novices", "money_farm", "growth_marketing_identity", "hype_farm")
DOWNGRADE = ("互动单项偏低", "中位÷订阅仅", "shorts虚胖", "体量小")


def numeric_flags(m, e):
    f = []
    lp, c10k = e.get("like_pct"), e.get("comment_per_10k")
    if lp is not None and c10k is not None:
        if lp < 0.5 and c10k < 5:
            f.append(f"互动双失配(赞{lp}%/评{c10k})")
        elif lp < 0.5 or c10k < 5:
            f.append(f"互动单项偏低待核(赞{lp}%/评{c10k})")
    if (m.get("days_since_last") or 0) > 180:
        f.append(f"停更{m['days_since_last']}天")
    if (m.get("subs") or 0) < 5000:
        f.append(f"体量小({m.get('subs')})")
    if m.get("ratio_long") is not None and m["ratio_long"] < 0.02:
        f.append(f"中位÷订阅仅{m['ratio_long']}")
    sm, ml = e.get("shorts_med_views"), m.get("med_views_long")
    if (e.get("n_shorts") or 0) >= 5 and sm and ml and sm > 3 * ml:
        f.append(f"shorts虚胖(short中位{sm} vs 长视频{ml})")
    if m.get("growth_bio_hits"):
        f.append("bio写growth/marketing:" + ",".join(m["growth_bio_hits"]))
    return f


def final_verdict(mv, nflags, cflags, signed):
    if signed:
        return "已签·豁免"
    joined = " ".join(nflags)
    if any(k in joined for k in KILL):
        return "弃"
    if "institution_or_brand" in cflags:
        return "弃"
    if mv == "捞" and (any(k in cflags for k in SOFT_CONTENT) or any(k in joined for k in DOWNGRADE)):
        return "观察"
    return mv if mv in ("捞", "观察", "弃") else "观察"


order = {"已签·豁免": 0, "捞": 1, "观察": 2, "弃": 3}
built = []
for k in CLS:
    m, c, e = M[k], CLS[k], ENG.get(k, {})
    nf, cf = numeric_flags(m, e), (c.get("hard_flags") or "")
    signed = args.signed in (m.get("src", "") + m.get("note", ""))
    fv = final_verdict(c.get("verdict", "?"), nf, cf, signed)
    orig = " / ".join(x for x in [m.get("src"), m.get("note"), m.get("dup_conflict", "")] if x)
    built.append((fv, m.get("subs") or 0, [
        fv, m.get("handle", ""), m.get("channel_name", ""), m["url"], m.get("src", ""),
        m.get("subs"), m.get("med_views_long"), m.get("ratio_long"),
        e.get("comment_per_10k"), e.get("like_pct"), e.get("n_shorts"), e.get("shorts_med_views"),
        m.get("days_since_last"), m.get("uploads_30d"),
        c.get("builder_index"), c.get("lane", ""), c.get("audience_layer", ""), c.get("ai_stance", ""),
        c.get("topic_3", ""), "；".join(nf), cf, c.get("verdict", "?"), (c.get("reason") or "")[:190],
        orig[:70], " | ".join(m.get("titles", [])[:5])[:150],
    ]))
built.sort(key=lambda t: (order.get(t[0], 4), -t[1]))
rows = [HEADER] + [b[2] for b in built]
json.dump(rows, open(os.path.join(DATA, "sheet_rows.json"), "w"), ensure_ascii=False)
print(f"{len(rows) - 1} 行 -> data/sheet_rows.json")
print(collections.Counter(r[0] for r in rows[1:]))
