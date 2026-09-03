#!/bin/bash
set -e
cd "$(dirname "$0")"

# 旧形式：数据 + 同序注音文件 + 级别字符串
oldv(){ # $1=data $2=furigana $3=lvkey $4=SPEC
  echo "_L=LV.$3;_i=0;"; cat "$2"
  awk -v SPEC="$4" -f tag.awk "$1" | grep -v '^//'
}
# 新形式：自包含（例文已注音，级别在第6字段）
wblk(){ local c="$1"; shift
  local any=0; for f in "$@"; do [ -f "$f" ] && any=1; done
  [ $any -eq 1 ] || return 0
  echo "_c=\"$c\";"
  for f in "$@"; do [ -f "$f" ] && grep '^W.push' "$f"; done; }

{
echo 'const VOCAB=[],GRAM=[],SPK=[];'
echo 'let _c="",_L="",_i=0,F=[];'
echo 'const P=s=>s.replace(/[（(][^）)]*[）)]/g,"");'
printf 'const '; cat lv.js
echo 'const V={push:a=>VOCAB.push({_t:"V",w:a[0],r:a[1],c:a[2],ex:a[3],exc:a[4],f:F[_i],lv:+_L[_i++],cat:_c})};'
echo 'const W={push:a=>VOCAB.push({_t:"V",w:a[0],r:a[1],c:a[2],ex:P(a[3]),exc:a[4],f:a[3],lv:a[5],cat:_c})};'
echo 'const G={push:a=>GRAM.push({_t:"G",p:a[0],c:a[1],ex:a[2],exc:a[3],note:a[4],f:F[_i],lv:+_L[_i++],cat:_c})};'
echo 'const S={push:a=>SPK.push({_t:"S",jp:a[0],zh:a[1],note:a[2]||"",f:F[_i],lv:+_L[_i++],cat:_c})};'

# ---- 動詞（最优先）----
wblk "動詞・自他ペア"   w01.js w02.js
wblk "動詞・複合動詞"   w03.js w04.js w05.js
oldv d3.js f3.js d3 '116:動詞・和語'
wblk "動詞・和語"       w06.js w07.js w08.js
wblk "動詞・上級"       w09.js
wblk "動詞・する"       w10.js
# ---- 形容詞・副詞 ----
oldv d4.js f4.js d4 '41:形容詞;65:副詞・接続;8:オノマトペ'
wblk "形容詞"           w11.js w12.js
wblk "副詞・接続"       w13.js w25.js
wblk "オノマトペ"       w14.js
# ---- 名詞 ----
oldv d5.js f5.js d5 '35:名詞・抽象;52:名詞・社会経済'
wblk "名詞・抽象"       w15.js w16.js
wblk "名詞・社会経済"   w17.js w18.js
wblk "名詞・人と心理"   w19.js
wblk "名詞・生活と身体" w20.js
# ---- 実務 ----
oldv d1.js f1.js d1 '103:職場・ビジネス'
wblk "職場・ビジネス"   w21.js
oldv d2.js f2.js d2 '101:IT・開発'
wblk "IT・開発"         w22.js
# ---- その他 ----
oldv d6.js f6.js d6 '25:カタカナ語;33:慣用句・四字熟語'
wblk "カタカナ語"       w23.js
wblk "慣用句・四字熟語" w24.js

# ---- 文法・会話 ----
echo '_L=LV.g1;_i=0;'; cat fg1.js
awk -v SPEC='14:原因・理由;16:逆接・譲歩;5:対比・対照;10:条件・仮定' -f tag.awk g1.js | grep -v '^//'
echo '_L=LV.g2;_i=0;'; cat fg2.js
awk -v SPEC='17:時・場面;10:変化・推移;13:程度・限定;14:判断・必然・傾向' -f tag.awk g2.js
echo '_L=LV.g3;_i=0;'; cat fg3.js
awk -v SPEC='6:付加・並列;16:基準・関係;4:意志・決定;9:依頼・敬語;10:義務・評価;13:伝聞・推量;7:N1 入門' -f tag.awk g3.js
echo '_L=LV.s1;_i=0;'; cat fs1.js
awk -v SPEC='10:朝会・進捗報告;15:確認・すり合わせ;9:依頼・お願い;11:断る・反対する;10:謝罪・障害報告' -f tag.awk s1.js | grep -v '^//'
echo '_L=LV.s2;_i=0;'; cat fs2.js
awk -v SPEC='15:会議・発表;11:電話・メール;14:案件面談・自己紹介;19:雑談・関係づくり' -f tag.awk s2.js
} > data.js
awk '/__DATA__/{ while((getline l < "data.js")>0) print l; next } {print}' part2.html > body.html
cat part1.html body.html > app.html
{ printf '%s' '<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="apple-mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-title" content="藍の単語帳"><meta name="theme-color" content="#EEF0F3">'
  cat part1.html; printf '%s' '</head><body>'; cat body.html; printf '%s' '</body></html>'
} > jlpt-tangocho.html
# ---- GitHub Pages 用 (PWA: manifest + service worker) ----
OUT=../..
{ printf '%s' '<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="apple-mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-title" content="藍の単語帳"><meta name="theme-color" content="#1B3A66"><link rel="manifest" href="./manifest.webmanifest"><link rel="apple-touch-icon" href="./apple-touch-icon.png"><link rel="icon" href="./icon-192.png">'
  cat part1.html; printf '%s' '</head><body>'; cat body.html
  printf '%s' '<script>if("serviceWorker" in navigator)addEventListener("load",()=>{var had=!!navigator.serviceWorker.controller;navigator.serviceWorker.register("./sw.js").catch(function(){});navigator.serviceWorker.addEventListener("controllerchange",function(){if(had&&window.__newVer)window.__newVer()})});</script></body></html>'
} > $OUT/index.html

echo "built: $(grep -c '^[VW]\.push' data.js) vocab / $(grep -c '^G\.push' data.js) grammar / $(grep -c '^S\.push' data.js) speak"
