from pathlib import Path
from typing import Protocol


from . import db


class APIHandler(Protocol):
    @staticmethod
    def create(name: str, path: str) -> int: ...

    @staticmethod
    def delete(name: str, path: str) -> int: ...


class MaterialAPIHandler:
    @staticmethod
    def create(name: str, path: str):
        data = db.DBSchema(name, Path(path))
        db.insert(db.Tables.MATERIALS, data)

    @staticmethod
    def delete(name: str, path: str):
        data = db.DBSchema(name, Path(path))
        db.delete(db.Tables.MATERIALS, data)


class ModelAPIHandler:
    @staticmethod
    def create(name: str, path: str):
        data = db.DBSchema(name, Path(path))
        db.insert(db.Tables.MODELS, data)

    @staticmethod
    def delete(name: str, path: str):
        data = db.DBSchema(name, Path(path))
        db.delete(db.Tables.MODELS, data)


class HDRIAPIHandler:
    @staticmethod
    def create(name: str, path: str):
        data = db.DBSchema(name, Path(path))
        db.insert(db.Tables.HDRIS, data)

    @staticmethod
    def delete(name: str, path: str):
        data = db.DBSchema(name, Path(path))
        db.delete(db.Tables.HDRIS, data)


class LightsetAPIHandler:
    @staticmethod
    def create(name: str, path: str):
        data = db.DBSchema(name, Path(path))
        db.insert(db.Tables.LIGHTSETS, data)

    @staticmethod
    def delete(name: str, path: str):
        data = db.DBSchema(name, Path(path))
        db.delete(db.Tables.LIGHTSETS, data)


def get_all_pools() -> tuple[dict, dict, dict, dict]:
    return db.select_all()
