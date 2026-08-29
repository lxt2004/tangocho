import re,sys,glob
BASE=r'[々ヶ一-鿿]'
def parse(path):
    out=[]
    for ln,l in enumerate(open(path,encoding="utf-8"),1):
        if not l.startswith(("E.push","P.push","S.push")): continue
        m=re.match(r'^[EPS]\.push\(\[(.*)\]\);\s*$',l.rstrip())
        if not m: out.append((ln,None,None,l[0])); continue
        f=re.findall(r'"((?:[^"\\]|\\.)*)"',m.group(1))
        lv=re.search(r',\s*([123])\]\);\s*$',l)
        out.append((ln,f,lv.group(1) if lv else None,l[0]))
    return out
NEED={"E":5,"P":5,"S":3}   # E:語 中 日 例文 和訳 / P:熟語 中 日 例文 和訳 / S:英文 中 和訳
bad=0; total=0; keys=[]
for path in sys.argv[1:]:
    items=parse(path); n=0
    for ln,f,lv,t in items:
        n+=1; total+=1
        if f is None or lv is None or len(f)!=NEED[t]:
            print(f"!! {path}:{ln} 種別{t} 字段数={len(f) if f else '?'} 級={lv}"); bad+=1; continue
        keys.append((f[0],path,ln))
        # 英語欄に全角・かなが混じっていないか
        if re.search(r'[ぁ-んァ-ン一-鿿０-９]', f[0]):
            print(f"!! {path}:{ln} 英単語に日本語が混入: {f[0]}"); bad+=1
        # 和訳のふりがな：漢字の直後に読みが必要
        targets = [f[2], f[4]] if t in "EP" else [f[2]]
        for ja in targets:
            html=re.sub(BASE+r'+[（(][^）)]+[）)]','\x01',ja)
            if '(' in html or '（' in html:
                print(f"!! {path}:{ln} ルビ変換後に括弧が残る（注釈は〔〕を使う）: {ja}"); bad+=1
            pl=re.sub(r'[（(][^）)]*[）)]','\x00',ja)
            for mm in re.finditer(BASE+r'+',pl):
                if mm.end()>=len(pl) or pl[mm.end()]!='\x00':
                    print(f"?? {path}:{ln} 未注音「{mm.group()}」 in {ja}"); bad+=1
        if re.search(r'[ᄀ-ᇿ가-힣]', "".join(f)):
            print(f"!! {path}:{ln} ハングル混入"); bad+=1
    print(f"{path}: {n} 件")
seen={}
for w,p2,ln in keys:
    k=w.lower()
    if k in seen: print(f"!! 重複「{w}」: {seen[k]} と {p2}:{ln}"); bad+=1
    else: seen[k]=f"{p2}:{ln}"
print(f"--- 合計 {total} 件 / 一意 {len(seen)} / 問題 {bad}")
