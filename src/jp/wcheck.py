import re,sys,glob
BASE=r'[々ヶ一-鿿]'
def parse(path):
    out=[]
    for ln,l in enumerate(open(path,encoding="utf-8"),1):
        if not l.startswith("W.push"): continue
        m=re.match(r'^W\.push\(\[(.*)\]\);\s*$',l.rstrip())
        if not m: out.append((ln,None,"shape")); continue
        f=re.findall(r'"((?:[^"\\]|\\.)*)"',m.group(1))
        lv=re.search(r',\s*([123])\]\);\s*$',l)
        out.append((ln,f,lv.group(1) if lv else None))
    return out
bad=0; total=0; words=[]
for path in sys.argv[1:]:
    items=parse(path); n=0
    for ln,f,lv in items:
        n+=1; total+=1
        if f is None or len(f)!=5 or lv is None:
            print(f"!! {path}:{ln} 字段数={len(f) if f else '?'} 级别={lv}"); bad+=1; continue
        words.append((f[0],path,ln))
        ann=f[3]
        plain=re.sub(r'[（(][^）)]*[）)]','\x00',ann)
        for mm in re.finditer(BASE+r'+',plain):
            if mm.end()>=len(plain) or plain[mm.end()]!='\x00':
                print(f"?? {path}:{ln} 未注音「{mm.group()}」 in {ann}"); bad+=1
        for ch in f[0]+f[1]+f[3]:
            o=ord(ch)
            if 0xAC00<=o<=0xD7A3 or 0x1100<=o<=0x11FF:
                print(f"!! {path}:{ln} ハングル混入「{ch}」 in {ann}"); bad+=1
        if "(" in re.sub(r'[（(][^）)]*[）)]','',ann): 
            print(f"?? {path}:{ln} 括号不配对: {ann}"); bad+=1
    print(f"{path}: {n} 条")
# 全局查重（含旧文件）
old=[]
for p in sorted(glob.glob("d?.js")):
    for ln,l in enumerate(open(p,encoding="utf-8"),1):
        m=re.match(r'^V\.push\(\["([^"]+)"',l)
        if m: old.append((m.group(1),p,ln))
seen={}
for w,p,ln in old+words:
    if w in seen: print(f"!! 重复「{w}」: {seen[w]} と {p}:{ln}"); bad+=1
    else: seen[w]=f"{p}:{ln}"
print(f"--- 新規 {total} 条 / 総語彙 {len(seen)} / 問題 {bad}")
