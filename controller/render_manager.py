from __future__ import annotations
import sys
import pathlib
from maya import cmds
import maya.standalone
import ast
import json

from render_vault.controller.logger import Logger
from render_vault.controller.renderer import Arnold, VRay
from render_vault.controller.settings import Renderer


class RenderManager:
    renderer = None
    logging_path = sys.argv[1]
    material_pool_path = sys.argv[2]
    single_mode = ast.literal_eval(sys.argv[3])

    user_render_settings = json.loads(sys.argv[4])
    render_type = Renderer(user_render_settings["material_renderer"])
    render_scene = user_render_settings["render_scene"]
    render_cam = user_render_settings["render_cam"]
    render_object = user_render_settings["render_object"]
    render_res_x = user_render_settings["render_resolution_x"]
    render_res_y = user_render_settings["render_resolution_y"]

    @classmethod
    def run(cls):
        cls.init_logger()
        cls.init_maya_standalone()
        cls.set_renderer()
        cls.load_render_scene()

        if cls.renderer:
            cls.renderer.render(cls.get_renderable_materials())
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
    def set_renderer(cls):
        args = (
            cls.render_cam,
            cls.render_object,
            (cls.render_res_x, cls.render_res_y),
            cls.material_pool_path,
            cls.single_mode,
        )

        if cls.render_type == Renderer.VRAY:
            cls.renderer = VRay(*args)
        elif cls.render_type == Renderer.ARNOLD:
            cls.renderer = Arnold(*args)

    @classmethod
    def load_render_scene(cls):
        try:
            cmds.file(cls.render_scene, open=True, force=True)
            Logger.info(f"loaded render scene: {cls.render_scene}")
        except Exception as e:
            Logger.exception(e)

    @classmethod
    def init_logger(cls):
        Logger.write_to_file(cls.logging_path)
        Logger.set_propagate(False)

    @classmethod
    def import_material(cls, material_path):
        try:
            cmds.file(material_path, i=True, defaultNamespace=True)
            Logger.info(f"imported {material_path}")
        except Exception as e:
            Logger.exception(e)

    @classmethod
    def get_renderable_materials(cls):
        default_mtls = cmds.ls(materials=True)

        if cls.single_mode:
            material_path = cls.material_pool_path
            cls.import_material(material_path)
        else:
            material_path = (
                pathlib.Path(cls.material_pool_path) / "MaterialPool" / "Materials"
            )
            items = material_path.glob("*.m[ab]")

            for mtl in list(items):
                cls.import_material(mtl)

        new_mtls = cmds.ls(materials=True)
        filtered = filter(lambda x: x not in default_mtls, new_mtls)
        return list(filtered)


if __name__ == "__main__":
    RenderManager.run()
