# 連番まとめ（AviUtl2 スクリプト）

[![最新リリース](https://img.shields.io/github/v/release/osakanamaki/renban-matome?label=release)](https://github.com/osakanamaki/renban-matome/releases/latest)
[![検証済みのAviUtl2](https://img.shields.io/badge/AviUtl2-2.1.17-blue)](https://spring-fragrance.mints.ne.jp/aviutl/)
[![🐠ピルリナでテスト](https://img.shields.io/badge/tested%20with-%F0%9F%90%A0%E3%83%94%E3%83%AB%E3%83%AA%E3%83%8A-blue)](https://github.com/osakanamaki/aviutl2-pyrrhulina)

AviUtl2 用のスクリプトです。

- **連番まとめ**: 複数の連番画像を1つのオブジェクトにまとめ、値で一括して切り替えます。

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/images/usage-dark.svg">
  <img src="docs/images/usage-light.svg" alt="使い方の図: 1. タイムラインの「オブジェクト追加」→「連番まとめ」→「連番まとめ（値）」を置いて土台にする。2. 土台のオブジェクト設定の [+] →「連番まとめ」から、連番スロットやテキスト数値スロットなどを使いたい数だけ付ける。3. 土台の値1〜値8を動かすと、その値に従うスロットが一緒に切り替わる。" width="880">
</picture>

## 動作環境

- AviUtl ExEdit2 v2.1.17 以降

## 導入

`script/` フォルダのファイルを、AviUtl2 の Script フォルダ（例：`C:\ProgramData\aviutl2\Script`）に置きます。
くわしくは Wiki の [導入](https://github.com/osakanamaki/renban-matome/wiki/導入) を参照してください。

## 最初の一歩

1. 「オブジェクト追加」→「連番まとめ」→「連番まとめ（値）」を置きます。
2. オブジェクト設定の [+] →「連番まとめ」から「連番スロット」を追加し、「画像」に連番の画像（例：`hp_000.png`）を指定します。
3. 土台の「値1」を動かすと、画像が切り替わります。

## 使い方

土台とスロットの項目、計算式の書き方、作例、困ったときは [Wiki](https://github.com/osakanamaki/renban-matome/wiki) にまとめています。

| 部品 | 役割 |
|---|---|
| [連番まとめ（値）](https://github.com/osakanamaki/renban-matome/wiki/連番まとめ（値）) | 土台。「値」を8つ持ち、付いたスロットをまとめて描く |
| [連番スロット](https://github.com/osakanamaki/renban-matome/wiki/連番スロット) | 値の番号の連番画像を表示する |
| [連番スロット（ゲージ）](https://github.com/osakanamaki/renban-matome/wiki/連番スロット（ゲージ）) | 値を「ゲージの上限」に対する割合で、HP バーなどの連番画像に割り振る |
| [連番スロット（計算式）](https://github.com/osakanamaki/renban-matome/wiki/連番スロット（計算式）) | 表示する番号を計算式で決める |
| [テキスト数値スロット](https://github.com/osakanamaki/renban-matome/wiki/テキスト数値スロット) | 値を文字で表示する |
| [連番スロット（複製並べ）](https://github.com/osakanamaki/renban-matome/wiki/連番スロット（複製並べ）) | 1つの画像を、値で決まる数だけ並べる |

## 開発

開発環境の作り方は [docs/development.md](docs/development.md)、要件は [requirements.md](requirements.md) を参照してください。

## ライセンス

[MIT License](LICENSE)
