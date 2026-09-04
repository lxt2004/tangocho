# 注音の打ち間違いを既存 3041 語の読みと突き合わせて探す。
# 辞書は持たないので「語彙に同じ表記があるのに読みが違う」ものだけ挙げる。
import re,sys,glob,subprocess,json
BASE=r'[々ヶ一-鿿]'
# 既存語彙の 表記->読み を data.js から取る
open("/tmp/_rc.js","w",encoding="utf-8").write(
  'const fs=require("fs");'
  'const {VOCAB}=new Function(fs.readFileSync("data.js","utf8")+"; return {VOCAB};")();'
  'const m={}; VOCAB.forEach(v=>{ (m[v.w]=m[v.w]||[]).push(v.r) });'
  'console.log(JSON.stringify(m));')
VOC=json.loads(subprocess.run(["node","/tmp/_rc.js"],capture_output=True,text=True).stdout)
# 既存の注音データから 漢字->読み を集める（例文での実績なので文脈つきで信頼できる）
ann_known={}
known={}
for p in glob.glob("f*.js")+glob.glob("w*.js"):
    for m in re.finditer('('+BASE+r'+)[（(]([^）)]+)[）)]',open(p,encoding="utf-8").read()):
        ann_known.setdefault(m.group(1),set()).add(m.group(2))
known={k:set(v) for k,v in ann_known.items()}
for w,rs in VOC.items():
    known.setdefault(w,set()).update(rs)

# 注音が入るフィールドだけを見る（中文や接続の欄に漢字＋中国語括弧があると誤検知する）
FIELD={"GW":2,"SW":0}
def annfield(line):
    tag = line.split(".push")[0]
    if tag not in FIELD: return None
    f=re.findall(r'"((?:[^"\\]|\\.)*)"',line)
    return f[FIELD[tag]] if len(f)>FIELD[tag] else None

# 熟語の後ろにつく音読み。1 文字なので既存の実績と食い違うが、これで正しい
OK={("書","しょ"),("者","しゃ"),("分","ふん"),("人","にん"),("月","げつ"),("間","かん"),
    ("日","にち"),("年","ねん"),("件","けん"),("名","めい"),("中","ちゅう"),("中","じゅう"),
    ("率","りつ"),("量","りょう"),("回","かい"),("目","め"),("先","せん"),("元","もと"),
    ("的","てき"),("外","がい"),("中","なか"),("来","く"),("不足","ぶそく"),("性","せい"),
    ("側","がわ"),("上","じょう"),("下","した"),("方","かた"),("方","ほう"),("時","じ"),
    ("分","ぶん"),("数","すう"),("化","か"),("感","かん"),("差","さ"),("値","ち"),("版","ばん"),("用","よう"),("先","さき"),("件","くだん"),("内","ない"),("証","しょう"),("次","じ"),("系","けい"),("策","さく"),("度","ど"),("的","まと"),("休","きゅう"),("費","ひ"),("力","りょく"),("強","づよ"),("地","ち"),("感","かん"),("者","もの"),("会","かい"),("料","りょう"),("面","めん"),("分","ぷん"),("点","てん"),("言","ごと"),("主","しゅ"),("限","げん"),("権","けん"),("時","とき"),("鍵","かぎ"),("会社","がいしゃ"),("辛","から"),("上","あ"),("下","さ"),("応","こた"),("活","い")}
bad=0;checked=0
for path in sys.argv[1:]:
    for ln,l in enumerate(open(path,encoding="utf-8"),1):
        ann=annfield(l)
        if not ann: continue
        for m in re.finditer('('+BASE+r'+)[（(]([^）)]+)[）)]',ann):
            k,r=m.group(1),m.group(2)
            # 1 文字の漢字は音読み・訓読みが多いので、例文での実績だけと比べる
            ref = ann_known.get(k) if len(k)==1 else known.get(k)
            if not ref: continue
            checked+=1
            if r not in ref:
                if (k,r) in OK: continue
                # 送り仮名で読みが変わる語は誤検知しやすいので、前方一致は許す
                if any(x.startswith(r) or r.startswith(x) for x in ref): continue
                print(f"?? {path}:{ln} 「{k}」を({r})と書いたが、既存は({'/'.join(sorted(ref))})")
                bad+=1
print(f"--- 照合 {checked} 箇所 / 疑い {bad}")
