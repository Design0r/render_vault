import json
import sys
from pathlib import Path
from typing import Generator, Union

import render_vault.controller.maya_cmds as mc

from ..core import Logger
from .settings import SettingsManager


class MayaHandler:
    @staticmethod
    def open_scene(path: Path):
        mc.open_scene(path)

    @staticmethod
    def save_scene_as(path: Path):
        mc.save_scene_as(path)

    @staticmethod
    def import_material(path: Union[Path, list[Path]], assign=False):
        if isinstance(path, Path):
            mc.import_material(path, assign=assign)
            return

        for p in path:
            mc.import_material(p, assign=assign)

    @staticmethod
    def reference_material(path: Union[Path, list[Path]], assign=False):
        if isinstance(path, Path):
            mc.reference_material(path, assign=assign)
            return
        for p in path:
            mc.reference_material(p, assign=assign)

    @staticmethod
    def replace_material_in_scene(path: Union[Path, list[Path]]):
        mc.replace_material_in_scene(path)

    @staticmethod
    def export_materials(path: Path, materials: list[str]):
        mc.export_materials(path, materials=materials)

    @staticmethod
    def get_non_default_materials() -> Generator[str, None, None]:
        return mc.get_non_default_materials()

    @staticmethod
    def import_model(path: Union[Path, list[Path]]):
        if isinstance(path, Path):
            mc.import_model(path)
            return
        for p in path:
            mc.import_model(p)

    @staticmethod
    def reference_model(path: Union[Path, list[Path]]):
        if isinstance(path, Path):
            mc.reference_model(path)
            return
        for p in path:
            mc.reference_model(p)

    @staticmethod
    def export_model(path: Path, name: str, file_extension: str):
        mc.export_selected(path, name, file_extension)

    @staticmethod
    def render_single_material_cmd(path: str):
        mayapy = mc.get_mayapy_path()
        settings = SettingsManager()
        render_script = str(settings.ROOT_PATH / "external" / "render_manager.py")
        logging_path = settings.LOGGING_PATH
        single_mode = True

        user_render_settings = json.dumps(settings.material_settings.to_dict())

        if sys.platform == "win32":
            user_render_settings = user_render_settings.replace('"', '\\"')
            return f'{mayapy} {render_script} {logging_path} {path} {single_mode} "{user_render_settings}"'

        elif sys.platform == "darwin":
            return [
                mayapy,
                render_script,
                logging_path,
                path,
                f"{single_mode}",
                user_render_settings,
            ]

    @staticmethod
    def render_all_materials_cmd(path: str):
        mayapy = mc.get_mayapy_path()
        settings = SettingsManager()
        render_script = str(settings.ROOT_PATH / "external" / "render_manager.py")
        single_mode = False
        logger_path = settings.LOGGING_PATH

        user_render_settings = json.dumps(settings.material_settings.to_dict())

        if sys.platform == "win32":
            user_render_settings = user_render_settings.replace('"', '\\"')
            return f'{mayapy} {render_script} {logger_path} {path} {single_mode} "{user_render_settings}"'

        elif sys.platform == "darwin":
            return [
                mayapy,
                render_script,
                logger_path,
                path,
                str(single_mode),
                user_render_settings,
            ]

    @staticmethod
    def repath_textures_cmd(
        pool_path: str, materials: Union[str, list[str]], model: str, mode: int
    ) -> Union[str, list[str]]:
        mayapy = mc.get_mayapy_path()
        settings = SettingsManager()
        render_script = str(settings.ROOT_PATH / "external" / "repath_manager.py")
        logger_path = settings.LOGGING_PATH

        if sys.platform == "win32":
            return f'{mayapy} {render_script} {logger_path} {pool_path} "{materials}" {model} {mode}'
        elif sys.platform == "darwin":
            return [
                mayapy,
                render_script,
                logger_path,
                pool_path,
                str(materials),
                model,
                str(mode),
            ]

    @staticmethod
    def create_domelight(path: Path):
        mc.import_as_dome_light(path)

    @staticmethod
    def create_arealight(path: Path):
        mc.import_as_area_light(path)

    @staticmethod
    def create_file_node(path: Path):
        mc.import_as_file_node(path)

    @staticmethod
    def import_render_settings(path: Path):
        if not path.exists():
            msg = f"error importing render settings, path: {path} does not exist"
            Logger.error(msg)
            return

        with open(path, "r", encoding="utf-8") as file:
            settings = json.load(file)
            mc.set_attr_recursive(settings)
            Logger.info(f"imported {path.stem} render settings")
