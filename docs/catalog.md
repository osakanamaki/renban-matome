# 配布と AviUtl2 Catalog への掲載

## 配布物

`tools/build-package.py`（`task package`）が、`dist/renban-matome-vX.Y.Z.au2pkg.zip` を作ります。
AviUtl2 のパッケージファイルの形で、プレビューへのドラッグ＆ドロップで入れられます（AviUtl2 の SDK の README「パッケージファイル」）。

```
renban-matome-vX.Y.Z.au2pkg.zip
├── package.ini            識別子 renban-matome、名前、情報（版）。uninstallSubFolderFile=1
├── package.txt            入れるときに表示する文（使い方の場所、ニコニ・コモンズの作品 ID）
└── Script/
    └── 連番まとめ/
        ├── *.obj2, *.anm2  script/ のスクリプト
        └── LICENSE.txt
```

- スクリプトと LICENSE.txt は、改行を CRLF にそろえて入れます。どこで作っても中身（ハッシュ値）が同じになるようにするためです。
- 版は `pyproject.toml` の `version` を使います。各スクリプトの `--information` の版と、タグ（`v` ＋版）をそろえます（`tools/check-release.py` で確かめる）。

AviUtl2 Catalog は、同じ zip を [`install.json`](../install.json) の手順で入れます（`Script/連番まとめ` を `{scriptsDir}/連番まとめ` へ写す）。

## 公開の手順

1. 手元で `task release-check` を通す（版と個人のパス、`script/` での試験、配布物を置いた試験）。
2. `pyproject.toml` と各スクリプトの `--information` の版を上げたコミットを `main` に入れる。
3. タグ `vX.Y.Z` を付けて push する。GitHub Actions（`.github/workflows/release.yml`）が、
   版と個人のパスを確かめ、配布物を作り、Releases に載せる。本文に、置かれるファイルの XXH3_128 が書かれる。

## カタログに登録する内容

カタログアプリの登録フォームから申請します。項目と、入れる値は次のとおりです。

| 項目 | 値 |
|---|---|
| ID | `osakanamaki.renban-matome` |
| パッケージ名 | 連番まとめ |
| 作者名 | osakanamaki |
| パッケージのサイト | https://github.com/osakanamaki/renban-matome |
| ニコニ・コモンズID | `nc516522` |
| パッケージの分類 | メインパッケージ |
| 種類 | スクリプト |
| 概要（35 文字以内） | 複数の連番画像を1つにまとめ、値で一括して切り替える |
| 詳細（外部 MD リンク） | https://raw.githubusercontent.com/osakanamaki/renban-matome/main/README.md |
| ライセンス | MIT License |
| サムネイル | `docs/images/thumbnail.webp`（https://raw.githubusercontent.com/osakanamaki/renban-matome/main/docs/images/thumbnail.webp） |
| インストーラーの取得元 | GitHub Release：owner `osakanamaki`、repo `renban-matome`、正規表現 `^renban-matome-v\d+\.\d+\.\d+\.au2pkg\.zip$` |
| インストール手順 | `download` → `extract` → `copy`（from `{tmp}/Script/連番まとめ`、to `{scriptsDir}/連番まとめ`） |
| アンインストール手順 | `delete`（path `{scriptsDir}/連番まとめ`） |
| バージョンのファイル | Releases の本文の XXH3_128 を写す |

## 動くサムネイル

`tools/make-thumbnail.py`（`task thumbnail`）が、AviUtl2 で描画して `docs/images/thumbnail.webp`（206px 四方、3 秒）を作ります。
デモのプロジェクトは、同梱のサンプル画像（`samples/`）だけでスクリプトの中に組み立てます（実素材は使わない。要件 CM-04）。
スロットの見た目や項目を変えたときに作り直します。
