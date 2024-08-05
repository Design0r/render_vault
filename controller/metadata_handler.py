import json
from pathlib import Path

from ..core import Logger


class MetadataHandler:
    default_metadata = {
        "name": "",
        "extension": "",
        "size": "",
        "path": "",
        "renderer": "",
        "tags": "",
        "notes": "",
    }

    @classmethod
    def load(cls, path: Path) -> dict:
        if not path.exists():
            cls.save(path, cls.default_metadata)
            return cls.load(path)

        with open(path, "r") as f:
            Logger.debug(f"Loading metadata for {path.stem}")
            return json.load(f)

    @classmethod
    def save(cls, path: Path, metadata: dict) -> None:
        with open(path, "w") as f:
            json.dump(metadata, f, indent=4)
            Logger.debug(f"Saving metadata for {path.stem}")
