import os
import sys
from enum import Enum
from pathlib import Path
from typing import Generator, Optional, Union

from maya import cmds

from ..core import Logger


class ColorManagementMode(Enum):
    DISABLED = 0
    SRGB = 1
    ACES = 2


def open_scene(path: str) -> None:
    if not cmds.file(query=True, modified=True):
        cmds.file(path, open=True, ignoreVersion=True)
        Logger.info(f"Opening scene {path}")
        return

    response = cmds.confirmDialog(
        title="Save Changes?",
        message="The scene has unsaved changes. Save now?",
        button=["Yes", "No", "Cancel"],
        defaultButton="Yes",
        cancelButton="Cancel",
        dismissString="No",
    )

    if response == "Yes":
        scene_name = cmds.file(q=True, sn=True, ignoreVersion=True)
        if not scene_name:
            Logger.warning("The scene has not been saved yet.")
            return

        cmds.file(save=True, ignoreVersion=True)
        Logger.info(f"The scene has been saved as: {scene_name}")
        cmds.file(path, open=True, ignoreVersion=True)
        Logger.info(f"Opening scene {path}")

    elif response == "No":
        cmds.file(path, open=True, force=True, ignoreVersion=True)
        Logger.info(f"Opening scene {path}")


def save_scene_as(path: Path) -> None:
    cmds.file(rename=path)
    cmds.file(save=True, force=True, type="mayaBinary")
    Logger.info(f"Saving scene {path}")


def get_non_default_materials() -> Generator[str, None, None]:
    default_materials = {"lambert1", "standardSurface1", "particleCloud1"}
    # materials = filter(lambda x: x not in default_materials, cmds.ls(materials=True))
    materials = (x for x in cmds.ls(materials=True) if x not in default_materials)

    return materials


def assign_material_to_selection(material: str, geometry: list[str]) -> None:
    if not material:
        Logger.debug(f"material to assign to selection is {material}")
        return

    sg = cmds.sets(
        renderable=True, noSurfaceShader=True, empty=True, name=f"{material}SG"
    )
    cmds.connectAttr(f"{material}.outColor", f"{sg}.surfaceShader")

    for sel in geometry:
        cmds.sets(sel, forceElement=sg)
        Logger.debug(f"assigned {material} to {sel}")


def replace_material_in_scene(material_path: Union[Path, list[Path]]) -> None:
    if not isinstance(material_path, Path):
        return

    name = material_path.stem
    if not is_duplciate_material(name):
        Logger.error(f"no material found in scene with name {name}")
        return

    old_mtl = cmds.ls(name, materials=True)[0]
    old_mtl = cmds.rename(old_mtl, f"{old_mtl}_this_is_about_to_be_replaced")

    import_material(material_path)
    objects_with_old_material = get_objects_with_assigned_mtl(old_mtl)

    try:
        for obj in objects_with_old_material:
            cmds.select(obj, replace=True)
            cmds.hyperShade(assign=name)
        Logger.info(f"{name} successfully replaced")
    except Exception as e:
        Logger.exception(e)

    try:
        cmds.delete(old_mtl)
        Logger.info(f"deleted {old_mtl}")
    except Exception as e:
        Logger.exception(e)

    cmds.select(name)


def get_objects_with_assigned_mtl(mtl_name: str) -> list[str]:
    all_objects = cmds.ls(dagObjects=True)
    objects_with_old_material = []

    for obj in all_objects:
        shading_engines = cmds.listConnections(obj, type="shadingEngine")
        if not shading_engines:
            continue
        for se in shading_engines:
            mtl = cmds.listConnections(se + ".surfaceShader")
            if mtl and mtl_name in mtl:
                objects_with_old_material.append(obj)

    return objects_with_old_material


def is_duplciate_material(mtl_name: str) -> bool:
    if mtl_name in cmds.ls(materials=True, showNamespace=True):
        return True

    return False


def import_material(path: Path, assign: bool = False) -> None:
    if not path:
        Logger.debug(f"can't import material, path is {path}")
        return

    if not path.exists():
        Logger.error(f"can't import material, path does not exist {path}")
        return

    mtl_name = path.stem

    geo = cmds.ls(selection=True)

    if is_duplciate_material(mtl_name):
        Logger.warning(f"material {mtl_name} already exists in scene, skipping import.")
        assign_material_to_selection(mtl_name, geo)
        return

    materials = cmds.file(path, i=True, returnNewNodes=True, ignoreVersion=True)
    material = next((mtl for mtl in materials if mtl_name == mtl), materials[0])

    Logger.info(f"imported material {material}")

    if not assign or not geo:
        return

    assign_material_to_selection(material, geo)


def reference_material(path: Path, assign: bool = False) -> None:
    if not path:
        Logger.debug(f"reference material path is {path}")
        return

    if not os.path.exists(path):
        Logger.error(f"can't reference material, path does not exist {path}")
        return

    mtl_name = path.stem

    if is_duplciate_material(mtl_name):
        Logger.warning(
            f"material {mtl_name} already exists in scene, skipping reference."
        )
        return

    geo = cmds.ls(selection=True)

    materials = cmds.file(
        path,
        reference=True,
        namespace=mtl_name,
        usingNamespaces=True,
        returnNewNodes=True,
        ignoreVersion=True,
    )[0]
    material = next((mtl for mtl in materials if mtl_name == mtl), materials[0])
    Logger.info(f"referenced material {path}")

    if not assign or not geo:
        return

    assign_material_to_selection(material, geo)


def export_materials(path: Path, materials: list[str]) -> None:
    if not path or not materials:
        Logger.error(
            f"can't export materials, either path: {path} or materials: {materials} are not valid."
        )
        return

    for mtl in materials:
        cmds.select(mtl)
        filename = str(path / f"{mtl}.mb")
        cmds.file(
            filename,
            exportSelected=True,
            type="mayaBinary",
            force=True,
            ignoreVersion=True,
        )
        Logger.info(f"exported {mtl} to {path}")


def export_all_materials(path: str) -> None:
    materials = get_non_default_materials()

    for mtl in materials:
        cmds.select(mtl)
        filename = f"{path}/{mtl}.mb"
        cmds.file(
            filename,
            exportSelected=True,
            type="mayaBinary",
            force=True,
            ignoreVersion=True,
        )
        Logger.debug(f"exported {mtl}")

    Logger.info(f"exported {len(list(materials))} materials to {path}")


def import_model(path: Path) -> None:
    if not path:
        Logger.debug(f"can't import model, path is {path}")
        return

    if not path.exists():
        Logger.error(f"can't import model, path does not exist {path}")
        return

    cmds.file(path, i=True, ignoreVersion=True)
    Logger.info(f"imported model {path}")


def reference_model(path: Path) -> None:
    if not path:
        Logger.debug(f"reference model path is {path}")
        return

    if not path.exists():
        Logger.error(f"can't reference model, path does not exist {path}")
        return

    model_name = path.stem
    cmds.file(
        path,
        reference=True,
        namespace=model_name,
        usingNamespaces=True,
        ignoreVersion=True,
    )
    Logger.info(f"referenced model {path}")


def get_file_nodes_in_scene() -> list[str]:
    file_nodes = cmds.ls(type="file")
    return file_nodes


def import_as_dome_light(path: Path):
    if not path:
        Logger.debug(f"cant create dome light, path is {path}")
        return

    if not cmds.getAttr("defaultRenderGlobals.currentRenderer") == "vray":
        Logger.error("can't create v-ray dome light, v-ray is not the active renderer")
        return

    dome_light = cmds.shadingNode("VRayLightDomeShape", asLight=True)
    cmds.setAttr(f"{dome_light}.useDomeTex", 1)
    cmds.setAttr(f"{dome_light}.invisible", 1)

    file_node = cmds.shadingNode("file", asTexture=True)
    cmds.setAttr(file_node + ".fileTextureName", path, type="string")
    cmds.setAttr(
        file_node + ".colorSpace",
        convert_to_color_space_rule(get_maya_color_management_mode()),
        type="string",
    )

    cmds.connectAttr(file_node + ".outColor", dome_light + ".domeTex", force=True)
    dome_light = cmds.rename(dome_light, path.stem)
    Logger.info(f"Creating Domelight with HDRI {path}")


def import_as_area_light(path: Path):
    if not path:
        Logger.debug(f"cant create area light, path is {path}")
        return

    if not cmds.getAttr("defaultRenderGlobals.currentRenderer") == "vray":
        Logger.error("can't create area light, v-ray is not the active renderer")
        return

    area_light = cmds.shadingNode("VRayLightRectShape", asLight=True)
    cmds.setAttr(f"{area_light}.useRectTex", 1)
    cmds.setAttr(f"{area_light}.showTex", 1)
    cmds.setAttr(f"{area_light}.invisible", 1)

    file_node = cmds.shadingNode("file", asTexture=True)
    cmds.setAttr(file_node + ".fileTextureName", path, type="string")
    cmds.setAttr(
        file_node + ".colorSpace",
        convert_to_color_space_rule(get_maya_color_management_mode()),
        type="string",
    )

    cmds.connectAttr(file_node + ".outColor", area_light + ".rectTex", force=True)
    area_light = cmds.rename(area_light, path.stem)
    Logger.info(f"Creating Arealight with HDRI {path}")


def import_as_file_node(path: Path):
    if not path:
        Logger.debug(f"cant create file node, path is {path}")
        return

    file_node = cmds.shadingNode("file", asTexture=True)
    cmds.setAttr(file_node + ".fileTextureName", path, type="string")
    cmds.setAttr(
        file_node + ".colorSpace",
        convert_to_color_space_rule(get_maya_color_management_mode()),
        type="string",
    )

    file_node = cmds.rename(file_node, path.stem)
    Logger.info(f"Creating File Node with HDRI {path}")


def export_selected(path: Path, name: str, file_extension: str) -> None:
    if not path or not name:
        Logger.error(f"can't export model, no path: {path} or name: {name} specified.")
        return

    filename = str(path / f"{name}.{file_extension}")
    file_type = "mayaBinary" if file_extension == "mb" else "mayaAscii"

    cmds.file(filename, exportSelected=True, type=file_type, force=True)
    Logger.debug(f"exported model: {name}")


def get_mayapy_path() -> str:
    if sys.platform == "win32":
        return f"{os.getenv('MAYA_LOCATION')}/bin/mayapy.exe"

    elif sys.platform == "darwin":
        return f"{os.getenv('MAYA_LOCATION')}/bin/mayapy"


def get_maya_color_management_mode() -> ColorManagementMode:
    if not cmds.colorManagementPrefs(query=True, cmEnabled=True):
        return ColorManagementMode.DISABLED

    rendering_space = cmds.colorManagementPrefs(query=True, renderingSpaceName=True)

    if "ACES" in rendering_space:
        return ColorManagementMode.ACES
    elif "sRGB" in rendering_space:
        return ColorManagementMode.SRGB

    return ColorManagementMode.DISABLED


def convert_to_color_space_rule(color_mode: ColorManagementMode) -> str:
    if color_mode == ColorManagementMode.SRGB:
        return "RAW"
    elif color_mode == ColorManagementMode.ACES:
        return "scene-linear Rec.709-sRGB"

    return ""


def set_attr_recursive(attr_dict: dict, node_name: Optional[str] = None) -> None:
    for attr, value in attr_dict.items():
        if isinstance(value, dict):
            set_attr_recursive(value, node_name=attr)
            continue

        try:
            if isinstance(value, str):
                cmds.setAttr(attr, value, type="string")
            else:
                cmds.setAttr(attr, value)
        except Exception:
            pass
