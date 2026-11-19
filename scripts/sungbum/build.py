"""合并三方松绷为“最全版”。
优先级：R(dhammareader 校正版) → O(ALL 官方 2026 包, pyewts 转 Unicode) → L(本地 ACIP 2016 Unicode)。
后两者只在“与已收内容不重复”的部分足够多时收入；重复判断按 6 音节 shingle 抽样。
"""
import pickle, gzip, json, os, re, csv, collections, shutil, sys

SCR = os.path.dirname(os.path.abspath(__file__))
LOCAL = os.environ.get("CANON_ROOT", ".") + "/藏文大藏经/ACIP/SUNGBUM (Tibetan Letters)/SUNGBUM (Tibetan Letters)"
REPO = os.environ.get("CANON_ROOT", ".") + "/_来源/dhammareader/repo"
OFF = os.environ.get("CANON_ROOT", ".") + "/_来源/ALL官方"
OUT = os.environ.get("CANON_ROOT", ".") + "/松绷最全版"
MIN_FRAC, MIN_ABS = 0.30, 20000   # 新内容占比 ≥30%，或新内容估计 ≥2 万音节，才收入

U = pickle.load(open(f"{SCR}/units.pkl", 'rb'))
offidx = {r['file']: r for r in csv.DictReader(open(f"{OFF}/flat_index.tsv", encoding='utf-8'), delimiter='\t')}

# ---------- 元数据 ----------
works = {r['acip_id']: r for r in csv.DictReader(open(f"{REPO}/catalog/works.tsv", encoding='utf-8'), delimiter='\t') if r['collection'] == 'sungbum'}
titles = {r['work_id']: r for r in csv.DictReader(open(f"{REPO}/catalog/titles.tsv", encoding='utf-8'), delimiter='\t') if r['collection'] == 'sungbum'}
persons = collections.defaultdict(list)
for r in csv.DictReader(open(f"{REPO}/catalog/persons.tsv", encoding='utf-8'), delimiter='\t'):
    if 'sungbum' in r.get('work_id', ''):
        persons[r['work_id']].append(r)
leftout = {}
for r in csv.DictReader(open(f"{REPO}/catalog/left_out.tsv", encoding='utf-8'), delimiter='\t'):
    if 'sungbum' in r['part_id']:
        leftout.setdefault(r['part_id'].split(':')[-1].split('.')[0], r['kind'])

# 本地目录：按编号切分条目，抽作者生卒
cat = open(os.environ.get("CANON_ROOT", ".") + "/藏文大藏经/《松繃》(Sungbum)《（大師）文集總目》.txt", encoding='utf-8', errors='replace').read()
lcat = {}
for e in re.split(r'(?=S\d{5}[-\w]*\((?:e|m|n|f)TB\))', cat)[1:]:
    m = re.match(r'(S\d{5}[-\w]*)\((?:e|m|n|f)TB\)\s*(.*)', e, re.S)
    if m and m.group(1) not in lcat:
        lcat[m.group(1)] = m.group(2).strip()[:400]

def death_year(s):
    m = re.search(r'\((\d{3,4})[@?]?-(\d{3,4}|[@&?]*)[@?]?\)', s or '')
    if not m:
        return None, None
    b = int(m.group(1))
    d = int(m.group(2)) if m.group(2).isdigit() else None
    return b, d

def copyright_flag(text, wid=None):
    if wid and leftout.get(wid) == 'excluded_copyright':
        return 'dhammareader 判定受版权保护'
    b, d = death_year(text)
    if d and d >= 1955:
        return f'作者卒于 {d}，可能仍受版权保护'
    if d is None and b and b >= 1890:
        return f'作者生于 {b}、卒年不详，可能仍受版权保护'
    if re.search(r'Michael Roach|GESHE MICHAEL', text or '', re.I):
        return '现代英文导言，受版权保护'
    return ''

# ---------- 输出 ----------
if os.path.exists(OUT):
    shutil.rmtree(OUT)
for d in ('1_校正版_dhammareader', '2_补自ALL官方2026', '3_补自本地ACIP2016'):
    os.makedirs(f"{OUT}/{d}")

chosen = set()
rows = []

def novelty(v):
    if not v['sh']:
        return 0.0, 0
    new = len(v['sh'] - chosen) / len(v['sh'])
    return new, int(new * v['n'])

def safe(s):
    return re.sub(r'[\\/:*?"<>|\s]+', '_', s)[:120]

# 1) R
for k, v in sorted(((k, v) for k, v in U.items() if v['src'] == 'R'), key=lambda kv: kv[1]['id']):
    wid = v['id']; full = f"tibetan:sungbum:{wid}"
    lines = []
    with gzip.open(f"{REPO}/{v['path']}", 'rt', encoding='utf-8') as f:
        for line in f:
            s = json.loads(line)
            t = s['tibetan_unicode_corrected']
            t = s['tibetan_unicode'] if t is None else t
            pages = [p for p in (s.get('pages') or []) if p.get('unicode_start') is not None and p.get('page')]
            for p in sorted(pages, key=lambda p: -p['unicode_start']):
                if p['unicode_start'] == 0 and lines and lines[-1].startswith(f"[{p['page']}]"):
                    continue
                t = t[:p['unicode_start']] + f"[{p['page']}]" + t[p['unicode_start']:]
            lines.append(t)
    open(f"{OUT}/1_校正版_dhammareader/{wid}.txt", 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    shutil.copy(f"{REPO}/{v['path']}", f"{OUT}/1_校正版_dhammareader/{wid}.jsonl.gz")
    t = titles.get(full, {}); w = works.get(wid, {})
    au = '; '.join(p.get('name', '') for p in persons.get(full, []))
    chosen |= v['sh']
    rows.append(dict(编号=wid, 来源='R 校正版', 文件=f"1_校正版_dhammareader/{wid}.txt", 音节数=v['n'], 新内容占比='1.00',
                     藏文标题=t.get('title_tibetan', ''), 威利转写标题=t.get('title_wylie', ''), 汉文标题=t.get('title_han', ''),
                     英文标题_或原路径='', 作者=au, 分类='', 版权提示='', 备注=''))
print('R', len(rows), file=sys.stderr)

# 2) O：按体量从大到小，只收新内容
skipped = collections.Counter()
for k, v in sorted(((k, v) for k, v in U.items() if v['src'] == 'O'), key=lambda kv: -kv[1]['n']):
    zp = offidx[v['path']]['zip_path']
    fn = zp.split('/')[-1]
    if 'META' in fn.upper() or v['n'] < 100:
        skipped['O 元数据/极短'] += 1; continue
    frac, est = novelty(v)
    if not (frac >= MIN_FRAC or est >= MIN_ABS):
        skipped['O 已被收入'] += 1; continue
    base = os.path.basename(v['path'])[:-4]
    src = f"{SCR}/official_unicode/{base}.txt"
    dst = f"2_补自ALL官方2026/{base}.txt"
    shutil.copy(src, f"{OUT}/{dst}")
    shutil.copy(f"{OFF}/{v['path']}", f"{OUT}/2_补自ALL官方2026/{base}.acip.TXT")
    chosen |= v['sh']
    parts = zp.split('/')
    rows.append(dict(编号=v['id'], 来源='O ALL官方2026', 文件=dst, 音节数=v['n'], 新内容占比=f"{frac:.2f}",
                     藏文标题='', 威利转写标题='', 汉文标题='', 英文标题_或原路径=zp, 作者='',
                     分类=parts[1] if len(parts) > 1 else '', 版权提示=copyright_flag(zp, v['id']),
                     备注='部分内容已见于前面来源' if frac < 0.95 else ''))
print('O added', sum(1 for r in rows if r['来源'].startswith('O')), file=sys.stderr)

# 3) L：去掉乱码，按体量从大到小
for k, v in sorted(((k, v) for k, v in U.items() if v['src'] == 'L'), key=lambda kv: -kv[1]['n']):
    if v['valid'] < 0.8:
        skipped['L 乱码'] += 1; continue
    if v['n'] < 100:
        skipped['L 极短'] += 1; continue
    frac, est = novelty(v)
    if not (frac >= MIN_FRAC or est >= MIN_ABS):
        skipped['L 已被收入'] += 1; continue
    raw = open(f"{LOCAL}/{v['path']}", 'rb').read().decode('utf-16', errors='replace').lstrip('﻿')
    name = safe(os.path.basename(v['path'])[:-4])
    dst = f"3_补自本地ACIP2016/{name}.txt"
    i = 2
    while os.path.exists(f"{OUT}/{dst}"):
        dst = f"3_补自本地ACIP2016/{name}_{i}.txt"; i += 1
    open(f"{OUT}/{dst}", 'w', encoding='utf-8').write(raw)
    chosen |= v['sh']
    incipit = re.sub(r'\[[^\]]*\]', '', raw).strip().split('\n')[0][:120]
    entry = lcat.get(v['id'], '')
    rows.append(dict(编号=v['id'], 来源='L 本地ACIP2016', 文件=dst, 音节数=v['n'], 新内容占比=f"{frac:.2f}",
                     藏文标题=incipit, 威利转写标题='', 汉文标题='', 英文标题_或原路径=v['path'], 作者='',
                     分类=v['path'].split('/')[0], 版权提示=copyright_flag(entry, v['id']),
                     备注=('本地目录著录：' + entry[:200]) if entry else '本地目录无此编号'))
print('L added', sum(1 for r in rows if r['来源'].startswith('L')), file=sys.stderr)

cols = list(rows[0].keys())
with open(f"{OUT}/总目录.tsv", 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=cols, delimiter='\t'); w.writeheader(); w.writerows(rows)
stats = collections.Counter(); syl = collections.Counter()
for r in rows:
    stats[r['来源']] += 1; syl[r['来源']] += int(r['音节数'])
json.dump(dict(stats=stats, syllables=syl, skipped=skipped,
               copyright_flagged=sum(1 for r in rows if r['版权提示'])), open(f"{SCR}/build_stats.json", 'w'), ensure_ascii=False, indent=1)
print(stats, syl, skipped, file=sys.stderr)
