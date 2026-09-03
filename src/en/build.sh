#!/bin/bash
set -e
cd "$(dirname "$0")"
blk(){ local c="$1"; shift
  local any=0; for f in "$@"; do [ -f "$f" ] && any=1; done
  [ $any -eq 1 ] || return 0
  echo "_c=\"$c\";"
  for f in "$@"; do [ -f "$f" ] && grep "^[EPS]\.push" "$f" || true; done; }
{
echo 'const VOCAB=[],GRAM=[],SPK=[];'
echo 'let _c="";'
echo 'const P0=s=>s.replace(/[（(][^）)]*[）)]/g,"");'
echo 'const E={push:a=>VOCAB.push({_t:"V",w:a[0],c:a[1],r:a[2],ex:a[3],exc:a[4],lv:a[5],cat:_c})};'
echo 'const P={push:a=>GRAM.push({_t:"G",p:a[0],c:a[1],note:a[2],ex:a[3],exc:a[4],lv:a[5],cat:_c})};'
echo 'const S={push:a=>SPK.push({_t:"S",jp:a[0],zh:a[1],exc:a[2],lv:a[3],cat:_c})};'
blk "動詞・基本"        e01.js
blk "不規則動詞"        e02.js
blk "名詞・学校と日常"   e03.js
blk "名詞・社会とテーマ" e04.js
blk "形容詞"           e05.js
blk "副詞・つなぎ語"     e06.js
blk "入試発展"          e07.js e08.js
blk "熟語・連語"        p01.js p02.js
echo '_c="教室で使う英語";'; sed -n '1,12p' s01.js
echo '_c="道案内・買い物";'; sed -n '13,22p' s01.js
echo '_c="電話・依頼・お礼";'; sed -n '23,32p' s01.js
echo '_c="自己紹介・スピーチ";'; sed -n '33,45p' s01.js
echo '_c="英作文で使える型";'; sed -n '46,58p' s01.js
echo '_c="長文の頻出構文";'; sed -n '59,100p' s01.js
} > data.js
awk '/__DATA__/{ while((getline l < "data.js")>0) print l; next } {print}' part2.html > body.html
cat part1.html body.html > app.html
{ printf '%s' '<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="apple-mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-title" content="英単語ノート"><meta name="theme-color" content="#0F7A6B">'
  cat part1.html; printf '%s' '</head><body>'; cat body.html; printf '%s' '</body></html>'
} > eitango.html
# ---- GitHub Pages 用（/tangocho/en/ に配置）----
DIST=../../en
if [ -d "$DIST" ]; then
{ printf '%s' '<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="apple-mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-title" content="英単語ノート"><meta name="theme-color" content="#0F7A6B"><link rel="manifest" href="./manifest.webmanifest"><link rel="apple-touch-icon" href="./apple-touch-icon.png"><link rel="icon" href="./icon-192.png">'
  cat part1.html; printf '%s' '</head><body>'; cat body.html
  printf '%s' '<script>if("serviceWorker" in navigator)addEventListener("load",()=>{var had=!!navigator.serviceWorker.controller;navigator.serviceWorker.register("./sw.js").catch(function(){});navigator.serviceWorker.addEventListener("controllerchange",function(){if(had&&window.__newVer)window.__newVer()})});</script></body></html>'
} > $DIST/index.html
echo "dist: $DIST/index.html"
fi

echo "built: $(grep -c '^E\.push' data.js) words / $(grep -c '^P\.push' data.js) phrases / $(grep -c '^S\.push' data.js) sentences"
