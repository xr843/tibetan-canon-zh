"""合并译名结果，输出：松绷汉文目录.xlsx / 松绷汉文目录.md / 总目录.tsv（加汉文列）"""
import csv, re, os, collections, sys, json
COL = os.environ.get("CANON_ROOT", ".") + "/松绷最全版"
W = f"{COL}/_目录工作"

def read_tsv(p):
    return list(csv.DictReader(open(p, encoding='utf-8-sig'), delimiter='\t'))

base = read_tsv(f"{W}/base.tsv")
# 按 (编号, 来源首字母) 排队，按输入批次中的出现顺序逐条对应，避免重复编号串行
queue = collections.defaultdict(list)
for idx, b in enumerate(base):
    queue[(b['编号'], b['来源'][0])].append(idx)
tr_by_idx = {}
problems = []
for k in range(1, 8):
    p = f"{W}/titles_out_{k}.tsv"
    ins = [json.loads(l) for l in open(f"{W}/titles_in_{k}.jsonl", encoding='utf-8')]
    outs = read_tsv(p) if os.path.exists(p) else []
    if [o['编号'] for o in outs] != [i['编号'] for i in ins]:
        problems.append(f"批次{k}: 输入{len(ins)} 输出{len(outs)}，编号顺序不一致")
        continue
    for i, o in zip(ins, outs):
        idx = queue[(i['编号'], i['来源'])].pop(0)
        tr_by_idx[idx] = o
au = {r['作者键']: r for r in read_tsv(f"{W}/authors_out.tsv")}
sg = {r['分类片段']: r for r in read_tsv(f"{W}/segments_out.tsv")}

def norm(a):
    return re.sub(r'\s+', ' ', a.lower().replace('’', "'").replace('tz', 'ts').strip())

TOPORDER = ["LAM RIM", "BLO SBYONG", "BKA' GDAMS PA", "NYAMS LEN", "DBU MA", "SEMS TZAM", "PHAR PHYIN", "TSAD MA", "MNGON PA",
            "'DUL BA", "GRUB MTHA'", "DRANG NGES", "MDO 'GREL", "RGYUD", "CHO GA", "BSTOD PA", "RNAM THAR", "RTOGS BRJOD", "BLA BRGYUD",
            "CHOS 'BYUNG", "GTSANG DGON PA CHOS 'BYUNG", "GSAN YIG", "DRI LAN", "'PHRIN YIG", "BCA' YIG", "SNYAN NGAG", "SGRA", "GSUM RTAGS",
            "TSIG MDZOD", "SMAN", "SKAR RTZIS", "LO THO", "LHA BZO", "GNAS YIG", "PHRAN TSEGS", ""]

def seg_zh(s):
    return (sg.get(s) or {}).get('汉译') or s

TIBCAT = {'བཀའ་གདམས་པ': "BKA' GDAMS PA_KADAMPA SCHOOL", 'སྐར་རྩིས': 'SKAR RTZIS_ASTROLOGY', 'གྲུབ་མཐའ': "GRUB MTHA'_COMPARATIVE PHILOSOPHY (SIDDHANTA)",
          'རྒྱུད': 'RGYUD_SECRET TEACHINGS (TANTRA)', 'སྒྲ': 'SGRA_STUDY OF SANSKRIT', 'མངོན་པ': 'MNGON PA_HIGHER KNOWLEDGE (ABHIDHARMA) (VAIBHASHIKA SCHOOL)',
          'བཅའ་ཡིག': "BCA' YIG_OFFICIAL DOCUMENTS", 'ཆོ་ག': 'CHO GA_RITUALS', 'ཆོས་འབྱུང': "CHOS 'BYUNG_RELIGIOUS HISTORIES", 'ཉམས་ལེན': 'NYAMS LEN_PERSONAL PRACTICE',
          'སྙན་ངག': 'SNYAN NGAG_CLASSICAL POETRY', 'རྟོགས་བརྗོད': 'RTOGS BRJOD_LIVES OF INDIAN SAINTS (AVADANA)', 'བསྟོད་པ': 'BSTOD PA_EULOGIES (STOTRA)',
          'དྲང་ངེས': 'DRANG NGES_ART OF INTERPRETATION', 'དྲི་ལན': 'DRI LAN_QUESTIONS AND ANSWERS', 'མདོ་འགྲེལ': "MDO 'GREL_COMMENTARIES TO SUTRAS",
          'འདུལ་བ': "'DUL BA_VOWED MORALITY (VINAYA)", 'རྣམ་ཐར': 'RNAM THAR_BIOGRAPHIES', 'གནས་ཡིག': 'GNAS YIG_PILGRIMAGE GUIDES',
          'ཕར་ཕྱིན': 'PHAR PHYIN_PERFECTION OF WISDOM (PRAJNA PARAMITA) (MADHYAMIKA SVATANTRIKA SCHOOL)', 'ཕྲན་ཚེགས': 'PHRAN TSEGS_MISCELLANEOUS',
          'འཕྲིན་ཡིག': "'PHRIN YIG_EPISTLES", 'དབུ་མ': 'DBU MA_MIDDLE-WAY PHILOSOPHY (MADHYAMIKA PRASANGIKA SCHOOL)', 'སྨན': 'SMAN_MEDICINE',
          'ཚད་མ': 'TSAD MA_STUDY OF ACCURATE PERCEPTION (SAUTRANTIKA SCHOOL)', 'ཚིག་མཛོད': 'TSIG MDZOD_LEXICAL MATERIALS', 'ལམ་རིམ': 'LAM RIM_STEPS OF THE PATH',
          'ལོ་ཐོ': 'LO THO_CALENDRICAL MATERIALS', 'བླ་བརྒྱུད': 'BLA BRGYUD_LAMA LINEAGE TREES', 'བློ་སྦྱོང': 'BLO SBYONG_DEVELOPING THE GOOD HEART',
          'སེམས་ཙམ': 'SEMS TZAM_MIND-ONLY SCHOOL (CHITTAMATRA)', 'གསན་ཡིག': 'GSAN YIG_RECORDS OF TEACHINGS RECEIVED', 'གསུམ་རྟགས': 'GSUM RTAGS_GRAMMAR',
          'ལྷ་བཟོ': 'LHA BZO_FINE ARTS'}

def tib_cat(s):
    for part in re.split(r'[/ ]', s or ''):
        k = part.strip('།་ ')
        k = re.sub(r'^[༠-༩]+\s*', '', k).strip('།་ ')
        if k in TIBCAT:
            return TIBCAT[k]
    for k, v in TIBCAT.items():
        if k in (s or ''):
            return v
    return ''

current_files = {r['文件'] for r in read_tsv(f"{COL}/总目录.tsv")}
rows = []
for idx, b in enumerate(base):
    t = tr_by_idx.get(idx, {})
    if b['文件'] not in current_files:
        continue  # 已剔除的变体
    a = au.get(norm(b['作者_威利']), {}) if b['作者_威利'] else {}
    if not b['分类_英']:
        b['分类_英'] = tib_cat(b['本地分类'])
    path_author = ''
    for s in [x for x in b['子类路径'].split(' / ') if x][::-1]:
        if (sg.get(s) or {}).get('类型') == '人名':
            path_author = sg[s]['汉译']; break
    top = b['分类_英']
    topkey = top.split('_')[0] if top else ''
    sub = [s for s in b['子类路径'].split(' / ') if s]
    rows.append({
        '序号': 0,
        '汉文书名': t.get('汉文书名', ''),
        '译名类型': t.get('译名类型', ''),
        '藏文书名': b['藏文标题'],
        '威利转写': b['威利标题'],
        '英文书名(ACIP)': b['英文标题'],
        '作者': a.get('汉译名', '') or (b['作者_威利'] and '（未译）' + b['作者_威利']) or (path_author and path_author + '〔据分类路径〕') or '',
        '作者生卒': a.get('生卒', '') or b['生卒'],
        '作者藏文转写': b['作者_威利'],
        '大类': seg_zh(top) if top else '未分类',
        '子类': ' › '.join(seg_zh(s) for s in sub),
        '编号': b['编号'],
        '来源': b['来源'],
        '文件': b['文件'],
        '音节数': int(b['音节数']),
        '版权提示': b['版权提示'],
        'dhammareader原译名': b['dr汉文标题'],
        '译名说明': t.get('说明', ''),
        '_topkey': topkey,
    })
# 跨批次统一（抽查发现的不一致）
UNIFY_SUB = [('独勇士', '独勇'), ('单勇', '独勇'), ('讲授施食行持', '讲授朵玛供行持')]
UNIFY_EXACT = {
    '第二品辨析·色拉杰尊却吉坚赞贝桑波口述': '第二品辨析·至尊却吉坚赞贝桑波口传',
    '第二品辨析·至尊却吉坚赞贝桑波语流': '第二品辨析·至尊却吉坚赞贝桑波口传',
    '上二戒补救法·依至尊实修编排': '上二律仪还净法·依至尊实修所编',
    '遍知嘉木样协巴文集所出三入门导引文·利他宝珠美鬘': '三入门导引文·利他宝珠美鬘',
    '大威德金刚教法史·三界尽胜成就宝藏': '吉祥大威德金刚教法史·三界尽胜成就宝藏',
    '独勇大威德金刚念修文略': '独勇大威德金刚略念修文',
    '独勇大威德金刚十分火供行法·一切成就源': '独勇大威德金刚十分火供作法·一切成就之源',
}
BY_ID = {'S05650E': '俱舍论广释·引对法宝之车'}  # 据正文首题补全
for r in rows:
    t = r['汉文书名']
    for a, b in UNIFY_SUB:
        t = t.replace(a, b)
    r['汉文书名'] = BY_ID.get(r['编号'], UNIFY_EXACT.get(t, t))
    if r['作者'].startswith('（未译）') and r['作者'].endswith('+'):
        r['作者'] = '（著录残缺：' + r['作者藏文转写'] + '）'
# 未分类条目：按同一部书的其他版本编号（SE/SL/SD/SN 前缀、数字相同）沿用分类
def numkey(i):
    m = re.match(r'S[A-Z]?0*(\d+)', i)
    return m.group(1) if m else None
known = {}
for r in rows:
    if r['大类'] != '未分类' and numkey(r['编号']):
        known.setdefault(numkey(r['编号']), (r['大类'], r['子类'], r['_topkey']))
for r in rows:
    if r['大类'] == '未分类' and numkey(r['编号']) in known:
        r['大类'], r['子类'], r['_topkey'] = known[numkey(r['编号'])]
        r['子类'] = (r['子类'] + ' ' if r['子类'] else '') + '〔据同书他本编号归类〕'
MANUAL = {}
for ids, key in [
    ('SE00070I SE0070M SL00070I SL00070N SB00218I SR00218A TD3947E', 'ལམ་རིམ'),
    ('SL0059E SL0059I SB00059I', 'འདུལ་བ'),
    ('SN06838I SS06838I SA05408E SK05408E ST05408E', 'དབུ་མ'),
    ('SE05414M SL05414N ST05414I', 'སེམས་ཙམ'),
    ('SE05525M SE5525M SL05525N', 'མངོན་པ'),
    ('SD12216E SN12216E SD12135E SN12135E SE00191M SL00191I SE06260A SL06260I', 'རྣམ་ཐར'),
    ('SP00024E SP00024M ST00024N', 'མདོ་འགྲེལ'),
    ('SP05939N SS05939E S0298D unknown SK00046E SS00046E', 'རྒྱུད'),
    ('S06393M S12416E', 'གསུམ་རྟགས'),
    ('SB25006 SP25006', 'ཆོས་འབྱུང'),
]:
    for i in ids.split():
        MANUAL[i] = TIBCAT[key]
for r in rows:
    if r['大类'] == '未分类' and r['编号'] in MANUAL:
        full = MANUAL[r['编号']]
        r['大类'] = seg_zh(full); r['_topkey'] = full.split('_')[0]; r['子类'] = '〔据书名归类〕'
order = {k: i for i, k in enumerate(TOPORDER)}
rows.sort(key=lambda r: (order.get(r['_topkey'], 99), r['子类'].startswith('〔'), r['子类'], r['作者'], r['编号']))
for i, r in enumerate(rows, 1):
    r['序号'] = i

cols = [c for c in rows[0] if not c.startswith('_')]
with open(f"{COL}/松绷汉文目录.tsv", 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=cols, delimiter='\t', extrasaction='ignore'); w.writeheader(); w.writerows(rows)

# ---- Excel ----
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
wb = Workbook()
ws = wb.active; ws.title = '总目录'
ws.append(cols)
for r in rows:
    ws.append([r[c] for c in cols])
widths = {'序号': 6, '汉文书名': 40, '译名类型': 12, '藏文书名': 45, '威利转写': 40, '英文书名(ACIP)': 40, '作者': 22, '作者生卒': 11,
          '作者藏文转写': 28, '大类': 12, '子类': 30, '编号': 11, '来源': 14, '文件': 36, '音节数': 9, '版权提示': 22,
          'dhammareader原译名': 28, '译名说明': 30}
hdr = Font(bold=True); fill = PatternFill('solid', fgColor='DDE5EE')
for i, c in enumerate(cols, 1):
    ws.column_dimensions[get_column_letter(i)].width = widths.get(c, 14)
    ws.cell(1, i).font = hdr; ws.cell(1, i).fill = fill
ws.freeze_panes = 'C2'; ws.auto_filter.ref = ws.dimensions

# 作者索引
wa = wb.create_sheet('作者索引')
wa.append(['作者', '生卒', '身份简注', '藏文转写', '收录条目数', '音节数合计', '所在大类'])
agg = collections.defaultdict(lambda: dict(n=0, syl=0, tops=collections.Counter(), dates='', note='', wy=''))
for r in rows:
    k = r['作者'] or '（作者不详）'
    g = agg[k]; g['n'] += 1; g['syl'] += r['音节数']; g['tops'][r['大类']] += 1
    g['dates'] = g['dates'] or r['作者生卒']; g['wy'] = g['wy'] or r['作者藏文转写']
    a = au.get(norm(r['作者藏文转写']), {}) if r['作者藏文转写'] else {}
    g['note'] = g['note'] or a.get('身份简注', '')
for k, g in sorted(agg.items(), key=lambda kv: -kv[1]['n']):
    wa.append([k, g['dates'], g['note'], g['wy'], g['n'], g['syl'], '、'.join(f"{t}{c}" for t, c in g['tops'].most_common())])
for i, wdt in enumerate([28, 12, 20, 40, 10, 12, 60], 1):
    wa.column_dimensions[get_column_letter(i)].width = wdt; wa.cell(1, i).font = hdr; wa.cell(1, i).fill = fill
wa.freeze_panes = 'A2'

# 分类统计
wc = wb.create_sheet('分类统计')
wc.append(['大类', '条目数', '音节数合计'])
tc = collections.OrderedDict()
for r in rows:
    x = tc.setdefault(r['大类'], [0, 0]); x[0] += 1; x[1] += r['音节数']
for k, (n, s) in tc.items():
    wc.append([k, n, s])
for i, wdt in enumerate([28, 10, 14], 1):
    wc.column_dimensions[get_column_letter(i)].width = wdt; wc.cell(1, i).font = hdr; wc.cell(1, i).fill = fill

# 待复核
FLAG = re.compile(r'拿不准|未能确认|无法|推断|推定|存疑|未核实|不确定|疑为|疑误|按正文认书|残缺|截断|乱码|字面')
wr = wb.create_sheet('待复核')
rcols = ['序号', '编号', '汉文书名', '译名类型', '译名说明', '藏文书名', '威利转写', '英文书名(ACIP)', '作者', 'dhammareader原译名']
wr.append(rcols)
nflag = 0
for r in rows:
    if FLAG.search(r['译名说明'] or ''):
        wr.append([r[c] for c in rcols]); nflag += 1
for i, wdt in enumerate([6, 11, 36, 12, 50, 40, 40, 36, 20, 28], 1):
    wr.column_dimensions[get_column_letter(i)].width = wdt; wr.cell(1, i).font = hdr; wr.cell(1, i).fill = fill
wr.freeze_panes = 'C2'
print('待复核', nflag, file=sys.stderr)

# 说明
wn = wb.create_sheet('说明')
notes = [
    '松绷（藏地祖师文集）汉文目录 —— 2026-11-18 编',
    '收录范围：松绷最全版的全部 1,874 个文件（dhammareader 校正版 1,613 部 + ACIP 官方包补入 189 + 本地 ACIP2016 补入 60 + 英文资料 12）。',
    '汉文书名：简体。“译名类型”说明来源——已有汉译：通行汉译本书名；沿用dhammareader：沿用韩国 dhammareader 项目的拟译，仅繁转简；校订dhammareader：对其拟译作了修改，见“译名说明”；新拟：本次新译。',
    '除“已有汉译”外，书名均为拟译，不是历史上真实存在的汉文书名，引用时请注明“拟译”。',
    '译名由 AI 按统一术语规范（_目录工作/译名规范.md）翻译，并经抽查，未经藏学专家逐条审定。',
    '本地补入部分有编号冲突（同一编号在不同来源是不同的书），这些条目按正文开头认书，见“译名说明”。',
    '版权提示：作者卒于 1955 年后或现代编纂的作品，只宜个人研究，不宜公开分发。',
    '文件：相对“松绷最全版”文件夹的路径。',
]
for n in notes:
    wn.append([n])
wn.column_dimensions['A'].width = 140
wb.save(f"{COL}/松绷汉文目录.xlsx")

# ---- Markdown ----
md = ['# 松绷（藏地祖师文集）汉文目录', '',
      f'共 {len(rows):,} 条。按大类、子类、作者排列。书名后的括号是作者和生卒；“〔拟〕”表示拟译书名，“〔通行〕”表示已有汉译本书名。完整字段（藏文、威利转写、英文、文件路径）见同目录的 `松绷汉文目录.xlsx`。', '']
md.append('## 分类一览'); md.append('')
md.append('| 大类 | 条目数 | 音节数 |'); md.append('|---|---|---|')
for k, (n, s) in tc.items():
    md.append(f'| {k} | {n} | {s:,} |')
cur_top = cur_sub = None
for r in rows:
    if r['大类'] != cur_top:
        cur_top = r['大类']; cur_sub = None
        md += ['', f"## {cur_top}", '']
    if r['子类'] != cur_sub:
        cur_sub = r['子类']
        if cur_sub:
            md += ['', f"### {cur_sub}", '']
    mark = '〔通行〕' if r['译名类型'] == '已有汉译' else '〔拟〕'
    au_s = f"（{r['作者']}{'，' + r['作者生卒'] if r['作者生卒'] else ''}）" if r['作者'] else ''
    cp = ' ⚠版权' if r['版权提示'] else ''
    md.append(f"{r['序号']}. **{r['汉文书名'] or '（未译）'}**{mark}{au_s}　{r['藏文书名'][:60]}　`{r['编号']}`{cp}")
open(f"{COL}/松绷汉文目录.md", 'w', encoding='utf-8').write('\n'.join(md) + '\n')

st = collections.Counter(r['译名类型'] for r in rows)
print('条目', len(rows), '译名类型', dict(st), '缺汉文书名', sum(1 for r in rows if not r['汉文书名']),
      '作者未译', sum(1 for r in rows if r['作者'].startswith('（未译）')), '问题', problems, file=sys.stderr)
