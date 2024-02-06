from typing import Generator, Protocol, Union
from datetime import datetime
from pathlib import Path
import sys
import json
from maya import cmds
import render_vault.controller.maya_cmds as mc
import render_vault.controller.settings as s
from .logger import Logger


class DCCHandler(Protocol):
    @staticmethod
    def open_scene(path: Path):
        ...

    @staticmethod
    def save_scene_as(path: Path):
        ...

    @staticmethod
    def import_material(path: Union[Path, list[Path]], assign=False):
        ...

    @staticmethod
    def reference_material(path: Union[Path, list[Path]], assign=False):
        ...

    @staticmethod
    def export_materials(path: Path, materials: list[str]):
        ...

    @staticmethod
    def get_non_default_materials() -> Generator:
        ...

    @staticmethod
    def import_model(path: Union[Path, list[Path]]):
        ...

    @staticmethod
    def reference_model(path: Union[Path, list[Path]]):
        ...

    @staticmethod
    def replace_material_in_scene(path: Union[Path, list[Path]]):
        ...

    @staticmethod
    def export_model(path: Path, name: str, file_extension: str):
        ...

    @staticmethod
    def render_single_material_cmd(path: str) -> Union[list[str], str]:
        ...

    @staticmethod
    def render_all_materials_cmd(path: str) -> Union[list[str], str]:
        ...

    @staticmethod
    def repath_textures_cmd(
        pool_path: str, materials: Union[str, list[str]], model: str, mode: int
    ) -> Union[list[str], str]:
        ...

    @staticmethod
    def create_domelight(path: Path):
        ...

    @staticmethod
    def create_arealight(path: Path):
        ...

    @staticmethod
    def create_file_node(path: Path):
        ...

    @staticmethod
    def import_render_settings(path: Path):
        ...


class MayaHandler:
    @staticmethod
    def open_scene(path: Path):
        if cmds.file(q=True, modified=True):
            response = cmds.confirmDialog(
                title="Save Changes?",
                message="The scene has unsaved changes. Save now?",
                button=["Yes", "No", "Cancel"],
                defaultButton="Yes",
                cancelButton="Cancel",
                dismissString="No",
            )
            if response == "Yes":
                scene_name = cmds.file(q=True, sn=True)
                if scene_name == "":
                    Logger.warning("The scene has not been saved yet.")
                else:
                    cmds.file(save=True)
                    cmds.file(path, open=True)
                    Logger.info(f"The scene has been saved as: {scene_name}")
            elif response == "No":
                cmds.file(path, open=True, force=True)
        else:
            cmds.file(path, open=True)

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
        render_script = str(Path(__file__).parent / "render_manager.py")
        single_mode = True
        logger_path = str(
            Path(__file__).parent.parent / "logs" / f"{datetime.now().date()}.log"
        )

        user_render_settings = json.dumps(s.SettingsManager.material_settings.to_dict())

        if sys.platform == "win32":
            user_render_settings = user_render_settings.replace('"', '\\"')
            return f'{mayapy} {render_script} {logger_path} {path} {single_mode} "{user_render_settings}"'
        elif sys.platform == "darwin":
            return [
                mayapy,
                render_script,
                logger_path,
                path,
                f"{single_mode}",
                user_render_settings,
            ]

    @staticmethod
    def render_all_materials_cmd(path: str):
        mayapy = mc.get_mayapy_path()
        render_script = str(Path(__file__).parent / "render_manager.py")
        single_mode = False
        logger_path = str(
            Path(__file__).parent.parent / "logs" / f"{datetime.now().date()}.log"
        )

        user_render_settings = json.dumps(s.SettingsManager.material_settings.to_dict())

        if sys.platform == "win32":
            user_render_settings = user_render_settings.replace('"', '\\"')
            return f'{mayapy} {render_script} {logger_path} {path} {single_mode} "{user_render_settings}"'
        elif sys.platform == "darwin":
            return [
                mayapy,
                render_script,
                logger_path,
                path,
                f"{single_mode}",
                user_render_settings,
            ]

    @staticmethod
    def repath_textures_cmd(
        pool_path: str, materials: Union[str, list[str]], model: str, mode: int
    ) -> Union[str, list[str]]:
        mayapy = mc.get_mayapy_path()
        render_script = str(Path(__file__).parent / "repath_manager.py")
        logger_path = str(
            Path(__file__).parent.parent / "logs" / f"{datetime.now().date()}.log"
        )

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
        with open(path, "r", encoding="utf-8") as file:
            settings = json.load(file)
            mc.set_attr_recursive(settings)
            Logger.info(f"imported {path.stem} render settings")
