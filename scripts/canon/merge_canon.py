"""合并某一部（kangyur / tengyur）的三方文本为“最全版”。
用法：venv/bin/python merge_canon.py kangyur|tengyur
来源：R = dhammareader 校正版（主体）；O = ALL 官方 zip（ACIP 转写→pyewts）；L = 本地 ACIP 2016 Unicode。
规则同松绷最全版：R 全收 → O、L 按新内容（抽样 6-gram）≥30% 或 ≥2 万音节收入 → 对跳过的文件做精确 4-gram 复核，新内容 ≥10% 补收
→ 剔除乱码/英文（常见音节率 <0.8）与元数据 → 对 R、O 阅读版应用梵文叠字修正。
"""
import sys, os, re, csv, gzip, json, zipfile, hashlib, collections, shutil, pickle
from multiprocessing import Pool
import pyewts

COL = sys.argv[1]
ROOT = os.environ.get("CANON_ROOT", ".") + ""
NAME = {'kangyur': '甘珠尔', 'tengyur': '丹珠尔'}[COL]
OUT = f"{ROOT}/{NAME}最全版"
WORK = f"{OUT}/_比对数据"
REPO = f"{ROOT}/_来源/dhammareader/repo"
ZIP = f"{ROOT}/_来源/ALL官方/zip/{COL.upper()}.zip"
FLAT = f"{ROOT}/_来源/ALL官方/{COL}_flat"
LOCAL = {'kangyur': f"{ROOT}/藏文大藏经/ACIP/KANGYUR (Tibetan Letters)/KANGYUR (Tibetan Letters",
         'tengyur': f"{ROOT}/藏文大藏经/ACIP/TENGYUR (Tibetan Letters)/TENGYUR (Tibetan Letters)"}[COL]
FIXMAP = json.load(open(f"{ROOT}/松绷最全版/_脚本与比对数据/fixmap_safe.json", encoding='utf-8'))
SYL = re.compile(r'[ཀ-ྼ]+')
K, SAMPLE = 6, 8
conv = pyewts.pyewts()

STRIP = dict.fromkeys(map(ord, 'ཿྭཱྰཾ྄ཻཽ༹ྃ'), None)

def syls(t):
    """比对用的归一化音节：去掉梵文附加符号，统一几种常见的叠字写法差异（只用于比较，不改文本）"""
    out = []
    for s in SYL.findall(re.sub(r'\[[^\]]*\]', ' ', t)):
        s = s.translate(STRIP).replace('བཧ', 'བྷ').replace('དཧ', 'དྷ').replace('གཧ', 'གྷ').replace('པདམ', 'པདྨ')
        if s:
            out.append(s)
    return out

def sh6(sy):
    out = set()
    for i in range(len(sy) - K + 1):
        h = int.from_bytes(hashlib.blake2b('་'.join(sy[i:i + K]).encode(), digest_size=8).digest(), 'little')
        if h % SAMPLE == 0:
            out.add(h)
    return out

def g4(sy):
    return {hash('་'.join(sy[i:i + 4])) for i in range(len(sy) - 3)}

def acip2uni(t):
    t = re.sub(r'@[^\s]*', ' ', t)
    t = re.sub(r'\[[^\]]*\]', ' ', t)
    out = []
    for line in t.splitlines():
        if not re.search(r'[A-Z]', line):
            continue
        try:
            out.append(conv.toUnicode(pyewts.ACIPtoEWTS(line)))
        except Exception:
            out.append('')
    return '\n'.join(out)

# ---------- 读取三方 ----------
def load_R(p):
    parts = []
    with gzip.open(p, 'rt', encoding='utf-8') as f:
        for line in f:
            s = json.loads(line)
            t = s['tibetan_unicode_corrected']
            t = s['tibetan_unicode'] if t is None else t
            pages = [x for x in (s.get('pages') or []) if x.get('unicode_start') is not None and x.get('page')]
            for x in sorted(pages, key=lambda x: -x['unicode_start']):
                t = t[:x['unicode_start']] + f"[{x['page']}]" + t[x['unicode_start']:]
            parts.append(t)
    text = '\n'.join(parts) + '\n'
    return ('R', os.path.basename(p)[:-9], p, text)

def load_L(p):
    text = open(p, 'rb').read().decode('utf-16', errors='replace').lstrip('﻿')
    m = re.match(r'([A-Z]+\d+[A-Z0-9-]*)', os.path.basename(p))
    return ('L', m.group(1) if m else 'NOID', p, text)

def load_O(row):
    fp, zp = row
    raw = open(fp, encoding='utf-8', errors='replace').read()
    text = acip2uni(raw)
    m = re.match(r'([A-Z]+\d+[A-Z0-9-]*|acip-k[^_]*)', os.path.basename(zp))
    return ('O', m.group(1) if m else 'NOID', fp, text, zp)

def profile(item):
    src, uid, path, text = item[:4]
    sy = syls(text)
    return dict(src=src, id=uid, path=path, zip=(item[4] if len(item) > 4 else ''), n=len(sy), sh=sh6(sy),
                cnt=collections.Counter(sy)), text

def main():
    os.makedirs(WORK, exist_ok=True)
    # 解压官方 zip（按编号+哈希重命名，避免超长文件名）
    if not os.path.isdir(FLAT):
        os.makedirs(FLAT)
        zf = zipfile.ZipFile(ZIP)
        rows = []
        for i in zf.infolist():
            n = i.filename; b = os.path.basename(n)
            if i.is_dir() or '__MACOSX' in n or b.startswith('.') or not b.upper().endswith('.TXT'):
                continue
            data = zf.read(i); h = hashlib.sha1(data).hexdigest()[:8]
            m = re.match(r'([A-Za-z]+[\d_-][A-Za-z0-9_-]*?)(?=_|\.|\s|$)', b)
            fid = re.sub(r'[^\w-]', '', (m.group(1) if m else 'NOID'))[:40]
            fp = f"{FLAT}/{fid}__{h}.TXT"; open(fp, 'wb').write(data); rows.append((fp, n))
        with open(f"{FLAT}/_index.tsv", 'w', encoding='utf-8') as f:
            f.write('file\tzip_path\n')
            for fp, n in rows:
                f.write(f"{fp}\t{n}\n")
    orows = [l.rstrip('\n').split('\t') for l in open(f"{FLAT}/_index.tsv", encoding='utf-8')][1:]
    orows = list({r[0]: r for r in orows}.values())
    Rj = sorted(f"{REPO}/text/{COL}/{x}" for x in os.listdir(f"{REPO}/text/{COL}") if x.endswith('.jsonl.gz'))
    Lj = sorted(os.path.join(d, f) for d, _, fs in os.walk(LOCAL) if '/RTF' not in d and '__MACOSX' not in d for f in fs if f.endswith('.txt'))
    print(f"R {len(Rj)}  O {len(orows)}  L {len(Lj)}", flush=True)
    units, texts = [], []
    with Pool(22) as pool:
        for loader, jobs in ((load_R, Rj), (load_L, Lj), (load_O, orows)):
            items = pool.map(loader, jobs, chunksize=4)
            for u, t in pool.imap(profile, items, chunksize=4):
                units.append(u); texts.append(t)
            print(loader.__name__, 'done', flush=True)
    # 常见音节率（以 R 为词表）
    vocab = collections.Counter()
    for u in units:
        if u['src'] == 'R':
            vocab.update(u['cnt'])
    common = {s for s, c in vocab.items() if c >= 3}
    for u in units:
        tot = sum(u['cnt'].values())
        u['valid'] = sum(c for s, c in u['cnt'].items() if s in common) / tot if tot else 0
        del u['cnt']

    # ---------- 合并 ----------
    if os.path.isdir(f"{OUT}/1_校正版_dhammareader"):
        for d in ('1_校正版_dhammareader', '2_补自ALL官方', '3_补自本地ACIP2016'):
            shutil.rmtree(f"{OUT}/{d}", ignore_errors=True)
    for d in ('1_校正版_dhammareader', '2_补自ALL官方', '3_补自本地ACIP2016'):
        os.makedirs(f"{OUT}/{d}")
    chosen = set(); rows = []; skipped = collections.Counter()

    def safe(s):
        return re.sub(r'[\\/:*?"<>|\s$]+', '_', s)[:110]

    def add(i, folder, name, frac, note=''):
        u, t = units[i], texts[i]
        dst = f"{folder}/{safe(name)}.txt"; k = 2
        while os.path.exists(f"{OUT}/{dst}"):
            dst = f"{folder}/{safe(name)}_{k}.txt"; k += 1
        open(f"{OUT}/{dst}", 'w', encoding='utf-8').write(t)
        if u['src'] == 'R':
            shutil.copy(u['path'], f"{OUT}/{folder}/{u['id']}.jsonl.gz")
        if u['src'] == 'O':
            shutil.copy(u['path'], f"{OUT}/{dst[:-4]}.acip.TXT")
        chosen.update(u['sh'])
        rows.append(dict(编号=u['id'], 来源={'R': 'R 校正版', 'O': 'O ALL官方', 'L': 'L 本地ACIP2016'}[u['src']], 文件=dst,
                         音节数=u['n'], 新内容占比=f"{frac:.2f}", 原路径=(u['zip'] or os.path.relpath(u['path'], ROOT)), 备注=note))

    idx = list(range(len(units)))
    for i in sorted([i for i in idx if units[i]['src'] == 'R'], key=lambda i: units[i]['id']):
        add(i, '1_校正版_dhammareader', units[i]['id'], 1.0)
    for src, folder in (('O', '2_补自ALL官方'), ('L', '3_补自本地ACIP2016')):
        for i in sorted([i for i in idx if units[i]['src'] == src], key=lambda i: -units[i]['n']):
            u = units[i]
            if u['valid'] < 0.8 or u['n'] < 100 or 'META' in (u['zip'] or '').upper().split('/')[-1]:
                skipped[f'{src} 乱码/英文/元数据/极短'] += 1; continue
            frac = len(u['sh'] - chosen) / len(u['sh']) if u['sh'] else 0
            if frac >= 0.30 or frac * u['n'] >= 20000:
                add(i, folder, f"{u['id']}__{os.path.basename(u['path'])[:-4].split('__')[-1]}" if src == 'O' else os.path.basename(u['path'])[:-4], frac,
                    '部分内容已见于前面来源' if frac < 0.95 else '')
            else:
                skipped[f'{src} 已被收入'] += 1
    print('初步合并', collections.Counter(r['来源'] for r in rows), dict(skipped), flush=True)

    # ---------- 精确复核（4-gram，全量）----------
    have = set()
    for r in rows:
        have |= g4(syls(open(f"{OUT}/{r['文件']}", encoding='utf-8').read()))
    included = {r['原路径'] for r in rows}
    added = 0; residual = []
    for i in sorted(idx, key=lambda i: -units[i]['n']):
        u = units[i]
        if u['src'] == 'R' or (u['zip'] or os.path.relpath(u['path'], ROOT)) in included:
            continue
        if u['valid'] < 0.8 or u['n'] < 8 or 'META' in (u['zip'] or '').upper().split('/')[-1]:
            continue
        g = g4(syls(texts[i]))
        if not g:
            continue
        f = len(g - have) / len(g)
        if f >= 0.10:
            have |= g; added += 1
            add(i, '2_补自ALL官方' if u['src'] == 'O' else '3_补自本地ACIP2016',
                f"{u['id']}__{os.path.basename(u['path'])[:-4].split('__')[-1]}" if u['src'] == 'O' else os.path.basename(u['path'])[:-4], f,
                '精确比对补收' + ('；大部分内容已见于前面来源' if f < 0.3 else ''))
        else:
            residual.append((round(f, 3), u['src'], u['n'], u['id']))
    print('精确补收', added, '剩余未收文件中新内容最高', max(residual)[:3] if residual else None, flush=True)

    # ---------- 梵文叠字修正（只改 R、O 阅读版 .txt）----------
    fixcnt = collections.Counter(); log = open(f"{OUT}/修正记录.tsv", 'w', encoding='utf-8'); log.write('文件\t原形\t改为\t次数\n')
    for r in rows:
        if r['来源'].startswith('L'):
            continue
        p = f"{OUT}/{r['文件']}"; t = open(p, encoding='utf-8').read(); loc = collections.Counter()
        def rep(m):
            s = m.group(0)
            if s in FIXMAP:
                loc[(s, FIXMAP[s])] += 1; return FIXMAP[s]
            if s.startswith('པདམ'):
                n = 'པདྨ' + s[3:]; loc[(s, n)] += 1; return n
            return s
        t2 = SYL.sub(rep, t)
        if loc:
            open(p, 'w', encoding='utf-8').write(t2)
            for (a, b), c in loc.items():
                log.write(f"{r['文件']}\t{a}\t{b}\t{c}\n"); fixcnt[(a, b)] += c
    log.close()

    with open(f"{OUT}/总目录.tsv", 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter='\t'); w.writeheader(); w.writerows(rows)
    stats = dict(units={s: sum(1 for u in units if u['src'] == s) for s in 'RLO'},
                 merged={s: [sum(1 for r in rows if r['来源'][0] == s), sum(int(r['音节数']) for r in rows if r['来源'][0] == s)] for s in 'ROL'},
                 skipped=dict(skipped), exact_added=added, fixes=sum(fixcnt.values()),
                 residual_over_3pct=sum(1 for x in residual if x[0] >= 0.03),
                 local_garbled=[(units[i]['path'], units[i]['n']) for i in idx if units[i]['src'] == 'L' and units[i]['valid'] < 0.8])
    json.dump(stats, open(f"{WORK}/stats.json", 'w'), ensure_ascii=False, indent=1)
    pickle.dump([{k: v for k, v in u.items() if k != 'sh'} for u in units], open(f"{WORK}/units_meta.pkl", 'wb'))
    print(json.dumps({k: v for k, v in stats.items() if k != 'local_garbled'}, ensure_ascii=False), '本地乱码', len(stats['local_garbled']), flush=True)

if __name__ == '__main__':
    main()
