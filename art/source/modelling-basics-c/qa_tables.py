"""README tables for the #69 round from the QA JSON in art/previews/modelling-basics-c/qa/ (before = a7e1e99c, after = this round).
  python qa_tables.py   (run from the repo root)"""
import json,collections,os
Q='art/previews/modelling-basics-c/qa/'
def lod(f):
    out={}
    for a in json.load(open(Q+f,encoding='utf-8')):
        c=collections.Counter()
        for x in a['findings']:c[x['kind']]+=x['count']
        out[os.path.basename(a['file'].replace(chr(92),'/'))[:-4]]=c
    return out
def txt(c):return '、'.join(f'{ {"coplanar overlap":"共面","zero-area UV":"零面積 UV","floating/detached":"浮空島"}.get(k,k)} {n}' for k,n in c.items()) or '0'
bs,bl,as_,al=lod('before-a7e1e99c-qa-lod0.json'),lod('before-a7e1e99c-qa-lod0-loose.json'),lod('qa-lod0.json'),lod('qa-lod0-loose.json')
print('| 件 | 嚴格（a7e1e99c → 現在） | 寬鬆 `--loose`（a7e1e99c → 現在） |\n|---|---|---|')
for k in sorted(as_):
    if bs.get(k) or bl.get(k) or as_[k] or al[k]:print(f'| {k} | {txt(bs.get(k,{}))} → {txt(as_[k])} | {txt(bl.get(k,{}))} → {txt(al[k])} |')
cb,ca=json.load(open(Q+'before-a7e1e99c-qa-contact.json',encoding='utf-8')),json.load(open(Q+'qa-contact.json',encoding='utf-8'))
print('\n| 散件（物件） | 件數 | 最大空隙 a7e1e99c → 現在 | 現在 >3 mm 的件數 |\n|---|---|---|---|')
for a in sorted(ca):
    for o,r in ca[a].items():
        b=cb.get(a,{}).get(o,{});bm=b.get('largest_mm',0)
        if r['pieces']>1 and (bm or r['largest_mm']):print(f"| {o.replace('_LOD0','')} | {r['pieces']} | {bm} mm → {r['largest_mm']} mm | {r['gap_3_10mm']+r['gap_over_10mm']} |")
