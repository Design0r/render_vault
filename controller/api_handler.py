from pathlib import Path
from typing import Union

from . import db


class APIHandler:
    @staticmethod
    def create(name: str, path: Union[str, Path], table: db.Tables) -> int:
        if isinstance(path, str):
            path = Path(path)
        data = db.DBSchema(name, path)
        db.insert(table, data)

    @staticmethod
    def delete(name: str, path: Union[str, Path], table: db.Tables) -> int:
        if isinstance(path, str):
            path = Path(path)

        data = db.DBSchema(name, Path(path))
        db.delete(table, data)


def get_all_pools() -> tuple[dict, dict, dict, dict]:
    return db.select_all()
