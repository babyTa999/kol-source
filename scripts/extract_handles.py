#!/usr/bin/env python3
"""从 data/sheet_current.csv 提取账号清单 -> data/handles.tsv
输出列: 行号 \t handle \t 分区 \t 类别 \t 身份
约定: 表第 1 行为表头; A 列以 @ 开头的行是账号; 含「合作池」等无 @ 的行视作分区标题。
列位置可用 .env 覆盖: COL_HANDLE/COL_CATEGORY/COL_IDENTITY (0-based, 默认 0/3/4)"""
import csv, os, pathlib
from fetch_sheet import load_env

ROOT = pathlib.Path(__file__).resolve().parent.parent

def main():
    load_env()
    ch = int(os.environ.get('COL_HANDLE', 0))
    cc = int(os.environ.get('COL_CATEGORY', 3))
    ci = int(os.environ.get('COL_IDENTITY', 4))
    rows = list(csv.reader(open(ROOT / 'data' / 'sheet_current.csv')))
    out = open(ROOT / 'data' / 'handles.tsv', 'w')
    section, n = '', 0
    for i, r in enumerate(rows, start=1):  # i = sheet 行号（表头=1）
        a = (r[ch] if len(r) > ch else '').strip()
        if not a:
            continue
        if not a.startswith('@'):
            section = a
            continue
        n += 1
        cat = r[cc] if len(r) > cc else ''
        ident = r[ci] if len(r) > ci else ''
        out.write(f'{i}\t{a[1:]}\t{section}\t{cat}\t{ident}\n')
    print(f'ok -> data/handles.tsv ({n} accounts)')

if __name__ == '__main__':
    main()
