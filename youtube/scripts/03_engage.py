#!/usr/bin/env python3
"""Stage 3｜互动质检层：最近 3 支长视频的 comment_count / like_count + /shorts 页。0 credits。

为什么必须单独跑：flat-playlist 拿不到评论/点赞数，而「异常高 views 低评论」是硬红线；
另外 /videos 页天然不含 Shorts，所以 shorts 占比必须单独抓 /shorts 页才不是假的 0。

输入 data/metrics.json + 一个 key 列表文件（每行一个 key，通常是分类后的存活者）
输出 data/engage.ndjson（断点续传）

用法: python3 youtube/scripts/03_engage.py data/survivors.txt [--workers 5]
"""
import argparse, json, os, shutil, subprocess
from concurrent.futures import ThreadPoolExecutor

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
OUT = os.path.join(DATA, "engage.ndjson")
YTDLP = shutil.which("yt-dlp") or os.path.expanduser("~/.local/bin/yt-dlp")

ap = argparse.ArgumentParser()
ap.add_argument("keys_file")
ap.add_argument("--workers", type=int, default=5)
ap.add_argument("--sample", type=int, default=3, help="每人抽几支长视频")
args = ap.parse_args()

RAW = {json.loads(l)["key"]: json.loads(l) for l in open(os.path.join(DATA, "raw_free.ndjson"))}
keys = [l.strip() for l in open(args.keys_file) if l.strip()]
done = {json.loads(l)["key"] for l in open(OUT)} if os.path.exists(OUT) else set()
todo = [k for k in keys if k not in done and k in RAW]
print(f"待抓 {len(todo)} 个频道 × 最多{args.sample}支长视频", flush=True)


def one_video(vid):
    try:
        p = subprocess.run([YTDLP, "--no-playlist", "-J", "--socket-timeout", "20", "--retries", "1",
                            f"https://www.youtube.com/watch?v={vid}"], capture_output=True, text=True, timeout=120)
        d = json.loads(p.stdout)
        return {"id": vid, "title": (d.get("title") or "")[:120], "views": d.get("view_count"),
                "likes": d.get("like_count"), "comments": d.get("comment_count"),
                "upload_date": d.get("upload_date"), "dur": d.get("duration")}
    except Exception as ex:
        return {"id": vid, "error": type(ex).__name__}


def shorts_tab(url):
    base = url.split("?")[0].rstrip("/")
    for suf in ("/videos", "/featured", "/about", "/streams", "/shorts"):
        if base.endswith(suf):
            base = base[: -len(suf)]
    try:
        p = subprocess.run([YTDLP, "--flat-playlist", "--playlist-end", "10", "-J",
                            "--socket-timeout", "20", "--retries", "1", base + "/shorts"],
                           capture_output=True, text=True, timeout=120)
        if p.returncode != 0 or not p.stdout.strip():
            return {"n_shorts": 0}
        d = json.loads(p.stdout)
        vs = sorted(e.get("view_count") for e in (d.get("entries") or []) if e.get("view_count"))
        return {"n_shorts": len(d.get("entries") or []), "shorts_med_views": vs[len(vs) // 2] if vs else None}
    except Exception:
        return {"n_shorts": None}


def per_channel(k):
    r = RAW[k]
    longs = [v for v in (r.get("videos") or []) if (v.get("dur") or 0) > 180][:args.sample]
    vs = [one_video(v["id"]) for v in longs if v.get("id")]
    rec = {"key": k, "videos": vs, **shorts_tab(r["url"])}
    good = [v for v in vs if v.get("views") and v.get("comments") is not None]
    if good:
        tot = sum(v["views"] for v in good)
        rec["comment_per_10k"] = round(sum(v["comments"] for v in good) / tot * 10000, 2)
        rec["like_pct"] = round(sum((v.get("likes") or 0) for v in good) / tot * 100, 2)
        rec["n_sampled"] = len(good)
    return rec


fh = open(OUT, "a")
n = 0
with ThreadPoolExecutor(max_workers=args.workers) as ex:
    for rec in ex.map(per_channel, todo):
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        fh.flush()
        n += 1
        if n % 10 == 0:
            print(f"  {n}/{len(todo)}", flush=True)
print(f"DONE {n} -> {OUT}", flush=True)
