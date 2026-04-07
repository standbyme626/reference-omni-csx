import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
SERVICE_ROOT = Path(__file__).resolve().parents[1]


def _prepend_path(path: Path) -> None:
    path_str = str(path)
    if path_str in sys.path:
        sys.path.remove(path_str)
    sys.path.insert(0, path_str)


def _purge_app_modules() -> None:
    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            sys.modules.pop(name, None)


_purge_app_modules()
_prepend_path(REPO_ROOT)
_prepend_path(SERVICE_ROOT)


def _activate_service_imports() -> None:
    _purge_app_modules()
    _prepend_path(REPO_ROOT)
    _prepend_path(SERVICE_ROOT)


def pytest_collect_file(file_path, parent):
    _activate_service_imports()
    return None


def pytest_runtest_setup(item):
    _activate_service_imports()
