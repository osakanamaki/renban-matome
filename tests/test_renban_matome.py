"""連番まとめ.anm2 を、要件定義書 1.6.6 の受け入れ基準で確かめる。"""

from pathlib import Path

import pytest
from aviutl2_pyrrhulina import Effect, Project, TimelineObject
from aviutl2_pyrrhulina.pytest_plugin import AviUtl2
from PIL import Image, ImageChops

RENBAN_MATOME = "連番まとめ"
SHIFT_BY_INDEX = "_試験_番号で横にずらす"
READ_EXPORTED = "_試験_公開値を読む"
SPLIT_IN_TWO = "_試験_二つに分ける"

SAMPLES = Path(__file__).parent.parent / "samples"
BAR = SAMPLES / "bar" / "bar_000.png"
NUMBER = SAMPLES / "number" / "number_000.png"

# ダミー画像の色。bar は緑（10 段階で長さが変わる）、number は白。
# bar にも白い枠線（876 画素）があるので、数字は bar と重ならない位置で確かめる。
BAR_GREEN = (50, 205, 50)
NUMBER_WHITE = (255, 255, 255)
# 数字の画像の大きさ。画面の高さの中央に置かれる。
NUMBER_WIDTH, NUMBER_HEIGHT = 160, 120

# 存在しない画像を obj.load() すると、処理は続くが AviUtl2 がログに [ERROR] を書く。
MISSING_IMAGE_ERROR = "ImageService::canLoadFile"
# 個別オブジェクトに分かれたオブジェクトに付けたときの警告。
SPLIT_HOST_WARNING = "個別オブジェクトに分かれたオブジェクトには付けられません"


def renban_matome(
    frame_position: int | str,
    *slots: dict[str, object],
    export_name: str = "",
    effect_name: str = RENBAN_MATOME,
) -> Effect:
    """slots は、スロット1から順に {"画像": パス, "オフセット": 数, "上限": 数}（省略した項目は既定値）。"""
    if isinstance(frame_position, int):
        frame_position = str(frame_position)
    params: dict[str, object] = {"フレーム位置": frame_position, "公開名": export_name}
    for slot_number, slot in enumerate(slots, start=1):
        for item, value in slot.items():
            params[f"スロット{slot_number}::{item}"] = value
    return Effect(effect_name, params)


def shift_by_index(step: int) -> Effect:
    """個別オブジェクトを、番号 × step だけ右へずらす。スロットどうしを重ならないようにする。"""
    return Effect(SHIFT_BY_INDEX, {"間隔": f"{step}.00"})


def project(
    *effects: Effect,
    width: int = 640,
    end: int = 9,
    midpoints: tuple[int, ...] = (),
    others: tuple[TimelineObject, ...] = (),
) -> Project:
    # 土台は 1 ピクセルの図形にする。空のテキストでは、何も描くものが無いためフィルタ効果が実行されない。
    host = TimelineObject(
        0, 0, end, [Effect("図形", {"サイズ": "1"}), *effects, Effect("標準描画")], midpoints=midpoints
    )
    return Project(width, 480, [host, *others])


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


def test_all_slots_follow_frame_position(aviutl2: AviUtl2) -> None:
    """複数スロットを登録した状態で、フレーム位置を変えると、全スロットの表示画像が同時に切り替わる。"""
    effect = renban_matome("0.00,10.00,直線移動,0", {"画像": BAR}, {"画像": NUMBER})

    # スロットは本来同じ位置に重なるので、番号でずらして別々に確かめる。
    # バー（番号0）は中央 x=640、数字（番号1）は 300 右の x=940。
    result = aviutl2.render(project(effect, shift_by_index(300), width=1280, end=10), [0, 5, 10])

    for frame in (0, 5, 10):
        assert count_pixels(result.images[frame], BAR_GREEN) == bar_pixels(frame), f"frame {frame}"
        assert_number_at(result.images[frame], 940, frame)


def test_starts_from_first_image_without_offset_and_limit(aviutl2: AviUtl2) -> None:
    """オフセットと上限を何も指定しなくても、先頭画像から順に表示される。"""
    effect = renban_matome(3, {"画像": BAR})

    image = aviutl2.render(project(effect), [0]).images[0]

    assert count_pixels(image, BAR_GREEN) == bar_pixels(3)


def test_offset_shifts_only_its_slot(aviutl2: AviUtl2) -> None:
    """RM-F05: オフセットは、フレーム位置に加算して、そのスロットの表示番号を決める。"""
    shifted = renban_matome(3, {"画像": BAR, "オフセット": "4"})

    image = aviutl2.render(project(shifted), [0]).images[0]

    assert count_pixels(image, BAR_GREEN) == bar_pixels(7)


@pytest.mark.parametrize(
    ("frame_position", "limit"),
    [(-1, "0"), (11, "0"), (6, "5")],
    ids=["負の値", "枚数を超える", "上限を超える"],
)
def test_out_of_range_draws_nothing(aviutl2: AviUtl2, frame_position: int, limit: str) -> None:
    """フレーム位置が負、連番の枚数を超える、または上限を超えるとき、何も表示されず、スクリプトエラーにならない。

    連番の枚数を超えるときは、存在しない画像を読もうとするため、AviUtl2 のログに記録される（要件 1.6.6）。
    """
    effect = renban_matome(frame_position, {"画像": BAR, "上限": limit}, {"画像": NUMBER, "上限": limit})

    result = aviutl2.render(project(effect), [0], ignore_log_errors=[MISSING_IMAGE_ERROR])

    assert result.images[0].getbbox() is None
    assert not result.log_lines("script exception")


def test_limit_itself_is_shown(aviutl2: AviUtl2) -> None:
    """RM-F06: 上限と同じ番号までは表示する。"""
    effect = renban_matome(5, {"画像": BAR, "上限": "5"})

    image = aviutl2.render(project(effect), [0]).images[0]

    assert count_pixels(image, BAR_GREEN) == bar_pixels(5)


def test_unset_slots_are_not_an_error(aviutl2: AviUtl2) -> None:
    """ファイルを指定していないスロットがあっても、エラーなく動作する。"""
    only_slot3 = renban_matome(2, {}, {}, {"画像": BAR})
    nothing = renban_matome(2)

    image = aviutl2.render(project(only_slot3, nothing), [0]).images[0]

    assert count_pixels(image, BAR_GREEN) == bar_pixels(2)


def test_two_instances_move_independently(aviutl2: AviUtl2) -> None:
    """「連番まとめ」を1つのオブジェクトに2つ付与したとき、それぞれが独立して動く（中間点も各自のもの）。"""
    number_fixed = renban_matome(3, {"画像": NUMBER})
    bar_up_and_down = renban_matome("0.00,10.00,0.00,直線移動,0", {"画像": BAR})

    # 数字（番号0）は中央 x=640、バー（番号4）は 400 右の x=1040。
    result = aviutl2.render(
        project(number_fixed, bar_up_and_down, shift_by_index(100), width=1280, end=10, midpoints=(5,)),
        [0, 5, 10],
    )

    assert count_pixels(result.images[0], BAR_GREEN) == bar_pixels(0)
    assert count_pixels(result.images[5], BAR_GREEN) == bar_pixels(10)
    assert count_pixels(result.images[10], BAR_GREEN) == bar_pixels(0)
    for frame in (0, 5, 10):
        assert_number_at(result.images[frame], 640, 3)
    # 2つ目は個別オブジェクトの中で実行されるが、正しい付け方なので警告しない。
    assert not result.log_lines(SPLIT_HOST_WARNING)


def test_slots_are_numbered_individual_objects(aviutl2: AviUtl2) -> None:
    """RM-F11: 各スロットは個別オブジェクトになり、番号でスロットを動かせる。

    番号は (何番目の連番まとめ - 1) × 4 + (スロット番号 - 1)。
    1つ目のスロット1（バー）は 0、2つ目のスロット1（数字）は 4。
    """
    first = renban_matome(10, {"画像": BAR})
    second = renban_matome(3, {"画像": NUMBER})

    image = aviutl2.render(project(first, second, shift_by_index(100), width=1280), [0]).images[0]

    # 画面の中央は x=640。バー（番号0）はそのまま、数字（番号4）は 400 右の x=1040 にずれる。
    bar_left, _, bar_right, _ = color_mask(image, BAR_GREEN).getbbox()
    assert (bar_left + bar_right) // 2 == pytest.approx(640, abs=2)
    assert_number_at(image, 1040, 3)


def test_frame_position_is_exported_by_name(aviutl2: AviUtl2) -> None:
    """フレーム位置の値が、利用者の付けた名前で、他のオブジェクトから参照できる。"""
    hp = renban_matome(7, {"画像": BAR}, export_name="HP")
    mp = renban_matome(2, {"画像": NUMBER}, export_name="MP")
    readers = [
        TimelineObject(1, 0, 9, [Effect(READ_EXPORTED, {"名前": "HP"}), Effect("標準描画")]),
        TimelineObject(2, 0, 9, [Effect(READ_EXPORTED, {"名前": "MP"}), Effect("標準描画")]),
    ]

    result = aviutl2.render(project(hp, mp, others=tuple(readers)), [0])

    assert result.log_lines("[公開値] HP=7")
    assert result.log_lines("[公開値] MP=2")


def test_works_after_renaming_the_file(aviutl2: AviUtl2, renamed_effect: str) -> None:
    """利用者がスクリプトのファイル名を変えても、複数付けたときも含めて、同じように動く。"""
    bar = renban_matome(5, {"画像": BAR}, effect_name=renamed_effect)
    number = renban_matome(3, {"画像": NUMBER}, effect_name=renamed_effect)

    image = aviutl2.render(project(bar, number, shift_by_index(100), width=1280), [0]).images[0]

    assert count_pixels(image, BAR_GREEN) == bar_pixels(5)
    assert_number_at(image, 1040, 3)


def test_warns_when_object_is_already_split(aviutl2: AviUtl2) -> None:
    """個別オブジェクトに分かれたオブジェクトに付けると描けないので、そのことをログに書く。"""
    effect = renban_matome(5, {"画像": BAR})

    result = aviutl2.render(project(Effect(SPLIT_IN_TWO), effect), [0])

    assert count_pixels(result.images[0], BAR_GREEN) == 0
    assert result.log_lines(SPLIT_HOST_WARNING)
