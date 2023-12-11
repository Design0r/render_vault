import json
import socket
from enum import Enum
from pathlib import Path

from ..controller import api_handler
from ..ui.viewport_container import ViewportMode
from .logger import Logger


class Renderer(Enum):
    DEFAULT = 0
    VRAY = 1
    ARNOLD = 2
    REDSHIFT = 3


class Settings:
    def to_dict(self) -> dict:
        return {
            key: value
            for key, value in self.__dict__.items()
            if not key.startswith("pools")
        }

    def from_dict(self, data: dict) -> None:
        if not data:
            return

        for key, default in self.__dict__.items():
            setattr(self, key, data.get(key, default))


class MaterialSettings(Settings):
    def __init__(self):
        self.pools = {}
        self.current_pool = ""
        self.material_renderer = Renderer.VRAY.value
        self.render_scene = "Path/to/render/scene"
        self.render_object = "shaderball_object"
        self.render_cam = "render_cam"
        self.render_resolution_x = 350
        self.render_resolution_y = 350


class ModelSettings(Settings):
    def __init__(self):
        self.pools = {}
        self.current_pool = ""
        self.screenshot_opacity = 0.30


class HdriSettings(Settings):
    def __init__(self):
        self.pools = {}
        self.current_pool = ""
        self.hdri_renderer = Renderer.VRAY.value
        self.auto_generate_thumbnails = True


class LightsetSettings(Settings):
    def __init__(self):
        self.pools = {}
        self.current_pool = ""


class WindowSettings(Settings):
    def __init__(self) -> None:
        self.window_geometry = [100, 100, 1000, 700]
        self.current_viewport = ViewportMode.Materials.value
        self.asset_button_size = 350
        self.attribute_width = 300


class SettingsManager:
    CONFIG_PATH = (
        Path(__file__).parent.parent / f"settings/config-{socket.gethostname()}.json"
    )

    window_settings = WindowSettings()
    material_settings = MaterialSettings()
    model_settings = ModelSettings()
    hdri_settings = HdriSettings()
    lightset_settings = LightsetSettings()

    def load_settings(self):
        if not self.CONFIG_PATH.exists():
            self.save_settings()

        if not self.CONFIG_PATH.exists():
            Logger.error(f"settings path {self.CONFIG_PATH} does not exist")
            return

        with open(self.CONFIG_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)
            self.set_all_settings(data)

        try:
            materials, models, hdris, lightsets = api_handler.get_all_pools()
            self.material_settings.pools = materials
            self.model_settings.pools = models
            self.hdri_settings.pools = hdris
            self.lightset_settings.pools = lightsets
        except Exception as e:
            Logger.exception(e)

        Logger.info(f"loading settings from {self.CONFIG_PATH}")

    def save_settings(self):
        if not Path(self.CONFIG_PATH).parent.exists():
            Logger.error(f"settings path {self.CONFIG_PATH} does not exist")
            return

        with open(self.CONFIG_PATH, "w", encoding="utf-8") as file:
            data = self.get_all_settings()
            json.dump(data, file)

        Logger.info(f"saving settings to {self.CONFIG_PATH}")

    def get_all_settings(self) -> dict:
        return {
            "window_settings": self.window_settings.to_dict(),
            "material_settings": self.material_settings.to_dict(),
            "model_settings": self.model_settings.to_dict(),
            "hdri_settings": self.hdri_settings.to_dict(),
            "lightset_settings": self.lightset_settings.to_dict(),
        }

    def set_all_settings(self, data: dict) -> None:
        if not data:
            return

        self.window_settings.from_dict(data.get("window_settings"))
        self.material_settings.from_dict(data.get("material_settings"))
        self.model_settings.from_dict(data.get("model_settings"))
        self.hdri_settings.from_dict(data.get("hdri_settings"))
        self.lightset_settings.from_dict(data.get("lightset_settings"))
