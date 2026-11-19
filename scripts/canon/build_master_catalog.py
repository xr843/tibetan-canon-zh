"""合并甘珠尔、丹珠尔、松绷三部汉文目录为《藏文大藏经总目录》。
用法：venv/bin/python build_master_catalog.py
输出：<数据根目录>/藏文大藏经总目录.xlsx / .md / .tsv
"""
import csv, os, re, json, collections, sys
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

ROOT = os.environ.get("CANON_ROOT", ".") + ""
DR = f"{ROOT}/_来源/dhammareader/repo/catalog"

def rd(p):
    return list(csv.DictReader(open(p, encoding='utf-8-sig'), delimiter='\t'))

# ---- 丹珠尔作者汉文名 ----
auth_zh = {}
for k in (1, 2):
    p = f"{ROOT}/_目录工作_甘丹/a{k}/out.tsv"
    if os.path.exists(p):
        ins = [json.loads(l)['梵文或藏文名'] for l in open(f"{ROOT}/_目录工作_甘丹/a{k}/in.jsonl", encoding='utf-8')]
        outs = rd(p)
        if [o['梵文或藏文名'] for o in outs] == ins:
            for o in outs:
                auth_zh[o['梵文或藏文名']] = o['汉文名']
        else:
            print(f'作者批次 a{k} 顺序不一致，跳过', file=sys.stderr)
work_auth = collections.defaultdict(list)
for r in csv.DictReader(open(f"{DR}/persons.tsv", encoding='utf-8'), delimiter='\t'):
    if ':tengyur:' in r['work_id'] and r['role'] == 'author':
        work_auth[r['work_id'].split(':')[-1]].append(r['name'])

MODERN = collections.defaultdict(list)
for k in (1, 2):
    p = f"{ROOT}/_目录工作_汉译核对/m{k}/out.tsv"
    if not os.path.exists(p):
        continue
    ins = [json.loads(l) for l in open(f"{ROOT}/_目录工作_汉译核对/m{k}/in.jsonl", encoding='utf-8')]
    outs = rd(p)
    if len(outs) != len(ins):
        print(f'汉译核对 m{k} 行数不一致，跳过', file=sys.stderr); continue
    for i, o in zip(ins, outs):
        if o['关系'] in ('全译', '节译', '讲记或编述') and o['对应总编号'] not in ('', '无'):
            for code in re.split(r'[;；,，\s]+', o['对应总编号']):
                if code:
                    MODERN[code].append(dict(书名=i['译本书名'], 来源=i['来源'], 链接=i['链接'], 关系=o['关系'], 把握=o['把握'], 作者行=i['译本作者行']))

TYPE = {'已有汉译': '已有汉译', '对应汉译': '对应汉译'}
COLS = ['总编号', '部', '部类', '子类', '汉文书名', '译名类型', '译名来源', '汉译情况', '大正藏对应', '近现代汉译', '所释典籍', '注疏数', '藏文书名', '威利转写', '梵文书名', '英文书名',
        '作者', '作者原名', '作者生卒', '译者', '德格编号', '拉萨版编号', 'ACIP编号', 'rKTs编号', '德格函·叶码',
        '主文本文件', '德格版文件', '音节数', '版权提示', 'dhammareader原译名', '备注']
rows = []

def canon(col, pre):
    for x in rd(f"{ROOT}/{col}最全版/{col}汉文目录.tsv"):
        acips = [a.replace('（合并文件）', '') for a in (x['ACIP编号'] or '').split('; ') if a]
        names = []
        for a in acips:
            names += work_auth.get(a, [])
        names = list(dict.fromkeys(names))
        zh = '；'.join(auth_zh.get(n, n) for n in names) if names else ''
        f1 = x['ACIP文件'].split('; ')[0] if x['ACIP文件'] else ''
        rows.append({
            '总编号': '', '部': col, '部类': x['部类'], '子类': '', '汉文书名': x['汉文书名'],
            '译名类型': TYPE.get(x['译名类型'], '拟译'), '译名来源': x['译名类型'], '大正藏对应': x['大正藏对应'],
            '藏文书名': x['藏文书名'], '威利转写': x['威利转写'], '梵文书名': x['梵文书名'], '英文书名': x['84000英文书名'],
            '作者': zh, '作者原名': '；'.join(names) or x['作者'], '作者生卒': '', '译者': x['译者'],
            '德格编号': x['德格编号'], '拉萨版编号': x['拉萨版编号'], 'ACIP编号': x['ACIP编号'], 'rKTs编号': x['rKTs编号'],
            '德格函·叶码': x['德格函·叶码'], '主文本文件': f"{col}最全版/{f1}" if f1 else '',
            '德格版文件': f"{col}最全版/{x['德格版文件']}" if x['德格版文件'] else '', '音节数': x['音节数'],
            '版权提示': '', 'dhammareader原译名': x.get('dhammareader原译名', ''), '备注': x['备注'], '_pre': pre})

canon('甘珠尔', 'K'); canon('丹珠尔', 'T')
for x in rd(f"{ROOT}/松绷最全版/松绷汉文目录.tsv"):
    rows.append({
        '总编号': '', '部': '松绷', '部类': x['大类'], '子类': x['子类'], '汉文书名': x['汉文书名'],
        '译名类型': '已有汉译' if x['译名类型'] == '已有汉译' else '拟译', '译名来源': x['译名类型'], '大正藏对应': '',
        '藏文书名': x['藏文书名'], '威利转写': x['威利转写'], '梵文书名': '', '英文书名': x['英文书名(ACIP)'],
        '作者': x['作者'], '作者原名': x['作者藏文转写'], '作者生卒': x['作者生卒'], '译者': '',
        '德格编号': '', '拉萨版编号': '', 'ACIP编号': x['编号'], 'rKTs编号': '', '德格函·叶码': '',
        '主文本文件': f"松绷最全版/{x['文件']}", '德格版文件': '', '音节数': x['音节数'], '版权提示': x['版权提示'],
        'dhammareader原译名': x['dhammareader原译名'], '备注': x['译名说明'], '_pre': 'S'})
cnt0 = collections.Counter()
for r in rows:
    cnt0[r['_pre']] += 1
    code = f"{r['_pre']}-{cnt0[r['_pre']]:04d}"
    ms = MODERN.get(code, [])
    r['近现代汉译'] = '；'.join(f"{m['书名']}（{m['来源']}，{m['关系']}，把握{m['把握']}）" for m in ms)
    r['_modern'] = any(m['关系'] in ('全译', '节译') and m['把握'] in ('高', '中') for m in ms)
for r in rows:
    if r['部'] == '松绷':
        r['汉译情况'] = '有近现代汉译（据书名）' if r['译名类型'] == '已有汉译' else '未见汉译'
    elif r['大正藏对应'] or r['译名类型'] in ('已有汉译', '对应汉译'):
        r['汉译情况'] = '有古代汉译' + ('' if r['大正藏对应'] else '（通行书名，未标大正藏号）')
    else:
        r['汉译情况'] = '未见汉译'
    if r['_modern']:
        r['汉译情况'] = ('有近现代汉译' if r['汉译情况'] in ('未见汉译', '有近现代汉译（据书名）') else r['汉译情况'] + '；有近现代汉译')
    elif r['汉译情况'] == '有近现代汉译（据书名）':
        r['汉译情况'] = '有近现代汉译（仅据书名，未匹配到译本）'
REL = collections.defaultdict(list); NC = collections.Counter()
rp = f"{ROOT}/_目录工作_注释关系/注释关系表.tsv"
if os.path.exists(rp):
    for x in rd(rp):
        if re.match(r'[KTS]-\d{4}$', x['所释编号']):
            REL[x['注疏编号']].append(f"{x['所释编号']} {x['所释书名']}（{x['关系']}，把握{x['把握']}）"); NC[x['所释编号']] += 1
cnt = collections.Counter()
for r in rows:
    cnt[r['_pre']] += 1
    r['总编号'] = f"{r['_pre']}-{cnt[r['_pre']]:04d}"
    r['所释典籍'] = '；'.join(REL.get(r['总编号'], [])); r['注疏数'] = NC.get(r['总编号'], '') or ''
missing = sum(1 for r in rows for c in ('主文本文件', '德格版文件') if r[c] and not os.path.exists(f"{ROOT}/{r[c]}"))

# ---- TSV ----
with open(f"{ROOT}/藏文大藏经总目录.tsv", 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=COLS, delimiter='\t', extrasaction='ignore'); w.writeheader(); w.writerows(rows)

def num(v):
    try:
        return int(v)
    except Exception:
        return 0

# ---- Excel ----
wb = Workbook(); hdr = Font(bold=True); fill = PatternFill('solid', fgColor='DDE5EE')
def sheet(ws, header, data, widths):
    ws.append(header)
    for d in data:
        ws.append(d)
    for i, wdt in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = wdt; ws.cell(1, i).font = hdr; ws.cell(1, i).fill = fill
    ws.freeze_panes = 'B2'
ws = wb.active; ws.title = '总目录'
W = [9, 7, 14, 22, 36, 9, 18, 16, 28, 34, 34, 7, 36, 32, 28, 30, 22, 26, 11, 24, 9, 10, 12, 8, 22, 34, 30, 9, 18, 26, 30]
sheet(ws, COLS, [[r[c] for c in COLS] for r in rows], W)
ws.freeze_panes = 'F2'; ws.auto_filter.ref = ws.dimensions

# 部类统计
stat = collections.OrderedDict()
for r in rows:
    s = stat.setdefault((r['部'], r['部类']), [0, 0, 0])
    s[0] += 1; s[1] += num(r['音节数']); s[2] += r['汉译情况'] != '未见汉译'
sheet(wb.create_sheet('部类统计'), ['部', '部类', '条目数', '音节数', '有古代或通行汉译', '无汉译（空白）'],
      [[b, c, n, s, h, n - h] for (b, c), (n, s, h) in stat.items()], [8, 30, 10, 14, 16, 14])

# 汉译覆盖
cov = collections.OrderedDict()
for r in rows:
    c = cov.setdefault(r['部'], collections.Counter())
    c['条目'] += 1; c['音节'] += num(r['音节数'])
    if r['_modern']:
        c['近现代'] += 1
    if r['汉译情况'] != '未见汉译':
        c['有汉译'] += 1; c['有汉译音节'] += num(r['音节数'])
sheet(wb.create_sheet('汉译覆盖'), ['部', '条目数', '有汉译条目', '其中有近现代汉译', '无汉译条目', '无汉译占比', '音节数', '有汉译部分音节数', '说明'],
      [[b, c['条目'], c['有汉译'], c['近现代'], c['条目'] - c['有汉译'], f"{(c['条目'] - c['有汉译']) / c['条目']:.0%}", c['音节'], c['有汉译音节'],
        '“有汉译”指有古代汉译本（大正藏）或通行汉译书名；松绷的“已有汉译”只按书名判断，未逐一核对译本' if b == '松绷' else '据大正藏对应（Lancaster 1979、大谷 1930–32）']
       for b, c in cov.items()], [8, 10, 12, 16, 12, 12, 14, 18, 70])

# 翻译空白清单
gap = [r for r in rows if r['汉译情况'] == '未见汉译' and not r['版权提示']]
sheet(wb.create_sheet('翻译空白清单'), ['总编号', '部', '部类', '汉文书名', '藏文书名', '作者', '音节数', '主文本文件'],
      [[r['总编号'], r['部'], r['部类'], r['汉文书名'], r['藏文书名'], r['作者'], num(r['音节数']), r['主文本文件']] for r in gap],
      [9, 7, 16, 40, 40, 24, 10, 36])
print('翻译空白', len(gap), '条', sum(num(r['音节数']) for r in gap), '音节', file=sys.stderr)

# 作者索引
ai = collections.OrderedDict()
for r in rows:
    if not r['作者'] or r['部'] == '甘珠尔':
        continue
    for a, o in zip(r['作者'].split('；'), (r['作者原名'] or '').split('；') + [''] * 9):
        k = (a, r['部'])
        x = ai.setdefault(k, dict(o=o, d=r['作者生卒'], n=0, s=0))
        x['n'] += 1; x['s'] += num(r['音节数'])
sheet(wb.create_sheet('作者索引'), ['作者', '原名', '生卒', '部', '条目数', '音节数'],
      [[a, x['o'], x['d'], b, x['n'], x['s']] for (a, b), x in sorted(ai.items(), key=lambda kv: (-kv[1]['n']))], [30, 36, 12, 8, 10, 12])

# 说明
notes = [
    '藏文大藏经总目录 —— 2026-11-18 编',
    '收录：甘珠尔（佛语部）、丹珠尔（论疏部）、松绷（藏地祖师文集，ACIP 所收，以格鲁派为主）三部。',
    '总编号：K-＝甘珠尔，T-＝丹珠尔，S-＝松绷；甘珠尔、丹珠尔按德格版次序编排，松绷按大类、子类、作者编排。',
    '译名类型：已有汉译＝与古代汉译本（大正藏）为同一部，或为汉传通行书名；对应汉译＝有对应的古代汉译（可能是异译或部分对应）；拟译＝本次或 dhammareader 的拟译书名。“译名来源”列给出细分。',
    '汉译情况：有古代汉译＝有大正藏对应或为汉传通行书名；有近现代汉译＝在大慈恩“月光藏”（253 部）或 CBETA《大藏经补编》等所收近代藏译汉典籍（71 部）中找到全译或节译，具体见“近现代汉译”列；“未见汉译”只表示上述资料中没有，不代表一定没有汉译（台海两岸大量出版物未纳入）。',
    '翻译空白清单：“未见汉译”且无版权提示的条目，可作翻译选题的起点。',
    '除“已有汉译”外，书名均为 AI 拟译，未经藏学专家审定，引用时请注明“拟译”。',
    '文件路径相对于本目录所在文件夹（<数据根目录>/）。主文本文件：甘珠尔、丹珠尔为 ACIP 校正版（dhammareader），松绷为最全版中的文件；德格版文件为 Esukhia 德格版。',
    '音节数：甘珠尔、丹珠尔取德格版，松绷取最全版文件；少数 ACIP 独有条目无数据。',
    '大正藏对应来源：Lancaster《高丽大藏经解题目录》（1979）、大谷大学《西藏大藏经甘殊尔勘同目录》（1930–32），经 dhammareader 整理。',
    '丹珠尔作者的汉文名为本次 AI 翻译（印度论师名用通行译名，其余意译或音译）；甘珠尔为佛语，不列作者。',
    '版权提示：仅松绷部分标注（作者卒于 1955 年后或现代编纂），只宜个人研究。',
    '所释典籍 / 注疏数：注释关系由 AI 依书名判断并在全目录检索得出（1,031 部注疏类条目，793 部找到目录内所释典籍；把握高 427、中 243、低 123），详见 _目录工作_注释关系/注释关系表.tsv 与 注疏谱系.md。来自本地补入、缺少藏文书名转写的条目（如嘉木样协巴俱舍辨析 6 品）未纳入。',
    '各部的详细目录、版本对照表、待复核表，见各部文件夹。',
]
wn = wb.create_sheet('说明')
for n in notes:
    wn.append([n])
wn.column_dimensions['A'].width = 150
wb.move_sheet('说明', offset=-4)
wb.save(f"{ROOT}/藏文大藏经总目录.xlsx")

# ---- Markdown ----
md = ['# 藏文大藏经总目录', '', f"共 {len(rows):,} 条：甘珠尔 {cnt['K']:,}、丹珠尔 {cnt['T']:,}、松绷 {cnt['S']:,}。完整字段见同目录 `藏文大藏经总目录.xlsx`。",
      '“〔古译 T…〕”表示有大正藏汉译对应；未标的为拟译书名。', '', '## 汉译覆盖', '', '| 部 | 条目 | 有汉译 | 无汉译 |', '|---|---|---|---|']
for b, c in cov.items():
    md.append(f"| {b} | {c['条目']:,} | {c['有汉译']:,} | {c['条目'] - c['有汉译']:,} |")
cb = cc = None
for r in rows:
    if r['部'] != cb:
        cb = r['部']; cc = None; md += ['', f"# {cb}", '']
    if r['部类'] != cc:
        cc = r['部类']; md += ['', f"## {cc}", '']
    mark = f"〔古译 {r['大正藏对应'].split(' | ')[0].split(' ')[0]}〕" if r['大正藏对应'] else ('〔通行〕' if r['译名类型'] == '已有汉译' else '')
    au = f"（{r['作者']}）" if r['作者'] else ''
    md.append(f"- `{r['总编号']}` **{r['汉文书名']}**{mark}{au}　{r['藏文书名'][:40]}")
open(f"{ROOT}/藏文大藏经总目录.md", 'w', encoding='utf-8').write('\n'.join(md) + '\n')
print('总条目', len(rows), dict(cnt), '文件缺失', missing, '丹珠尔有汉文作者', sum(1 for r in rows if r['部'] == '丹珠尔' and r['作者'] and r['作者'] != r['作者原名']),
      {b: (c['条目'], c['有汉译']) for b, c in cov.items()}, file=sys.stderr)
