import pickle,csv,re,os,shutil
OUT=os.environ.get("CANON_ROOT", ".") + "/松绷最全版"; OFF=os.environ.get("CANON_ROOT", ".") + "/_来源/ALL官方"
LOCAL=os.environ.get("CANON_ROOT", ".") + "/藏文大藏经/ACIP/SUNGBUM (Tibetan Letters)/SUNGBUM (Tibetan Letters)"
SYL=re.compile(r'[ཀ-ྼ]+'); N=4
def grams(sy): return {hash('་'.join(sy[i:i+N])) for i in range(len(sy)-N+1)}
rows=list(csv.DictReader(open(f"{OUT}/总目录.tsv",encoding='utf-8-sig'),delimiter='\t'))
have=set()
for r in rows: have|=grams(SYL.findall(re.sub(r'\[[^\]]*\]',' ',open(f"{OUT}/{r['文件']}",encoding='utf-8').read())))
off={r['file']:r['zip_path'] for r in csv.DictReader(open(f"{OFF}/flat_index.tsv",encoding='utf-8'),delimiter='\t')}
U={v['path']:v for v in pickle.load(open('units.pkl','rb')).values()}
res=[r for r in pickle.load(open('lost.pkl','rb')) if r[1]>=0.10]
res.sort(key=lambda r:(-r[1]))
add=0
for est,f0,src,n,path in res:
    if src=='O': t=open(f"official_unicode/{os.path.basename(path)[:-4]}.txt",encoding='utf-8').read()
    else: t=open(f"{LOCAL}/{path}",'rb').read().decode('utf-16',errors='replace').lstrip('﻿')
    g=grams(SYL.findall(re.sub(r'\[[^\]]*\]',' ',t))); f=len(g-have)/len(g)
    if f<0.10: continue
    have|=g; add+=1
    if src=='O':
        base=os.path.basename(path)[:-4]; dst=f"2_补自ALL官方2026/{base}.txt"; shutil.copy(f"{OFF}/{path}",f"{OUT}/2_补自ALL官方2026/{base}.acip.TXT"); info=off[path]
    else:
        name=re.sub(r'[\\/:*?"<>|\s]+','_',os.path.basename(path)[:-4])[:120]; dst=f"3_补自本地ACIP2016/{name}.txt"; i=2
        while os.path.exists(f"{OUT}/{dst}"): dst=f"3_补自本地ACIP2016/{name}_{i}.txt"; i+=1
        info=path
    open(f"{OUT}/{dst}",'w',encoding='utf-8').write(t)
    rows.append({**{k:'' for k in rows[0]},'编号':U[path]['id'],'来源':'O ALL官方2026' if src=='O' else 'L 本地ACIP2016','文件':dst,'音节数':n,
      '新内容占比':f"{f:.2f}",'英文标题_或原路径':info,'藏文标题':re.sub(r'\s+',' ',re.sub(r'\[[^\]]*\]','',t)).strip()[:120],
      '备注':'精确比对补收' + ('；大部分内容已见于前面来源，含异文' if f<0.3 else '')})
with open(f"{OUT}/总目录.tsv",'w',encoding='utf-8-sig',newline='') as fo:
    w=csv.DictWriter(fo,fieldnames=list(rows[0].keys()),delimiter='\t'); w.writeheader(); w.writerows(rows)
print('补收',add,'总条目',len(rows))
