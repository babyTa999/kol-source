#!/usr/bin/env python3
"""生成「表内标签 vs 实际内容」逐人对照摘要，供 agent/人工判断。
用法: python3 scripts/digest.py > data/digests.txt"""
import json, re, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'

def main():
    for line in open(DATA / 'handles.tsv'):
        row, h, section, cat, ident = line.rstrip('\n').split('\t')
        head = f'=== @{h} (row {row}) [{section}]\n表: {cat} | {ident}'
        try:
            d = json.load(open(DATA / f'tl_{h}.json'))
            tweets = d['toolResponse']['raw']['tweets']
        except Exception as e:
            print(f'{head}\n!! 拉取失败: {e}\n'); continue
        if not tweets:
            print(f'{head}\n!! 无推文（停更/封号/改名？）\n'); continue
        a = tweets[0]['author']
        bio = re.sub(r'\s+', ' ', a.get('description') or '')
        print(head)
        print(f'实: name={a["name"]} | 粉={a["followers"]} | bio={bio[:120]}')
        orig = [t for t in tweets if not t.get('isReply')][:8]
        if not orig:
            print('  （近段全是回复，无原创）')
        for t in orig:
            txt = re.sub(r'\s+', ' ', t['text'])[:90]
            print(f'  [{t["createdAt"][4:10]}] L{t["likeCount"]} {txt}')
        print()

if __name__ == '__main__':
    main()
