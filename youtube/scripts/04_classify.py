#!/usr/bin/env python3
"""Stage 4｜定性判断层：deepline deeplineagent 批量打标（rubric v2，见 youtube/RUBRIC.md）。

只让模型做定性判断（个人/机构、受众层、AI 姿态、builder 指数、合格通道、主线）。
**数值红线一律不交给模型** —— 实测把 like%=0.06 喂进去它照样判「捞」，所以数值判定放在 05_export.py 里用代码算。

成本：gpt-5.4-mini，20 人/批，约 $0.02/批（301 人 ≈ $0.3）。

用法: python3 youtube/scripts/04_classify.py data/all_keys.txt data/classified.ndjson
"""
import collections, json, os, subprocess, sys

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
keys = [l.strip() for l in open(sys.argv[1]) if l.strip()]
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(DATA, "classified.ndjson")
MODEL = os.environ.get("YT_CLASSIFY_MODEL", "openai/gpt-5.4-mini")

M = {m["key"]: m for m in json.load(open(os.path.join(DATA, "metrics.json")))}
ENG = {}
p = os.path.join(DATA, "engage.ndjson")
if os.path.exists(p):
    for l in open(p):
        d = json.loads(l)
        ENG[d["key"]] = d

FIELDS = ["entity_type", "audience_layer", "ai_stance", "builder_index", "lane", "topic_3", "hard_flags",
          "verdict", "reason"]
item = {"type": "object", "properties": {
    "i": {"type": "integer"},
    "entity_type": {"type": "string", "enum": ["individual", "brand_or_company", "institution", "media_or_podcast", "unclear"]},
    "audience_layer": {"type": "string", "enum": ["builder_practitioner", "mixed", "novice_consumer", "general_public"]},
    "ai_stance": {"type": "string", "enum": ["hands_on_builder", "explainer_analyst", "news_commentary", "tool_reviewer", "no_ai", "unclear"]},
    "builder_index": {"type": "integer"},
    "lane": {"type": "string", "enum": ["build", "explain_to_devs", "neither"]},
    "topic_3": {"type": "string"}, "hard_flags": {"type": "string"},
    "verdict": {"type": "string", "enum": ["捞", "观察", "弃"]},
    "reason": {"type": "string"}},
    "required": ["i"] + FIELDS, "additionalProperties": False}
schema = {"type": "object", "properties": {"results": {"type": "array", "items": item}},
          "required": ["results"], "additionalProperties": False}

RUBRIC = open(os.path.join(os.path.dirname(DATA), "RUBRIC.md")).read()


def line(i, k):
    m, e = M.get(k, {}), ENG.get(k, {})
    parts = [f"{i}. name={m.get('channel_name') or m.get('handle')}", f"subs={m.get('subs')}",
             f"近15支中位播放={m.get('med_views_all')}", f"长视频中位播放={m.get('med_views_long')}",
             f"中位÷订阅={m.get('ratio_long')}", f"距上次发布={m.get('days_since_last')}天",
             f"近30天更新={m.get('uploads_30d')}支"]
    if e.get("comment_per_10k") is not None:
        parts += [f"每万播放评论数={e['comment_per_10k']}", f"点赞率%={e.get('like_pct')}"]
    parts += [f"builder词命中={','.join(m.get('builder_hits', [])[:12]) or '无'}",
              f"小白词命中={','.join(m.get('novice_hits', [])[:8]) or '无'}",
              f"赚钱词命中={','.join(m.get('money_hits', [])[:8]) or '无'}",
              f"hype词命中={','.join(m.get('hype_hits', [])[:8]) or '无'}",
              f"bio里growth/marketing词={','.join(m.get('growth_bio_hits', [])) or '无'}",
              f"bio={(m.get('bio') or '')[:300]}",
              f"近15支标题=[{' / '.join(m.get('titles', [])[:12])}]"]
    return " | ".join(parts)


def run_batch(batch):
    prompt = RUBRIC + "\n\n以下是本批频道：\n" + "\n".join(line(i + 1, k) for i, k in enumerate(batch))
    inp = {"model": MODEL, "prompt": prompt, "jsonSchema": json.dumps(schema)}
    p = subprocess.run(["deepline", "tools", "execute", "deeplineagent", "--input", json.dumps(inp), "--json"],
                       capture_output=True, text=True)
    d = json.loads(p.stdout)
    raw = d.get("toolResponse", {}).get("raw") or {}
    res = raw.get("result", {}) if isinstance(raw, dict) else {}
    obj = res.get("object") or (json.loads(res["text"]) if res.get("text") else None)
    return (obj or {}).get("results", [])


fh = open(OUT, "w")
allr = []
for bi in range(0, len(keys), 20):
    batch = keys[bi:bi + 20]
    try:
        got = run_batch(batch)
    except Exception as ex:
        print("batch fail", ex)
        got = []
    bym = {g["i"]: g for g in got}
    for j, k in enumerate(batch):
        c = bym.get(j + 1, {})
        rec = {"key": k, **{f: c.get(f, "?") for f in FIELDS}}
        allr.append(rec)
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    fh.flush()
    print(f"batch {bi // 20 + 1}/{(len(keys) + 19) // 20} done ({len(allr)})", flush=True)
print(collections.Counter(r["verdict"] for r in allr))
print(f"-> {OUT}")
