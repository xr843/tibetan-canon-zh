"""把本项目的藏汉对照译稿（Markdown）转成 Word（.docx）。
做法借鉴 sat-docx-punctuate：python-docx + 每个 run 显式指定字体（汉字宋体、藏文作复杂文字用 Microsoft Himalaya）。
支持的 Markdown 子集：# 标题、> 引用块（藏文原文）、普通段落、**粗体**、表格、列表、--- 分隔线、行尾两空格换行。
用法：python3 md2docx.py 译稿.md [输出.docx]
"""
import re, sys, pathlib
import docx
from docx.shared import Pt, Cm, RGBColor
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH

ZH, TIB, LAT = 'SimSun', 'Microsoft Himalaya', 'Times New Roman'
TIB_RE = re.compile(r'([ༀ-࿿]+(?:[\sༀ-࿿]*[ༀ-࿿])?)')

def set_font(run, size, bold=False, tib=False, color=None):
    rpr = run._element.get_or_add_rPr()
    f = rpr.find(qn('w:rFonts'))
    if f is None:
        f = rpr.makeelement(qn('w:rFonts'), {}); rpr.insert(0, f)
    for a, v in (('w:ascii', LAT), ('w:hAnsi', LAT), ('w:eastAsia', ZH), ('w:cs', TIB)):
        f.set(qn(a), v)
    if tib:  # 藏文属复杂文字：要设 cs 字号与 w:cs 标志
        rpr.append(rpr.makeelement(qn('w:cs'), {}))
    run.font.size = Pt(size)
    sz = rpr.makeelement(qn('w:szCs'), {qn('w:val'): str(int(size * 2 * (1.5 if tib else 1)))}); rpr.append(sz)
    run.bold = bold
    if bold:
        rpr.append(rpr.makeelement(qn('w:bCs'), {}))
    if color: run.font.color.rgb = RGBColor.from_string(color)

def add_inline(p, text, size=11, color=None):
    """处理 **粗体**，并把藏文片段单独成 run。"""
    for k, seg in enumerate(re.split(r'\*\*', text)):
        bold = k % 2 == 1
        for piece in TIB_RE.split(seg):
            if not piece: continue
            tib = bool(re.match(r'[ༀ-࿿]', piece))
            r = p.add_run(piece); set_font(r, size, bold, tib, color)

def para(d, text, size=11, style=None, indent=0, color=None, align=None, space_after=4):
    p = d.add_paragraph(style=style) if style else d.add_paragraph()
    pf = p.paragraph_format; pf.space_after = Pt(space_after); pf.space_before = Pt(0); pf.line_spacing = 1.35
    if indent: pf.left_indent = Cm(indent)
    if align: p.alignment = align
    lines = text.split('\n')
    for i, ln in enumerate(lines):
        add_inline(p, ln, size, color)
        if i < len(lines) - 1: p.add_run().add_break()
    return p

def convert(src, dst):
    md = pathlib.Path(src).read_text(encoding='utf-8')
    d = docx.Document()
    sec = d.sections[0]; sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)
    sec.left_margin = sec.right_margin = Cm(2.2); sec.top_margin = sec.bottom_margin = Cm(2.2)
    st = d.styles['Normal']; st.font.name = LAT; st.element.rPr.rFonts.set(qn('w:eastAsia'), ZH)
    for lvl in range(1, 5):  # 标题样式字体
        hs = d.styles[f'Heading {lvl}']; hs.font.name = LAT; hs.element.rPr.rFonts.set(qn('w:eastAsia'), ZH); hs.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
    lines = md.split('\n'); i = 0; buf = []
    def flush():
        if buf:
            text = '\n'.join(l[:-2] if l.endswith('  ') else l for l in buf).strip()
            if text: para(d, text)
            buf.clear()
    while i < len(lines):
        ln = lines[i]
        m = re.match(r'^(#{1,6}) (.*)', ln)
        if m:
            flush(); lvl = min(len(m.group(1)), 4)
            h = d.add_heading(level=lvl); add_inline(h, m.group(2).strip(), {1: 18, 2: 15, 3: 13, 4: 12}[lvl])
            i += 1; continue
        if ln.startswith('>'):
            flush(); q = []
            while i < len(lines) and lines[i].startswith('>'):
                t = lines[i][1:].strip()
                if t: q.append(t)
                i += 1
            para(d, '\n'.join(q), size=12, indent=0.6, color='3A3A3A', space_after=6)
            continue
        if ln.startswith('|'):
            flush(); rows = []
            while i < len(lines) and lines[i].startswith('|'):
                cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-{2,}:?', c) for c in cells if c): rows.append(cells)
                i += 1
            if rows:
                n = max(len(r) for r in rows); t = d.add_table(rows=len(rows), cols=n); t.style = 'Table Grid'
                for r_i, r in enumerate(rows):
                    for c_i in range(n):
                        cell = t.cell(r_i, c_i); cell.text = ''
                        add_inline(cell.paragraphs[0], r[c_i] if c_i < len(r) else '', 9)
                        if r_i == 0:
                            for run in cell.paragraphs[0].runs: run.bold = True
            continue
        if re.match(r'^\s*([-*]|\d+\.) ', ln):
            flush(); para(d, re.sub(r'^\s*[-*] ', '• ', ln), indent=0.5, space_after=2); i += 1; continue
        if ln.strip() in ('---', '***'):
            flush(); para(d, '', space_after=2); i += 1; continue
        if not ln.strip():
            flush(); i += 1; continue
        buf.append(ln); i += 1
    flush()
    d.core_properties.title = pathlib.Path(src).stem
    d.core_properties.comments = 'AI 翻译，未经人工审定。tibetan-canon-zh'
    d.save(dst)

def check(src, dst):
    """仿 sat-docx-punctuate 的交付检查：docx 中的藏文必须与 Markdown 中的藏文逐字一致。"""
    norm = lambda s: re.sub(r'[^ༀ-࿿]', '', s)
    a = norm(pathlib.Path(src).read_text(encoding='utf-8'))
    dd = docx.Document(dst)
    # 按正文中段落与表格的实际先后顺序取文字
    parts = []
    for el in dd.element.body.iterchildren():
        parts.append(''.join(t.text or '' for t in el.iter(qn('w:t'))))
    txt = '\n'.join(parts)
    b = norm(txt)
    return a == b, len(a), len(b)

if __name__ == '__main__':
    src = sys.argv[1]; dst = sys.argv[2] if len(sys.argv) > 2 else str(pathlib.Path(src).with_suffix('.docx'))
    convert(src, dst); ok, a, b = check(src, dst)
    print(f'{dst}：藏文 {b}/{a} 字', '一致' if ok else '不一致'); sys.exit(0 if ok else 1)
