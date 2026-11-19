"""第2步：把 Esukhia 德格版按 {D…} 标记切成单部文本，并用 rKTs 建立版本对照表。
用法：python3 derge_and_map.py kangyur|tengyur
输出：<部>最全版/4_德格版_Esukhia/D####.txt  与  <部>最全版/版本对照表.tsv
"""
import sys, os, re, csv, glob, collections, xml.etree.ElementTree as ET

COL = sys.argv[1]
ROOT = os.environ.get("CANON_ROOT", ".") + ""
NAME = {'kangyur': '甘珠尔', 'tengyur': '丹珠尔'}[COL]
OUT = f"{ROOT}/{NAME}最全版"
ESU = f"{ROOT}/_来源/Esukhia/derge-{COL}/text"
RK = f"{ROOT}/_来源/rKTs/repo"
DR = f"{ROOT}/_来源/dhammareader/repo/catalog"
DST = f"{OUT}/4_德格版_Esukhia"
os.makedirs(DST, exist_ok=True)

# ---------- 1. 切分德格版 ----------
VAR = re.compile(r'\{([^{},]*),([^{},]*)\}')        # {原刻,现代} → 取原刻
MARK = re.compile(r'\{(D\d+[a-z]?)\}')               # 单部起点
SUB = re.compile(r'\{(D\d+[a-z]?-\d+)\}')            # 品/子部标记
texts = collections.OrderedDict(); cur = '_前置'; vols = collections.defaultdict(list)
for fp in sorted(glob.glob(f"{ESU}/*.txt")):
    vol = os.path.basename(fp)[:-4]
    t = open(fp, encoding='utf-8').read()
    t = VAR.sub(lambda m: m.group(1), t)
    t = t.replace('{DN}', '')
    pos = 0
    for m in MARK.finditer(t):
        texts.setdefault(cur, []).append(t[pos:m.start()])
        cur = m.group(1); vols[cur].append(vol); pos = m.end()
    texts.setdefault(cur, []).append(t[pos:])
    if cur in vols and vols[cur][-1] != vol:
        vols[cur].append(vol)
def dkey(d):
    m = re.match(r'D(\d+)([a-z]?)', d); return (int(m.group(1)), m.group(2))
n = 0
for d, parts in texts.items():
    if d == '_前置':
        continue
    body = SUB.sub(lambda m: f"〔{m.group(1)}〕", ''.join(parts)).strip()
    num, suf = dkey(d)
    open(f"{DST}/D{num:04d}{suf}.txt", 'w', encoding='utf-8').write(body + '\n'); n += 1
print('德格版切分', n, '部', file=sys.stderr)
syl = {d: len(re.findall(r'[ཀ-ྼ]+', ''.join(p))) for d, p in texts.items() if d != '_前置'}

# ---------- 2. rKTs 目录 ----------
def items(path, numtag):
    xml = open(path, encoding='utf-8').read()
    xml = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;)', '&amp;', xml)
    root = ET.fromstring(xml)
    for it in root.iter('item'):
        yield {c.tag: c for c in it}, it
kernel = {}
kfile = f"{RK}/Kernel/{'rkts' if COL == 'kangyur' else 'rktst'}.xml"
numtag = 'rkts' if COL == 'kangyur' else 'rktst'
for _, it in items(kfile, numtag):
    k = (it.findtext(numtag) or '').strip()
    if not k:
        continue
    kernel[k] = dict(
        rkts=k, section=(it.findtext('section') or '').strip(),
        std_tib=(it.find('StandardTibetan').text if it.find('StandardTibetan') is not None else '') or '',
        std_skt=(it.find('StandardSanskrit').text if it.find('StandardSanskrit') is not None else '') or '',
        en84000=(it.find('English84000').text if it.find('English84000') is not None else '') or '')
dxml = f"{RK}/Collections/D Derge {'Kanjur' if COL == 'kangyur' else 'Tanjur'}/D.xml"
d2r = {}; dinfo = {}
for _, it in items(dxml, numtag):
    ref = (it.findtext('ref') or '').strip(); k = (it.findtext(numtag) or '').strip()
    if not ref:
        continue
    loc = it.find('loc')
    dinfo[ref] = dict(rkts=k, tib=(it.findtext('tib') or '').strip(),
                      author='; '.join((a.text or '').strip() for a in it.findall('author')),
                      translator='; '.join((a.text or '').strip() for a in it.findall('translator')),
                      vol=(loc.findtext('vol') if loc is not None else '') or '', pages=(loc.findtext('p') if loc is not None else '') or '')
    d2r[ref] = k
r2h = collections.defaultdict(list)
if COL == 'kangyur':
    for _, it in items(f"{RK}/Collections/H Lhasa Kanjur/H.xml", 'rkts'):
        ref = (it.findtext('ref') or '').strip(); k = (it.findtext('rkts') or '').strip()
        if ref and k:
            r2h[k].append(ref)

# ---------- 3. 与合并后的 ACIP 文件（拉萨版/ACIP 德格版）对应 ----------
works = [r for r in csv.DictReader(open(f"{DR}/works.tsv", encoding='utf-8'), delimiter='\t') if r['collection'] == COL]
titles = {r['work_id']: r for r in csv.DictReader(open(f"{DR}/titles.tsv", encoding='utf-8'), delimiter='\t') if r['collection'] == COL}
toh2acip = collections.defaultdict(list)
for w in works:
    for t in re.findall(r'D\d+[a-z]?', w['toh'] or ''):
        toh2acip[t].append(w['acip_id'])
# 书名表里的德格编号（含 ACIP 合并文件中的单部经）
toh2title = {}
for r in titles.values():
    for t in re.findall(r'D\d+[a-z]?', r['toh'] or ''):
        if t not in toh2title or not r['part_of']:
            toh2title[t] = r
        if r['part_of']:
            pid = r['part_of'].split(':')[-1]
            if pid not in toh2acip[t]:
                toh2acip[t].append(pid + '（合并文件）')
lan = collections.defaultdict(list)
for r in csv.DictReader(open(f"{DR}/sources/lancaster1979/chinese_parallels.tsv", encoding='utf-8'), delimiter='\t'):
    if r['taisho']:
        lan[r['toh']].append(f"T{r['taisho']} {r['title_han']}")
if COL == 'kangyur':
    for r in csv.DictReader(open(f"{DR}/sources/otani1930/chinese_parallels.tsv", encoding='utf-8'), delimiter='\t'):
        t = r.get('taisho') or ''
        if t and r.get('toh') and r.get('check') != 'taisho_title_differs':
            s = f"T{t} {r.get('title_han', '')}".strip()
            if s not in lan[r['toh']]:
                lan[r['toh']].append(s)

def dnorm(ref):
    m = re.match(r'D(\d+)([a-z]?)', ref)
    return f"D{int(m.group(1))}{m.group(2)}" if m else ref

rows = []
alld = sorted(set(dnorm(x) for x in list(dinfo) + list(syl)), key=dkey)
merged_dir = f"{OUT}/1_校正版_dhammareader"
for d in alld:
    info = dinfo.get(d, {}); k = info.get('rkts', ''); kn = kernel.get(k, {})
    num, suf = dkey(d)
    acips = toh2acip.get(d, [])
    tt = toh2title.get(d) or (titles.get(f"tibetan:{COL}:{acips[0]}", {}) if acips else {})
    rows.append({
        '德格编号': d,
        'rKTs编号': k,
        '拉萨版编号': '; '.join(r2h.get(k, [])) if COL == 'kangyur' else '',
        'ACIP编号': '; '.join(acips),
        '藏文书名(威利)': kn.get('std_tib') or info.get('tib', ''),
        '梵文书名': kn.get('std_skt', ''),
        '84000英文书名': kn.get('en84000', ''),
        '汉文书名(dhammareader)': tt.get('title_han', ''),
        '汉文书名类型': {'established': '已有汉译', 'parallel': '对应汉译', 'coined': '拟译'}.get(tt.get('title_han_source', ''), ''),
        '大正藏对应': ' | '.join(lan.get(d, [])),
        '作者': info.get('author', ''),
        '译者': info.get('translator', ''),
        '德格函': info.get('vol', ''),
        '德格叶码': info.get('pages', ''),
        '部类': kn.get('section', ''),
        '德格版文件': f"4_德格版_Esukhia/D{num:04d}{suf}.txt" if d in syl else '',
        '德格版音节数': syl.get(d, ''),
        'ACIP文件': '; '.join(f"1_校正版_dhammareader/{a.replace('（合并文件）','')}.txt" for a in acips if os.path.exists(f"{merged_dir}/{a.replace('（合并文件）','')}.txt")),
    })
with open(f"{OUT}/版本对照表.tsv", 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter='\t'); w.writeheader(); w.writerows(rows)
c = collections.Counter()
for r in rows:
    for k in ('rKTs编号', '拉萨版编号', 'ACIP编号', '德格版文件', 'ACIP文件', '大正藏对应', '汉文书名(dhammareader)'):
        c[k] += bool(r[k])
print(f"{NAME} 对照表 {len(rows)} 行", dict(c), file=sys.stderr)
