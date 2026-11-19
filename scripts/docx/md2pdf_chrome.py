"""藏汉对照译稿 Markdown → HTML → Chrome 无界面打印 PDF（嵌入字体、按标题生成书签）。
用法：WIN_TEMP=<Windows 临时目录的 WSL 路径> CHROME_EXE=<chrome.exe 的 WSL 路径> python3 md2pdf_chrome.py 译稿.md 输出.pdf [--html 输出.html]
解析的 Markdown 子集与 md2docx.py 相同；字体与 Word 版一致（汉字宋体，藏文 Microsoft Himalaya）。
"""
import re, sys, html, pathlib, subprocess, os, shutil, time
TIB = re.compile(r'([ༀ-࿿][ༀ-࿿\s]*[ༀ-࿿]|[ༀ-࿿])')
CSS = """
@page { size: A4; margin: 22mm 22mm 22mm 22mm; }
body { font-family: "Times New Roman", "SimSun", serif; font-size: 11pt; line-height: 1.6; color: #111; }
.bo { font-family: "Microsoft Himalaya", "Noto Serif Tibetan", serif; font-size: 16.5pt; line-height: 1.35; }
h1 { font-size: 18pt; margin: 0 0 10pt; } h2 { font-size: 15pt; margin: 18pt 0 8pt; page-break-after: avoid; }
h3 { font-size: 13pt; margin: 14pt 0 6pt; page-break-after: avoid; } h4 { font-size: 12pt; margin: 10pt 0 4pt; }
h1, h2, h3, h4 { color: #222; font-weight: bold; font-family: "Times New Roman", "SimSun", serif; }
blockquote { margin: 4pt 0 8pt 17pt; padding: 0; color: #3a3a3a; }
p { margin: 0 0 5pt; }
table { border-collapse: collapse; width: 100%; font-size: 9pt; margin: 6pt 0; page-break-inside: auto; }
td, th { border: 0.5pt solid #888; padding: 2pt 4pt; vertical-align: top; } th { background: #eee; }
tr { page-break-inside: avoid; }
hr { border: 0; border-top: 0.5pt solid #bbb; margin: 8pt 0; }
li { margin: 0 0 2pt; }
"""
def inline(s):
    s = html.escape(s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    return TIB.sub(r'<span class="bo">\1</span>', s)

def to_html(md, title):
    out = []; lines = md.split('\n'); i = 0; buf = []
    def flush():
        if buf:
            t = '<br>'.join(inline(l.rstrip()) for l in buf)
            out.append(f'<p>{t}</p>'); buf.clear()
    while i < len(lines):
        ln = lines[i]
        m = re.match(r'^(#{1,6}) (.*)', ln)
        if m:
            flush(); n = min(len(m.group(1)), 4); out.append(f'<h{n}>{inline(m.group(2).strip())}</h{n}>'); i += 1; continue
        if ln.startswith('>'):
            flush(); q = []
            while i < len(lines) and lines[i].startswith('>'):
                t = lines[i][1:].strip()
                if t: q.append(inline(t))
                i += 1
            out.append('<blockquote>' + '<br>'.join(q) + '</blockquote>'); continue
        if ln.startswith('|'):
            flush(); rows = []
            while i < len(lines) and lines[i].startswith('|'):
                cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-{2,}:?', c) for c in cells if c): rows.append(cells)
                i += 1
            if rows:
                h = ''.join(f'<th>{inline(c)}</th>' for c in rows[0])
                b = ''.join('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>' for r in rows[1:])
                out.append(f'<table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>')
            continue
        if re.match(r'^\s*([-*]|\d+\.) ', ln):
            flush(); out.append(f'<p style="margin-left:12pt">{inline(re.sub(r"^\s*[-*] ", "• ", ln))}</p>'); i += 1; continue
        if ln.strip() in ('---', '***'): flush(); out.append('<hr>'); i += 1; continue
        if not ln.strip(): flush(); i += 1; continue
        buf.append(ln); i += 1
    flush()
    return f'<!doctype html><html lang="zh"><head><meta charset="utf-8"><title>{html.escape(title)}</title><style>{CSS}</style></head><body>' + '\n'.join(out) + '</body></html>'

def main():
    src, dst = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    h = to_html(src.read_text(encoding='utf-8'), src.stem)
    if '--html' in sys.argv: pathlib.Path(sys.argv[sys.argv.index('--html') + 1]).write_text(h, encoding='utf-8')
    # WIN_TEMP：Windows 临时目录在 WSL 中的路径；CHROME_EXE：Windows Chrome 在 WSL 中的路径（由调用方设置）
    T = pathlib.Path(os.environ['WIN_TEMP']) / f'tczc_{os.getpid()}'; T.mkdir(parents=True, exist_ok=True)
    (T / 'in.html').write_text(h, encoding='utf-8')
    win = lambda p: subprocess.run(['wslpath', '-w', str(p)], capture_output=True, text=True).stdout.strip()
    chrome = os.environ['CHROME_EXE']
    t0 = time.time()
    subprocess.run([chrome, '--headless=new', '--disable-gpu', '--no-pdf-header-footer', '--generate-pdf-document-outline',
                    f'--user-data-dir={win(T / "prof")}', f'--print-to-pdf={win(T / "out.pdf")}', 'file:///' + win(T / 'in.html').replace('\\', '/')],
                   check=True, capture_output=True, timeout=1800)
    shutil.copy(T / 'out.pdf', dst); shutil.rmtree(T, ignore_errors=True)
    print(f'{dst} 用时 {time.time() - t0:.0f} 秒')

if __name__ == '__main__': main()
