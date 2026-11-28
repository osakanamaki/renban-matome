"""AviUtl2 Catalog に載せる、動くサムネイル（docs/images/thumbnail.webp）を作る。

使い方:
    uv run python tools/make-thumbnail.py

AviUtl2 を起動して描画する（環境変数 AVIUTL2_APP、無ければ C:\\Program Files\\AviUtl2 の本体を複製して使う）。
デモのプロジェクトは、同梱のサンプル画像（samples/）だけで、このスクリプトの中で組み立てる（要件 CM-04）。

デモの内容（3 秒・30fps）:
    猫のアニメーション（連番スロット、値2でループ）、HP バー（連番スロット（ゲージ））、
    HP の数値（テキスト数値スロット）を、1つの土台で描く。値1（HP）は 100 から 0 へ減る。
"""

import os
import sys
from pathlib import Path

from aviutl2_pyrrhulina import Effect, Project, TimelineObject, create_environment, make_thumbnail

REPOSITORY = Path(__file__).resolve().parent.parent
SAMPLES = REPOSITORY / "samples"
OUTPUT = REPOSITORY / "docs" / "images" / "thumbnail.webp"
WORK_DIR = REPOSITORY / ".aviutl2-pyrrhulina"
DEFAULT_APP_DIR = Path(r"C:\Program Files\AviUtl2")

SECONDS = 3
FPS = 30
LAST_FRAME = SECONDS * FPS - 1
# 背景（カタログの明るい画面でも、白い文字が見えるように暗い色にする）。
BACKGROUND = (32, 40, 58)


def demo_project() -> Project:
    # 縮小したときに細い線がつぶれないよう、大きめの正方形で作る。
    base = Effect(
        "連番まとめ（値）",
        {
            # HP は 100 から 0 へ。猫のアニメーション（150 枚）は、3 秒で 1 周させる。
            "値1": "100.00,0.00,直線移動,0",
            "値2": "0.00,149.00,直線移動,0",
            "案内の表示": "表示しない",
        },
    )
    animation = Effect(
        "連番スロット",
        {
            "画像": SAMPLES / "animation" / "animation_000.png",
            "従う値": "値2",
            "範囲外の扱い": "ループ",
            "Y": "-110.0",
            "拡大率": "150.00",
        },
    )
    gauge = Effect(
        "連番スロット（ゲージ）",
        {
            "画像": SAMPLES / "bar" / "bar_000.png",
            "従う値": "値1",
            "ゲージの上限": "100",
            "Y": "150.0",
            "拡大率": "130.00",
        },
    )
    number = Effect(
        "テキスト数値スロット",
        {
            "テキスト": "HP {値1}",
            "サイズ": "72",
            "文字装飾": "縁取り文字",
            "Y": "240.0",
        },
    )
    host = TimelineObject(0, 0, LAST_FRAME, [base, animation, gauge, number, Effect("標準描画")])
    return Project(640, 640, [host], rate=FPS)


def main() -> int:
    app_dir = Path(os.environ.get("AVIUTL2_APP", DEFAULT_APP_DIR))
    environment = create_environment(WORK_DIR / "app", app_dir, {"renban-matome-dev": REPOSITORY / "script"})
    make_thumbnail(environment, demo_project(), OUTPUT, seconds=SECONDS, fps=FPS, background=BACKGROUND)
    print(OUTPUT.relative_to(REPOSITORY).as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main())
