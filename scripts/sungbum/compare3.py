"""三方按正文内容比对松绷：
  L = 本地 ACIP 2016 Unicode txt (UTF-16)
  O = Asian Legacy Library 官方 SUNGBUM.zip（ACIP 转写，经 pyewts 转 Unicode）
  R = dhammareader 校正版 text/sungbum/*.jsonl.gz
每个单元：音节序列 → 6 音节 shingle（取 hash%8==0 的样本）。
输出 units.pkl：{key: dict(src, id, path, n, valid, sh(set), md5)}，以及 Unicode 文本缓存（O 的转换结果）。
"""
import gzip, json, os, re, sys, pickle, hashlib, collections, glob, csv
from multiprocessing import Pool

LOCAL = os.environ.get("CANON_ROOT", ".") + "/藏文大藏经/ACIP/SUNGBUM (Tibetan Letters)/SUNGBUM (Tibetan Letters)"
REPO = os.environ.get("CANON_ROOT", ".") + "/_来源/dhammareader/repo"
OFF = os.environ.get("CANON_ROOT", ".") + "/_来源/ALL官方"
SCR = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SCR, "units.pkl")
UCACHE = os.path.join(SCR, "official_unicode")

SYL = re.compile(r'[ཀ-ྼ]+')
K, SAMPLE = 6, 8

def syls(text):
    return SYL.findall(text)

def shingles(sy):
    out = set()
    for i in range(len(sy) - K + 1):
        h = int.from_bytes(hashlib.blake2b('་'.join(sy[i:i+K]).encode(), digest_size=8).digest(), 'little')
        if h % SAMPLE == 0:
            out.add(h)
    return out

def pack(src, uid, path, sy):
    return (f"{src}:{path}", dict(src=src, id=uid, path=path, n=len(sy), sh=shingles(sy),
                                   md5=hashlib.md5('་'.join(sy).encode()).hexdigest(),
                                   sylcount=collections.Counter(sy)))

def do_local(rel):
    raw = open(os.path.join(LOCAL, rel), 'rb').read()
    t = raw.decode('utf-16', errors='replace')
    t = re.sub(r'\[[^\]]*\]', ' ', t)
    m = re.match(r'([A-Z]\d{4,5}[-\w]*)', os.path.basename(rel))
    return pack('L', m.group(1) if m else 'NOID', rel, syls(t))

def acip_to_uni(t):
    import pyewts
    conv = pyewts.pyewts()
    t = re.sub(r'@[^\s]*', ' ', t)            # 页码标记 @01A 等
    t = re.sub(r'\[[^\]]*\]', ' ', t)         # [ ] 编者注/存疑
    out = []
    for line in t.splitlines():
        if not re.search(r"[A-Z]", line):
            continue
        try:
            out.append(conv.toUnicode(pyewts.ACIPtoEWTS(line)))
        except Exception:
            out.append('')
    return '\n'.join(out)

def do_off(row):
    path, uid = row
    t = open(os.path.join(OFF, path), 'rb').read().decode('utf-8', errors='replace')
    u = acip_to_uni(t)
    with open(os.path.join(UCACHE, os.path.basename(path)[:-4] + '.txt'), 'w', encoding='utf-8') as f:
        f.write(u)
    return pack('O', uid, path, syls(u))

def do_repo(p):
    parts = []
    with gzip.open(p, 'rt', encoding='utf-8') as f:
        for line in f:
            s = json.loads(line)
            t = s['tibetan_unicode_corrected']
            parts.append(s['tibetan_unicode'] if t is None else t)
    wid = os.path.basename(p)[:-9]
    return pack('R', wid, os.path.relpath(p, REPO), syls(' '.join(parts)))

if __name__ == '__main__':
    os.makedirs(UCACHE, exist_ok=True)
    jobs_L = [os.path.relpath(os.path.join(d, f), LOCAL) for d, _, fs in os.walk(LOCAL) for f in fs if f.endswith('.txt')]
    jobs_O = [(r['file'], r['acip_id']) for r in csv.DictReader(open(f"{OFF}/flat_index.tsv", encoding='utf-8'), delimiter='\t')]
    jobs_O = list({p: (p, i) for p, i in jobs_O}.values())
    jobs_R = sorted(glob.glob(f"{REPO}/text/sungbum/*.jsonl.gz"))
    units = {}
    with Pool(22) as pool:
        for name, fn, jobs in (('R', do_repo, jobs_R), ('L', do_local, jobs_L), ('O', do_off, jobs_O)):
            done = 0
            for k, v in pool.imap_unordered(fn, jobs, chunksize=4):
                units[k] = v
                done += 1
                if done % 500 == 0:
                    print(name, done, '/', len(jobs), flush=True)
            print(name, 'done', len(jobs), flush=True)
    # 公共词表：在 R 中出现 >=3 次的音节；用于判定 L 文件是否乱码
    vocab = collections.Counter()
    for v in units.values():
        if v['src'] == 'R':
            vocab.update(v['sylcount'])
    common = {s for s, c in vocab.items() if c >= 3}
    for v in units.values():
        tot = sum(v['sylcount'].values())
        v['valid'] = sum(c for s, c in v['sylcount'].items() if s in common) / tot if tot else 0
        del v['sylcount']
    pickle.dump(units, open(OUT, 'wb'))
    print('saved', len(units), flush=True)
