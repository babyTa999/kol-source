#!/usr/bin/env bash
# 批量拉时间线（deepline twitterapi，~$0.001/条）。断点续传：已存在且非空的 tl_*.json 跳过。
# 用法: bash scripts/pull_timelines.sh
set -uo pipefail
cd "$(dirname "$0")/.."

[ -f data/handles.tsv ] || { echo "先跑 extract_handles.py"; exit 1; }
command -v deepline >/dev/null || { echo "缺 deepline CLI: https://deepline.ai"; exit 1; }

total=0; pulled=0; skipped=0; empty=()
while IFS=$'\t' read -r row handle rest; do
  total=$((total+1))
  f="data/tl_${handle}.json"
  if [ -s "$f" ] && python3 -c "import json,sys; d=json.load(open('$f')); sys.exit(0 if d.get('toolResponse',{}).get('raw',{}).get('tweets') else 1)" 2>/dev/null; then
    skipped=$((skipped+1)); continue
  fi
  deepline tools execute twitterapi_advanced_search \
    --input "{\"query\":\"from:${handle}\",\"queryType\":\"Latest\"}" --json > "$f" 2>/dev/null
  if python3 -c "import json,sys; d=json.load(open('$f')); sys.exit(0 if d.get('toolResponse',{}).get('raw',{}).get('tweets') else 1)" 2>/dev/null; then
    pulled=$((pulled+1)); echo "ok  @${handle}"
  else
    empty+=("$handle"); echo "EMPTY @${handle}（停更/封号/改名？）"
  fi
done < data/handles.tsv

echo "----"
echo "total=$total pulled=$pulled skipped(cached)=$skipped empty=${#empty[@]}"
[ ${#empty[@]} -gt 0 ] && printf 'EMPTY: %s\n' "${empty[@]}"
exit 0
