# 単語帳（2つのアプリ）

| アプリ | URL | 中身 |
|---|---|---|
| 藍の単語帳（日本語 / JLPT） | `/tangocho/` | 語彙 3041・文法 164・会話 114 |
| 英単語ノート（高校入試 英語） | `/tangocho/en/` | 語彙 690・熟語 160・例文 70 |

単一ページアプリ。全例文にふりがな、三段階のレベル分け、間隔反復（SRS）、
音声読み上げ、小試験、しおり、毎日のノルマ・連続日数・バッジを備える。

## 構成

```
/                     ← GitHub Pages の公開ルート（日本語版）
  index.html          ビルド成果物
  sw.js  manifest  icons
  en/                 英語版（同じ構成）
  src/jp/             日本語版のソース
  src/en/             英語版のソース
```

`src/` 以下がソースの正本。ルートの `index.html` などはそこからビルドした成果物で、
`src/*/build.sh` を実行すれば必ず再生成できる。

## ビルド

```bash
cd src/jp && ./build.sh     # → /index.html
cd src/en && ./build.sh     # → /en/index.html
```

## データを増やすとき

- 日本語版：`src/jp/` の `wNN.js`（自己完結形式）に追記 → `python3 wcheck.py w*.js`
- 英語版：`src/en/` の `eNN.js` / `pNN.js` / `s01.js` に追記 → `python3 wcheck.py e0*.js p0*.js s01.js`
- 検査は 字段数・レベル・ふりがな網羅・括弧の衝突・全体重複 を見る。**0 件になるまで直す**
- 文法・熟語・例文の通し番号はユーザーのしおりが指すので、**追記は末尾に限る**

注意点：
- ふりがなは `漢字(かんじ)` 記法。注釈には全角括弧ではなく `〔〕` を使う
- 学習記録は localStorage。オリジン単位なので保存キーを分けてある
  （`ai-no-tangocho/v1` / `eitango-note/v1`）

## 公開設定

Settings → Pages → `Deploy from a branch` / `main` / `/ (root)`
