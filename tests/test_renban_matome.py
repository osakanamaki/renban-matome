"""連番まとめ（土台「連番まとめ（値）」＋スロット）を、要件定義書 1.6.12 の受け入れ基準で確かめる。

証跡のパスが Windows の上限（260 文字）を超えると描画できないため、テスト名と id は短くする。
"""

from pathlib import Path

import pytest
from aviutl2_pyrrhulina import Effect, Project, TimelineObject
from aviutl2_pyrrhulina.pytest_plugin import AviUtl2
from PIL import Image, ImageChops

BASE = "連番まとめ（値）"
SLOT = "連番スロット"
# 土台が対応していない種類のスロット（案内の確認用）。
UNKNOWN_SLOT = "_試験_未知のスロット"

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


@pytest.mark.parametrize("source", [2, 3, 4, 5, 6, 7, 8])
def test_each_value_can_be_followed(aviutl2: AviUtl2, source: int) -> None:
    """RM-F03: 値1〜値8のどれにも従える。ほかの値には従わない。"""
    values = [0] * 8
    values[source - 1] = 7

    image = aviutl2.render(project(base(*values), slot(BAR, source=source)), [0]).images[0]

    assert count_pixels(image, BAR_GREEN) == bar_pixels(7)


def test_selected_image_is_value_zero(aviutl2: AviUtl2) -> None:
    """RM-F11: 途中の画像を選ぶと、値 0 でその画像が表示され、値の分だけ後ろの画像になる。"""
    result = aviutl2.render(
        project(base("0.00,4.00,直線移動,0"), slot(SAMPLES / "bar" / "bar_003.png"), end=4), [0, 4]
    )

    assert count_pixels(result.images[0], BAR_GREEN) == bar_pixels(3)
    assert count_pixels(result.images[4], BAR_GREEN) == bar_pixels(7)


# ---- 範囲外の扱いと枚数 ----


@pytest.mark.parametrize(
    ("value", "count"),
    [(-1, 0), (IMAGE_COUNT, 0), (6, 6)],
    ids=["negative", "beyond_count", "beyond_given_count"],
)
def test_hide_out_of_range(aviutl2: AviUtl2, value: int, count: int) -> None:
    """RM-F14: 「表示しない」のとき、範囲外なら何も表示されず、スクリプトエラーも、ログのエラーも出ない。"""
    slots = (slot(BAR, count=count), slot(NUMBER, count=count))

    # ログにエラーがあれば、render() が失敗する（allow_log_errors を渡していない）。
    result = aviutl2.render(project(base(value), *slots), [0])

    assert result.images[0].getbbox() is None


@pytest.mark.parametrize(
    ("value", "count", "expected"),
    [(IMAGE_COUNT, 0, 0), (IMAGE_COUNT + 3, 0, 3), (-1, 0, 10), (6, 5, 1), (-1, 5, 4)],
    ids=["count", "count_plus_3", "minus_1", "given_count", "given_minus_1"],
)
def test_loop(aviutl2: AviUtl2, value: int, count: int, expected: int) -> None:
    """RM-F14: 「ループ」のとき、枚数以上は先頭に戻り、負の番号は後ろから数える。枚数は自動でも指定でもよい。

    土台の値は -1 までなので、-2 以下は計算式スロットのテストで確かめる。
    """
    image = aviutl2.render(project(base(value), slot(BAR, outside="ループ", count=count)), [0]).images[0]

    assert count_pixels(image, BAR_GREEN) == bar_pixels(expected)


@pytest.mark.parametrize(
    ("value", "count", "expected"),
    [(-1, 0, 0), (50, 0, 10), (8, 5, 4)],
    ids=["negative", "beyond_count", "given_count"],
)
def test_clamp(aviutl2: AviUtl2, value: int, count: int, expected: int) -> None:
    """RM-F14: 「端で止める」のとき、負は最初の画像、枚数以上は最後の画像になる。"""
    image = aviutl2.render(project(base(value), slot(BAR, outside="端で止める", count=count)), [0]).images[0]

    assert count_pixels(image, BAR_GREEN) == bar_pixels(expected)


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


# ---- 案内 ----

GUIDE_CASES = [
    (),
    (slot(),),
    (slot(NOT_SEQUENTIAL),),
    (slot(MISSING),),
    (Effect(UNKNOWN_SLOT),),
]
GUIDE_IDS = ["no_slot", "no_image", "not_sequential", "missing", "unknown_kind"]


@pytest.mark.parametrize("slots", GUIDE_CASES, ids=GUIDE_IDS)
def test_guide_not_in_output(aviutl2: AviUtl2, slots: tuple[Effect, ...]) -> None:
    """「案内の表示」が「選択中だけ」なら、出力には案内が表示されない。"""
    result = aviutl2.render(project(base(0), *slots), [0])

    assert result.images[0].getbbox() is None


def test_guide_shown_only_when_selected(aviutl2: AviUtl2) -> None:
    """RM-F08: 「選択中だけ」なら、土台を選択しているときのプレビューにだけ案内が表示される。"""
    selected_project = project(base(0))
    host = selected_project.objects[0]

    selected = aviutl2.render(selected_project, [0], selected=host)
    output = aviutl2.render(selected_project, [0])

    assert selected.images[0].getbbox() is not None
    assert output.images[0].getbbox() is None


def test_guide_is_never_shown_when_disabled(aviutl2: AviUtl2) -> None:
    """「案内の表示」が「表示しない」なら、選択していても案内は表示されない。"""
    disabled_project = project(base(0, guide="表示しない"))

    result = aviutl2.render(disabled_project, [0], selected=disabled_project.objects[0])

    assert result.images[0].getbbox() is None


@pytest.mark.parametrize("slots", GUIDE_CASES, ids=GUIDE_IDS)
def test_guide_always_shown(aviutl2: AviUtl2, slots: tuple[Effect, ...]) -> None:
    """「案内の表示」が「常に」なら、出力にも案内が表示される。見た目は基準画像（目視で確認済み）と比べる。"""
    result = aviutl2.render(project(base(0, guide="常に"), *slots), [0])

    assert result.images[0].getbbox() is not None
    aviutl2.assert_snapshot(result)


def test_guide_shown_with_slots(aviutl2: AviUtl2) -> None:
    """不備のあるスロットがあっても、ほかのスロットは描かれ、案内は土台の位置に表示される。"""
    effect = base(10, guide="常に")

    result = aviutl2.render(project(effect, slot(BAR, y=-150), slot(NOT_SEQUENTIAL), width=1280), [0])

    assert count_pixels(result.images[0], BAR_GREEN) == bar_pixels(10)
    aviutl2.assert_snapshot(result)
