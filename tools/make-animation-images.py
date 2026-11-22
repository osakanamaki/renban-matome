"""動作確認用の連番アニメーション画像を作成する。

    samples/animation/animation_000.png ～ animation_149.png : 30fps で 5 秒

猫の AA が、ばね付きの魚の玩具を猫パンチする。魚は揺れて止まり、
最後の 1 秒はスタート状態のまま待つので、そのままループできる。

既存のサンプルに合わせて「透明な背景に白い線」で描く。
色は白だけなので、不透明度 8 段階のパレット PNG にし、さらに oxipng (zopfli) で
圧縮して容量を抑える（JPEG は透明を持てず、線画では PNG より大きくなる）。

    uv run --with pyoxipng python tools/make-animation-images.py

zopfli は遅いので、全フレームの作成に数分かかる。
"""

import math
from pathlib import Path

import oxipng
from PIL import Image, ImageChops, ImageDraw, ImageFont

WIDTH, HEIGHT = 320, 240
SCALE = 4  # 4 倍の大きさで描いて縮小し、線を滑らかにする
FPS = 30
FRAME_COUNT = 150
LINE = 3 * SCALE
ALPHA_LEVELS = 8

FONT_PATH = Path("C:/Windows/Fonts/msgothic.ttc")
FONT_INDEX = 1  # MS Pゴシック
FONT = ImageFont.truetype(str(FONT_PATH), 34 * SCALE, index=FONT_INDEX)
TEXT_STROKE = SCALE  # 文字を図形の線の太さに近づける

OUTPUT_FOLDER = Path(__file__).resolve().parent.parent / "samples" / "animation"

# 玩具の配置（等倍の座標）
BASE_X = 248
BASE_TOP = 196
SPRING_LENGTH = 38

# 猫の配置（等倍の座標）
FACE_LEFT = 8
FACE_TOP = 112

# 時間割（フレーム番号）
WINDUP_START = 12
PUNCH_START = 24
HIT = 28
RECOIL_END = 46
SETTLE_END = 118  # ここから最後まで、スタート状態で待つ


def s(value: float) -> float:
    return value * SCALE


def new_layer() -> Image.Image:
    return Image.new("L", (WIDTH * SCALE, HEIGHT * SCALE), 0)


def ease_in_out(t: float) -> float:
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def text_size(text: str) -> tuple[float, float, float, float]:
    return ImageDraw.Draw(new_layer()).textbbox((0, 0), text, font=FONT)


def draw_text(layer: Image.Image, x: float, y: float, text: str) -> None:
    ImageDraw.Draw(layer).text(
        (s(x), s(y)), text, font=FONT, fill=255, stroke_width=TEXT_STROKE, stroke_fill=255
    )


# ---------------------------------------------------------------- 猫


# 顔は文字ごとに置く。プロポーショナルフォントでは目の文字で幅が変わるので、
# 目を差し替えても枠の「（ ）」と「∀」が動かないよう、通常の顔の位置に固定する。
FACE_PARTS = ["（", " ", "´", "∀", "｀", "）"]
EYE_LEFT, EYE_RIGHT = 2, 4
EYES_NORMAL = ("´", "｀")
EYES_PUNCH = ("ﾟ", "ﾟ")
EARS = "∧＿∧"
EARS_GAP = 6  # 耳の「＿」と目の間のすき間（等倍）


def advance(text: str) -> float:
    return FONT.getlength(text) / SCALE


_face_slots = []
_x = 0.0
for _part in FACE_PARTS:
    _face_slots.append((_x, advance(_part)))
    _x += advance(_part)
FACE_WIDTH = _x
FACE_RIGHT = FACE_LEFT + FACE_WIDTH

# 耳の下端（「＿」）が、目の上端より EARS_GAP だけ上になるように置く
_ears_box = text_size(EARS)
_eyes_top = min(text_size(eye)[1] for eye in EYES_NORMAL + EYES_PUNCH) / SCALE
EARS_LEFT = FACE_LEFT + (FACE_WIDTH - (_ears_box[2] - _ears_box[0]) / SCALE) / 2
EARS_TOP = FACE_TOP + _eyes_top - EARS_GAP - _ears_box[3] / SCALE


def draw_face(layer: Image.Image, eyes: tuple[str, str]) -> None:
    for index, part in enumerate(FACE_PARTS):
        x, width = _face_slots[index]
        if index == EYE_LEFT:
            part = eyes[0]
        elif index == EYE_RIGHT:
            part = eyes[1]
        # 枠の幅の中央に置く
        draw_text(layer, FACE_LEFT + x + (width - advance(part)) / 2, FACE_TOP, part)


TAIL_TIP_X = BASE_X - 50
_fist_box = text_size("≡⊃")
FIST_WIDTH = (_fist_box[2] - _fist_box[0]) / SCALE


def draw_cat(frame: int) -> Image.Image:
    """猫の頭と手を描く。"""
    head = new_layer()
    punching = PUNCH_START <= frame < RECOIL_END - 6
    draw_text(head, EARS_LEFT, EARS_TOP, EARS)
    draw_face(head, EYES_PUNCH if punching else EYES_NORMAL)

    # 頭の傾き：振りかぶりで少し後ろへ、パンチで前へ
    if frame < WINDUP_START:
        tilt = 0.0
    elif frame < PUNCH_START:
        tilt = lerp(0, 6, ease_in_out((frame - WINDUP_START) / (PUNCH_START - WINDUP_START)))
    elif frame < HIT:
        tilt = lerp(6, -10, ease_in_out((frame - PUNCH_START) / (HIT - PUNCH_START)))
    elif frame < RECOIL_END:
        tilt = lerp(-10, 0, ease_in_out((frame - HIT) / (RECOIL_END - HIT)))
    else:
        tilt = 0.0
    pivot = (s(FACE_LEFT + FACE_WIDTH / 2), s(FACE_TOP + 40))
    head = head.rotate(tilt, resample=Image.Resampling.BICUBIC, center=pivot)

    paw = new_layer()
    rest_x, rest_y = FACE_RIGHT + 2, FACE_TOP - 4
    if frame < WINDUP_START or frame >= RECOIL_END:
        draw_text(paw, rest_x, rest_y, "∩")
    elif frame < PUNCH_START:
        t = ease_in_out((frame - WINDUP_START) / (PUNCH_START - WINDUP_START))
        draw_text(paw, rest_x - 6 * t, rest_y - 12 * t, "∩")
    elif frame < HIT:
        # 伸ばした手が魚のしっぽへ
        t = (frame - PUNCH_START) / (HIT - PUNCH_START)
        x = lerp(FACE_RIGHT - 30, TAIL_TIP_X - FIST_WIDTH + 4, t)
        draw_text(paw, x, FACE_TOP + 18, "≡⊃")
    elif frame < RECOIL_END - 6:
        # 打ったあと、手を引く（下絵の「⊂≡」と「//」）
        t = ease_in_out((frame - HIT) / (RECOIL_END - 6 - HIT))
        x = lerp(TAIL_TIP_X - FIST_WIDTH, FACE_RIGHT - 34, t)
        draw_text(paw, x, FACE_TOP + 20, "⊂≡")
        if t < 0.7:
            draw_text(paw, FACE_RIGHT - 6, FACE_TOP - 2, "//")
    else:
        t = ease_in_out((frame - (RECOIL_END - 6)) / 6)
        draw_text(paw, rest_x, lerp(FACE_TOP + 20, rest_y, t), "∩")

    return ImageChops.lighter(head, paw)


# ---------------------------------------------------------------- 魚の玩具


def spring_angle(frame: int) -> float:
    """ばねの傾き（度）。正で右（時計回り）。"""
    if frame < HIT:
        return 0.0
    if frame >= SETTLE_END:
        return 0.0
    t = (frame - HIT) / FPS
    angle = 55 * math.exp(-1.6 * t) * math.cos(2 * math.pi * 1.6 * t)
    # 最後は 0 へ確実に戻す
    fade = 1 - ease_in_out((frame - (SETTLE_END - 15)) / 15)
    return angle * fade


def rotate(point: tuple[float, float], degrees: float) -> tuple[float, float]:
    r = math.radians(degrees)
    x, y = point
    return (x * math.cos(r) - y * math.sin(r), x * math.sin(r) + y * math.cos(r))


def draw_toy(frame: int) -> Image.Image:
    layer = new_layer()
    draw = ImageDraw.Draw(layer)
    angle = spring_angle(frame)

    # 台
    draw.rectangle(
        (s(BASE_X - 34), s(BASE_TOP), s(BASE_X + 34), s(BASE_TOP + 24)),
        outline=255,
        width=LINE,
    )

    # ばね：根元は真上、先端は angle だけ傾いた二次ベジェ曲線に沿ってコイルを描く
    base = (BASE_X, BASE_TOP)
    top_offset = rotate((0, -SPRING_LENGTH), angle * 0.9)
    top = (base[0] + top_offset[0], base[1] + top_offset[1])
    control = (base[0], base[1] - SPRING_LENGTH * 0.55)

    def curve(u: float) -> tuple[tuple[float, float], tuple[float, float]]:
        x = (1 - u) ** 2 * base[0] + 2 * (1 - u) * u * control[0] + u * u * top[0]
        y = (1 - u) ** 2 * base[1] + 2 * (1 - u) * u * control[1] + u * u * top[1]
        dx = 2 * (1 - u) * (control[0] - base[0]) + 2 * u * (top[0] - control[0])
        dy = 2 * (1 - u) * (control[1] - base[1]) + 2 * u * (top[1] - control[1])
        length = math.hypot(dx, dy) or 1
        return (x, y), (dx / length, dy / length)

    turns = 4
    points = []
    steps = 160
    for i in range(steps + 1):
        u = i / steps
        (cx, cy), (tx, ty) = curve(u)
        nx, ny = -ty, tx
        phase = 2 * math.pi * turns * u
        radius = 9
        along = -5 * math.sin(phase)
        side = radius * math.cos(phase) * (1 if u > 0.02 else 0)
        points.append((s(cx + nx * side + tx * along), s(cy + ny * side + ty * along)))
    draw.line(points, fill=255, width=LINE, joint="curve")

    # 魚：ばねの先端を原点に、angle 分傾ける
    fish_angle = angle * 1.15

    def place(p: tuple[float, float]) -> tuple[float, float]:
        x, y = rotate(p, fish_angle)
        return (s(top[0] + x), s(top[1] + y))

    body = [(30 * math.cos(a), -22 + 20 * math.sin(a)) for a in (math.tau * i / 72 for i in range(73))]
    draw.line([place(p) for p in body], fill=255, width=LINE, joint="curve")
    tail = [(-30, -22), (-50, -38), (-50, -6), (-30, -22)]
    draw.line([place(p) for p in tail], fill=255, width=LINE, joint="curve")

    dizzy = HIT <= frame < HIT + 40
    if dizzy:
        for a, b in (((10, -32), (20, -22)), ((20, -32), (10, -22))):
            draw.line((place(a), place(b)), fill=255, width=LINE)
    else:
        ex, ey = place((15, -27))
        r = s(3.5)
        draw.ellipse((ex - r, ey - r, ex + r, ey + r), fill=255)

    return layer


# ---------------------------------------------------------------- 出力


def render(frame: int) -> Image.Image:
    mask = ImageChops.lighter(draw_cat(frame), draw_toy(frame))
    mask = mask.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)

    # 不透明度を ALPHA_LEVELS 段階にして、白一色のパレット PNG にする
    step = 255 / (ALPHA_LEVELS - 1)
    indexed = mask.point(lambda v: round(v / step))
    image = Image.frombytes("P", indexed.size, indexed.tobytes())
    image.putpalette([255, 255, 255] * ALPHA_LEVELS)
    image.info["transparency"] = bytes(round(i * step) for i in range(ALPHA_LEVELS))
    return image


def main() -> None:
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
    for old in OUTPUT_FOLDER.glob("animation_*.png"):
        old.unlink()
    for frame in range(FRAME_COUNT):
        path = OUTPUT_FOLDER / f"animation_{frame:03d}.png"
        image = render(frame)
        image.save(path, optimize=True, bits=3, transparency=image.info["transparency"])
        oxipng.optimize(path, level=6, deflate=oxipng.Deflaters.zopfli(15))


if __name__ == "__main__":
    main()
