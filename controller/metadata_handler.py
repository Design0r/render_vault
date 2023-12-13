from email.policy import default
import json
from pathlib import Path


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
    def load_metadata(cls, path: Path) -> dict:
        if not path.exists():
            cls.save_metadata(path, cls.default_metadata)
            return cls.load_metadata(path)

        with open(path, "r") as f:
            return json.load(f)

    @classmethod
    def save_metadata(cls, path: Path, metadata: dict) -> None:
        with open(path, "w") as f:
            json.dump(metadata, f, indent=4)
