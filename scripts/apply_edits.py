#!/usr/bin/env python3
"""把 edits.json 定点写回 Google Sheet（经 Apps Script webhook，逐单元格 setblock）。
默认只预览；加 --write 才实际写入。备注列只前置追加，原文以｜保留。

用法:
  python3 scripts/apply_edits.py data/edits.json          # 预览
  python3 scripts/apply_edits.py data/edits.json --write  # 写入

edits.json:
[
  {"row": 9, "cells": {"E": "新身份", "F": "弱"}, "note_prepend": "🔴删除候选：…"}
]

需要 .env: WEBHOOK_URL / WEBHOOK_TOKEN / TAB（NOTE_COL 默认 J）
铁律: 写回前先重新跑 fetch_sheet.py 读现状；本脚本会校验 sheet_current.csv 是否新鲜(<30min)。"""
import csv, json, os, sys, time, pathlib, urllib.parse, urllib.request
from fetch_sheet import load_env

ROOT = pathlib.Path(__file__).resolve().parent.parent
COL = {c: i for i, c in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}

def set_cell(base, token, tab, row, col_letter, value):
    q = urllib.parse.urlencode({'token': token, 'action': 'setblock', 'tab': tab,
                                'startRow': row, 'startCol': COL[col_letter] + 1})
    req = urllib.request.Request(f'{base}?{q}', data=value.encode('utf-8'),
                                 headers={'Content-Type': 'text/plain; charset=utf-8'})
    resp = urllib.request.urlopen(req, timeout=30).read().decode('utf-8', 'replace')
    if 'ok' not in resp.lower():
        raise RuntimeError(f'webhook 返回异常: {resp[:200]}')

def main():
    load_env()
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    edits = json.load(open(sys.argv[1]))
    write = '--write' in sys.argv
    note_col = os.environ.get('NOTE_COL', 'J')

    cur_file = ROOT / 'data' / 'sheet_current.csv'
    if not cur_file.exists():
        sys.exit('缺 data/sheet_current.csv：先跑 fetch_sheet.py 读回现状')
    age = time.time() - cur_file.stat().st_mtime
    if age > 1800:
        sys.exit(f'sheet_current.csv 已 {age/60:.0f} 分钟未刷新——重新跑 fetch_sheet.py 再写（防覆盖他人手动改动）')
    rows = list(csv.reader(open(cur_file)))

    plan = []  # (row, col, new, old)
    for e in edits:
        r = e['row']
        old_row = rows[r - 1] if r - 1 < len(rows) else []
        for col, val in e.get('cells', {}).items():
            plan.append((r, col.upper(), val, old_row[COL[col.upper()]] if len(old_row) > COL[col.upper()] else ''))
        if e.get('note_prepend'):
            oldn = (old_row[COL[note_col]] if len(old_row) > COL[note_col] else '').strip()
            plan.append((r, note_col, f'{e["note_prepend"]}｜{oldn}' if oldn else e['note_prepend'], oldn))

    for r, c, new, old in plan:
        mark = '->' if write else '(preview)'
        print(f'{mark} {c}{r}: {old[:40]!r} => {new[:60]!r}')
    print(f'\n{len(plan)} cells / {len(edits)} rows')

    if not write:
        print('预览模式。确认无误后加 --write 执行。')
        return
    base, token, tab = (os.environ.get(k) for k in ('WEBHOOK_URL', 'WEBHOOK_TOKEN', 'TAB'))
    if not all([base, token, tab]):
        sys.exit('写入需要 .env 里的 WEBHOOK_URL / WEBHOOK_TOKEN / TAB')
    for r, c, new, _ in plan:
        set_cell(base, token, tab, r, c, new)
    print(f'done：已写入 {len(plan)} 个单元格。请在聊天中向表格 owner 汇报改动明细。')

if __name__ == '__main__':
    main()
