#!/usr/bin/env python3
"""Stage 6｜给「捞」出来的人排建联优先级：契合度 + 可排期性 + 触达 + 互动健康。

分层：T1-首发 / T2-次轮 / T3-补位 各占存活者的三分之一；停更 >180 天单列 T4-存档（不排期）。
动作：已建联中的标「推进」，筛掉池新捞的标「新建联」。

输入 data/sheet_rows.json → 输出 data/priority.json（含 sheet 行号，便于定点写列）

用法: python3 youtube/scripts/06_priority.py
"""
import collections, json, os

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
rows = json.load(open(os.path.join(DATA, "sheet_rows.json")))
lao = []
for i, r in enumerate(rows[1:], start=2):      # i = Sheet 行号（表头占第 1 行）
    if r[0] != "捞":
        continue
    subs, medl, ratio = r[5] or 0, r[6] or 0, r[7] or 0
    like, days, up30 = r[9], (r[12] if r[12] is not None else 999), r[13] or 0
    bi = r[14] if isinstance(r[14], int) else 0
    lane, aud, nf, cf = r[15], r[16], r[19] or "", r[20] or ""
    fit = bi * 2 + (3 if aud == "builder_practitioner" else (1 if aud == "mixed" else 0))
    fit += 2 if lane in ("build", "explain_to_devs") else 0
    fit -= 2 if cf else 0
    sch = 5 if days <= 30 else (3 if days <= 90 else (1 if days <= 180 else -99))
    sch += 2 if up30 >= 4 else (1 if up30 >= 1 else 0)
    reach = 4 if medl >= 100000 else (3 if medl >= 30000 else (2 if medl >= 10000 else (1 if medl >= 5000 else 0)))
    reach -= 1 if (ratio and ratio < 0.02) else 0
    eng = (1 if (like or 0) >= 3 else 0) - (2 if "偏低待核" in nf else 0)
    lao.append(dict(row=i, name=r[2], handle=r[1], src=r[4], subs=subs, medl=medl, days=days,
                    bi=bi, lane=lane, fit=fit, sch=sch, reach=reach, eng=eng,
                    total=fit + sch + reach + eng, dormant=sch < 0))
live = sorted([d for d in lao if not d["dormant"]], key=lambda d: (-d["total"], -d["medl"]))
dead = sorted([d for d in lao if d["dormant"]], key=lambda d: -d["medl"])
third = max(1, len(live) // 3)
for n, d in enumerate(live, 1):
    d["rank"] = n
    d["tier"] = "T1-首发" if n <= third else ("T2-次轮" if n <= third * 2 else "T3-补位")
for n, d in enumerate(dead, len(live) + 1):
    d["rank"], d["tier"] = n, "T4-存档(停更)"
for d in lao:
    d["act"] = ("存档·不排期" if d["tier"].startswith("T4") and "建联" not in d["src"]
                else ("推进(已建联)" if "建联" in d["src"] else "新建联"))
    d["why"] = (f"契合{d['fit']}/排期{d['sch'] if d['sch'] > 0 else '停更'}/触达{d['reach']}/互动{d['eng']}"
                f"｜{d['lane']}·bi{d['bi']}｜长中位{d['medl']}·停更{d['days']}d")
json.dump(sorted(lao, key=lambda d: d["rank"]), open(os.path.join(DATA, "priority.json"), "w"), ensure_ascii=False)
print(collections.Counter(d["tier"] for d in lao), collections.Counter(d["act"] for d in lao))
for d in sorted(lao, key=lambda x: x["rank"]):
    print(f"{d['rank']:3d} {d['tier']:12s} {d['name'][:26]:28s} subs={d['subs']:>8} 长中位={d['medl']:>7} "
          f"{d['lane'][:15]:16s} {d['act']:12s} {d['src'][:24]}")
print("\n-> data/priority.json（含 row 字段，可按行号定点写 Sheet 的优先级列）")
