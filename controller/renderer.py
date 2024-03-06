import sys
import pathlib
from maya import mel, cmds
from abc import ABC, abstractmethod
from render_vault.controller.logger import Logger
from typing import Generator


class Renderer(ABC):
    def __init__(
        self,
        render_cam: str,
        render_geo: str,
        render_res: tuple[int, int],
        path: str,
        single_mode: bool,
    ):
        self.render_cam = render_cam
        self.render_res_x, self.render_res_y = render_res
        self.render_geo = render_geo
        self.pool_path = path
        self.single_mode = single_mode

    @abstractmethod
    def set_render_settings(self):
        ...

    @abstractmethod
    def set_as_active_renderer(self):
        ...

    @abstractmethod
    def remove_render_elements(self):
        ...

    @abstractmethod
    def assign_material(self, mtl):
        ...

    @abstractmethod
    def set_image_path(self, mtl):
        ...

    @abstractmethod
    def render(self, materials: Generator[str, None, None] | None):
        ...


class Arnold(Renderer):
    def __init__(
        self,
        render_cam: str,
        render_geo: str,
        render_res: tuple[int, int],
        path: str,
        single_mode: bool,
    ):
        self.render_cam = render_cam
        self.render_res_x, self.render_res_y = render_res
        self.render_geo = render_geo
        self.pool_path = path
        self.single_mode = single_mode

    def set_render_settings(self):
        # rendersettin
        cmds.setAttr("defaultResolution.aspectLock", 0)
        cmds.setAttr("defaultArnoldDriver.ai_translator", "jpeg", type="string")
        Logger.info("set arnold render settings")
        pass

    def set_as_active_renderer(self):
        arnold_extension = "dll" if sys.platform == "win32" else "bundle"
        if not cmds.pluginInfo(f"mtoa.{arnold_extension}", q=True, loaded=True):
            cmds.loadPlugin(f"mtoa.{arnold_extension}")

        if cmds.getAttr("defaultRenderGlobals.currentRenderer") == "arnold":
            return

        cmds.setAttr("defaultRenderGlobals.currentRenderer", "arnold", type="string")
        Logger.info("set arnold as active renderer")
        pass

    def remove_render_elements(self):
        Logger.info("removed all render elements")
        pass

    def assign_material(self, mtl):
        try:
            sg = f"{mtl}SG"
            cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg)
            shaderGeoShape = cmds.listRelatives(self.render_geo, shapes=True)[0]
            cmds.sets(shaderGeoShape, forceElement=sg)
            cmds.connectAttr(f"{mtl}.outColor", f"{sg}.surfaceShader")
            Logger.info(f"assigned {mtl} to {self.render_geo}")
        except Exception as e:
            Logger.exception(e)

    def set_image_path(self, mtl):
        if self.single_mode:
            out_path = str(pathlib.Path(self.pool_path).parent.parent / "Thumbnails")
        else:
            out_path = str(pathlib.Path(self.pool_path) / "MaterialPool" / "Thumbnails")

        cmds.setAttr("defaultRenderGlobals.outFormatControl", False)
        cmds.setAttr(
            "defaultRenderGlobals.imageFilePrefix", out_path + f"/{mtl}", type="string"
        )
        # cmds.workspace(fileRule=["images", out_path])
        Logger.info(f"set image output path: {out_path}")

    def render(self, materials: Generator[str, None, None] | None):
        if not materials:
            Logger.error(f"can't render, no materials: {materials}")
            return

        self.set_render_settings()
        self.set_as_active_renderer()
        self.remove_render_elements()

        for mtl in materials:
            self.assign_material(mtl)
            self.set_image_path(mtl)
            cmds.arnoldRender(
                width=self.render_res_x,
                height=self.render_res_y,
                cam=self.render_cam,
            )
            Logger.info(f"finished rendering {mtl}")


class VRay(Renderer):
    def __init__(
        self,
        render_cam: str,
        render_geo: str,
        render_res: tuple[int, int],
        path: str,
        single_mode: bool,
    ):
        self.render_cam = render_cam
        self.render_geo = render_geo
        self.render_res_x, self.render_res_y = render_res
        self.pool_path = path
        self.single_mode = single_mode

    def set_render_settings(self):
        cmds.setAttr("vraySettings.imageFormatStr", "jpg", type="string")
        cmds.setAttr("vraySettings.dontSaveImage", 0)
        cmds.setAttr("vraySettings.aspectLock", 0)
        cmds.setAttr("vraySettings.width", self.render_res_x)
        cmds.setAttr("vraySettings.height", self.render_res_y)
        cmds.setAttr("vraySettings.samplerType", 4)
        cmds.setAttr("vraySettings.dmcMaxSubdivs", 8)
        cmds.setAttr("vraySettings.sys_regsgen_xc", 32)
        cmds.setAttr("vraySettings.dmcThreshold", 0.01)
        cmds.setAttr("vraySettings.productionEngine", 0)
        mel.eval("vray vfbControl -testresolutionenabled 0")
        Logger.info("set v-ray render settings")

    def set_as_active_renderer(self):
        if cmds.getAttr("defaultRenderGlobals.currentRenderer") != "vray":
            cmds.setAttr("defaultRenderGlobals.currentRenderer", "vray", type="string")
        Logger.info("set v-ray as active renderer")

    def remove_render_elements(self):
        all_render_elements = cmds.ls(type="VRayRenderElement")
        if not all_render_elements:
            return

        for i in all_render_elements:
            try:
                Logger.info(f"Deleting Render Element: {i}")
                cmds.delete(i)
            except Exception as error:
                Logger.exception(error)
        Logger.info("removed all render elements")

    def assign_material(self, mtl):
        if not mtl:
            Logger.error(f"can't assign material, mtl is {mtl}")
            return

        sg = f"{mtl}SG"
        cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg)
        shaderGeoShape = cmds.listRelatives(self.render_geo, shapes=True)[0]
        cmds.sets(shaderGeoShape, forceElement=sg)
        cmds.connectAttr(f"{mtl}.outColor", f"{sg}.surfaceShader")
        Logger.info(f"assigned {mtl} to {self.render_geo}")

    def set_image_path(self, mtl):
        if self.single_mode:
            out_path = str(pathlib.Path(self.pool_path).parent.parent / "Thumbnails")
        else:
            out_path = str(pathlib.Path(self.pool_path) / "MaterialPool" / "Thumbnails")
        mel.eval('string $fileNamePrefix = "%s";' % mtl)
        mel.eval(
            'setAttr "vraySettings.fileNamePrefix" -type "string" $fileNamePrefix;'
        )
        cmds.workspace(fileRule=("images", out_path))
        Logger.info(f"set image output path: {out_path}")

    def render(self, materials: Generator[str, None, None] | None):
        if not materials:
            Logger.error(f"can't render, no materials: {materials}")
            return

        self.set_as_active_renderer()
        self.remove_render_elements()
        self.set_render_settings()

        for mtl in materials:
            self.set_image_path(mtl)
            self.assign_material(mtl)
            cmds.vrend(camera=self.render_cam)
            Logger.info(f"finished rendering {mtl}")
