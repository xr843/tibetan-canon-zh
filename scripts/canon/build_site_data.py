"""为本地检索网站生成数据：检索/data/catalog.json
依赖：藏文大藏经总目录.tsv、_目录工作_注释关系/注释关系表.tsv（若已生成）
"""
import csv, json, os, re, collections

ROOT = os.environ.get("CANON_ROOT", ".") + ""
OUT = f"{ROOT}/检索/data"
os.makedirs(OUT, exist_ok=True)
M = list(csv.DictReader(open(f"{ROOT}/藏文大藏经总目录.tsv", encoding='utf-8-sig'), delimiter='\t'))
rel = collections.defaultdict(list); rev = collections.defaultdict(list)
rp = f"{ROOT}/_目录工作_注释关系/注释关系表.tsv"
if os.path.exists(rp):
    for r in csv.DictReader(open(rp, encoding='utf-8-sig'), delimiter='\t'):
        if re.match(r'[KTS]-\d{4}$', r['所释编号'] or ''):
            rel[r['注疏编号']].append([r['所释编号'], r['关系']])
            rev[r['所释编号']].append([r['注疏编号'], r['关系']])
KEYS = [('id', '总编号'), ('b', '部'), ('c', '部类'), ('sc', '子类'), ('zh', '汉文书名'), ('zt', '译名来源'), ('tr', '汉译情况'),
        ('ts', '大正藏对应'), ('mo', '近现代汉译'), ('bo', '藏文书名'), ('wy', '威利转写'), ('sa', '梵文书名'), ('en', '英文书名'),
        ('au', '作者'), ('ao', '作者原名'), ('ad', '作者生卒'), ('tl', '译者'), ('d', '德格编号'), ('h', '拉萨版编号'), ('a', 'ACIP编号'),
        ('rk', 'rKTs编号'), ('dv', '德格函·叶码'), ('f1', '主文本文件'), ('f2', '德格版文件'), ('n', '音节数'), ('cp', '版权提示'),
        ('dr', 'dhammareader原译名'), ('nt', '备注')]
data = []
for r in M:
    o = {k: r[v] for k, v in KEYS if r.get(v)}
    if r['总编号'] in rel:
        o['cm'] = rel[r['总编号']]
    if r['总编号'] in rev:
        o['cb'] = rev[r['总编号']]
    data.append(o)
json.dump(data, open(f"{OUT}/catalog.json", 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('条目', len(data), '有所释', sum(1 for d in data if 'cm' in d), '有注疏', sum(1 for d in data if 'cb' in d),
      '大小', os.path.getsize(f"{OUT}/catalog.json") // 1024, 'KB')
