"""第3步：甘珠尔 / 丹珠尔 汉文目录。用法：venv/bin/python build_canon_catalog.py
输出：<部>最全版/<部>汉文目录.xlsx / .md / .tsv
"""
import csv, re, os, json, collections, sys
import opencc, pyewts
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = os.environ.get("CANON_ROOT", ".") + ""
DR = f"{ROOT}/_来源/dhammareader/repo/catalog"
T2S = opencc.OpenCC('t2s'); EW = pyewts.pyewts()
UNIFY = [('金刚怖畏', '大威德金刚'), ('怖畏金刚', '大威德金刚')]

def rd(p):
    return list(csv.DictReader(open(p, encoding='utf-8-sig'), delimiter='\t'))

tr = {}
for k in (1, 2):
    p = f"{ROOT}/_目录工作_甘丹/w{k}/out.tsv"
    ins = [json.loads(l) for l in open(f"{ROOT}/_目录工作_甘丹/w{k}/in.jsonl", encoding='utf-8')]
    outs = rd(p)
    assert [o['编号'] for o in outs] == [i['编号'] for i in ins], f"批次{k} 编号不一致"
    for i, o in zip(ins, outs):
        tr[(i['部'], i['编号'])] = o

REV = {}
for k in range(1, 9):
    d = f"{ROOT}/_目录工作_甘丹/r{k}"
    if not os.path.exists(f"{d}/out.tsv"):
        continue
    ins = [json.loads(l) for l in open(f"{d}/in.jsonl", encoding='utf-8')]
    outs = rd(f"{d}/out.tsv")
    assert [o['编号'] for o in outs] == [i['编号'] for i in ins], f"校订批次 r{k} 编号不一致"
    for i, o in zip(ins, outs):
        REV[(i['部'], i['编号'])] = o
REVTYPE = {'沿用dhammareader': '拟译（dhammareader，已核）', '校订dhammareader': '拟译（本次校订）', '已有汉译': '已有汉译'}

def apply_rev(col, key, row):
    o = REV.get((col, key))
    if o and row['译名类型'] == '拟译（dhammareader）':
        row['dhammareader原译名'] = row['汉文书名']
        row['汉文书名'] = o['汉文书名']; row['译名类型'] = REVTYPE.get(o['译名类型'], row['译名类型'])
        row['备注'] = (o.get('说明') or '') + (('；' + row['备注']) if row['备注'] else '')

OVERRIDE = {('甘珠尔', 'D359a'): ('四十二章经', '已有汉译', '藏译自汉文，对应大正藏 T784《四十二章经》（人工补标）'),
            ('甘珠尔', 'D956'): ('圣大威德金刚陀罗尼', '拟译（本次）', "rdo rje 'jigs byed 按术语规范统一译“大威德金刚”")}
for k, (n, t, note) in OVERRIDE.items():
    tr[k] = {'汉文书名': n, '译名类型': t, '说明': note}

CAT = {
 '甘珠尔': [("'dul ba", '律部'), ("'bum", '十万颂般若部'), ('nyi khri', '二万颂般若部'), ('khri brgyad', '一万八千颂般若部'), ('khri pa', '一万颂般若部'),
          ('brgyad stong', '八千颂般若部'), ('sher phyin', '般若部（诸品）'), ('phal chen', '华严部'), ('dkon brtsegs', '宝积部'), ('mdo sde', '经部'),
          ("myang 'das", '涅槃部'), ('rgyud', '密续部'), ('rnying rgyud', '旧译密续部'), ("dus 'khor", '时轮部'), ('gzungs', '陀罗尼集'), ('dkar chag', '目录')],
 '丹珠尔': [('bstod tshogs', '赞颂部'), ("rgyud 'grel", '密续释部'), ("mdo 'grel (sher phyin)", '般若部'), ("mdo 'grel (dbu ma)", '中观部'),
          ("mdo 'grel (mdo)", '经释部'), ("mdo 'grel (sems tsam)", '唯识部'), ("mdo 'grel (mngon pa)", '对法部'), ("mdo 'grel ('dul ba)", '律部'),
          ("mdo 'grel (skyes rabs)", '本生部'), ("mdo 'grel (spring yig)", '书翰部'), ("mdo 'grel (tshad ma)", '量论部'), ("mdo 'grel (sgra mdo)", '声明部'),
          ("mdo 'grel (gso rig)", '医方明部'), ("mdo 'grel (bzo rig)", '工巧明部'), ("mdo 'grel (thun mong ba lugs kyi bstan bcos)", '世俗论部'),
          ("mdo 'grel (bstan bcos sna tshogs)", '杂部'), ('dkar chag', '目录')],
}

def cat_of(col, vol):
    pre = vol.split(',')[0].strip()
    for i, (k, v) in enumerate(CAT[col]):
        if pre == k:
            return i, v
    return 98, '未详'

def tib(wy):
    try:
        return EW.toUnicode(wy) if wy else ''
    except Exception:
        return ''

def zh(s):
    s = T2S.convert(s or '')
    for a, b in UNIFY:
        s = s.replace(a, b)
    return s

for col, COL in (('甘珠尔', 'kangyur'), ('丹珠尔', 'tengyur')):
    OUT = f"{ROOT}/{col}最全版"
    conc = rd(f"{OUT}/版本对照表.tsv")
    merged = rd(f"{OUT}/总目录.tsv")
    works = {r['acip_id']: r for r in rd(f"{DR}/works.tsv") if r['collection'] == COL}
    titles = {r['work_id'].split(':')[-1]: r for r in rd(f"{DR}/titles.tsv") if r['collection'] == COL}
    rows = []
    used_acip = set()
    for x in conc:
        for a in x['ACIP编号'].split('; '):
            used_acip.add(a.replace('（合并文件）', ''))
        t = tr.get((col, x['德格编号']))
        if t:
            name, typ, note = t['汉文书名'], ('已有汉译' if t['译名类型'] == '已有汉译' else '拟译（本次）'), t['说明']
        else:
            name = zh(x['汉文书名(dhammareader)'])
            typ = {'已有汉译': '已有汉译', '对应汉译': '对应汉译', '拟译': '拟译（dhammareader）'}.get(x['汉文书名类型'], '')
            note = ''
        ci, cn = cat_of(col, x['德格函'])
        syl = x['德格版音节数']
        rows.append({'汉文书名': name, '译名类型': typ, '大正藏对应': zh(x['大正藏对应']), '藏文书名': tib(x['藏文书名(威利)']),
                     '威利转写': x['藏文书名(威利)'], '梵文书名': x['梵文书名'], '84000英文书名': x['84000英文书名'], '作者': x['作者'], '译者': x['译者'],
                     '部类': cn, '德格编号': x['德格编号'], '拉萨版编号': x['拉萨版编号'], 'ACIP编号': x['ACIP编号'], 'rKTs编号': x['rKTs编号'],
                     '德格函·叶码': (x['德格函'] + ' ' + x['德格叶码']).strip(), '德格版文件': x['德格版文件'], 'ACIP文件': x['ACIP文件'],
                     '音节数': syl, '备注': note, '_o': (ci, re.sub(r'\D', '', x['德格编号']).zfill(5), x['德格编号'])})
    # ACIP 有、德格编号未对上的
    for a, w in works.items():
        if a in used_acip:
            continue
        t = titles.get(a, {})
        f = f"1_校正版_dhammareader/{a}.txt"
        rows.append({'汉文书名': zh(t.get('title_han', '')), '译名类型': {'established': '已有汉译', 'parallel': '对应汉译', 'coined': '拟译（dhammareader）'}.get(t.get('title_han_source', ''), ''),
                     '大正藏对应': '', '藏文书名': t.get('title_tibetan', ''), '威利转写': t.get('title_wylie', ''), '梵文书名': t.get('title_sanskrit', ''),
                     '84000英文书名': '', '作者': '', '译者': '', '部类': 'ACIP 独有（未对上德格编号）', '德格编号': w.get('toh', ''), '拉萨版编号': '',
                     'ACIP编号': a, 'rKTs编号': '', '德格函·叶码': '', '德格版文件': '', 'ACIP文件': f if os.path.exists(f"{OUT}/{f}") else '',
                     '音节数': '', '备注': f"德格对应状态：{w.get('toh_status', '') or '无'}", '_o': (97, a, a)})
    # 本地补入
    for m in merged:
        if not m['来源'].startswith(('L', 'O')):
            continue
        base = re.match(r'([A-Z]+0*\d+)', m['编号'])
        cand = [k for k in titles if base and k.startswith(base.group(1))]
        t = titles.get(cand[0], {}) if cand else {}
        LOCALT = {'KL00296(eTB)': ('童子喻经', "gzhon nu dpe'i mdo"), 'KL04568-P(fTB)': ('胜者甘珠尔诸法类名目略录（甘珠尔目录）', "rgyal ba'i bka' 'gyur rin po che'i chos tshan so so'i mtshan byang dkar chag bsdus pa"),
                  'acip-k_lha_sa-099-016': ('世间供赞成就根本续', "'jig rten mchod bstod sgrub pa rtsa ba'i rgyud"), 'acip-k_lha_sa-099-015': ('猛咒集金刚根本续', "drag sngags 'dus pa rdo rje rtsa ba'i rgyud"),
                  'acip-k_lha_sa-091-052': ('圣青颈陀罗尼', "'phags pa nI la kaN+Tha zhes bya ba'i gzungs"), 'acip-k_lha_sa-096-013': ('令欢喜陀罗尼（据卷末题，存疑）', '')}
        lk = os.path.basename(m['文件'])[:-4]
        if lk in LOCALT:
            t = {'title_han': LOCALT[lk][0], 'title_wylie': LOCALT[lk][1]}
        rows.append({'汉文书名': zh(t.get('title_han', '')) + ('' if lk in LOCALT else ('（本地异本或补卷）' if t else '')), '译名类型': ('拟译（本次，据正文首题）' if lk in LOCALT else ('拟译（dhammareader）' if t else '')),
                     '大正藏对应': '', '藏文书名': tib(t.get('title_wylie', '')), '威利转写': t.get('title_wylie', ''), '梵文书名': '', '84000英文书名': '', '作者': '', '译者': '',
                     '部类': '本地 ACIP2016 补入', '德格编号': '', '拉萨版编号': '', 'ACIP编号': m['编号'], 'rKTs编号': '', '德格函·叶码': '', '德格版文件': '',
                     'ACIP文件': m['文件'], '音节数': m['音节数'], '备注': f"新内容占比 {m['新内容占比']}；{m['备注']}；原路径 {m['原路径']}", '_o': (99, m['编号'], m['编号'])})
    for r in rows:
        r.setdefault('dhammareader原译名', '')
        if r['部类'] != '本地 ACIP2016 补入':
            key = r['德格编号'] if (r['德格编号'] and not r['部类'].startswith('ACIP')) else 'ACIP:' + r['ACIP编号']
            apply_rev(col, key, r)
    POST = [('多罗', '度母', None), ('观自在', '观音', None), ('胜乐轮', '胜乐金刚', None), ('阎曼德迦', '阎魔敌', None),
            ('护摩', '火供', 'sbyin sreg'), ('教王', '续王', 'rgyud'), ('曼荼罗', '坛城', "dkyil 'khor")]
    npost = collections.Counter()
    for r in rows:
        if r['译名类型'] in ('已有汉译', '对应汉译'):
            continue
        t0 = r['汉文书名']; w = (r['威利转写'] or '').lower()
        for a, b, need in POST:
            if a in r['汉文书名'] and (need is None or need in w) and not (a == '曼荼罗' and 'maN' in (r['威利转写'] or '')):
                r['汉文书名'] = r['汉文书名'].replace(a, b); npost[a] += 1
        r['汉文书名'] = r['汉文书名'].replace('胜乐金刚金刚', '胜乐金刚').replace('坛城坛城', '坛城')
    print(col, '最终术语统一', dict(npost), file=sys.stderr)
    rows.sort(key=lambda r: r['_o'])
    cols = ['序号'] + [c for c in rows[0] if not c.startswith('_')]
    for i, r in enumerate(rows, 1):
        r['序号'] = i
    with open(f"{OUT}/{col}汉文目录.tsv", 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter='\t', extrasaction='ignore'); w.writeheader(); w.writerows(rows)
    wb = Workbook(); ws = wb.active; ws.title = '总目录'; ws.append(cols)
    for r in rows:
        ws.append([r[c] for c in cols])
    hdr = Font(bold=True); fill = PatternFill('solid', fgColor='DDE5EE')
    W = {'序号': 6, '汉文书名': 36, '译名类型': 14, '大正藏对应': 30, '藏文书名': 40, '威利转写': 36, '梵文书名': 30, '84000英文书名': 34, '作者': 22, '译者': 26,
         '部类': 14, '德格编号': 9, '拉萨版编号': 10, 'ACIP编号': 12, 'rKTs编号': 8, '德格函·叶码': 24, '德格版文件': 28, 'ACIP文件': 32, '音节数': 9, '备注': 30}
    for i, c in enumerate(cols, 1):
        ws.column_dimensions[get_column_letter(i)].width = W.get(c, 12); ws.cell(1, i).font = hdr; ws.cell(1, i).fill = fill
    ws.freeze_panes = 'C2'; ws.auto_filter.ref = ws.dimensions
    wc = wb.create_sheet('部类统计'); wc.append(['部类', '条目数', '有古代汉译（已有/对应）'])
    tc = collections.OrderedDict()
    for r in rows:
        x = tc.setdefault(r['部类'], [0, 0]); x[0] += 1; x[1] += r['译名类型'] in ('已有汉译', '对应汉译')
    for k, (n, h) in tc.items():
        wc.append([k, n, h])
    wh = wb.create_sheet('有古代汉译的')
    wh.append(['序号', '汉文书名', '译名类型', '大正藏对应', '藏文书名', '德格编号', '部类'])
    nh = 0
    for r in rows:
        if r['译名类型'] in ('已有汉译', '对应汉译') or r['大正藏对应']:
            wh.append([r['序号'], r['汉文书名'], r['译名类型'], r['大正藏对应'], r['藏文书名'], r['德格编号'], r['部类']]); nh += 1
    FLAG = re.compile(r'拿不准|未能确认|无法|推断|推定|存疑|未核|不确定|疑为|疑误|残缺|截断|字面|勉强')
    wr = wb.create_sheet('待复核'); rc = ['序号', '德格编号', 'ACIP编号', '汉文书名', '译名类型', '备注', '威利转写', '梵文书名', '84000英文书名', 'dhammareader原译名']
    wr.append(rc); nf = 0
    for r in rows:
        if FLAG.search(r['备注'] or ''):
            wr.append([r.get(c, '') for c in rc]); nf += 1
    print(col, '待复核', nf, file=sys.stderr)
    wn = wb.create_sheet('说明')
    for n in [f'{col}汉文目录 —— 2026-11-18 编', '以德格版（Esukhia，公有领域）为主序，附 ACIP 拉萨版/德格版编号与文件、rKTs 编号；另列 ACIP 独有和本地补入的条目。',
              '译名类型：已有汉译＝与大正藏汉译为同一部；对应汉译＝有对应的汉译本（可能是异译或部分对应）；拟译（dhammareader）＝韩国 dhammareader 项目的 AI 拟译，已转简体并统一“大威德金刚”等术语，未逐条校订；拟译（本次）＝本次新译。',
              '大正藏对应来自 Lancaster《高丽大藏经解题目录》（1979）与大谷大学《西藏大藏经甘殊尔勘同目录》（1930–32），经 dhammareader 整理。',
              '德格版文件保留德格原刻拼写（Esukhia 标注的现代写法未采用）；叶码格式如 [1b.2]＝第 1 叶背面第 2 行。']:
        wn.append([n])
    wn.column_dimensions['A'].width = 140
    wb.save(f"{OUT}/{col}汉文目录.xlsx")
    md = [f"# {col}汉文目录", '', f"共 {len(rows):,} 条，以德格版为序。“〔古译〕”表示有大正藏汉译对应。完整字段见 `{col}汉文目录.xlsx`。", '']
    cur = None
    for r in rows:
        if r['部类'] != cur:
            cur = r['部类']; md += ['', f"## {cur}", '']
        mark = '〔古译：' + r['大正藏对应'].split(' | ')[0] + '〕' if r['大正藏对应'] else ''
        md.append(f"{r['序号']}. **{r['汉文书名'] or '（未译）'}**{mark}　{r['藏文书名'][:50]}　`{r['德格编号'] or r['ACIP编号']}`")
    open(f"{OUT}/{col}汉文目录.md", 'w', encoding='utf-8').write('\n'.join(md) + '\n')
    st = collections.Counter(r['译名类型'] for r in rows)
    print(col, len(rows), '条', dict(st), '有大正藏对应', sum(1 for r in rows if r['大正藏对应']), '无汉文书名', sum(1 for r in rows if not r['汉文书名']),
          '部类', dict(collections.Counter(r['部类'] for r in rows)), file=sys.stderr)
