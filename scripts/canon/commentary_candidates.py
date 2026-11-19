"""第2项·规则粗配：找出注疏类条目，并在全目录中找它们所释典籍的候选。
输出：_目录工作_注释关系/candidates.jsonl
"""
import csv, re, json, collections, os

ROOT = os.environ.get("CANON_ROOT", ".") + ""
OUT = f"{ROOT}/_目录工作_注释关系"
os.makedirs(OUT, exist_ok=True)
M = list(csv.DictReader(open(f"{ROOT}/藏文大藏经总目录.tsv", encoding='utf-8-sig'), delimiter='\t'))

MARK = re.compile(r"'grel|bshad|t[iī]\+?k|ṭīk|mchan|bsdus don|spyi don|mtha' dpyod|zin bris|sa bcad|dka' gnas|brjed byang|dgongs pa rab gsal|bsdus pa'i don|rnam 'grel(?! pa)", re.I)
# 体裁、修饰词：比对时去掉
GEN = set("""zhes bya ba bya ba'i ba bstan bcos 'phags pa dpal tshig le'ur byas pa byas pa'i rab tu byed pa slob dpon chen po'i
'grel pa 'grel ba rnam par bshad pa rnam bshad bshad pa dka' 'grel TIka Tika ṭīkā mchan bsdus don spyi don mtha' dpyod zin bris sa bcad
legs bshad snying po rgyan gyi kyi gi 'i yi dang bcas pa'i ces la las nas""".split())

def toks(w):
    w = (w or '').lower().replace('’', "'").replace('‘', "'")
    w = re.sub(r"[^a-z'+ .-]", ' ', w)
    return [t for t in w.split() if t]

def core(w):
    return [t for t in toks(w) if t not in GEN and not t.endswith("'i") or t in ("'di'i",)]

titles = []
for i, r in enumerate(M):
    titles.append(toks(r['威利转写']))

# 倒排：按 3-gram 找包含关系
idx = collections.defaultdict(set)
for i, tk in enumerate(titles):
    for j in range(len(tk) - 2):
        idx[tuple(tk[j:j + 3])].add(i)

def contains(big, small):
    n = len(small)
    if n == 0 or n > len(big):
        return False
    return any(big[k:k + n] == small for k in range(len(big) - n + 1))

cands = []
for i, r in enumerate(M):
    w = r['威利转写'] or ''
    if not MARK.search(w):
        continue
    tk = titles[i]
    pool = collections.Counter()
    for j in range(len(tk) - 2):
        for k in idx.get(tuple(tk[j:j + 3]), ()):
            if k != i:
                pool[k] += 1
    out = []
    for k, _ in pool.most_common(60):
        root = titles[k]
        # 根本典：去掉末尾 zhes bya ba 等后，核心词序列须包含在注疏书名中；且不能本身更长
        rcore = [t for t in root if t not in ('zhes', 'bya', 'ba', "ba'i")]
        if len(rcore) < 2 or len(rcore) >= len(tk):
            continue
        if contains(tk, rcore):
            out.append((len(rcore), k))
    out.sort(reverse=True)
    cands.append(dict(总编号=r['总编号'], 部=r['部'], 部类=r['部类'], 汉文书名=r['汉文书名'], 威利转写=w, 梵文书名=r['梵文书名'],
                      英文书名=r['英文书名'][:120], 作者=r['作者'],
                      候选=[dict(总编号=M[k]['总编号'], 汉文书名=M[k]['汉文书名'], 威利转写=M[k]['威利转写'][:120], 作者=M[k]['作者'], 匹配长度=n) for n, k in out[:4]]))
with open(f"{OUT}/candidates.jsonl", 'w', encoding='utf-8') as f:
    for c in cands:
        f.write(json.dumps(c, ensure_ascii=False) + '\n')
by = collections.Counter(c['部'] for c in cands)
hit = collections.Counter(c['部'] for c in cands if c['候选'])
print('注疏类条目', len(cands), dict(by), '有规则候选', dict(hit))
