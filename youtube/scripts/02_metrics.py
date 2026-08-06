#!/usr/bin/env python3
"""Stage 2｜算指标 + 按 channel_id 去重。0 credits。

输入 data/raw_free.ndjson → 输出 data/metrics.json
去重很关键：同一人以 @handle 和 /channel/ID 两种写法进表会被当两个人
（2026-08 实测 319 行里 18 个频道重复，其中 6 人同时躺在合作池和筛掉池）。

用法: python3 youtube/scripts/02_metrics.py [--today 2026-08-06]
"""
import argparse, datetime as dt, json, os, statistics as st

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
ap = argparse.ArgumentParser()
ap.add_argument("--today", default=dt.date.today().isoformat())
args = ap.parse_args()
TODAY = dt.date.fromisoformat(args.today)

BUILDER_KW = [
    "agent", "agentic", "claude code", "codex", "cursor", "mcp", "api", "sdk", "python", "typescript",
    "open source", "opensource", "open-source", "self-host", "selfhost", "local", "ollama", "vllm",
    "llama", "qwen", "deepseek", "kimi", "mistral", "fine-tun", "finetun", "lora", "rag", "vector",
    "embedding", "benchmark", "eval", "inference", "quantiz", "hugging face", "huggingface", "github",
    "docker", "kubernetes", "terminal", "cli", "repo", "codebase", "refactor", "debug", "n8n",
    "langchain", "langgraph", "pydantic", "transformer", "attention", "gradient", "pytorch", "cuda",
    "prompt engineer", "context window", "tool call", "function call", "harness", "workflow", "pipeline",
    "build", "built", "building", "ship", "deploy",
]
NOVICE_KW = [
    "beginner", "for beginners", "step by step", "step-by-step", "tutorial for", "complete guide",
    "everything you need", "explained for", "in 5 minutes", "in 10 minutes", "crash course",
    "how to use chatgpt", "best ai tools", "top 10", "top 5", "ai tools you", "must have",
    "for free", "no code", "nocode", "no-code", "anyone can",
]
MONEY_KW = [
    "$", "money", "income", "revenue", "rich", "profit", "salary", "earn", "quit my job", "side hustle",
    "passive", "millionaire", "6-figure", "six figure", "monetiz", "make money", "get paid", "freelanc",
]
HYPE_KW = [
    "shocking", "insane", "crazy", "terrifying", "the end of", "is dead", "changes everything",
    "nobody is talking", "you won't believe", "breaking", "just changed", "game over", "scary",
    "agi", "we're cooked", "wtf", "mind blow",
]
GROWTH_BIO = [
    "growth marketer", "growth hacker", "growth hacking", "marketing consultant", "digital marketing",
    "seo expert", "brand strategist", "social media manager", "content marketer", "affiliate",
    "lead generation", "agency owner", "smma", "dropship",
]


def med(xs):
    xs = [x for x in xs if isinstance(x, (int, float))]
    return int(st.median(xs)) if xs else None


def hits(text, kws):
    t = text.lower()
    return sorted({k for k in kws if k in t})


def compute(r):
    vids = r.get("videos") or []
    titles = " || ".join(v["title"] for v in vids)
    longs = [v for v in vids if (v.get("dur") or 0) > 180]
    subs = r.get("subs") or 0
    m_all, m_long = med([v["views"] for v in vids]), med([v["views"] for v in longs])
    days_since = per_30d = None
    dates = [d for d in (r.get("pub_dates") or []) if d]
    if dates:
        try:
            ds = sorted(dt.date.fromisoformat(d) for d in dates)
            days_since = (TODAY - ds[-1]).days
            per_30d = sum(1 for d in ds if (TODAY - d).days <= 30)
        except Exception:
            pass
    bio = r.get("bio") or ""
    o = {"key": r["key"], "channel_id": r.get("channel_id", ""), "url": r["url"],
         "handle": r.get("handle") or r.get("channel_name", ""), "channel_name": r.get("channel_name", ""),
         "src": r.get("src", ""), "note": r.get("note", ""),
         "subs": subs or None, "n_videos": len(vids),
         "med_views_all": m_all, "med_views_long": m_long,
         "ratio_long": round(m_long / subs, 4) if (m_long and subs) else None,
         "days_since_last": days_since, "uploads_30d": per_30d,
         "builder_hits": hits(titles, BUILDER_KW), "novice_hits": hits(titles, NOVICE_KW),
         "money_hits": hits(titles, MONEY_KW), "hype_hits": hits(titles, HYPE_KW),
         "growth_bio_hits": hits(bio, GROWTH_BIO),
         "titles": [v["title"] for v in vids][:15], "bio": bio[:600], "error": r.get("error", "")}
    return o


rows = [json.loads(l) for l in open(os.path.join(DATA, "raw_free.ndjson"))]
out = [compute(r) for r in rows]
byid, dedup = {}, []
for o in out:
    cid = o["channel_id"] or o["key"]
    if cid in byid:
        prev = byid[cid]
        prev.setdefault("alt_keys", []).append(o["key"])
        if prev["src"] != o["src"] and prev["src"] and o["src"]:
            prev["dup_conflict"] = f"同一频道两种写法，来源冲突：{prev['src']} / {o['src']}"
        continue
    byid[cid] = o
    dedup.append(o)
json.dump(dedup, open(os.path.join(DATA, "metrics.json"), "w"), ensure_ascii=False, indent=1)
ok = [o for o in dedup if not o["error"]]
print(f"{len(out)} 行 -> {len(dedup)} 个唯一频道（{sum(1 for o in dedup if o.get('dup_conflict'))} 个来源冲突），抓取失败 {len(dedup) - len(ok)}")
rl = sorted(o["ratio_long"] for o in ok if o["ratio_long"])
if rl:
    q = lambda p: rl[int(len(rl) * p)]
    print(f"长视频中位播放÷订阅 分位：p10={q(.1)} p25={q(.25)} p50={q(.5)} p75={q(.75)} p90={q(.9)}")
