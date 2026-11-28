"""公開する前に、公開物に直接響くものを確かめる（AviUtl2 は使わない）。

使い方:
    uv run python tools/check-release.py            # 版がそろっているか、個人のパスが無いか
    uv run python tools/check-release.py --tag v0.3.0  # あわせて、タグが版と同じか

確かめること:
    - pyproject.toml の版と、script/ の各スクリプトの --information の版が同じか
    - （--tag を渡したとき）タグが「v」＋版か
    - Git で管理しているファイルに、個人のパス（ユーザー名を含む絶対パス）が無いか
"""

import argparse
import re
import subprocess
import sys
import tomllib
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parent.parent
SCRIPT_DIR = REPOSITORY / "script"
SCRIPT_EXTENSIONS = (".obj2", ".anm2")

# --information の行の版（例: "--information:連番スロット v0.3.0（…）" の "0.3.0"）。
INFORMATION_VERSION = re.compile(r"^--information:.*?\bv(\d+\.\d+\.\d+)\b", re.MULTILINE)
# ユーザー名を含む絶対パス（Windows の Users フォルダの下、Linux・macOS の home・Users フォルダの下）。
PERSONAL_PATH = re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+[^\\/\s\"'`]+|/home/[^/\s\"'`]+|/Users/[^/\s\"'`]+")
# 中身を調べないファイル（画像など）。
BINARY_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico", ".zip"}


def read_version() -> str:
    with (REPOSITORY / "pyproject.toml").open("rb") as file:
        return tomllib.load(file)["project"]["version"]


def check_script_versions(version: str) -> list[str]:
    problems = []
    for path in sorted(SCRIPT_DIR.iterdir()):
        if path.suffix not in SCRIPT_EXTENSIONS:
            continue
        match = INFORMATION_VERSION.search(path.read_text(encoding="utf-8"))
        if match is None:
            problems.append(f"{path.name}: --information に版（vX.Y.Z）がありません")
        elif match.group(1) != version:
            problems.append(
                f"{path.name}: --information の版 {match.group(1)} が pyproject.toml の {version} と違います"
            )
    return problems


def check_tag(tag: str, version: str) -> list[str]:
    if tag != f"v{version}":
        return [f"タグ {tag} が pyproject.toml の版 v{version} と違います"]
    return []


def tracked_files() -> list[Path]:
    output = subprocess.run(
        ["git", "ls-files", "-z"], cwd=REPOSITORY, check=True, capture_output=True
    ).stdout.decode("utf-8")
    return [REPOSITORY / name for name in output.split("\0") if name]


def check_personal_paths() -> list[str]:
    problems = []
    this_script = Path(__file__).resolve()
    for path in tracked_files():
        if path.suffix.lower() in BINARY_EXTENSIONS or not path.is_file():
            continue
        if path.resolve() == this_script:
            # このスクリプト自身は、探す形（正規表現）を書いているので調べない。
            continue
        text = path.read_bytes().decode("utf-8", errors="replace")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if PERSONAL_PATH.search(line):
                relative = path.relative_to(REPOSITORY).as_posix()
                problems.append(f"{relative}:{line_number}: 個人のパスがあります")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tag", help="付けるタグ（例: v0.3.0）")
    arguments = parser.parse_args(argv)

    version = read_version()
    problems = check_script_versions(version)
    if arguments.tag is not None:
        problems += check_tag(arguments.tag, version)
    problems += check_personal_paths()

    if problems:
        for problem in problems:
            print(problem, file=sys.stderr)
        return 1
    print(f"v{version}: 問題ありません")
    return 0


if __name__ == "__main__":
    sys.exit(main())
