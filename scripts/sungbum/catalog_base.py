"""汇总每个条目的元数据：藏文/威利标题、英文标题、作者及生卒、分类。输出 _目录工作/base.tsv"""
import csv, re, os, collections, sys, json
import pyewts
conv = pyewts.pyewts()
ROOT = os.environ.get("CANON_ROOT", ".") + ""
COL = f"{ROOT}/松绷最全版"
OFF = f"{ROOT}/_来源/ALL官方"
REPO = f"{ROOT}/_来源/dhammareader/repo/catalog"
WORK = f"{COL}/_目录工作"
os.makedirs(WORK, exist_ok=True)

def acip2uni(s):
    try:
        return conv.toUnicode(pyewts.ACIPtoEWTS(s))
    except Exception:
        return ''

def rtf2txt(t):
    t = re.sub(r"\\'92", "’", t); t = re.sub(r"\\'9[34]", '"', t)
    t = re.sub(r'\\[a-z]+-?\d* ?', '', t); t = re.sub(r'[{}]', '', t)
    return re.sub(r'\s+', ' ', t).strip()

rows = list(csv.DictReader(open(f"{COL}/总目录.tsv", encoding='utf-8-sig'), delimiter='\t'))
off = list(csv.DictReader(open(f"{OFF}/flat_index.tsv", encoding='utf-8'), delimiter='\t'))
by_id = collections.defaultdict(list)
for r in off:
    by_id[r['acip_id']].append(r)

def off_lookup(i):
    if i in by_id:
        return by_id[i]
    for k in range(len(i) - 1, 5, -1):     # S00001A → S00001A5 之类：向下找前缀
        pass
    c = [r for k, v in by_id.items() if k.startswith(i) for r in v]
    return c

def parse_fn(fn):
    """S00004M_WYLIE_English_AUTHOR (b-d).TXT → (wylie, english, author, dates)"""
    b = re.sub(r'\.TXT$', '', fn, flags=re.I)
    parts = b.split('_')
    wy = parts[1].strip() if len(parts) > 1 else ''
    en = parts[2].strip() if len(parts) > 2 else ''
    au = parts[3].strip() if len(parts) > 3 else ''
    m = re.search(r'\(([^()]*-[^()]*)\)\s*$', au)
    dates = m.group(1) if m else ''
    au = re.sub(r'\s*\([^()]*\)\s*$', '', au)
    return wy, en.rstrip('+'), au, dates

def meta_for(i):
    for r in by_id.get(i, []):
        if 'META' in r['zip_path'].upper().split('/')[-1]:
            t = rtf2txt(open(f"{OFF}/{r['file']}", encoding='utf-8', errors='replace').read())
            return t
    return ''

# 本地目录（三语）
cat = open(f"{ROOT}/藏文大藏经/《松繃》(Sungbum)《（大師）文集總目》.txt", encoding='utf-8', errors='replace').read()
lcat = {}
for e in re.split(r'(?=S\d{5}[-\w]*\((?:e|m|n|f|a)TB\))', cat)[1:]:
    m = re.match(r'(S\d{5}[-\w]*)\((?:e|m|n|f|a)TB\)\s*(.*)', e, re.S)
    if not m or m.group(1) in lcat:
        continue
    body = m.group(2)
    # 结构：WYLIE 藏文 English_AUTHOR (dates) AUTHORWYLIE 藏文作者 dates 分类
    mt = re.match(r"([^\u0f00-\u0fff]+?)\s+([\u0f00-\u0fff][\u0f00-\u0fff\s]*?)\s+(.*?)_([^_]+?)\s*\(([^()]*)\)\s+(.*)", body, re.S)
    if mt:
        rest = mt.group(6)
        subj = re.findall(r'[\u0f00-\u0fff/་།\s]+$', rest)
        lcat[m.group(1)] = dict(wylie=mt.group(1).strip(), tib=mt.group(2).strip(), en=mt.group(3).strip(),
                                author=mt.group(4).strip(), dates=mt.group(5).strip(),
                                subject=subj[0].strip() if subj else '')
print('本地目录解析', len(lcat), file=sys.stderr)

titles = {r['work_id'].split(':')[-1]: r for r in csv.DictReader(open(f"{REPO}/titles.tsv", encoding='utf-8'), delimiter='\t') if r['collection'] == 'sungbum'}
persons = collections.defaultdict(list)
for r in csv.DictReader(open(f"{REPO}/persons.tsv", encoding='utf-8'), delimiter='\t'):
    if ':sungbum:' in r['work_id']:
        persons[r['work_id'].split(':')[-1]].append(r)

out = []
for r in rows:
    i = r['编号']; src = r['来源'][0]
    rec = dict(编号=i, 来源=r['来源'], 文件=r['文件'], 音节数=r['音节数'], 版权提示=r['版权提示'],
               藏文标题='', 威利标题='', 英文标题='', 作者_威利='', 作者_藏文='', 生卒='', 作者BDRC='',
               分类_英='', 子类路径='', 本地分类='', dr汉文标题='', dr汉文来源='')
    if src == 'R':
        t = titles.get(i, {})
        rec['藏文标题'] = t.get('title_full_tibetan') or t.get('title_tibetan', '')
        rec['威利标题'] = t.get('title_full_wylie') or t.get('title_wylie', '')
        rec['dr汉文标题'] = t.get('title_han', ''); rec['dr汉文来源'] = t.get('title_han_source', '')
        p = [x for x in persons.get(i, []) if x.get('role') in ('author', '')] or persons.get(i, [])
        if p:
            rec['作者_威利'] = p[0].get('name', ''); rec['作者BDRC'] = p[0].get('bdrc_id', '')
    cands = off_lookup(i) if src != 'L' else (by_id.get(i, []) or off_lookup(i))
    if src == 'O':
        cands = [x for x in off if x['file'].endswith(os.path.basename(r['文件'])[:-4].replace('.en', '') + '.TXT')] or cands
    main = [x for x in cands if 'META' not in x['zip_path'].upper().split('/')[-1]]
    if main:
        zp = main[0]['zip_path']
        segs = zp.split('/')
        wy, en, au, dates = parse_fn(segs[-1])
        rec['分类_英'] = segs[1] if len(segs) > 2 else ''
        rec['子类路径'] = ' / '.join(segs[2:-1])
        rec['威利标题'] = rec['威利标题'] or wy
        rec['英文标题'] = en
        rec['作者_威利'] = rec['作者_威利'] or au
        rec['生卒'] = dates
        meta = meta_for(main[0]['acip_id'])
        if meta:
            pm = parse_fn('X_' + meta) if '_' in meta else None
            if pm and len(pm[1]) > len(rec['英文标题']):
                rec['英文标题'] = pm[1]
            if pm and pm[3]:
                rec['生卒'] = rec['生卒'] or pm[3]
    base = re.match(r'(S\d{5}(?:-\d+)?)', i)
    lc = lcat.get(i) or (lcat.get(base.group(1)) if base else None)
    if src == 'L' or not rec['英文标题']:
        if lc:
            rec['威利标题'] = rec['威利标题'] or lc['wylie']
            rec['藏文标题'] = rec['藏文标题'] or lc['tib']
            rec['英文标题'] = rec['英文标题'] or lc['en']
            rec['作者_威利'] = rec['作者_威利'] or lc['author']
            rec['生卒'] = rec['生卒'] or lc['dates']
    if lc:
        rec['本地分类'] = lc['subject']
    if src == 'L':
        rec['本地分类'] = rec['本地分类'] or r['英文标题_或原路径'].split('/')[0]
        if not rec['藏文标题']:
            rec['藏文标题'] = r['藏文标题']
    if not rec['藏文标题'] and rec['威利标题']:
        rec['藏文标题'] = acip2uni(rec['威利标题'])
    out.append(rec)

cols = list(out[0].keys())
with open(f"{WORK}/base.tsv", 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=cols, delimiter='\t'); w.writeheader(); w.writerows(out)
c = collections.Counter()
for r in out:
    for k in ('藏文标题', '英文标题', '作者_威利', '生卒', '分类_英', '本地分类', 'dr汉文标题'):
        c[k] += bool(r[k])
print(len(out), dict(c), file=sys.stderr)
