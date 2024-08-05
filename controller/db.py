from __future__ import annotations

import sqlite3
from enum import Enum, auto
from pathlib import Path
from typing import NamedTuple

from ..core import Logger
from .settings import SettingsManager


class DBSchema(NamedTuple):
    name: str
    path: Path

    @classmethod
    def fields(cls) -> str:
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


def create_connection() -> sqlite3.Connection:
    path = SettingsManager.DB_PATH

    conn = sqlite3.connect(path)

    conn.executescript("""
        PRAGMA synchronous = NORMAL;
        PRAGMA journal_mode = WAL;
        PRAGMA temp_store = MEMORY;
        PRAGMA cache_size = 10000;
    """)

    return conn


def close_connection(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA optimize;")
    conn.close()


def insert(table: Tables, data: DBSchema) -> None:
    if not isinstance(data, DBSchema):
        Logger.error(f"invalid db schema. expected: {DBSchema}, got {type(data)}")
        return

    conn = create_connection()
    try:
        conn.execute(
            f"INSERT INTO {table.name}{data.fields()} VALUES (?, ?);",
            (data.name, str(data.path)),
        )
        conn.commit()
    except Exception as e:
        Logger.exception(e)
    finally:
        close_connection(conn)


def select(table: Tables) -> dict[str, str]:
    data = {}
    conn = create_connection()
    try:
        cursor = conn.execute(f"SELECT name, path FROM {table.name};")
        p = {name: path for name, path in cursor.fetchall()}
        data = dict(sorted(p.items()))
    except Exception as e:
        Logger.exception(e)
    finally:
        close_connection(conn)

    return data


def delete(table: Tables, data: DBSchema) -> None:
    conn = create_connection()
    try:
        conn.execute(f"DELETE FROM {table.name} WHERE NAME = '{data.name}';")
        conn.commit()
    except Exception as e:
        Logger.exception(e)
    finally:
        close_connection(conn)


def select_all() -> tuple[dict, dict, dict, dict]:
    data = []
    conn = create_connection()
    try:
        for table in Tables.members():
            cursor = conn.execute(f"SELECT name, path FROM {table}")
            p = {name: path for name, path in cursor.fetchall()}
            data.append(dict(sorted(p.items())))

    except Exception as e:
        Logger.exception(e)
    finally:
        close_connection(conn)

    return tuple(data)


def run_migration(data: dict[str, dict[str, str]]) -> None:
    for pool, entrys in data.items():
        for name, path in entrys.items():
            schema = DBSchema(name, Path(path))
            insert(pool.upper(), schema)


def init_db():
    path = SettingsManager.DB_PATH
    if path.exists():
        Logger.debug("DB already exists.")
        return

    path.parent.mkdir(exist_ok=True)

    conn = create_connection()
    try:
        tables = Tables.members()
        for table in tables:
            conn.execute(
                f"""CREATE TABLE IF NOT EXISTS {table}
                (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                NAME CHAR(128) NOT NULL,
                PATH TEXT NOT NULL);"""
            )

        conn.commit()

        Logger.debug(f"Created DB {path.stem}")
    except Exception as e:
        Logger.exception(e)
    finally:
        close_connection(conn)

    """
    with open(Path(__file__).parent / "sql.json") as file:
        data = json.load(file)
        run_migration(data)
    """
