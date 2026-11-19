"""短文件（<100 音节）补收：用全量 4 音节组合精确比对，不抽样。
候选对照文本 = 合集中所有已收文件（全量 4-gram 集合，用 64 位哈希存）。"""
import pickle, csv, re, os, collections, hashlib, sys, json
SCR = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get("CANON_ROOT", ".") + "/松绷最全版"
LOCAL = os.environ.get("CANON_ROOT", ".") + "/藏文大藏经/ACIP/SUNGBUM (Tibetan Letters)/SUNGBUM (Tibetan Letters)"
OFF = os.environ.get("CANON_ROOT", ".") + "/_来源/ALL官方"
SYL = re.compile(r'[ཀ-ྼ]+')
N = 4

def grams(sy):
    return {hash('་'.join(sy[i:i+N])) for i in range(len(sy) - N + 1)}

rows = list(csv.DictReader(open(f"{OUT}/总目录.tsv", encoding='utf-8-sig'), delimiter='\t'))
have = set()
for r in rows:
    t = open(f"{OUT}/{r['文件']}", encoding='utf-8').read()
    have |= grams(SYL.findall(re.sub(r'\[[^\]]*\]', ' ', t)))
print('已收 4-gram', len(have), file=sys.stderr)

U = pickle.load(open(f"{SCR}/units.pkl", 'rb'))
off = {r['file']: r['zip_path'] for r in csv.DictReader(open(f"{OFF}/flat_index.tsv", encoding='utf-8'), delimiter='\t')}
cands = []
for v in U.values():
    if v['n'] >= 100 or v['n'] < 8:
        continue
    if v['src'] == 'O' and 'META' not in off[v['path']].upper().split('/')[-1]:
        t = open(f"{SCR}/official_unicode/{os.path.basename(v['path'])[:-4]}.txt", encoding='utf-8').read()
        cands.append(('O', v, t))
    elif v['src'] == 'L' and v['valid'] >= 0.8:
        t = open(f"{LOCAL}/{v['path']}", 'rb').read().decode('utf-16', errors='replace').lstrip('﻿')
        cands.append(('L', v, t))
cands.sort(key=lambda c: (c[0] != 'O', -c[1]['n']))
added = collections.Counter(); seen = collections.Counter()
new_rows = []
for src, v, t in cands:
    g = grams(SYL.findall(re.sub(r'\[[^\]]*\]', ' ', t)))
    if not g:
        continue
    frac = len(g - have) / len(g)
    seen[src] += 1
    if frac < 0.5:
        continue
    have |= g
    if src == 'O':
        base = os.path.basename(v['path'])[:-4]
        dst = f"2_补自ALL官方2026/{base}.txt"
        open(f"{OUT}/{dst}", 'w', encoding='utf-8').write(t)
        path_info = off[v['path']]
    else:
        name = re.sub(r'[\\/:*?"<>|\s]+', '_', os.path.basename(v['path'])[:-4])[:120]
        dst = f"3_补自本地ACIP2016/{name}.txt"; i = 2
        while os.path.exists(f"{OUT}/{dst}"):
            dst = f"3_补自本地ACIP2016/{name}_{i}.txt"; i += 1
        open(f"{OUT}/{dst}", 'w', encoding='utf-8').write(t)
        path_info = v['path']
    added[src] += 1
    new_rows.append({**{k: '' for k in rows[0]}, '编号': v['id'], '来源': 'O ALL官方2026' if src == 'O' else 'L 本地ACIP2016',
                     '文件': dst, '音节数': v['n'], '新内容占比': f"{frac:.2f}", '英文标题_或原路径': path_info,
                     '藏文标题': re.sub(r'\s+', ' ', re.sub(r'\[[^\]]*\]', '', t)).strip()[:120], '备注': '短篇（<100 音节），精确比对补收'})
with open(f"{OUT}/总目录.tsv", 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter='\t'); w.writeheader(); w.writerows(rows + new_rows)
print('检查', seen, '补收', added, file=sys.stderr)
json.dump(dict(checked=seen, added=added), open(f"{SCR}/short_stats.json", 'w'))
