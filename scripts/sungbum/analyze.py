import os
import pickle, collections, csv, re, sys
U = pickle.load(open(sys.argv[1], 'rb'))
REPO = os.environ.get("CANON_ROOT", ".") + "/_来源/dhammareader/repo"
by = collections.defaultdict(dict)
for k, v in U.items():
    by[v['src']][k] = v
union = {s: set().union(*(v['sh'] for v in d.values() if s != 'L' or v['valid'] >= 0.8)) for s, d in by.items()}
idx = collections.defaultdict(lambda: collections.defaultdict(set))
for s, d in by.items():
    for k, v in d.items():
        for h in v['sh']:
            idx[s][h].add(k)

def cover(v, s):
    return len(v['sh'] & union[s]) / len(v['sh']) if v['sh'] else None

def best(v, s):
    c = collections.Counter()
    for h in v['sh']:
        for k in idx[s].get(h, ()):
            c[k] += 1
    return c.most_common(3)

for s, d in by.items():
    for k, v in d.items():
        v['cov'] = {t: cover(v, t) for t in by if t != s}

def bucket(x):
    if x is None: return '空/极短'
    if x >= 0.95: return '≥95%'
    if x >= 0.8: return '80-95%'
    if x >= 0.3: return '30-80%'
    if x > 0: return '<30%'
    return '0'

lo = {r['part_id'].split(':')[-1].split('.')[0]: r for r in csv.DictReader(open(f"{REPO}/catalog/left_out.tsv", encoding='utf-8'), delimiter='\t') if 'sungbum' in r['part_id']}

for s in 'LOR':
    d = by[s]
    print(f"\n=== {s}: {len(d)} 单元, 音节总数 {sum(v['n'] for v in d.values()):,}, 内容去重 {len({v['md5'] for v in d.values()})}")
    if s == 'L':
        bad = [v for v in d.values() if v['valid'] < 0.8]
        print('  乱码(常见音节率<80%):', len(bad), '音节', sum(v['n'] for v in bad))
    for t in 'LOR':
        if t == s: continue
        c = collections.Counter(bucket(v['cov'][t]) for v in d.values() if s != 'L' or v['valid'] >= 0.8)
        print(f"  在 {t} 中的覆盖率分布:", dict(sorted(c.items())))

# 输出明细
w = csv.writer(open('detail.tsv', 'w', encoding='utf-8'), delimiter='\t')
w.writerow(['src', 'id', 'path', 'syllables', 'valid', 'cov_L', 'cov_O', 'cov_R', 'best_R', 'best_O', 'left_out_kind'])
for s in 'LOR':
    for k, v in sorted(by[s].items()):
        bR = best(v, 'R')[:1] if s != 'R' else []
        bO = best(v, 'O')[:1] if s != 'O' else []
        base = re.match(r'([A-Z]\d{4,5}[A-Z]?)', v['id'])
        w.writerow([s, v['id'], v['path'], v['n'], round(v['valid'], 3),
                    *(round(v['cov'][t], 3) if v['cov'].get(t) is not None else '' for t in 'LOR'),
                    by['R'][bR[0][0]]['id'] if bR else '', by['O'][bO[0][0]]['path'] if bO else '',
                    lo.get(v['id'], {}).get('kind', '')])
pickle.dump({k: v['cov'] for k, v in U.items()}, open('cov.pkl', 'wb'))
