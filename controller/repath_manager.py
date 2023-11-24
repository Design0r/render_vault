from typing import Union
from maya import cmds
import shutil
import sys
from pathlib import Path
import ast
import maya.standalone

from render_vault.controller import Logger, core, maya_cmds


class TextureManager:
    logging_path = sys.argv[1]
    pool_path = sys.argv[2]
    materials = ast.literal_eval(sys.argv[3])
    model = sys.argv[4]
    mode = int(sys.argv[5])

    @classmethod
    def run(cls):
        cls.init_logger()
        cls.init_maya_standalone()
        cls.setup()
        cls.uninit_maya_standalone()

    @staticmethod
    def init_maya_standalone():
        Logger.info("initializing maya standalone...")
        maya.standalone.initialize(name="python")

    @staticmethod
    def uninit_maya_standalone():
        Logger.info("uninitializing maya standalone...")
        maya.standalone.uninitialize()

    @classmethod
    def init_logger(cls):
        Logger.write_to_file(cls.logging_path)
        Logger.set_propagate(False)

    @classmethod
    def load_scene(cls, path: Union[str, Path]):
        try:
            cmds.file(path, open=True, force=True)
            Logger.info(f"loaded scene: {path}")
        except Exception as e:
            Logger.exception(e)

    @classmethod
    def copy_texture(cls, texture_path, destination) -> str | None:
        try:
            shutil.copy2(texture_path, destination)
            Logger.info(f"copied {texture_path} to {destination}")
            return str(Path(destination) / Path(texture_path).name)
        except Exception as e:
            Logger.exception(e)

    @classmethod
    def setup(cls):
        if cls.mode == 0:
            cls.materials_mode()
        elif cls.mode == 1:
            cls.model_mode()

    @classmethod
    def model_mode(cls):
        model_name = Path(cls.model).stem
        texture_path = Path(cls.pool_path) / "ModelPool" / "Textures" / model_name
        cls.load_scene(cls.model)
        file_nodes = maya_cmds.get_file_nodes_in_scene()
        cls.repath_file_nodes(file_nodes, texture_path, cls.model)

    @classmethod
    def materials_mode(cls):
        for mtl in cls.materials:
            texture_path = Path(cls.pool_path) / "MaterialPool" / "Textures" / mtl

            materials_path = Path(cls.pool_path) / "MaterialPool" / "Materials"
            try:
                scene_path = list(materials_path.glob(f"{mtl}.m[ab]"))[0]
            except Exception as e:
                Logger.exception(e)
                return

            cls.load_scene(scene_path)
            file_nodes = maya_cmds.get_file_nodes_in_scene()
            cls.repath_file_nodes(file_nodes, texture_path, scene_path)

    @classmethod
    def repath_file_nodes(
        cls, file_nodes: list[str], texture_path: Path, scene_path: Union[str, Path]
    ):
        for file_node in file_nodes:
            file_path = cmds.getAttr(file_node + ".fileTextureName")
            cmds.setAttr(f"{file_node}.ignoreColorSpaceFileRules", True)
            if not file_path:
                continue

            core.create_folder(texture_path)
            new_path = cls.copy_texture(file_path, texture_path)
            if not new_path:
                return

            cmds.setAttr(file_node + ".fileTextureName", new_path, type="string")
            cmds.setAttr(f"{file_node}.ignoreColorSpaceFileRules", False)
            Logger.info(f"set path of file node: {file_node} to {new_path}")
            try:
                cmds.file(save=True, type="mayaBinary", force=True)
                Logger.info(f"saved scene {scene_path}")
            except Exception as e:
                Logger.exception(e)


if __name__ == "__main__":
    TextureManager.run()
