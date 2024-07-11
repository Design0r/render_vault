from __future__ import annotations
from enum import Enum, auto
from pathlib import Path
import sqlite3
from typing import NamedTuple
import render_vault.controller.logger as logger
import render_vault.controller.settings as settings


class DBSchema(NamedTuple):
    name: str
    path: Path

    @classmethod
    def fields(cls):
        return f"({','.join([f.upper() for f in cls._fields])})"

    @classmethod
    def from_db(cls, data: list[tuple]) -> list[DBSchema]:
        return [DBSchema(*x) for x in data]


class Tables(Enum):
    MATERIALS = auto()
    MODELS = auto()
    HDRIS = auto()
    LIGHTSETS = auto()

    @classmethod
    def members(cls) -> tuple[str, ...]:
        return tuple(cls.__members__)


def insert(table: Tables, data: DBSchema):
    if not isinstance(data, DBSchema):
        logger.Logger.error(
            f"invalid db schema. expected: {DBSchema}, got {type(data)}"
        )
        return

    path = settings.SettingsManager.DB_PATH
    try:
        conn = sqlite3.connect(path)
        conn.execute(
            f"INSERT INTO {table.name}{data.fields()} VALUES (?, ?);",
            (data.name, str(data.path)),
        )
        conn.commit()
    except Exception as e:
        logger.Logger.exception(e)
    finally:
        conn.close()


def select(table: Tables) -> dict:
    path = settings.SettingsManager.DB_PATH
    data = {}
    try:
        conn = sqlite3.connect(path)
        cursor = conn.execute(f"SELECT name, path FROM {table.name};")
        p = {name: path for name, path in cursor.fetchall()}
        data = dict(sorted(p.items()))
    except Exception as e:
        logger.Logger.exception(e)
    finally:
        conn.close()

    return data


def delete(table: Tables, data: DBSchema):
    path = settings.SettingsManager.DB_PATH
    try:
        conn = sqlite3.connect(path)
        print(table, data)
        conn.execute(f"DELETE FROM {table.name} WHERE NAME = '{data.name}';")
        conn.commit()
    except Exception as e:
        logger.Logger.exception(e)
    finally:
        conn.close()


def select_all() -> tuple[dict, dict, dict, dict]:
    path = settings.SettingsManager.DB_PATH
    data = []
    try:
        conn = sqlite3.connect(path)
        for table in Tables.members():
            cursor = conn.execute(f"SELECT name, path FROM {table}")
            p = {name: path for name, path in cursor.fetchall()}
            data.append(dict(sorted(p.items())))

    except Exception as e:
        logger.Logger.exception(e)
    finally:
        conn.close()

    return tuple(data)


def run_migration(data: dict[str, dict[str, str]]):
    for pool, entrys in data.items():
        for name, path in entrys.items():
            schema = DBSchema(name, Path(path))
            insert(pool.upper(), schema)


def init_db():
    path = settings.SettingsManager.DB_PATH
    if path.exists:
        logger.Logger.debug("DB already exists.")
        return

    try:
        conn = sqlite3.connect(path)

        tables = Tables.members()
        for table in tables:
            conn.execute(
                f"""CREATE TABLE {table}
                (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                NAME CHAR(128) NOT NULL,
                PATH TEXT NOT NULL);"""
            )

        conn.commit()

        logger.Logger.debug(f"Created DB {path.stem}")
    except Exception as e:
        logger.Logger.exception(e)
    finally:
        conn.close()

    """
    with open(Path(__file__).parent / "sql.json") as file:
        data = json.load(file)
        run_migration(data)
    """
