#!/usr/bin/env python3
"""Stage 1｜免费抓取层：yt-dlp flat-playlist + 频道 RSS。0 credits，只读。

输入 youtube/data/channels.csv（表头 url,handle,src,note；url 必填，其余可空）
输出 youtube/data/raw_free.ndjson（断点续传：已抓过的 url 自动跳过）

用法: python3 youtube/scripts/01_fetch_free.py [--workers 4] [--videos 15]
"""
import argparse, csv, json, os, re, shutil, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from urllib.request import urlopen, Request
from xml.etree import ElementTree as ET

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
OUT = os.path.join(DATA, "raw_free.ndjson")
YTDLP = shutil.which("yt-dlp") or os.path.expanduser("~/.local/bin/yt-dlp")

ap = argparse.ArgumentParser()
ap.add_argument("--workers", type=int, default=4)
ap.add_argument("--videos", type=int, default=15, help="每个频道取最近 N 支长视频列表")
args = ap.parse_args()

if not os.path.exists(YTDLP):
    sys.exit("yt-dlp 未安装：pip install yt-dlp")


def norm_key(url):
    """按 @handle 或 channel/ID 归一化，供后续按 channel_id 去重前的初步 key。"""
    m = re.search(r"youtube\.com/(@[\w\.\-]+|channel/[\w\-]+)", url)
    return m.group(1).lower() if m else url.lower()


def videos_url(url):
    u = url.split("?")[0].rstrip("/")
    for suf in ("/videos", "/featured", "/about", "/streams", "/shorts"):
        if u.endswith(suf):
            u = u[: -len(suf)]
    return u + "/videos"


def rss_dates(channel_id):
    """频道 RSS：最近 15 支的发布日期。免费，用于算发布节奏/停更天数。"""
    try:
        req = Request(f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}",
                      headers={"User-Agent": "Mozilla/5.0"})
        xml = urlopen(req, timeout=20).read()
        ns = {"a": "http://www.w3.org/2005/Atom"}
        return [e.findtext("a:published", "", ns)[:10] for e in ET.fromstring(xml).findall("a:entry", ns)]
    except Exception:
        return []


def fetch(row):
    rec = {"key": norm_key(row["url"]), "url": row["url"], "handle": row.get("handle", ""),
           "src": row.get("src", ""), "note": row.get("note", "")}
    try:
        p = subprocess.run([YTDLP, "--flat-playlist", "--playlist-end", str(args.videos), "-J",
                            "--socket-timeout", "20", "--retries", "1", videos_url(row["url"])],
                           capture_output=True, text=True, timeout=150)
        if p.returncode != 0 or not p.stdout.strip():
            rec["error"] = (p.stderr or "")[-300:]
            return rec
        d = json.loads(p.stdout)
        rec.update(channel_name=d.get("channel") or d.get("uploader") or "",
                   channel_id=d.get("channel_id") or "",
                   subs=d.get("channel_follower_count"),
                   bio=(d.get("description") or "")[:1200],
                   videos=[{"title": e.get("title") or "", "views": e.get("view_count"),
                            "dur": e.get("duration"), "id": e.get("id")} for e in (d.get("entries") or [])])
        if rec["channel_id"]:
            rec["pub_dates"] = rss_dates(rec["channel_id"])
    except subprocess.TimeoutExpired:
        rec["error"] = "timeout"
    except Exception as ex:
        rec["error"] = f"{type(ex).__name__}: {ex}"[:300]
    return rec


rows = [r for r in csv.DictReader(open(os.path.join(DATA, "channels.csv"))) if (r.get("url") or "").startswith("http")]
done = set()
if os.path.exists(OUT):
    done = {json.loads(l)["url"] for l in open(OUT)}
todo = [r for r in rows if r["url"] not in done]
print(f"channels.csv {len(rows)} 条，已完成 {len(done)}，待抓 {len(todo)}", flush=True)

fh = open(OUT, "a")
n = 0
with ThreadPoolExecutor(max_workers=args.workers) as ex:
    for rec in ex.map(fetch, todo):
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        fh.flush()
        n += 1
        if n % 20 == 0:
            print(f"  {n}/{len(todo)}", flush=True)
err = sum(1 for l in open(OUT) if json.loads(l).get("error"))
print(f"DONE 新增 {n} 条；累计失败 {err} -> {OUT}", flush=True)
