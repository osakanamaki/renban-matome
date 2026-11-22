import shutil
from pathlib import Path

import pytest

REPOSITORY = Path(__file__).parent.parent
SCRIPT = REPOSITORY / "script"

# 利用者がファイル名を変えても動くことを確かめるための、改名した複製の名前。
RENAMED_EFFECT = "連番まとめ_改名"


@pytest.fixture(scope="session")
def aviutl2_scripts(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    renamed = tmp_path_factory.mktemp("renamed")
    shutil.copyfile(SCRIPT / "連番まとめ.anm2", renamed / f"{RENAMED_EFFECT}.anm2")
    return {
        "renban-matome-dev": SCRIPT,
        "renban-matome-test": REPOSITORY / "tests" / "scripts",
        "renban-matome-renamed": renamed,
    }


@pytest.fixture(scope="session")
def renamed_effect() -> str:
    """ファイル名を変えた「連番まとめ」の効果名。"""
    return RENAMED_EFFECT
