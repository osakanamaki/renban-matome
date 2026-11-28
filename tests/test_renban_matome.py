"""連番まとめ（土台「連番まとめ（値）」＋スロット）を、要件定義書 1.6.14 の受け入れ基準で確かめる。

証跡のパスが Windows の上限（260 文字）を超えると描画できないため、テスト名と id は短くする。
"""

import shutil
from collections.abc import Sequence
from pathlib import Path

import pytest
from aviutl2_pyrrhulina import Effect, Project, TimelineObject
from aviutl2_pyrrhulina.pytest_plugin import AviUtl2
from PIL import Image, ImageChops

BASE = "連番まとめ（値）"
SLOT = "連番スロット"
FORMULA_SLOT = "連番スロット（計算式）"
NUMBER_SLOT = "テキスト数値スロット"
REPEAT_SLOT = "連番スロット（複製並べ）"
GAUGE_SLOT = "連番スロット（ゲージ）"
STILL_SLOT = "静止画スロット"
# 土台が対応していない種類のスロット（案内の確認用）。
UNKNOWN_SLOT = "_試験_未知のスロット"
# 土台が使う kernel32 の関数を、違う型で先に ffi で宣言するカスタムオブジェクト（何も描かない）。
DECLARE_FFI = "_試験_ffiの宣言"

SAMPLES = Path(__file__).parent.parent / "samples"
BAR = SAMPLES / "bar" / "bar_000.png"
NUMBER = SAMPLES / "number" / "number_000.png"
# bar・number は、どちらも 000〜010 の 11 枚。
IMAGE_COUNT = 11
# 拡張子の直前に番号が無い、連番として扱えないファイル名（案内の確認用。ファイルは無くてよい）。
NOT_SEQUENTIAL = SAMPLES / "bar" / "bar.png"
# 連番の規則には合うが、存在しない画像（案内の確認用）。
MISSING = SAMPLES / "bar" / "bar_050.png"

# ダミー画像の色。bar は緑（10 段階で長さが変わる）、number は白。
# bar にも白い枠線（876 画素）があるので、数字は bar と重ならない位置で確かめる。
BAR_GREEN = (50, 205, 50)
NUMBER_WHITE = (255, 255, 255)
# 数字の画像の大きさ。画面の高さの中央に置かれる。
NUMBER_WIDTH, NUMBER_HEIGHT = 160, 120


def base(*values: int | str, guide: str = "選択中だけ", name: str = BASE) -> Effect:
    """土台。values は値1から順（省略した値は 0）。文字列なら中間点つきのトラックバーの書き方。"""
    params: dict[str, object] = {"案内の表示": guide}
    for value_number, value in enumerate(values, start=1):
        params[f"値{value_number}"] = str(value)
    return Effect(name, params)


def slot(
    image: Path | str = "",
    *,
    source: int = 1,
    outside: str = "表示しない",
    count: int = 0,
    x: float = 0,
    y: float = 0,
    scale: float = 100,
    name: str = SLOT,
) -> Effect:
    """連番スロット。outside は範囲外の扱い、count は枚数（0 は自動）。

    x・y は土台からのずれ、scale は拡大率（%）。
    """
    params: dict[str, object] = {
        "画像": image,
        "従う値": f"値{source}",
        "範囲外の扱い": outside,
        "枚数": str(count),
        "X": f"{x:.1f}",
        "Y": f"{y:.1f}",
        "拡大率": f"{scale:.2f}",
    }
    return Effect(name, params)


def formula_slot(image: Path | str, formula: str, *, outside: str = "表示しない", x: float = 0) -> Effect:
    """連番スロット（計算式）。outside は範囲外の扱い。"""
    params: dict[str, object] = {
        "画像": image,
        "計算式": formula,
        "範囲外の扱い": outside,
        "X": f"{x:.1f}",
    }
    return Effect(FORMULA_SLOT, params)


def gauge_slot(image: Path | str = "", *, gauge_max: int = 100, count: int = 0, y: float = 0) -> Effect:
    """連番スロット（ゲージ）。従う値は値1。gauge_max はゲージの上限、count は枚数（0 は自動）。"""
    params: dict[str, object] = {
        "画像": image,
        "従う値": "値1",
        "ゲージの上限": str(gauge_max),
        "枚数": str(count),
        "Y": f"{y:.1f}",
    }
    return Effect(GAUGE_SLOT, params)


def still_slot(image: Path | str = "", *, x: float = 0, y: float = 0, scale: float = 100) -> Effect:
    """静止画スロット。x・y は土台からのずれ、scale は拡大率（%）。"""
    params: dict[str, object] = {
        "画像": image,
        "X": f"{x:.1f}",
        "Y": f"{y:.1f}",
        "拡大率": f"{scale:.2f}",
    }
    return Effect(STILL_SLOT, params)


def number_slot(
    text: str,
    *,
    decimal: str = "四捨五入",
    digits: int = 0,
    text_color: str = "ffffff",
    decoration: str = "縁取り文字",
    x: float = 0,
) -> Effect:
    """テキスト数値スロット。decimal は小数の扱い、digits は桁数（0 は「しない」）。

    text_color は「テキスト」と同じ 16 進数の書き方。
    """
    params: dict[str, object] = {
        "テキスト": text,
        "小数の扱い": decimal,
        "桁数": str(digits),
        "文字色": text_color,
        "文字装飾": decoration,
        "X": f"{x:.1f}",
    }
    return Effect(NUMBER_SLOT, params)


def repeat_slot(
    image: Path | str,
    *,
    image_value: int = 1,
    count_value: int = 2,
    wrap: int = 0,
    margin: float = 0,
    align: str = "左揃え",
    scale: float = 100,
) -> Effect:
    """連番スロット（複製並べ）。wrap は折り返しの数（0 は折り返さない）、margin は余白。"""
    params: dict[str, object] = {
        "画像": image,
        "画像を選ぶ値": f"値{image_value}",
        "数を決める値": f"値{count_value}",
        "折り返しの数": str(wrap),
        "余白": f"{margin:.1f}",
        "並べ方": align,
        "拡大率": f"{scale:.2f}",
    }
    return Effect(REPEAT_SLOT, params)


def project(
    base_effect: Effect,
    *effects: Effect,
    width: int = 640,
    end: int = 9,
    midpoints: tuple[int, ...] = (),
) -> Project:
    # 土台だけを置く。ダミーの図形などは用意しない（受け入れ基準の1つ目）。
    host = TimelineObject(0, 0, end, [base_effect, *effects, Effect("標準描画")], midpoints=midpoints)
    return Project(width, 480, [host])


def cases_project(cases: Sequence[Sequence[Effect]], *, width: int = 640) -> Project:
    """ケースごとに土台を1フレームずつずらして置いたプロジェクト。ケース i の土台はフレーム i だけにある。

    cases の各要素は、1つの土台に付ける効果（土台、スロット…）。標準描画は自動で足す。
    """
    objects = [
        TimelineObject(0, frame, frame, [*effects, Effect("標準描画")]) for frame, effects in enumerate(cases)
    ]
    return Project(width, 480, objects)


def render_cases(
    aviutl2: AviUtl2, cases: Sequence[Sequence[Effect]], *, width: int = 640
) -> list[Image.Image]:
    """cases を cases_project() で並べ、AviUtl2 を1回だけ起動してまとめて描く。返す画像の i 番目がケース i。

    AviUtl2 の起動が試験時間のほとんどを占めるため、1フレームで確かめられるケースはまとめて描く。

    同じ起動の中で描くので、土台が使い回す状態（数えた枚数など）はケースをまたいで残る。
    初めて描くときの動きを確かめたいケースは、ほかのケースと違う画像を使う。
    """
    frames = list(range(len(cases)))
    result = aviutl2.render(cases_project(cases, width=width), frames)
    return [result.images[frame] for frame in frames]


def color_mask(image: Image.Image, color: tuple[int, int, int]) -> Image.Image:
    rgba = image.convert("RGBA")
    pixels = [255 if a == 255 and (r, g, b) == color else 0 for r, g, b, a in rgba.get_flattened_data()]
    mask = Image.new("L", rgba.size)
    mask.putdata(pixels)
    return mask


def count_pixels(image: Image.Image, color: tuple[int, int, int]) -> int:
    return color_mask(image, color).histogram()[255]


def bar_pixels(number: int) -> int:
    """bar_00n の緑の画素数。"""
    return count_pixels(Image.open(SAMPLES / "bar" / f"bar_{number:03d}.png"), BAR_GREEN)


def assert_number_at(image: Image.Image, center_x: int, number: int) -> None:
    """画面の x=center_x を中心に、number_00n の白い画素がそのまま描かれている。"""
    left = center_x - NUMBER_WIDTH // 2
    top = (image.height - NUMBER_HEIGHT) // 2
    actual = image.crop((left, top, left + NUMBER_WIDTH, top + NUMBER_HEIGHT))
    expected = Image.open(SAMPLES / "number" / f"number_{number:03d}.png")
    difference = ImageChops.difference(color_mask(actual, NUMBER_WHITE), color_mask(expected, NUMBER_WHITE))
    assert difference.getbbox() is None, f"数字 {number} が x={center_x} に描かれていない"


# ---- 表示と切り替え ----


def test_shows_image_without_dummy_object(aviutl2: AviUtl2) -> None:
    """土台を置き、連番スロットを付けて画像を指定するだけで、ほかのオブジェクトを用意せずに画像が表示される。"""
    image = aviutl2.render(project(base(3), slot(BAR)), [0]).images[0]

    assert count_pixels(image, BAR_GREEN) == bar_pixels(3)


def test_slots_following_same_value_switch_together(aviutl2: AviUtl2) -> None:
    """同じ値に従う複数のスロットは、値を変えると表示が同時に切り替わる。"""
    effect = base("0.00,10.00,直線移動,0")

    # バーは中央 x=640、数字は X で 300 右の x=940 に置いて、別々に確かめる。
    result = aviutl2.render(project(effect, slot(BAR), slot(NUMBER, x=300), width=1280, end=10), [0, 5, 10])

    for frame in (0, 5, 10):
        assert count_pixels(result.images[frame], BAR_GREEN) == bar_pixels(frame), f"frame {frame}"
        assert_number_at(result.images[frame], 940, frame)


def test_slots_follow_only_their_own_value(aviutl2: AviUtl2) -> None:
    """値1と値2に従うスロットは、それぞれの値だけに従って切り替わる（中間点も各自の値のもの）。"""
    effect = base(3, "0.00,10.00,0.00,直線移動,0")

    # 数字（値1）は中央 x=640、バー（値2）は 300 右。
    result = aviutl2.render(
        project(
            effect,
            slot(NUMBER, source=1),
            slot(BAR, source=2, x=300),
            width=1280,
            end=10,
            midpoints=(5,),
        ),
        [0, 5, 10],
    )

    assert count_pixels(result.images[0], BAR_GREEN) == bar_pixels(0)
    assert count_pixels(result.images[5], BAR_GREEN) == bar_pixels(10)
    assert count_pixels(result.images[10], BAR_GREEN) == bar_pixels(0)
    for frame in (0, 5, 10):
        assert_number_at(result.images[frame], 640, 3)


def test_each_value_can_be_followed(aviutl2: AviUtl2) -> None:
    """RM-F03: 値1〜値8のどれにも従える。ほかの値には従わない。

    値1 はほかの試験で確かめているので、値2〜値8 を確かめる。従う値だけを 7、ほかを 0 にする。
    """
    sources = [2, 3, 4, 5, 6, 7, 8]
    cases = []
    for source in sources:
        values = [0] * 8
        values[source - 1] = 7
        cases.append((base(*values), slot(BAR, source=source)))

    images = render_cases(aviutl2, cases)

    actual = {
        f"値{source}": count_pixels(image, BAR_GREEN) for source, image in zip(sources, images, strict=True)
    }
    expected = {f"値{source}": bar_pixels(7) for source in sources}
    assert actual == expected


def test_selected_image_is_value_zero(aviutl2: AviUtl2) -> None:
    """RM-F11: 途中の画像を選ぶと、値 0 でその画像が表示され、値の分だけ後ろの画像になる。"""
    result = aviutl2.render(
        project(base("0.00,4.00,直線移動,0"), slot(SAMPLES / "bar" / "bar_003.png"), end=4), [0, 4]
    )

    assert count_pixels(result.images[0], BAR_GREEN) == bar_pixels(3)
    assert count_pixels(result.images[4], BAR_GREEN) == bar_pixels(7)


# ---- 範囲外の扱いと枚数 ----


def test_hide_out_of_range(aviutl2: AviUtl2) -> None:
    """RM-F14: 「表示しない」のとき、範囲外なら何も表示されず、スクリプトエラーも、ログのエラーも出ない。"""
    # (id, 値, 枚数（0 は自動）)
    cases = [("negative", -1, 0), ("beyond_count", IMAGE_COUNT, 0), ("beyond_given_count", 6, 6)]

    # ログにエラーがあれば、render() が失敗する（allow_log_errors を渡していない）。
    images = render_cases(
        aviutl2,
        [(base(value), slot(BAR, count=count), slot(NUMBER, count=count)) for _, value, count in cases],
    )

    drawn = [
        case_id for (case_id, _, _), image in zip(cases, images, strict=True) if image.getbbox() is not None
    ]
    assert drawn == [], "何も表示しないはずのケースで、何かが描かれた"


def test_loop(aviutl2: AviUtl2) -> None:
    """RM-F14: 「ループ」のとき、枚数以上は先頭に戻り、負の番号は後ろから数える。枚数は自動でも指定でもよい。

    土台の値は -1 までなので、-2 以下は連番スロット（計算式）のテストで確かめる。
    """
    # (id, 値, 枚数（0 は自動）, 表示される bar の番号)
    cases = [
        ("count", IMAGE_COUNT, 0, 0),
        ("count_plus_3", IMAGE_COUNT + 3, 0, 3),
        ("minus_1", -1, 0, 10),
        ("given_count", 6, 5, 1),
        ("given_minus_1", -1, 5, 4),
    ]

    images = render_cases(
        aviutl2, [(base(value), slot(BAR, outside="ループ", count=count)) for _, value, count, _ in cases]
    )

    actual = {case[0]: count_pixels(image, BAR_GREEN) for case, image in zip(cases, images, strict=True)}
    expected = {case_id: bar_pixels(number) for case_id, _, _, number in cases}
    assert actual == expected


def test_clamp(aviutl2: AviUtl2) -> None:
    """RM-F14: 「端で止める」のとき、負は最初の画像、枚数以上は最後の画像になる。"""
    # (id, 値, 枚数（0 は自動）, 表示される bar の番号)
    cases = [("negative", -1, 0, 0), ("beyond_count", 50, 0, 10), ("given_count", 8, 5, 4)]

    images = render_cases(
        aviutl2, [(base(value), slot(BAR, outside="端で止める", count=count)) for _, value, count, _ in cases]
    )

    actual = {case[0]: count_pixels(image, BAR_GREEN) for case, image in zip(cases, images, strict=True)}
    expected = {case_id: bar_pixels(number) for case_id, _, _, number in cases}
    assert actual == expected


def test_given_count_beyond_files(aviutl2: AviUtl2) -> None:
    """枚数を実際（11 枚）より多く指定し、無い番号の画像になったときは、何も表示しない（仕様）。

    存在しない画像を読み込まないので、ログにエラーも出ない。
    """
    # 枚数 20 で値 19 は、ループでも端で止めるでも 19 番（bar_019.png、存在しない）になる。
    outsides = ["ループ", "端で止める"]

    # ログにエラーがあれば、render() が失敗する（allow_log_errors を渡していない）。
    images = render_cases(
        aviutl2,
        [
            (base(19), slot(BAR, outside=outside, count=20), slot(NUMBER, outside=outside, count=20))
            for outside in outsides
        ],
    )

    drawn = [outside for outside, image in zip(outsides, images, strict=True) if image.getbbox() is not None]
    assert drawn == [], "何も表示しないはずのケースで、何かが描かれた"


def make_sequence(folder: Path, image_count: int) -> Path:
    """bar_000〜 を複製して、image_count 枚の連番 seq_000〜 を作る。選ぶ画像（seq_000.png）を返す。"""
    folder.mkdir()
    for number in range(image_count):
        shutil.copyfile(SAMPLES / "bar" / f"bar_{number:03d}.png", folder / f"seq_{number:03d}.png")
    return folder / "seq_000.png"


def test_auto_count_boundary(aviutl2: AviUtl2, tmp_path: Path) -> None:
    """RM-F15: 枚数を自動で数える処理（倍々に調べてから二分探索）が、2 の累乗の前後でも正しく数える。

    端で止めるで大きな値を指定すると、最後の画像（image_count - 1 番）が表示される。
    連番はケースごとに別のフォルダに作るので、数えた枚数の使い回しは効かず、どれも初めて数える。
    """
    image_counts = [1, 2, 3, 4, 5, 8, 9, 11]
    first_images = [
        make_sequence(tmp_path / f"seq{image_count}", image_count) for image_count in image_counts
    ]

    images = render_cases(
        aviutl2, [(base(50), slot(first_image, outside="端で止める")) for first_image in first_images]
    )

    actual = {f"{n}枚": count_pixels(image, BAR_GREEN) for n, image in zip(image_counts, images, strict=True)}
    expected = {f"{n}枚": bar_pixels(n - 1) for n in image_counts}
    assert actual == expected
    # bar_000 は緑が無いので、1 枚のときも何かが描かれていることを別に確かめる。
    assert all(image.getbbox() is not None for image in images)


def test_auto_count_reused_across_frames(aviutl2: AviUtl2, tmp_path: Path) -> None:
    """数えた枚数を使い回しても、別の連番の枚数と混ざらず、フレームが進んでも正しい。"""
    five = make_sequence(tmp_path / "five", 5)
    nine = make_sequence(tmp_path / "nine", 9)
    # 値1 は 0 → 9。5 枚の連番はループで 9 → 4、9 枚の連番は端で止めるで 9 → 8。
    effect = base("0.00,9.00,直線移動,0")
    # バー（高さ 40）は、5 枚の連番を中央 y=240、9 枚の連番を Y で 100 下の y=340 に置く。
    slots = (slot(five, outside="ループ"), slot(nine, outside="端で止める", y=100))

    result = aviutl2.render(project(effect, *slots, end=9), [0, 6, 9])

    # 2つのバーを、画面の上下に分けて数える。
    for frame, expected_five, expected_nine in ((0, 0, 0), (6, 1, 6), (9, 4, 8)):
        upper = result.images[frame].crop((0, 0, 640, 290))
        lower = result.images[frame].crop((0, 290, 640, 480))
        assert count_pixels(upper, BAR_GREEN) == bar_pixels(expected_five), f"frame {frame}"
        assert count_pixels(lower, BAR_GREEN) == bar_pixels(expected_nine), f"frame {frame}"


def test_auto_count_from_selected_image(aviutl2: AviUtl2) -> None:
    """RM-F15: 枚数は、選んだ画像から数える（bar_004 から数えると 7 枚）。"""
    image = aviutl2.render(
        project(base(7), slot(SAMPLES / "bar" / "bar_004.png", outside="ループ")), [0]
    ).images[0]

    # 7 枚なので、表示番号 7 は先頭（bar_004）に戻る。
    assert count_pixels(image, BAR_GREEN) == bar_pixels(4)


def test_unset_slots_are_not_an_error(aviutl2: AviUtl2) -> None:
    """画像を指定していないスロットがあっても、エラーなく動作する。"""
    image = aviutl2.render(project(base(2), slot(), slot(BAR), slot()), [0]).images[0]

    assert count_pixels(image, BAR_GREEN) == bar_pixels(2)


# ---- 連番スロット（計算式） ----


def test_formula(aviutl2: AviUtl2) -> None:
    """RM-F30・RM-F31: 計算式の結果（小数点以下は切り捨て）を表示番号にする。

    結果が 0 未満なら何も出さない（"値1 - 1" で値 0）。
    """
    # (id, 土台の値, 計算式, 表示される bar の番号。None は何も出さない)
    cases = [
        ("minus", (1,), "値1 - 1", 0),
        ("below_zero", (0,), "値1 - 1", None),
        ("sum", (3, 4), "値1 + 値2", 7),
        ("ratio", (10,), "値1 * 53 / 100", 5),
        ("math", (9,), "math.min(値1, 6)", 6),
        ("if_true", (20,), "値1 < 30 and 1 or 0", 1),
        ("if_false", (40,), "値1 < 30 and 1 or 0", 0),
        ("nested_2", (120,), "値1 >= 100 and 2 or (値1 >= 50 and 1 or 0)", 2),
        ("nested_1", (60,), "値1 >= 100 and 2 or (値1 >= 50 and 1 or 0)", 1),
        # 100 * 0.29 は、計算の誤差で 28.999999999999996 になる。誤差を取り除いてから切り捨てる。
        ("float_error", (100,), "値1 * 0.29 - 20", 9),
    ]

    images = render_cases(
        aviutl2, [(base(*values), formula_slot(BAR, formula)) for _, values, formula, _ in cases]
    )

    actual = {}
    expected = {}
    for (case_id, _, _, number), image in zip(cases, images, strict=True):
        if number is None:
            actual[case_id] = image.getbbox()
            expected[case_id] = None
        else:
            actual[case_id] = count_pixels(image, BAR_GREEN)
            expected[case_id] = bar_pixels(number)
    assert actual == expected


def test_formula_loop_counts_from_the_end(aviutl2: AviUtl2) -> None:
    """RM-F14: ループのとき、-3 は後ろから3つ目の画像になる。"""
    image = aviutl2.render(project(base(0), formula_slot(BAR, "値1 - 3", outside="ループ")), [0]).images[0]

    assert count_pixels(image, BAR_GREEN) == bar_pixels(8)


REJECTED_FORMULAS = {
    "io": "io.open",
    "os": "os.execute",
    "require": "require",
    "loadstring": "loadstring",
    "function": "(function() return 1 end)()",
    "random": "math.random(1, 6)",
    "string": "string.rep",
    "method": "(値1 .. 値2):rep(3)",
    "quote": '"1"',
    "v9": "値9",
    "syntax": "値1 +",
    "empty": "",
    "boolean": "値1 < 30",
}


def test_formula_rejected(aviutl2: AviUtl2) -> None:
    """RM-F32: 使えない名前や記号を含む計算式は計算せず、画像を出さずに案内を出す。

    「案内の表示」が「表示しない」なら何も出ず、「常に」なら案内だけが出る。
    """
    case_ids = list(REJECTED_FORMULAS)
    formulas = list(REJECTED_FORMULAS.values())
    hidden_cases = [(base(1, guide="表示しない"), formula_slot(BAR, formula)) for formula in formulas]
    guided_cases = [(base(1, guide="常に"), formula_slot(BAR, formula)) for formula in formulas]

    # 計算式を実行してしまい、スクリプトエラーになれば、render() が失敗する（ログの script exception）。
    images = render_cases(aviutl2, hidden_cases + guided_cases)
    hidden_images = images[: len(case_ids)]
    guided_images = images[len(case_ids) :]

    drawn_when_hidden = [
        case_id for case_id, image in zip(case_ids, hidden_images, strict=True) if image.getbbox() is not None
    ]
    no_guide = [
        case_id for case_id, image in zip(case_ids, guided_images, strict=True) if image.getbbox() is None
    ]
    bar_drawn = [
        case_id
        for case_id, image in zip(case_ids, guided_images, strict=True)
        if count_pixels(image, BAR_GREEN) > 0
    ]
    assert drawn_when_hidden == [], "「表示しない」なのに何かが描かれた"
    assert no_guide == [], "「常に」なのに案内が出ていない"
    assert bar_drawn == [], "使えない計算式なのに画像が描かれた"


# ---- 連番スロット（ゲージ） ----


def test_gauge(aviutl2: AviUtl2) -> None:
    """RM-F60: 表示番号は 切り捨て(値 × (枚数 - 1) ÷ ゲージの上限)。上限を超えた値は満タンのまま。"""
    # (id, 値, ゲージの上限, 枚数（0 は自動）, 表示される bar の番号)
    cases = [
        ("empty", 0, 100, 0, 0),
        ("full", 100, 100, 0, 10),
        ("middle", 55, 100, 0, 5),
        ("floor", 59, 100, 0, 5),
        ("over", 150, 100, 0, 10),
        ("over_999", 999, 100, 0, 10),
        ("max_10", 7, 10, 0, 7),
        ("max_500", 500, 500, 0, 10),
        ("given", 100, 100, 5, 4),
        ("given_half", 50, 100, 5, 2),
    ]

    images = render_cases(
        aviutl2,
        [
            (base(value), gauge_slot(BAR, gauge_max=gauge_max, count=count))
            for _, value, gauge_max, count, _ in cases
        ],
    )

    actual = {case[0]: count_pixels(image, BAR_GREEN) for case, image in zip(cases, images, strict=True)}
    expected = {case_id: bar_pixels(number) for case_id, _, _, _, number in cases}
    assert actual == expected


def test_gauge_counts_from_selected_image(aviutl2: AviUtl2) -> None:
    """RM-F60: 枚数は、連番スロットと同じく選んだ画像から自動で数える（bar_004 から 7 枚）。"""
    image = aviutl2.render(project(base(100), gauge_slot(SAMPLES / "bar" / "bar_004.png")), [0]).images[0]

    # 7 枚なので、満タンは 6 番目（bar_010）。
    assert count_pixels(image, BAR_GREEN) == bar_pixels(10)


def test_gauge_hides_negative(aviutl2: AviUtl2) -> None:
    """RM-F61: 値が負なら何も表示しない。-1 から 0 へ動かす途中（-0.5）も表示しない。"""
    slots = (gauge_slot(BAR), gauge_slot(NUMBER, y=100))

    # ログにエラーがあれば、render() が失敗する（allow_log_errors を渡していない）。
    result = aviutl2.render(project(base("-1.00,0.00,直線移動,0"), *slots, end=2), [0, 1, 2])

    assert result.images[0].getbbox() is None
    assert result.images[1].getbbox() is None
    assert count_pixels(result.images[2], BAR_GREEN) == bar_pixels(0)


def test_gauge_and_still_guide(aviutl2: AviUtl2) -> None:
    """RM-F08: ゲージ・静止画スロットも、画像に不備があるときは、連番スロットと同じ案内を出す。

    ゲージは未設定・連番の規則に合わない・見つからないとき、静止画は未設定・見つからないとき
    （静止画は番号の無い画像を使うので、連番の規則は問わない）。
    """
    # (id, 確かめるスロット, 同じ画像の連番スロット)
    cases = [
        ("gauge_no_image", gauge_slot(""), slot("")),
        ("gauge_not_sequential", gauge_slot(NOT_SEQUENTIAL), slot(NOT_SEQUENTIAL)),
        ("gauge_missing", gauge_slot(MISSING), slot(MISSING)),
        ("still_no_image", still_slot(""), slot("")),
        ("still_missing", still_slot(MISSING), slot(MISSING)),
    ]
    target_cases = [(base(0, guide="常に"), target) for _, target, _ in cases]
    sequence_cases = [(base(0, guide="常に"), sequence) for _, _, sequence in cases]

    images = render_cases(aviutl2, target_cases + sequence_cases)
    target_images = images[: len(cases)]
    sequence_images = images[len(cases) :]

    no_guide = [case[0] for case, image in zip(cases, target_images, strict=True) if image.getbbox() is None]
    different = [
        case[0]
        for case, target, sequence in zip(cases, target_images, sequence_images, strict=True)
        if ImageChops.difference(target, sequence).getbbox() is not None
    ]
    assert no_guide == [], "案内が出ていない"
    assert different == [], "連番スロットの案内と見た目が違う"


def test_gauge_given_count_beyond_files(aviutl2: AviUtl2) -> None:
    """枚数を実際（11 枚）より多く指定し、無い番号の画像になったときは、何も表示しない。"""
    image = aviutl2.render(project(base(100), gauge_slot(BAR, count=20)), [0]).images[0]

    assert image.getbbox() is None


# ---- 静止画スロット ----


@pytest.fixture
def still_image(tmp_path: Path) -> Path:
    """番号の無いファイル名の、日本語を含む静止画（bar_007 の複製）。"""
    path = tmp_path / "アイコン.png"
    shutil.copyfile(SAMPLES / "bar" / "bar_007.png", path)
    return path


def test_still_ignores_values(aviutl2: AviUtl2, still_image: Path) -> None:
    """RM-F70: 番号の無いファイル名の画像を、値に左右されず常に表示する（値が -1 でも 999 でも）。"""
    effect = base("-1.00,999.00,直線移動,0", 5, 6, 7, 8, 9, 10, 11)

    result = aviutl2.render(project(effect, still_slot(still_image), end=2), [0, 1, 2])

    for frame in (0, 1, 2):
        assert count_pixels(result.images[frame], BAR_GREEN) == bar_pixels(7), f"frame {frame}"


def test_still_position_and_scale(aviutl2: AviUtl2, still_image: Path) -> None:
    """RM-F17: 静止画スロットの X・Y・拡大率で、ずらした位置に指定の大きさで描く。"""
    plain, moved = render_cases(
        aviutl2,
        [(base(0), still_slot(still_image)), (base(0), still_slot(still_image, x=-100, y=50, scale=50))],
    )

    left, top, right, bottom = color_mask(plain, BAR_GREEN).getbbox()
    moved_left, moved_top, moved_right, moved_bottom = color_mask(moved, BAR_GREEN).getbbox()
    assert (moved_left + moved_right) / 2 == pytest.approx(320 - 100 + ((left + right) / 2 - 320) / 2, abs=2)
    assert (moved_top + moved_bottom) / 2 == pytest.approx(240 + 50 + ((top + bottom) / 2 - 240) / 2, abs=2)
    assert moved_right - moved_left == pytest.approx((right - left) / 2, abs=2)


def test_still_with_other_slots(aviutl2: AviUtl2, still_image: Path) -> None:
    """静止画スロットは、ほかのスロットと一緒に1つの土台で描ける。"""
    effect = base(3)

    image = aviutl2.render(
        project(effect, still_slot(still_image, y=-150), slot(NUMBER), width=1280), [0]
    ).images[0]

    upper = image.crop((0, 0, 1280, 160))
    assert count_pixels(upper, BAR_GREEN) == bar_pixels(7)
    assert_number_at(image, 640, 3)


# ---- テキスト数値スロット ----

RED = (255, 0, 0)


def test_number_text(aviutl2: AviUtl2) -> None:
    """RM-F40・RM-F41: テキストの中の {計算式} が、計算結果に置き換わって表示される。

    見た目は基準画像（目視で確認済み）と比べる。
    """
    result = aviutl2.render(project(base(7, 3), number_slot("HP {値1} / {値1 * 10}  残り {値2 - 1} 回")), [0])

    assert result.images[0].getbbox() is not None
    aviutl2.assert_snapshot(result)


def test_number_follows_value(aviutl2: AviUtl2) -> None:
    """テキスト数値スロットは、従う値が変わると、表示する文字が変わる。"""
    result = aviutl2.render(project(base("0.00,10.00,直線移動,0"), number_slot("{値1}"), end=10), [0, 10])

    assert result.images[0].getbbox() is not None
    assert ImageChops.difference(result.images[0], result.images[10]).getbbox() is not None


def test_number_text_color(aviutl2: AviUtl2) -> None:
    """RM-F42: 「テキスト」と同じ書き方の文字色が反映される。"""
    image = aviutl2.render(
        project(base(8), number_slot("{値1}", text_color="ff0000", decoration="標準文字")), [0]
    ).images[0]

    assert count_pixels(image, RED) > 0


def test_number_rejected_formula(aviutl2: AviUtl2) -> None:
    """RM-F32: 使えない計算式を含むテキストは表示せず、案内を出す。"""
    hidden, guided = render_cases(
        aviutl2,
        [
            (base(1, guide="表示しない"), number_slot("HP {io}")),
            (base(1, guide="常に"), number_slot("HP {io}")),
        ],
    )

    assert hidden.getbbox() is None
    assert guided.getbbox() is not None


# (id, 値1, 計算式を書いたテキスト, 小数の扱い, 桁数（0 は「しない」）, 期待する文字)
NUMBER_FORMAT_CASES = [
    ("minus_zero", 0, "{値1 * -1}", "四捨五入", 0, "0"),
    ("exact_limit", 1, "{値1 * 2^53}", "四捨五入", 0, "9007199254740992"),
    ("huge", 1, "{値1 * 1e20}", "四捨五入", 0, "1e+20"),
    ("huge_styled", 1, "{値1 * 1e20}", "小数第2位まで", 10, "1e+20"),
    ("round", 100, "{値1 / 3}", "四捨五入", 0, "33"),
    ("one_place", 100, "{値1 / 3}", "小数第1位まで", 0, "33.3"),
    ("truncate", 100, "{値1 / 6}", "切り捨て", 0, "16"),
    ("round_up", 100, "{値1 / 6}", "四捨五入", 0, "17"),
    ("two_places", 100, "{値1 / 6}", "小数第2位まで", 0, "16.67"),
    ("pad", 100, "{値1 / 20}", "四捨五入", 3, "005"),
    ("one_place_zero", 100, "{値1 / 20}", "小数第1位まで", 0, "5.0"),
    ("one_place_half", 100, "{値1 / 400}", "小数第1位まで", 0, "0.3"),
    ("two_places_zero", 100, "{値1 / 1000}", "小数第2位まで", 0, "0.10"),
    ("pad_fraction", 100, "{値1 / 8}", "小数第1位まで", 3, "012.5"),
    ("pad_negative", 100, "{値1 * -7 / 100}", "四捨五入", 3, "-007"),
    ("truncate_negative", 100, "{値1 * -1 / 6}", "切り捨て", 0, "-16"),
    ("round_negative", 100, "{値1 * -1 / 6}", "四捨五入", 0, "-17"),
    ("round_negative_half", 100, "{値1 * -1 / 40}", "四捨五入", 0, "-3"),
    ("round_to_zero", 100, "{値1 * -1 / 250}", "四捨五入", 0, "0"),
    ("pad_max", 100, "{値1}", "四捨五入", 10, "0000000100"),
    ("longer_than_digits", 100, "{値1 * 100000000}", "四捨五入", 10, "10000000000"),
    ("every_formula", 100, "HP {値1} / {値1 / 4}", "四捨五入", 3, "HP 100 / 025"),
    # 計算の誤差（100 * 0.29 は 28.999999999999996 になる）を取り除いてから丸める。
    ("float_truncate", 100, "{値1 * 0.29}", "切り捨て", 0, "29"),
    ("float_round", 10, "{値1 * 0.1005}-{1.005}", "小数第2位まで", 0, "1.01-1.01"),
    ("float_round_negative", 1, "{値1 * -1.005}", "小数第2位まで", 0, "-1.01"),
]


def test_number_format(aviutl2: AviUtl2) -> None:
    """RM-F43・RM-F44: 計算結果は、小数の扱いで丸め、桁数に満たない整数部分の前を 0 で埋めて表示される。

    全桁を正確に表せない大きな数は、Lua の書き方で表示される。
    計算式を書いたテキストと、期待する文字をそのまま書いたテキストの描画を比べる。
    """
    actual_cases = [
        (base(value), number_slot(formula, decimal=decimal, digits=digits))
        for _, value, formula, decimal, digits, _ in NUMBER_FORMAT_CASES
    ]
    expected_cases = [
        (base(value), number_slot(expected_text)) for _, value, _, _, _, expected_text in NUMBER_FORMAT_CASES
    ]

    images = render_cases(aviutl2, actual_cases + expected_cases)
    actual_images = images[: len(NUMBER_FORMAT_CASES)]
    expected_images = images[len(NUMBER_FORMAT_CASES) :]

    case_ids = [case[0] for case in NUMBER_FORMAT_CASES]
    nothing_drawn = [
        case_id for case_id, image in zip(case_ids, actual_images, strict=True) if image.getbbox() is None
    ]
    different = [
        f"{case[0]}（期待: {case[5]!r}）"
        for case, actual, expected in zip(NUMBER_FORMAT_CASES, actual_images, expected_images, strict=True)
        if ImageChops.difference(actual, expected).getbbox() is not None
    ]
    assert nothing_drawn == [], "何も描かれていない"
    assert different == [], "期待する文字の描画と違う"


# ---- 連番スロット（複製並べ） ----


def number_white_box(number: int) -> tuple[int, int, int, int]:
    """number_00n の画像の中の、白い部分の範囲（左, 上, 右, 下）。"""
    return color_mask(Image.open(SAMPLES / "number" / f"number_{number:03d}.png"), NUMBER_WHITE).getbbox()


def test_repeat_count_follows_value(aviutl2: AviUtl2) -> None:
    """RM-F50: 2つ目の値の数だけ、1つ目の値で選んだ画像が並ぶ。"""
    image = aviutl2.render(project(base(3, 4), repeat_slot(NUMBER), width=1280), [0]).images[0]

    single = count_pixels(Image.open(SAMPLES / "number" / "number_003.png"), NUMBER_WHITE)
    assert count_pixels(image, NUMBER_WHITE) == single * 4


def test_repeat_alignment(aviutl2: AviUtl2) -> None:
    """RM-F52: 並べ方と余白で、並びの位置が決まる。並びの上端は土台の位置。"""
    # (id, 並べ方, 余白)
    cases = [
        ("left", "左揃え", 0),
        ("left_margin", "左揃え", 10),
        ("center", "中央揃え", 10),
        ("right", "右揃え", 10),
    ]

    images = render_cases(
        aviutl2,
        [(base(3, 3), repeat_slot(NUMBER, margin=margin, align=align)) for _, align, margin in cases],
        width=1280,
    )

    white_left, white_top, white_right, _ = number_white_box(3)
    actual = {}
    expected = {}
    for (case_id, align, margin), image in zip(cases, images, strict=True):
        cell_width = NUMBER_WIDTH + margin * 2
        row_width = cell_width * 3
        if align == "左揃え":
            row_left = 640
        elif align == "右揃え":
            row_left = 640 - row_width
        else:
            row_left = 640 - row_width / 2
        left, top, right, _ = color_mask(image, NUMBER_WHITE).getbbox()
        actual[case_id] = (left, right, top)
        expected[case_id] = (
            pytest.approx(row_left + margin + white_left, abs=1),
            pytest.approx(row_left + cell_width * 2 + margin + white_right, abs=1),
            pytest.approx(240 + margin + white_top, abs=1),
        )
    assert actual == expected


def test_repeat_wraps(aviutl2: AviUtl2) -> None:
    """RM-F52: 折り返しの数ごとに、次の行に並ぶ。"""
    image = aviutl2.render(project(base(3, 3), repeat_slot(NUMBER, wrap=2), width=1280), [0]).images[0]

    white_left, white_top, white_right, white_bottom = number_white_box(3)
    left, top, right, bottom = color_mask(image, NUMBER_WHITE).getbbox()
    # 2 列・2 行（2 行目は 1 つ）。3 行目は画面の下にはみ出すため、2 行で確かめる。
    assert right - left == pytest.approx(NUMBER_WIDTH + white_right - white_left, abs=1)
    assert bottom - top == pytest.approx(NUMBER_HEIGHT + white_bottom - white_top, abs=1)


def test_repeat_nothing_below_one(aviutl2: AviUtl2) -> None:
    """RM-F51: 並べる数が 0 以下なら、何も表示しない。"""
    zero, negative = render_cases(
        aviutl2, [(base(3, 0), repeat_slot(NUMBER)), (base(3, -1), repeat_slot(NUMBER))]
    )

    assert zero.getbbox() is None
    assert negative.getbbox() is None


def test_repeat_limit(aviutl2: AviUtl2) -> None:
    """RM-F51: 並べる数は 100 まで。150 を指定しても 100 個と同じになる。"""
    counts = [100, 150, 99]
    at_limit, over_limit, under_limit = render_cases(
        aviutl2,
        [(base(3, count), repeat_slot(NUMBER, wrap=20, scale=5)) for count in counts],
        width=1280,
    )

    assert ImageChops.difference(at_limit, over_limit).getbbox() is None
    assert ImageChops.difference(at_limit, under_limit).getbbox() is not None


# ---- 位置と大きさ ----


def test_slot_position_and_scale(aviutl2: AviUtl2) -> None:
    """RM-F17: スロットの X・Y・拡大率で、そのスロットの画像だけを、ずらした位置に指定の大きさで描く。"""
    effect = base(10, 3)

    image = aviutl2.render(
        project(
            effect, slot(BAR, x=-300, y=-150), slot(NUMBER, source=2, x=300, y=50, scale=200), width=1280
        ),
        [0],
    ).images[0]

    # バーは X=-300・Y=-150：中心が (640-300, 240-150)。大きさはそのまま。
    bar_left, bar_top, bar_right, bar_bottom = color_mask(image, BAR_GREEN).getbbox()
    assert (bar_left + bar_right) // 2 == pytest.approx(340, abs=2)
    assert (bar_top + bar_bottom) // 2 == pytest.approx(90, abs=2)
    assert count_pixels(image, BAR_GREEN) == bar_pixels(10)

    # 数字は X=300・Y=50・拡大率 200%：中心が (940, 290)、白い部分の大きさが 2 倍。
    expected_left, expected_top, expected_right, expected_bottom = color_mask(
        Image.open(SAMPLES / "number" / "number_003.png"), NUMBER_WHITE
    ).getbbox()
    # バーにも白い枠線があるので、バーより右（x >= 700）だけを見る。
    right_side = image.crop((700, 0, image.width, image.height))
    number_left, number_top, number_right, number_bottom = color_mask(right_side, NUMBER_WHITE).getbbox()
    number_left, number_right = number_left + 700, number_right + 700
    assert number_right - number_left == pytest.approx((expected_right - expected_left) * 2, abs=4)
    assert number_bottom - number_top == pytest.approx((expected_bottom - expected_top) * 2, abs=4)
    image_center_x = (expected_left + expected_right) / 2 - NUMBER_WIDTH / 2
    image_center_y = (expected_top + expected_bottom) / 2 - NUMBER_HEIGHT / 2
    assert (number_left + number_right) / 2 == pytest.approx(940 + image_center_x * 2, abs=3)
    assert (number_top + number_bottom) / 2 == pytest.approx(290 + image_center_y * 2, abs=3)


# ---- ファイル名の変更 ----


def test_works_after_renaming_the_files(aviutl2: AviUtl2, renamed_names: tuple[str, str]) -> None:
    """RM-F19・RM-F23: 利用者がスクリプトのファイル名を変えても、同じように動く。"""
    renamed_base, renamed_slot = renamed_names
    effect = base(5, 3, name=renamed_base)
    slots = (slot(BAR, name=renamed_slot), slot(NUMBER, source=2, x=400, name=renamed_slot))

    image = aviutl2.render(project(effect, *slots, width=1280), [0]).images[0]

    assert count_pixels(image, BAR_GREEN) == bar_pixels(5)
    assert_number_at(image, 1040, 3)


# ---- 日本語のパス ----


@pytest.fixture
def japanese_bar(tmp_path: Path) -> Path:
    """フォルダ名とファイル名に日本語を含む、bar の連番の複製。選ぶ画像（てすと_000.png）を返す。"""
    folder = tmp_path / "てすと"
    folder.mkdir()
    for number in range(IMAGE_COUNT):
        shutil.copyfile(SAMPLES / "bar" / f"bar_{number:03d}.png", folder / f"てすと_{number:03d}.png")
    return folder / "てすと_000.png"


def test_japanese_path(aviutl2: AviUtl2, japanese_bar: Path) -> None:
    """フォルダ名やファイル名に日本語を含む画像も、表示でき、枚数も数えられる。"""
    # ループで、枚数（11 枚）を数える処理も通す。値 14 は 3 番目に戻る。
    image_shown, image_loop = render_cases(
        aviutl2,
        [
            (base(3, 0), slot(japanese_bar, source=1)),
            (base(0, 14), slot(japanese_bar, source=2, outside="ループ")),
        ],
    )

    assert count_pixels(image_shown, BAR_GREEN) == bar_pixels(3)
    assert count_pixels(image_loop, BAR_GREEN) == bar_pixels(3)


def test_other_ffi_declarations(aviutl2: AviUtl2, japanese_bar: Path) -> None:
    """ほかのスクリプトが、ファイルの確かめに使う関数を違う型で先に宣言していても、土台は動く。

    ffi の宣言はスクリプト同士で共有され、同じ名前の宣言は先のものが使われ続ける。
    """
    # 描画は上のレイヤーから行われるので、宣言するスクリプトを土台より上（レイヤー 0）に置く。
    declarer = TimelineObject(0, 0, 9, [Effect(DECLARE_FFI), Effect("標準描画")])
    host = TimelineObject(1, 0, 9, [base(14), slot(japanese_bar, outside="ループ"), Effect("標準描画")])

    image = aviutl2.render(Project(640, 480, [declarer, host]), [0]).images[0]

    assert count_pixels(image, BAR_GREEN) == bar_pixels(3)


# ---- 案内 ----

# 案内が出るスロットの組み合わせ。id は、基準画像のフレーム番号の順（frame_00000 が no_slot）。
GUIDE_CASES = {
    "no_slot": (),
    "no_image": (slot(),),
    "not_sequential": (slot(NOT_SEQUENTIAL),),
    "missing": (slot(MISSING),),
    "unknown_kind": (Effect(UNKNOWN_SLOT),),
}


def test_guide_not_in_output(aviutl2: AviUtl2) -> None:
    """「案内の表示」が「選択中だけ」なら、出力には案内が表示されない。"""
    images = render_cases(aviutl2, [(base(0), *slots) for slots in GUIDE_CASES.values()])

    drawn = [
        case_id for case_id, image in zip(GUIDE_CASES, images, strict=True) if image.getbbox() is not None
    ]
    assert drawn == [], "出力に案内が描かれた"


def test_guide_shown_only_when_selected(aviutl2: AviUtl2) -> None:
    """RM-F08: 「選択中だけ」なら、土台を選択しているときのプレビューに案内が表示される。

    選択していない出力に表示されないことは、test_guide_not_in_output で確かめている。
    """
    selected_project = project(base(0))
    host = selected_project.objects[0]

    selected = aviutl2.render(selected_project, [0], selected=host)

    assert selected.images[0].getbbox() is not None


def test_guide_is_never_shown_when_disabled(aviutl2: AviUtl2) -> None:
    """「案内の表示」が「表示しない」なら、選択していても案内は表示されない。"""
    disabled_project = project(base(0, guide="表示しない"))

    result = aviutl2.render(disabled_project, [0], selected=disabled_project.objects[0])

    assert result.images[0].getbbox() is None


def test_guide_always_shown(aviutl2: AviUtl2) -> None:
    """「案内の表示」が「常に」なら、出力にも案内が表示される。見た目は基準画像（目視で確認済み）と比べる。

    GUIDE_CASES の順に1フレームずつ描くので、基準画像の frame_0000n は n 番目のケース。
    """
    result = aviutl2.render(
        cases_project([(base(0, guide="常に"), *slots) for slots in GUIDE_CASES.values()]),
        list(range(len(GUIDE_CASES))),
    )

    nothing_drawn = [
        case_id for frame, case_id in enumerate(GUIDE_CASES) if result.images[frame].getbbox() is None
    ]
    assert nothing_drawn == [], "案内が出ていない"
    aviutl2.assert_snapshot(result)


def test_guide_shown_with_slots(aviutl2: AviUtl2) -> None:
    """不備のあるスロットがあっても、ほかのスロットは描かれ、案内は土台の位置に表示される。"""
    effect = base(10, guide="常に")

    result = aviutl2.render(project(effect, slot(BAR, y=-150), slot(NOT_SEQUENTIAL), width=1280), [0])

    assert count_pixels(result.images[0], BAR_GREEN) == bar_pixels(10)
    aviutl2.assert_snapshot(result)
