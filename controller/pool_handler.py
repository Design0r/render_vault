import shutil
from pathlib import Path
from typing import Generator, Optional, Protocol

from ..core import Logger, fs
from . import db
from .api_handler import APIHandler

THUMBNAIL_EXTENSTIONS = (".png", ".jpg", ".jpeg")
MODEL_EXTENSIONS = (".mb", ".ma", ".fbx", ".obj")
MATERIAL_EXTENSIONS = (".mb", ".ma")
HDRI_EXTENSIONS = (".hdr", ".exr")
UTILITY_EXTENSTIONS = (".mb", ".mb", ".py", ".json")


class PoolHandler(Protocol):
    def create_pool(self, name: str, path: str) -> None: ...

    def delete_pool(self, name: str, path: str) -> None: ...

    @staticmethod
    def open_pool_dir(path: str) -> None: ...

    @staticmethod
    def get_assets_and_thumbnails(
        path: str,
    ) -> Generator[tuple[str, Path, Optional[str], int], None, None]: ...

    @staticmethod
    def delete_asset(path: Path) -> None: ...


class MaterialPoolHandler:
    __slots__ = "_api_handler"

    def __init__(self):
        self._api_handler = APIHandler()

    def create_pool(self, name: str, path: str):
        root_path = Path(path, "MaterialPool")
        fs.create_folder(root_path)
        fs.create_folder(root_path / "Materials")
        fs.create_folder(root_path / "Textures")
        fs.create_folder(root_path / "Thumbnails")
        fs.create_folder(root_path / "Metadata")

        self._api_handler.create(name, path, db.Tables.MATERIALS)

        Logger.info(f'created new material pool "{name}" in {path}')

    def delete_pool(self, name: str, path: str):
        root_path = Path(path, "MaterialPool")
        fs.remove_folder(root_path)

        self._api_handler.delete(name, path, db.Tables.MATERIALS)

        Logger.info(f"deleted current material pool in {path}")

    @staticmethod
    def open_pool_dir(path: str):
        if not path:
            Logger.error(f"can't open folder, path: {path} is invalid")
            return

        pool_path = Path(path, "MaterialPool")
        fs.open_dir(pool_path)

    @staticmethod
    def get_assets_and_thumbnails(
        path: str,
    ) -> Generator[tuple[str, Path, Optional[str], int], None, None]:
        pool_path = Path(path, "MaterialPool")
        materials_path = pool_path / "Materials"
        thumbnail_path = pool_path / "Thumbnails"

        thumbnail_files = {
            file.stem: str(file)
            for file in thumbnail_path.iterdir()
            if file.suffix.lower() in THUMBNAIL_EXTENSTIONS
        }
        asset_files = sorted(
            (
                file
                for file in materials_path.iterdir()
                if file.suffix.lower() in MATERIAL_EXTENSIONS
            ),
            key=lambda x: x.name.lower(),
        )

        for asset_file in asset_files:
            asset_name = asset_file.stem
            asset_path = materials_path / asset_file
            asset_size = asset_path.stat().st_size
            thumbnail_path = thumbnail_files.get(asset_name)

            yield asset_name, asset_path, thumbnail_path, asset_size

    @staticmethod
    def delete_asset(path: Path):
        if not path:
            Logger.debug(f"can't delete asset, path is: {path}")
            return

        if not path.exists():
            Logger.error(f"can't delete asset, path does not exist: {path}")
            return

        thumbnails_path = path.parent.parent / "Thumbnails"
        textures_path = path.parent.parent / "Textures"
        archive_path = path.parent.parent / "Archive"
        metadata_path = path.parent.parent / "Metadata"

        asset_name = path.stem

        thumbnails_to_delete = (
            thumbnails_path / i
            for i in thumbnails_path.iterdir()
            if i.stem == asset_name
        )

        textures_to_delete = (
            textures_path / i for i in textures_path.iterdir() if i.stem == asset_name
        )

        archive_to_delete = (
            archive_path / i for i in archive_path.iterdir() if i.stem == asset_name
        )

        metadata_to_delete = (
            (metadata_path / i for i in metadata_path.iterdir() if i.stem == asset_name)
            if metadata_path.exists()
            else []
        )

        try:
            for thumb in thumbnails_to_delete:
                thumb.unlink()
                Logger.info(f"deleted {thumb}")

            for tex in textures_to_delete:
                fs.remove_folder(tex)
                Logger.info(f"deleted {tex}")

            for archive in archive_to_delete:
                fs.remove_folder(archive)
                Logger.info(f"deleted {archive}")

            for metadata in metadata_to_delete:
                metadata.unlink()
                Logger.info(f"deleted {metadata}")

            path.unlink()
            Logger.info(f"deleted {path}")
        except Exception as e:
            Logger.exception(e)

    @staticmethod
    def get_archived_versions(material_path: Path) -> dict[str, Path]:
        archive_path = material_path.parent.parent / "Archive"
        files = {i.stem: i for i in archive_path.iterdir()}
        return files

    @staticmethod
    def _get_latest_archive_version(archive_path: Path) -> str:
        numbers = (int(str(i.stem).split("_")[-1]) for i in archive_path.iterdir())
        version = max(numbers) + 1 if numbers else 1
        return str(version).zfill(3)

    def archive_asset(self, path: Path):
        name = path.stem
        archive_folder = path.parent.parent / "Archive" / name
        archive_folder.mkdir(parents=True, exist_ok=True)
        archive_version = self._get_latest_archive_version(archive_folder)
        archive = archive_folder / f"{name}_{archive_version}{path.suffix}"

        shutil.copy2(path, archive)

        Logger.info(f"archived {name} to {archive}")


class ModelPoolHandler:
    __slots__ = "_api_handler"

    def __init__(self):
        self._api_handler = APIHandler()

    def create_pool(self, name: str, path: str):
        root_path = Path(path, "ModelPool")
        fs.create_folder(root_path)
        fs.create_folder(root_path / "Models")
        fs.create_folder(root_path / "Textures")
        fs.create_folder(root_path / "Thumbnails")
        fs.create_folder(root_path / "Archive")
        fs.create_folder(root_path / "Metadata")

        self._api_handler.create(name, path, db.Tables.MODELS)

        Logger.info(f'created new model pool "{name}" in {path}')

    def delete_pool(self, name: str, path: str):
        root_path = Path(path, "ModelPool")
        fs.remove_folder(root_path)

        self._api_handler.delete(name, path, db.Tables.MODELS)

        Logger.info(f'deleted current model pool "{name}" in {path}')

    @staticmethod
    def open_pool_dir(path: str):
        if not path:
            Logger.error(f"can't open folder, path: {path} is invalid")
            return

        pool_path = Path(path, "ModelPool")
        fs.open_dir(pool_path)

    @staticmethod
    def get_assets_and_thumbnails(
        path: str,
    ) -> Generator[tuple[str, Path, Optional[str], int], None, None]:
        pool_path = Path(path, "ModelPool")
        model_path = pool_path / "Models"
        thumbnail_path = pool_path / "Thumbnails"

        thumbnail_files = {
            file.stem: str(file)
            for file in thumbnail_path.iterdir()
            if file.suffix.lower() in THUMBNAIL_EXTENSTIONS
        }
        asset_files = (
            file
            for file in model_path.iterdir()
            if file.suffix.lower() in MODEL_EXTENSIONS
        )

        for asset_file in sorted(asset_files, key=lambda x: x.name.lower()):
            asset_name = asset_file.stem
            asset_path = model_path / asset_file
            asset_size = asset_path.stat().st_size
            thumbnail_path = thumbnail_files.get(asset_name)

            yield asset_name, asset_path, thumbnail_path, asset_size

    @staticmethod
    def delete_asset(path: Path):
        if not path:
            Logger.debug(f"can't delete asset, path is: {path}")
            return

        if not path.exists():
            Logger.error(f"can't delete asset, path does not exist: {path}")
            return

        thumbnails_path = path.parent.parent / "Thumbnails"
        textures_path = path.parent.parent / "Textures"
        archive_path = path.parent.parent / "Archive"
        metadata_path = path.parent.parent / "Metadata"
        asset_name = path.stem

        thumbnails_to_delete = (
            thumbnails_path / i
            for i in thumbnails_path.iterdir()
            if i.stem == asset_name
        )

        textures_to_delete = (
            textures_path / i for i in textures_path.iterdir() if i.stem == asset_name
        )

        archive_to_delete = (
            archive_path / i for i in archive_path.iterdir() if i.stem == asset_name
        )

        metadata_to_delete = (
            (metadata_path / i for i in metadata_path.iterdir() if i.stem == asset_name)
            if metadata_path.exists()
            else []
        )

        try:
            for thumb in thumbnails_to_delete:
                thumb.unlink()
                Logger.info(f"deleted {thumb}")

            for tex in textures_to_delete:
                fs.remove_folder(tex)
                Logger.info(f"deleted {tex}")

            for archive in archive_to_delete:
                fs.remove_folder(archive)
                Logger.info(f"deleted {archive}")

            for metadata in metadata_to_delete:
                metadata.unlink()
                Logger.info(f"deleted {metadata}")

            path.unlink()
            Logger.info(f"deleted {path}")
        except Exception as e:
            Logger.exception(e)

    @staticmethod
    def get_archived_versions(model_path: Path) -> dict[str, Path]:
        archive_path = model_path.parent.parent / "Archive"
        files = {i.stem: i for i in archive_path.iterdir()}
        return files

    @staticmethod
    def _get_latest_archive_version(archive_path: Path) -> str:
        numbers = [int(str(i.stem).split("_")[-1]) for i in archive_path.iterdir()]
        version = max(numbers) + 1 if numbers else 1
        Logger.debug(f"{version=}")
        return str(version).zfill(3)

    def archive_asset(self, path: Path):
        name = path.stem
        archive_folder = path.parent.parent / "Archive" / name
        archive_folder.mkdir(parents=True, exist_ok=True)
        archive_version = self._get_latest_archive_version(archive_folder)
        archive = archive_folder / f"{name}_{archive_version}{path.suffix}"

        shutil.copy2(path, archive)

        Logger.info(f"archived {name} to {archive}")


class HDRIPoolHandler:
    __slots__ = "_api_handler"

    def __init__(self):
        self._api_handler = APIHandler()

    def create_pool(self, name: str, path: str):
        root_path = Path(path, "HDRIPool")
        fs.create_folder(root_path)
        fs.create_folder(root_path / "HDRIs")
        fs.create_folder(root_path / "Thumbnails")
        fs.create_folder(root_path / "Metadata")

        self._api_handler.create(name, path, db.Tables.HDRIS)

        Logger.info(f"created new hdri pool in {path}")

    def delete_pool(self, name: str, path: str):
        root_path = Path(path, "HDRIPool")
        fs.remove_folder(root_path)

        self._api_handler.delete(name, path, db.Tables.HDRIS)

        Logger.info(f"deleted current hdri model pool in {path}")

    @staticmethod
    def open_pool_dir(path: str):
        if not path:
            Logger.error(f"can't open folder, path: {path} is invalid")
            return

        pool_path = Path(path, "HDRIPool")
        fs.open_dir(pool_path)

    @staticmethod
    def get_assets_and_thumbnails(
        path: str,
    ) -> Generator[tuple[str, Path, Optional[str], int], None, None]:
        pool_path = Path(path, "HDRIPool")
        hdri_path = pool_path / "HDRIs"
        thumbnail_path = pool_path / "Thumbnails"

        thumbnail_files = {
            file.stem: str(file)
            for file in thumbnail_path.iterdir()
            if file.suffix.lower() in THUMBNAIL_EXTENSTIONS
        }
        asset_files = (
            file
            for file in hdri_path.iterdir()
            if file.suffix.lower() in HDRI_EXTENSIONS
        )

        for asset_file in sorted(asset_files, key=lambda x: x.name.lower()):
            asset_name: str = asset_file.stem
            asset_path: Path = hdri_path / asset_file
            asset_size: int = asset_path.stat().st_size
            thumbnail = thumbnail_files.get(asset_name)

            yield asset_name, asset_path, thumbnail, asset_size

    @staticmethod
    def delete_asset(path: Path):
        if not path:
            Logger.debug(f"can't delete asset, path is: {path}")
            return

        if not path.exists():
            Logger.error(f"can't delete asset, path does not exist: {path}")
            return

        thumbnails_path = path.parent.parent.resolve() / "Thumbnails"
        metadata_path = path.parent.parent / "Metadata"
        asset_name = path.stem

        thumbnails_to_delete = [
            thumbnails_path / i
            for i in thumbnails_path.iterdir()
            if i.stem == asset_name
        ]

        metadata_to_delete = (
            [metadata_path / i for i in metadata_path.iterdir() if i.stem == asset_name]
            if metadata_path.exists()
            else []
        )

        try:
            for thumb in thumbnails_to_delete:
                thumb.unlink()
                Logger.info(f"deleted {thumb}")

            for metadata in metadata_to_delete:
                metadata.unlink()
                Logger.info(f"deleted {metadata}")

            path.unlink()
            Logger.info(f"deleted {path}")
        except Exception as e:
            Logger.exception(e)


class LightsetPoolHandler:
    __slots__ = "_api_handler"

    def __init__(self):
        self._api_handler = APIHandler()

    def create_pool(self, name: str, path: str):
        root_path = Path(path, "LightsetPool")
        fs.create_folder(root_path)
        fs.create_folder(root_path / "Lightsets")
        fs.create_folder(root_path / "Textures")
        fs.create_folder(root_path / "Thumbnails")
        fs.create_folder(root_path / "Metadata")

        self._api_handler.create(name, path, db.Tables.LIGHTSETS)

        Logger.info(f"created new lightset pool in {path}")

    def delete_pool(self, name: str, path: str):
        root_path = Path(path, "LightsetPool")
        fs.remove_folder(root_path)

        self._api_handler.delete(name, path, db.Tables.LIGHTSETS)

        Logger.info(f"deleted current lightset model pool in {path}")

    @staticmethod
    def open_pool_dir(path: str):
        if not path:
            Logger.error(f"can't open folder, path: {path} is invalid")
            return

        pool_path = Path(path, "LightsetPool")
        fs.open_dir(pool_path)

    @staticmethod
    def get_assets_and_thumbnails(
        path: str,
    ) -> Generator[tuple[str, Path, Optional[str], int], None, None]:
        pool_path = Path(path, "LightsetPool")
        ls_path = pool_path / "Lightsets"
        thumbnail_path = pool_path / "Thumbnails"

        thumbnail_files = {
            file.stem: str(file)
            for file in thumbnail_path.iterdir()
            if file.suffix.lower() in MODEL_EXTENSIONS
        }
        asset_files = (
            file
            for file in ls_path.iterdir()
            if file.suffix.lower() in MODEL_EXTENSIONS
        )

        for asset_file in sorted(asset_files, key=lambda x: x.name.lower()):
            asset_name = asset_file.stem
            asset_path = ls_path / asset_file
            asset_size = asset_path.stat().st_size
            thumbnail_path = thumbnail_files.get(asset_name)

            yield asset_name, asset_path, thumbnail_path, asset_size

    @staticmethod
    def delete_asset(path: Path):
        if not path:
            Logger.debug(f"can't delete asset, path is: {path}")
            return

        if not path.exists():
            Logger.error(f"can't delete asset, path does not exist: {path}")
            return

        thumbnails_path = path.parent.parent / "Thumbnails"
        archive_path = path.parent.parent / "Archive"
        metadata_path = path.parent.parent / "Metadata"
        asset_name = path.stem

        thumbnails_to_delete = [
            thumbnails_path / i
            for i in thumbnails_path.iterdir()
            if i.stem == asset_name
        ]

        archive_to_delete = [
            archive_path / i for i in archive_path.iterdir() if i.stem == asset_name
        ]

        metadata_to_delete = (
            [metadata_path / i for i in metadata_path.iterdir() if i.stem == asset_name]
            if metadata_path.exists()
            else []
        )

        try:
            for thumb in thumbnails_to_delete:
                thumb.unlink()
                Logger.info(f"deleted {thumb}")

            for archive in archive_to_delete:
                fs.remove_folder(archive)
                Logger.info(f"deleted {archive}")

            for metadata in metadata_to_delete:
                metadata.unlink()
                Logger.info(f"deleted {metadata}")

            path.unlink()
            Logger.info(f"deleted {path}")
        except Exception as e:
            Logger.exception(e)

    @staticmethod
    def get_archived_versions(model_path: Path) -> dict[str, Path]:
        archive_path = model_path.parent.parent / "Archive"
        files = {i.stem: i for i in archive_path.iterdir()}
        return files

    @staticmethod
    def _get_latest_archive_version(archive_path: Path) -> str:
        numbers = [int(str(i.stem).split("_")[-1]) for i in archive_path.iterdir()]
        version = max(numbers) + 1 if numbers else 1
        Logger.debug(f"{version=}")
        return str(version).zfill(3)

    def archive_asset(self, path: Path):
        name = path.stem
        archive_folder = path.parent.parent / "Archive" / name
        archive_folder.mkdir(parents=True, exist_ok=True)
        archive_version = self._get_latest_archive_version(archive_folder)
        archive = archive_folder / f"{name}_{archive_version}{path.suffix}"

        shutil.copy2(path, archive)

        Logger.info(f"archived {name} to {archive}")


class UtilityPoolHandler:
    def create_pool(self, name: str, path: str):
        raise NotImplementedError

    def delete_pool(self, name: str, path: str):
        raise NotImplementedError

    @staticmethod
    def open_pool_dir(path: str):
        if not path:
            Logger.error(f"can't open folder, path: {path} is invalid")
            return

        pool_path = Path(path, "UtilityPool")
        fs.open_dir(pool_path)

    @staticmethod
    def get_assets_and_thumbnails(
        path: str,
    ) -> Generator[tuple[str, Path, Optional[str], int], None, None]:
        util_folder = Path(__file__).parent.parent / "settings" / "utility_settings"
        asset_files = (
            file
            for file in util_folder.iterdir()
            if file.suffix.lower() in UTILITY_EXTENSTIONS
        )

        for asset_file in asset_files:
            asset_name = asset_file.stem
            asset_path = util_folder / asset_file
            asset_size = asset_path.stat().st_size

            yield asset_name, asset_path, None, asset_size

    @staticmethod
    def delete_asset(path: Path):
        raise NotImplementedError
