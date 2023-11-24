from typing import Generator, Optional, Protocol
from subprocess import Popen
import sys
from pathlib import Path
import shutil
import render_vault.controller.core as core
import render_vault.controller.logger as logger
import render_vault.controller.api_handler as api

THUMBNAIL_EXTENSTIONS = ("*.png", "*.jpg", "*.jpeg")
MODEL_EXTENSIONS = ("*.mb", "*.ma", "*.fbx", "*.obj")
MATERIAL_EXTENSIONS = ("*.mb", "*.ma")
HDRI_EXTENSIONS = ("*.hdr", "*.exr")
UTILITY_EXTENSTIONS = ("*.mb", "*.mb", "*.py", "*.json")


class PoolHandler(Protocol):
    def create_pool(self, name: str, path: str) -> None:
        ...

    def delete_pool(self, name: str, path: str) -> None:
        ...

    @staticmethod
    def open_pool_dir(path: str) -> None:
        ...

    @staticmethod
    def get_assets_and_thumbnails(
        path: str,
    ) -> Generator[tuple[str, Path, Optional[str], int], None, None]:
        ...

    @staticmethod
    def delete_asset(path: Path) -> None:
        ...


class MaterialPoolHandler:
    __slots__ = "_api_handler"

    def __init__(self, api_handler: api.APIHandler):
        self._api_handler = api_handler

    def create_pool(self, name: str, path: str):
        root_path = Path(path, "MaterialPool")
        core.create_folder(root_path)
        core.create_folder(root_path / "Materials")
        core.create_folder(root_path / "Textures")
        core.create_folder(root_path / "Thumbnails")

        self._api_handler.create(name, path)

        logger.Logger.info(f"created new material pool in {path}")

    def delete_pool(self, name: str, path: str):
        root_path = Path(path, "MaterialPool")
        core.remove_folder(root_path)

        self._api_handler.delete(name, path)

        logger.Logger.info(f"deleted current material pool in {path}")

    @staticmethod
    def open_pool_dir(path: str):
        if not path:
            logger.Logger.error(f"can't open folder, path: {path} is invalid")
            return

        pool_path = Path(path, "MaterialPool")

        if not pool_path.exists():
            logger.Logger.error(f"can't open folder, path: {path} does not exist")
            return

        if sys.platform == "darwin":
            with Popen(["open", path]):
                pass
        elif sys.platform == "win32":
            with Popen(f"explorer {pool_path}"):
                pass

    @staticmethod
    def get_assets_and_thumbnails(
        path: str,
    ) -> Generator[tuple[str, Path, Optional[str], int], None, None]:
        pool_path = Path(path, "MaterialPool")
        asset_path = pool_path / "Materials"
        thumbnail_path = pool_path / "Thumbnails"

        thumbnail_files = (
            file for p in THUMBNAIL_EXTENSTIONS for file in thumbnail_path.glob(p)
        )
        thumbnail_files = sorted(thumbnail_files, key=lambda x: x.name.lower())
        thumbnail_names = {p.stem: p for p in thumbnail_files}
        asset_files = (file for p in MATERIAL_EXTENSIONS for file in asset_path.glob(p))

        for asset_file in sorted(asset_files, key=lambda x: x.name.lower()):
            asset_name = asset_file.stem
            file_path = asset_path / asset_file
            asset_size = file_path.stat().st_size
            thumbnail_path = thumbnail_names.get(asset_name)
            thumbnail_path = str(thumbnail_path) if thumbnail_path else None

            yield asset_name, file_path, thumbnail_path, asset_size

    @staticmethod
    def delete_asset(path: Path):
        if not path:
            logger.Logger.debug(f"can't delete asset, path is: {path}")
            return

        if not path.exists():
            logger.Logger.error(f"can't delete asset, path does not exist: {path}")
            return

        thumbnails_path = path.parent.parent / "Thumbnails"
        textures_path = path.parent.parent / "Textures"
        archive_path = path.parent.parent / "Archive"
        asset_name = path.stem

        thumbnails_to_delete = [
            thumbnails_path / i
            for i in thumbnails_path.iterdir()
            if i.stem == asset_name
        ]

        textures_to_delete = [
            textures_path / i for i in textures_path.iterdir() if i.stem == asset_name
        ]

        archive_to_delete = [
            archive_path / i for i in archive_path.iterdir() if i.stem == asset_name
        ]

        try:
            for thumb in thumbnails_to_delete:
                thumb.unlink()
                logger.Logger.info(f"deleted {thumb}")

            for tex in textures_to_delete:
                core.remove_folder(tex)
                logger.Logger.info(f"deleted {tex}")

            for archive in archive_to_delete:
                core.remove_folder(archive)
                logger.Logger.info(f"deleted {archive}")

            path.unlink()
            logger.Logger.info(f"deleted {path}")
        except Exception as e:
            logger.Logger.exception(e)

    @staticmethod
    def get_archived_versions(material_path: Path) -> dict[str, Path]:
        archive_path = material_path.parent.parent / "Archive"
        files = {i.stem: i for i in archive_path.iterdir()}
        return files

    @staticmethod
    def _get_newest_archive_version(archive_path: Path) -> str:
        numbers = [int(str(i.stem).split("_")[-1]) for i in archive_path.iterdir()]
        version = max(numbers) + 1 if numbers else 1
        return str(version).zfill(3)

    def archive_asset(self, path: Path):
        name = path.stem
        archive_folder = path.parent.parent / "Archive" / name
        archive_folder.mkdir(parents=True, exist_ok=True)
        archive_version = self._get_newest_archive_version(archive_folder)
        archive = archive_folder / f"{name}_{archive_version}{path.suffix}"

        shutil.copy2(path, archive)

        logger.Logger.info(f"archived {name} to {archive}")


class ModelPoolHandler:
    __slots__ = "_api_handler"

    def __init__(self, api_handler: api.APIHandler):
        self._api_handler = api_handler

    def create_pool(self, name: str, path: str):
        root_path = Path(path, "ModelPool")
        core.create_folder(root_path)
        core.create_folder(root_path / "Models")
        core.create_folder(root_path / "Textures")
        core.create_folder(root_path / "Thumbnails")
        core.create_folder(root_path / "Archive")

        self._api_handler.create(name, path)

        logger.Logger.info(f"created new model pool in {path}")

    def delete_pool(self, name: str, path: str):
        root_path = Path(path, "ModelPool")
        core.remove_folder(root_path)

        self._api_handler.delete(name, path)

        logger.Logger.info(f"deleted current model pool in {path}")

    @staticmethod
    def open_pool_dir(path: str):
        if not path:
            logger.Logger.error(f"can't open folder, path: {path} is invalid")
            return

        pool_path = Path(path, "ModelPool")

        if not pool_path.exists():
            logger.Logger.error(f"can't open folder, path: {path} does not exist")
            return

        if sys.platform == "darwin":
            with Popen(["open", path]):
                pass
        elif sys.platform == "win32":
            with Popen(f"explorer {pool_path}"):
                pass

    @staticmethod
    def get_assets_and_thumbnails(
        path: str,
    ) -> Generator[tuple[str, Path, Optional[str], int], None, None]:
        pool_path = Path(path, "ModelPool")
        asset_path = pool_path / "Models"
        thumbnail_path = pool_path / "Thumbnails"

        thumbnail_files = (
            file for p in THUMBNAIL_EXTENSTIONS for file in thumbnail_path.glob(p)
        )
        thumbnail_files = sorted(thumbnail_files, key=lambda x: x.name.lower())
        thumbnail_names = {p.stem: p for p in thumbnail_files}
        asset_files = (file for p in MODEL_EXTENSIONS for file in asset_path.glob(p))

        for asset_file in sorted(asset_files, key=lambda x: x.name.lower()):
            asset_name = asset_file.stem
            file_path = asset_path / asset_file
            asset_size = file_path.stat().st_size
            thumbnail_path = thumbnail_names.get(asset_name)
            thumbnail_path = str(thumbnail_path) if thumbnail_path else None

            yield asset_name, file_path, thumbnail_path, asset_size

    @staticmethod
    def delete_asset(path: Path):
        if not path:
            logger.Logger.debug(f"can't delete asset, path is: {path}")
            return

        if not path.exists():
            logger.Logger.error(f"can't delete asset, path does not exist: {path}")
            return

        thumbnails_path = path.parent.parent / "Thumbnails"
        textures_path = path.parent.parent / "Textures"
        archive_path = path.parent.parent / "Archive"
        asset_name = path.stem

        thumbnails_to_delete = [
            thumbnails_path / i
            for i in thumbnails_path.iterdir()
            if i.stem == asset_name
        ]

        textures_to_delete = [
            textures_path / i for i in textures_path.iterdir() if i.stem == asset_name
        ]

        archive_to_delete = [
            archive_path / i for i in archive_path.iterdir() if i.stem == asset_name
        ]

        try:
            for thumb in thumbnails_to_delete:
                thumb.unlink()
                logger.Logger.info(f"deleted {thumb}")

            for tex in textures_to_delete:
                core.remove_folder(tex)
                logger.Logger.info(f"deleted {tex}")

            for archive in archive_to_delete:
                core.remove_folder(archive)
                logger.Logger.info(f"deleted {archive}")

            path.unlink()
            logger.Logger.info(f"deleted {path}")
        except Exception as e:
            logger.Logger.exception(e)

    @staticmethod
    def get_archived_versions(model_path: Path) -> dict[str, Path]:
        archive_path = model_path.parent.parent / "Archive"
        files = {i.stem: i for i in archive_path.iterdir()}
        return files

    @staticmethod
    def _get_newest_archive_version(archive_path: Path) -> str:
        numbers = [int(str(i.stem).split("_")[-1]) for i in archive_path.iterdir()]
        version = max(numbers) + 1 if numbers else 1
        logger.Logger.debug(f"{version=}")
        return str(version).zfill(3)

    def archive_asset(self, path: Path):
        name = path.stem
        archive_folder = path.parent.parent / "Archive" / name
        archive_folder.mkdir(parents=True, exist_ok=True)
        archive_version = self._get_newest_archive_version(archive_folder)
        archive = archive_folder / f"{name}_{archive_version}{path.suffix}"

        shutil.copy2(path, archive)

        logger.Logger.info(f"archived {name} to {archive}")


class HDRIPoolHandler:
    __slots__ = "_api_handler"

    def __init__(self, api_handler: api.APIHandler):
        self._api_handler = api_handler

    def create_pool(self, name: str, path: str):
        root_path = Path(path, "HDRIPool")
        core.create_folder(root_path)
        core.create_folder(root_path / "HDRIs")
        core.create_folder(root_path / "Thumbnails")

        self._api_handler.create(name, path)

        logger.Logger.info(f"created new hdri pool in {path}")

    def delete_pool(self, name: str, path: str):
        root_path = Path(path, "HDRIPool")
        core.remove_folder(root_path)

        self._api_handler.delete(name, path)

        logger.Logger.info(f"deleted current hdri model pool in {path}")

    @staticmethod
    def open_pool_dir(path: str):
        if not path:
            logger.Logger.error(f"can't open folder, path: {path} is invalid")
            return

        pool_path = Path(path, "HDRIPool")

        if not pool_path.exists():
            logger.Logger.error(f"can't open folder, path: {path} does not exist")
            return

        if sys.platform == "darwin":
            with Popen(["open", path]):
                pass
        elif sys.platform == "win32":
            with Popen(f"explorer {pool_path}"):
                pass

    @staticmethod
    def get_assets_and_thumbnails(
        path: str,
    ) -> Generator[tuple[str, Path, Optional[str], int], None, None]:
        pool_path = Path(path, "HDRIPool")
        asset_path = pool_path / "HDRIs"
        thumbnail_path = pool_path / "Thumbnails"

        thumbnail_files = (
            file for p in THUMBNAIL_EXTENSTIONS for file in thumbnail_path.glob(p)
        )
        thumbnail_files = sorted(thumbnail_files, key=lambda x: x.name.lower())
        thumbnail_names = {p.stem: p for p in thumbnail_files}
        asset_files = (file for p in HDRI_EXTENSIONS for file in asset_path.glob(p))

        for asset_file in sorted(asset_files, key=lambda x: x.name.lower()):
            asset_name: str = asset_file.stem
            file_path: Path = asset_path / asset_file
            asset_size: int = file_path.stat().st_size
            thumbnail = thumbnail_names.get(asset_name)
            thumbnail = str(thumbnail) if thumbnail else None

            yield asset_name, file_path, thumbnail, asset_size

    @staticmethod
    def delete_asset(path: Path):
        if not path:
            logger.Logger.debug(f"can't delete asset, path is: {path}")
            return

        if not path.exists():
            logger.Logger.error(f"can't delete asset, path does not exist: {path}")
            return

        thumbnails_path = path.parent.parent.resolve() / "Thumbnails"
        asset_name = path.stem

        thumbnails_to_delete = [
            thumbnails_path / i
            for i in thumbnails_path.iterdir()
            if i.stem == asset_name
        ]

        try:
            for thumb in thumbnails_to_delete:
                thumb.unlink()
                logger.Logger.info(f"deleted {thumb}")

            path.unlink()
            logger.Logger.info(f"deleted {path}")
        except Exception as e:
            logger.Logger.exception(e)


class LightsetPoolHandler:
    __slots__ = "_api_handler"

    def __init__(self, api_handler: api.APIHandler):
        self._api_handler = api_handler

    def create_pool(self, name: str, path: str):
        root_path = Path(path, "LightsetPool")
        core.create_folder(root_path)
        core.create_folder(root_path / "Lightsets")
        core.create_folder(root_path / "Textures")
        core.create_folder(root_path / "Thumbnails")

        self._api_handler.create(name, path)

        logger.Logger.info(f"created new lightset pool in {path}")

    def delete_pool(self, name: str, path: str):
        root_path = Path(path, "LightsetPool")
        core.remove_folder(root_path)

        self._api_handler.delete(name, path)

        logger.Logger.info(f"deleted current lightset model pool in {path}")

    @staticmethod
    def open_pool_dir(path: str):
        if not path:
            logger.Logger.error(f"can't open folder, path: {path} is invalid")
            return

        pool_path = Path(path, "LightsetPool")

        if not pool_path.exists():
            logger.Logger.error(f"can't open folder, path: {path} does not exist")
            return

        if sys.platform == "darwin":
            with Popen(["open", path]):
                pass
        elif sys.platform == "win32":
            with Popen(f"explorer {pool_path}"):
                pass

    @staticmethod
    def get_assets_and_thumbnails(
        path: str,
    ) -> Generator[tuple[str, Path, Optional[str], int], None, None]:
        pool_path = Path(path, "LightsetPool")
        asset_path = pool_path / "Lightsets"
        thumbnail_path = pool_path / "Thumbnails"

        thumbnail_files = (
            file for p in THUMBNAIL_EXTENSTIONS for file in thumbnail_path.glob(p)
        )
        thumbnail_files = sorted(thumbnail_files, key=lambda x: x.name.lower())
        thumbnail_names = {p.stem: p for p in thumbnail_files}
        asset_files = (file for p in MODEL_EXTENSIONS for file in asset_path.glob(p))

        for asset_file in sorted(asset_files, key=lambda x: x.name.lower()):
            asset_name = asset_file.stem
            file_path = asset_path / asset_file
            asset_size = file_path.stat().st_size
            thumbnail_path = thumbnail_names.get(asset_name)
            thumbnail_path = str(thumbnail_path) if thumbnail_path else None

            yield asset_name, file_path, thumbnail_path, asset_size

    @staticmethod
    def delete_asset(path: Path):
        if not path:
            logger.Logger.debug(f"can't delete asset, path is: {path}")
            return

        if not path.exists():
            logger.Logger.error(f"can't delete asset, path does not exist: {path}")
            return

        thumbnails_path = path.parent.parent / "Thumbnails"
        archive_path = path.parent.parent / "Archive"
        asset_name = path.stem

        thumbnails_to_delete = [
            thumbnails_path / i
            for i in thumbnails_path.iterdir()
            if i.stem == asset_name
        ]

        archive_to_delete = [
            archive_path / i for i in archive_path.iterdir() if i.stem == asset_name
        ]

        try:
            for thumb in thumbnails_to_delete:
                thumb.unlink()
                logger.Logger.info(f"deleted {thumb}")

            for archive in archive_to_delete:
                core.remove_folder(archive)
                logger.Logger.info(f"deleted {archive}")

            path.unlink()
            logger.Logger.info(f"deleted {path}")
        except Exception as e:
            logger.Logger.exception(e)

    @staticmethod
    def get_archived_versions(model_path: Path) -> dict[str, Path]:
        archive_path = model_path.parent.parent / "Archive"
        files = {i.stem: i for i in archive_path.iterdir()}
        return files

    @staticmethod
    def _get_newest_archive_version(archive_path: Path) -> str:
        numbers = [int(str(i.stem).split("_")[-1]) for i in archive_path.iterdir()]
        version = max(numbers) + 1 if numbers else 1
        logger.Logger.debug(f"{version=}")
        return str(version).zfill(3)

    def archive_asset(self, path: Path):
        name = path.stem
        archive_folder = path.parent.parent / "Archive" / name
        archive_folder.mkdir(parents=True, exist_ok=True)
        archive_version = self._get_newest_archive_version(archive_folder)
        archive = archive_folder / f"{name}_{archive_version}{path.suffix}"

        shutil.copy2(path, archive)

        logger.Logger.info(f"archived {name} to {archive}")


class UtilityPoolHandler:
    def create_pool(self, name: str, path: str):
        raise NotImplementedError

    def delete_pool(self, name: str, path: str):
        raise NotImplementedError

    @staticmethod
    def open_pool_dir(path: str):
        if not path:
            logger.Logger.error(f"can't open folder, path: {path} is invalid")
            return

        pool_path = Path(path, "UtilityPool")

        if not pool_path.exists():
            logger.Logger.error(f"can't open folder, path: {path} does not exist")
            return

        if sys.platform == "darwin":
            with Popen(["open", path]):
                pass
        elif sys.platform == "win32":
            with Popen(f"explorer {path}"):
                pass

    @staticmethod
    def get_assets_and_thumbnails(
        path: str,
    ) -> Generator[tuple[str, Path, Optional[str], int], None, None]:
        util_folder = Path(__file__).parent.parent / "settings" / "utility_settings"
        asset_files = (
            file for p in UTILITY_EXTENSTIONS for file in util_folder.glob(p)
        )

        for asset_file in asset_files:
            asset_name = asset_file.stem
            file_path = util_folder / asset_file
            asset_size = file_path.stat().st_size

            yield asset_name, file_path, None, asset_size

    @staticmethod
    def delete_asset(path: Path):
        raise NotImplementedError
