import shutil
import sys
from pathlib import Path
from subprocess import Popen
from typing import Union

from . import Logger


def create_folder(path: Union[str, Path]) -> None:
    if not path:
        Logger.error(f"can't create folder, path: {path} is invalid")
        return

    if isinstance(path, str):
        path = Path(path)

    if path.exists():
        Logger.error(f"can't create folder, path: {path} already exists")
        return

    try:
        path.mkdir()
    except Exception as e:
        Logger.exception(e)

    return


def remove_folder(path: Union[str, Path]) -> None:
    if not path:
        Logger.error(f"can't delete folder, path: {path} is invalid")
        return

    if isinstance(path, str):
        path = Path(path)

    if not path.exists():
        Logger.error(f"can't delete folder, path: {path} does not exist")
        return

    try:
        shutil.rmtree(path)
    except Exception as e:
        Logger.exception(e)

    return


def open_dir(path: Union[str, Path]) -> None:
    if not path:
        Logger.error(f"can't open path, {path} does not exist")

    if isinstance(path, str):
        path = Path(path)

    if not path.exists():
        Logger.error(f"can't open path, {path} does not exist")
        return

    if sys.platform == "darwin":
        with Popen(["open", path]):
            pass
    elif sys.platform == "win32":
        with Popen(f"explorer {path}"):
            pass
