# 自包含形式の文法(GW)・会話(SW)ファイルの校验
# 使い方: python3 gscheck.py gw*.js sw*.js
import re,sys,glob
BASE=r'[々ヶ一-鿿]'
SPEC={"GW":6,"SW":4}
ANN ={"GW":2,"SW":0}          # 注音が入るフィールドの位置
KEYF={"GW":0,"SW":0}          # 重複判定に使うフィールド

def furi_ok(ann,path,ln,tag):
    """漢字がすべて直後の括弧で注音されているか"""
    bad=0
    plain=re.sub(r'[（(][^）)]*[）)]','\x00',ann)
    for mm in re.finditer(BASE+r'+',plain):
        if mm.end()>=len(plain) or plain[mm.end()]!='\x00':
            print(f"?? {path}:{ln} 未注音「{mm.group()}」 in {ann}"); bad+=1
    if "(" in re.sub(r'[（(][^）)]*[）)]','',ann) or "（" in re.sub(r'[（(][^）)]*[）)]','',ann):
        print(f"?? {path}:{ln} 括号不配对: {ann}"); bad+=1
    return bad

bad=0; total=0; keys={}
for path in sys.argv[1:]:
    tag = "GW" if re.search(r'^GW\.push', open(path,encoding="utf-8").read(), re.M) else "SW"
    n=0
    for ln,l in enumerate(open(path,encoding="utf-8"),1):
        if not l.startswith(tag+".push"): continue
        n+=1; total+=1
        m=re.match(r'^'+tag+r'\.push\(\[(.*)\]\);\s*$',l.rstrip())
        if not m: print(f"!! {path}:{ln} 形が違う"); bad+=1; continue
        f=re.findall(r'"((?:[^"\\]|\\.)*)"',m.group(1))
        lv=re.search(r',\s*([123])\]\);\s*$',l)
        if len(f)!=SPEC[tag]-1 or not lv:
            print(f"!! {path}:{ln} 字段数={len(f)}(期待 {SPEC[tag]-1}) 级别={lv and lv.group(1)}"); bad+=1; continue
        k=f[KEYF[tag]]
        if k in keys: print(f"!! {path}:{ln} 重複「{k}」: {keys[k]} と同じ"); bad+=1
        else: keys[k]=f"{path}:{ln}"
        bad+=furi_ok(f[ANN[tag]],path,ln,tag)
        # 意外な文字体系の混入。ハングルだけでなくキリル文字なども実際に混ざったことがある
        for ch in "".join(f):
            o=ord(ch)
            if (0xAC00<=o<=0xD7A3 or 0x1100<=o<=0x11FF          # ハングル
                or 0x0400<=o<=0x04FF or 0x0500<=o<=0x052F        # キリル
                or 0x0370<=o<=0x03FF                             # ギリシャ
                or 0x0590<=o<=0x06FF or 0x0900<=o<=0x097F         # ヘブライ・アラビア・デーヴァナーガリー
                or 0x0E00<=o<=0x0E7F):                            # タイ
                print(f"!! {path}:{ln} 想定外の文字「{ch}」(U+{o:04X})"); bad+=1
        if not f[1].strip():
            print(f"!! {path}:{ln} 中文が空"); bad+=1
    print(f"{path}: {n} 件 [{tag}]")

# 旧形式との重複も見る（文法は句型、会話は本文）
old={}
for p in sorted(glob.glob("g?.js"))+sorted(glob.glob("s?.js")):
    push = "G" if p.startswith("g") else "S"
    for ln,l in enumerate(open(p,encoding="utf-8"),1):
        m=re.match(r'^'+push+r'\.push\(\["([^"]+)"',l)
        if m: old[m.group(1)]=f"{p}:{ln}"
for k,v in keys.items():
    if k in old: print(f"!! 旧ファイルと重複「{k}」: {old[k]} と {v}"); bad+=1
print(f"--- 新規 {total} 件 / 一意 {len(keys)} / 旧 {len(old)} / 問題 {bad}")
sys.exit(1 if bad else 0)
