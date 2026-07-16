#!/usr/bin/env python3
"""读回 Google Sheet 当前状态（公开 gviz CSV 接口）-> data/sheet_current.csv
用法: python3 scripts/fetch_sheet.py  （SPREADSHEET_ID/GID 从 .env 或环境变量取）"""
import os, sys, urllib.request, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent

def load_env():
    envfile = ROOT / '.env'
    if envfile.exists():
        for line in envfile.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())

def main():
    load_env()
    sid = os.environ.get('SPREADSHEET_ID')
    gid = os.environ.get('GID', '0')
    if not sid:
        sys.exit('缺 SPREADSHEET_ID：复制 .env.example 为 .env 并填写')
    url = f'https://docs.google.com/spreadsheets/d/{sid}/gviz/tq?tqx=out:csv&gid={gid}'
    out = ROOT / 'data' / 'sheet_current.csv'
    out.parent.mkdir(exist_ok=True)
    data = urllib.request.urlopen(url, timeout=30).read()
    if data[:15].lower().startswith(b'<!doctype html') or b'<html' in data[:200].lower():
        sys.exit('读回失败：sheet 未开「知道链接可查看」或 ID/GID 错误')
    out.write_bytes(data)
    print(f'ok -> {out} ({len(data.splitlines())} rows)')

if __name__ == '__main__':
    main()
