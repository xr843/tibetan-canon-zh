"""从 R(校正版) 与 L(本地 2016) 的对齐中学习“单音节替换”，找出 pyewts 的系统性转换错误。
条件：错误形在 L 全库中 0 次；替换对出现 ≥5 次；且该错误形在 R 中 ≥80% 的出现都对应到同一个正确形。"""
import pickle, re, os, collections, difflib, gzip, json, random, sys
from multiprocessing import Pool
SCR = os.path.dirname(os.path.abspath(__file__))
LOCAL = os.environ.get("CANON_ROOT", ".") + "/藏文大藏经/ACIP/SUNGBUM (Tibetan Letters)/SUNGBUM (Tibetan Letters)"
OUT = os.environ.get("CANON_ROOT", ".") + "/松绷最全版"
SYL = re.compile(r'[ཀ-ྼ]+')

def lsyl(path):
    return SYL.findall(re.sub(r'\[[^\]]*\]', ' ', open(f"{LOCAL}/{path}", 'rb').read().decode('utf-16', 'replace')))

def rsyl(wid):
    return SYL.findall(re.sub(r'\[[^\]]*\]', ' ', open(f"{OUT}/1_校正版_dhammareader/{wid}.txt", encoding='utf-8').read()))

def align(pair):
    wid, lp = pair
    r, l = rsyl(wid), lsyl(lp)
    out = collections.Counter(); seen = collections.Counter()
    # 分块对齐，避免过慢
    sm = difflib.SequenceMatcher(None, r[:60000], l[:60000], autojunk=False)
    for op, a1, a2, b1, b2 in sm.get_opcodes():
        if op == 'replace' and a2 - a1 == b2 - b1 and a2 - a1 <= 3:
            for x, y in zip(r[a1:a2], l[b1:b2]):
                out[(x, y)] += 1
        elif op == 'equal':
            for x in r[a1:a2]:
                seen[x] += 1
    return out, seen

if __name__ == '__main__':
    U = pickle.load(open(f"{SCR}/units.pkl", 'rb'))
    R = {v['id']: v for v in U.values() if v['src'] == 'R'}
    L = [v for v in U.values() if v['src'] == 'L' and v['valid'] >= 0.8 and v['n'] >= 200]
    idx = collections.defaultdict(set)
    for v in R.values():
        for h in v['sh']:
            idx[h].add(v['id'])
    pairs = []
    for v in L:
        c = collections.Counter()
        for h in v['sh']:
            for w in idx.get(h, ()):
                c[w] += 1
        if c:
            w, n = c.most_common(1)[0]
            if n / len(v['sh']) >= 0.8:
                pairs.append((w, v['path']))
    random.seed(0)
    pairs = list({w: (w, p) for w, p in pairs}.values())
    print('对齐对数', len(pairs), file=sys.stderr)
    tot = collections.Counter(); eq = collections.Counter()
    with Pool(22) as pool:
        for i, (o, s) in enumerate(pool.imap_unordered(align, pairs, chunksize=2)):
            tot.update(o); eq.update(s)
            if i % 200 == 0:
                print(i, file=sys.stderr, flush=True)
    # L 全库音节频次
    lfreq = collections.Counter()
    for v in L:
        pass
    pickle.dump(dict(tot=tot, eq=eq, pairs=len(pairs)), open(f"{SCR}/fixpairs.pkl", 'wb'))
    print('done', len(tot), file=sys.stderr)
