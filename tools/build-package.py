"""配布物（AviUtl2 のパッケージファイル .au2pkg.zip）を dist/ に作る。

使い方:
    uv run python tools/build-package.py

zip の中身（AviUtl2 のパッケージファイルの形。プレビューへのドラッグ＆ドロップで入れられる）:
    package.ini                  パッケージの識別子・名前・情報
    package.txt                  入れるときに表示する文
    Script/連番まとめ/*.obj2, *.anm2  script/ のスクリプト
    Script/連番まとめ/LICENSE.txt     ライセンス

AviUtl2 Catalog は、同じ zip を install.json の手順で入れる（Script/連番まとめ を {scriptsDir} の下へ写す）。
"""

import sys
import tomllib
import zipfile
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parent.parent
SCRIPT_DIR = REPOSITORY / "script"
DIST_DIR = REPOSITORY / "dist"

# パッケージの識別子（ファイル名に使える文字だけ）と、Script フォルダの下に置くフォルダの名前。
PACKAGE_ID = "renban-matome"
PACKAGE_NAME = "連番まとめ"
SCRIPT_FOLDER = "連番まとめ"
AUTHOR = "osakanamaki"
NICONI_COMMONS_ID = "nc516522"
REPOSITORY_URL = "https://github.com/osakanamaki/renban-matome"

# 配布するスクリプトの拡張子。
SCRIPT_EXTENSIONS = (".obj2", ".anm2")


def read_version() -> str:
    """pyproject.toml の版を返す。"""
    with (REPOSITORY / "pyproject.toml").open("rb") as file:
        return tomllib.load(file)["project"]["version"]


def to_crlf(text: str) -> bytes:
    """改行を CRLF にそろえて UTF-8 にする。

    取り出した環境（Windows の CRLF、GitHub Actions の Linux の LF）で中身が変わらないようにする。
    カタログに登録するハッシュ値が、どこで作っても同じになる。
    """
    return text.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8")


def package_ini(version: str) -> str:
    return (
        "[package]\n"
        f"id={PACKAGE_ID}\n"
        f"name={PACKAGE_NAME}\n"
        f"information={PACKAGE_NAME} v{version} by {AUTHOR}\n"
        # アンインストールのとき、Script/連番まとめ の中のファイルを全て消す。
        "uninstallSubFolderFile=1\n"
    )


def package_txt(version: str) -> str:
    return (
        f"{PACKAGE_NAME} v{version}\n"
        "\n"
        "複数の連番画像を1つのオブジェクトにまとめ、値で一括して切り替えるスクリプトです。\n"
        "「オブジェクト追加」→「連番まとめ」→「連番まとめ（値）」から使い始めます。\n"
        "\n"
        f"使い方: {REPOSITORY_URL}/wiki\n"
        "\n"
        f"ニコニ・コモンズの作品 ID は {NICONI_COMMONS_ID} です。\n"
        "動画などで使ったときは、ニコニ・コモンズで親作品に登録していただけるとうれしいです。\n"
    )


def script_files() -> list[Path]:
    files = [path for path in sorted(SCRIPT_DIR.iterdir()) if path.suffix in SCRIPT_EXTENSIONS]
    if not files:
        raise SystemExit(f"配布するスクリプトがありません: {SCRIPT_DIR}")
    return files


def build(version: str) -> Path:
    DIST_DIR.mkdir(exist_ok=True)
    archive_path = DIST_DIR / f"{PACKAGE_ID}-v{version}.au2pkg.zip"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("package.ini", to_crlf(package_ini(version)))
        archive.writestr("package.txt", to_crlf(package_txt(version)))
        for path in script_files():
            archive.writestr(f"Script/{SCRIPT_FOLDER}/{path.name}", to_crlf(path.read_text(encoding="utf-8")))
        license_text = (REPOSITORY / "LICENSE").read_text(encoding="utf-8")
        archive.writestr(f"Script/{SCRIPT_FOLDER}/LICENSE.txt", to_crlf(license_text))
    return archive_path


def main() -> int:
    archive_path = build(read_version())
    print(archive_path.relative_to(REPOSITORY).as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main())
