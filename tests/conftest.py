import shutil
from pathlib import Path

import pytest

REPOSITORY = Path(__file__).parent.parent
SCRIPT = REPOSITORY / "script"

BASE_FILE = "連番まとめ（値）.obj2"
SLOT_FILE = "連番スロット.anm2"

# 利用者がファイル名を変えても動くことを確かめるための、改名した複製の名前。
RENAMED_BASE = "連番まとめ（値）_改名"
RENAMED_SLOT = "連番スロット_改名"


@pytest.fixture(scope="session")
def aviutl2_scripts(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    renamed = tmp_path_factory.mktemp("renamed")
    shutil.copyfile(SCRIPT / BASE_FILE, renamed / f"{RENAMED_BASE}.obj2")
    shutil.copyfile(SCRIPT / SLOT_FILE, renamed / f"{RENAMED_SLOT}.anm2")
    return {
        "renban-matome-dev": SCRIPT,
        "renban-matome-test": REPOSITORY / "tests" / "scripts",
        "renban-matome-renamed": renamed,
    }


@pytest.fixture(scope="session")
def renamed_names() -> tuple[str, str]:
    """ファイル名を変えた土台と連番スロットの名前。"""
    return RENAMED_BASE, RENAMED_SLOT
