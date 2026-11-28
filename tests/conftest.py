import shutil
from pathlib import Path

import pytest
from aviutl2_pyrrhulina import Package

REPOSITORY = Path(__file__).parent.parent
SCRIPT = REPOSITORY / "script"
# AviUtl2 Catalog に登録するインストール手順（カタログの installer.install と同じ形）。
INSTALL_JSON = REPOSITORY / "install.json"

BASE_FILE = "連番まとめ（値）.obj2"
SLOT_FILE = "連番スロット.anm2"

# 利用者がファイル名を変えても動くことを確かめるための、改名した複製の名前。
RENAMED_BASE = "連番まとめ（値）_改名"
RENAMED_SLOT = "連番スロット_改名"


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--package",
        default=None,
        help="配布物（.au2pkg.zip）。指定すると、script/ の代わりに install.json の手順で置いて検査する",
    )


@pytest.fixture(scope="session")
def aviutl2_package(pytestconfig: pytest.Config) -> Package | None:
    archive = pytestconfig.getoption("--package")
    if archive is None:
        return None
    return Package.from_json(Path(archive), INSTALL_JSON)


@pytest.fixture(scope="session")
def aviutl2_scripts(
    tmp_path_factory: pytest.TempPathFactory, aviutl2_package: Package | None
) -> dict[str, Path]:
    renamed = tmp_path_factory.mktemp("renamed")
    shutil.copyfile(SCRIPT / BASE_FILE, renamed / f"{RENAMED_BASE}.obj2")
    shutil.copyfile(SCRIPT / SLOT_FILE, renamed / f"{RENAMED_SLOT}.anm2")
    scripts = {
        "renban-matome-test": REPOSITORY / "tests" / "scripts",
        "renban-matome-renamed": renamed,
    }
    # 配布物で検査するときは、同じ名前のスクリプトが二重にならないよう、script/ は置かない。
    if aviutl2_package is None:
        scripts["renban-matome-dev"] = SCRIPT
    return scripts


@pytest.fixture(scope="session")
def renamed_names() -> tuple[str, str]:
    """ファイル名を変えた土台と連番スロットの名前。"""
    return RENAMED_BASE, RENAMED_SLOT
