from enum import Enum

from PySide2.QtWidgets import QStackedWidget

from ..controller import Logger
from ..controller import api_handler as api
from ..controller import dcc_handler as dcc
from ..controller import pool_handler as pool
from .ui_components import viewports as vp


class ViewportMode(Enum):
    Base = 0
    Materials = 1
    Models = 2
    Hdri = 3
    Lightsets = 4
    Utility = 5
    Help = 6
    About = 7
    Settings = 8


class ViewportContainer(QStackedWidget):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.viewport_mode = ViewportMode.Materials
        self.settings = settings
        self.init_widgets()
        self.init_layouts()

    def init_widgets(self):
        maya_handler = dcc.MayaHandler()

        material_api = api.MaterialAPIHandler()
        material_pool = pool.MaterialPoolHandler(material_api)
        self.material_vp = vp.MaterialsViewport(
            self.settings, material_pool, maya_handler
        )

        model_api = api.ModelAPIHandler()
        model_pool = pool.ModelPoolHandler(model_api)
        self.model_vp = vp.ModelsViewport(self.settings, model_pool, maya_handler)

        hdri_api = api.HDRIAPIHandler()
        hdri_pool = pool.HDRIPoolHandler(hdri_api)
        self.hdri_vp = vp.HdriViewport(self.settings, hdri_pool, maya_handler)

        lightsets_api = api.LightsetAPIHandler()
        lightsets_pool = pool.LightsetPoolHandler(lightsets_api)
        self.lightsets_vp = vp.LightsetsViewport(
            self.settings, lightsets_pool, maya_handler
        )

        util_pool = pool.UtilityPoolHandler()
        self.utility_vp = vp.UtilityVieport(util_pool, maya_handler, self.settings)
        self.help_vp = vp.HelpViewport()
        self.about_vp = vp.AboutViewport()
        self.settings_vp = vp.SettingsViewport(self.settings)

        self.setCurrentWidget(self.material_vp)

    def init_layouts(self):
        self.addWidget(self.material_vp)
        self.addWidget(self.model_vp)
        self.addWidget(self.hdri_vp)
        self.addWidget(self.lightsets_vp)
        self.addWidget(self.utility_vp)
        self.addWidget(self.help_vp)
        self.addWidget(self.about_vp)
        self.addWidget(self.settings_vp)

    def write_to_settings_manager(self):
        self.settings.window_settings.current_viewport = self.viewport_mode.value

        self.settings_vp.write_to_settings_manager()
        Logger.debug("updated settings manager values.")

    def read_from_settings_manager(self):
        self.settings_vp.read_from_settings_manager()

        self.material_vp.load_pools()
        self.model_vp.load_pools()
        self.hdri_vp.load_pools()
        self.lightsets_vp.load_pools()

        current_vp = self.settings.window_settings.current_viewport
        self.set_mode(ViewportMode(current_vp))

    def set_mode(self, mode: ViewportMode):
        if mode == ViewportMode.Materials:
            self.setCurrentWidget(self.material_vp)
            self.material_vp.draw_objects()
        elif mode == ViewportMode.Models:
            self.setCurrentWidget(self.model_vp)
            self.model_vp.draw_objects()
        elif mode == ViewportMode.Hdri:
            self.setCurrentWidget(self.hdri_vp)
            self.hdri_vp.draw_objects()
        elif mode == ViewportMode.Lightsets:
            self.setCurrentWidget(self.lightsets_vp)
            self.lightsets_vp.draw_objects()
        elif mode == ViewportMode.Utility:
            self.setCurrentWidget(self.utility_vp)
            self.utility_vp.draw_objects()
        elif mode == ViewportMode.Help:
            self.setCurrentWidget(self.help_vp)
        elif mode == ViewportMode.About:
            self.setCurrentWidget(self.about_vp)
        elif mode == ViewportMode.Settings:
            self.setCurrentWidget(self.settings_vp)

        self.viewport_mode = mode
