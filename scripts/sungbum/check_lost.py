import pickle,csv,re,os,collections,sys
SCR='.'; OUT=os.environ.get("CANON_ROOT", ".") + "/松绷最全版"
LOCAL=os.environ.get("CANON_ROOT", ".") + "/藏文大藏经/ACIP/SUNGBUM (Tibetan Letters)/SUNGBUM (Tibetan Letters)"
SYL=re.compile(r'[ཀ-ྼ]+'); N=4
def grams(sy): return {hash('་'.join(sy[i:i+N])) for i in range(len(sy)-N+1)}
rows=list(csv.DictReader(open(f"{OUT}/总目录.tsv",encoding='utf-8-sig'),delimiter='\t'))
inc={r['文件'] for r in rows}
have=set()
for r in rows:
    have|=grams(SYL.findall(re.sub(r'\[[^\]]*\]',' ',open(f"{OUT}/{r['文件']}",encoding='utf-8').read())))
U=pickle.load(open('units.pkl','rb'))
incl_O={os.path.basename(r['文件'])[:-4] for r in rows if r['来源'].startswith('O')}
incl_L={r['英文标题_或原路径'] for r in rows if r['来源'].startswith('L')}
res=[]
for v in U.values():
    if v['n']<100 or v['src']=='R': continue
    if v['src']=='O':
        if os.path.basename(v['path'])[:-4] in incl_O: continue
        t=open(f"official_unicode/{os.path.basename(v['path'])[:-4]}.txt",encoding='utf-8').read()
    else:
        if v['valid']<0.8 or v['path'] in incl_L: continue
        t=open(f"{LOCAL}/{v['path']}",'rb').read().decode('utf-16',errors='replace')
    g=grams(SYL.findall(re.sub(r'\[[^\]]*\]',' ',t)))
    if not g: continue
    f=len(g-have)/len(g); res.append((int(f*v['n']),round(f,3),v['src'],v['n'],v['path']))
res.sort(reverse=True)
b=collections.Counter()
for est,f,s,n,p in res:
    k='≥30%' if f>=.3 else '10-30%' if f>=.1 else '3-10%' if f>=.03 else '<3%'
    b[(s,k)]+=1
print(sorted(b.items())); print('估计未收新音节合计(含拼写差异)',sum(r[0] for r in res))
for r in res[:25]: print(r)
pickle.dump(res,open('lost.pkl','wb'))
