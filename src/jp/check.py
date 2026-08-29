import re,sys
def sents(path,idx):
    out=[]
    for l in open(path,encoding="utf-8"):
        if re.match(r'^[VGS]\.push',l):
            f=re.findall(r'"((?:[^"\\]|\\.)*)"',l)
            out.append(f[idx])
    return out
def anns(path):
    t=open(path,encoding="utf-8").read()
    return re.findall(r'^"(.*)",$',t,re.M)
def strip(s): return re.sub(r'[（(][^）)]*[）)]','',s)
bad=0
for src,idx,fur in [tuple(x.split(":")) for x in sys.argv[1:]]:
    a=sents(src,int(idx)); b=anns(fur)
    if len(a)!=len(b):
        print(f"!! {fur}: {len(b)} annotated vs {len(a)} source"); bad+=1; continue
    for i,(x,y) in enumerate(zip(a,b)):
        if strip(y)!=x:
            print(f"!! {fur} line {i+1}\n   src: {x}\n   got: {strip(y)}"); bad+=1
    # every kanji covered?
    for i,y in enumerate(b):
        plain=re.sub(r'[（(][^）)]*[）)]','\x00',y)
        for m in re.finditer(r'[々ヶ一-鿿]+',plain):
            if m.end()>=len(plain) or plain[m.end()]!='\x00':
                print(f"?? {fur} line {i+1}: 未注音 「{m.group()}」 in {y}"); bad+=1
    print(f"{fur}: {len(b)} sentences OK" if not bad else f"{fur}: checked")
print("PROBLEMS:",bad)
