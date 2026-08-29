import re
t=open('lv.js',encoding='utf-8').read()
body=t[t.index('{')+1:t.rindex('}')]
ok=True
for m in re.finditer(r'(\w+):((?:"[123]*"\s*\+?\s*)+),',body):
    k=m.group(1); s="".join(re.findall(r'"([123]*)"',m.group(2)))
    n=sum(1 for l in open(k+'.js',encoding='utf-8') if re.match(r'^[VGS]\.push',l))
    flag='OK' if len(s)==n else '<<< MISMATCH'
    if flag!='OK': ok=False
    print(f"{k}: levels {len(s)} / items {n} {flag}  [N3-:{s.count('3')} N2:{s.count('2')} N1:{s.count('1')}]")
print("ALL OK" if ok else "FIX NEEDED")
