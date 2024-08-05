from Qt.QtWidgets import QStackedWidget

from ...controller import SettingsManager
from ...core import Logger
from ..ui_components import AttributeEditor
from .about_viewport import AboutViewport
from .hdri_viewport import HdriViewport
from .help_viewport import HelpViewport
from .lightsets_viewport import LightsetsViewport
from .material_viewport import MaterialsViewport
from .model_viewport import ModelsViewport
from .settings_viewport import SettingsViewport
from .utility_viewport import UtilityVieport
from .viewport_mode import ViewportMode


class ViewportContainer(QStackedWidget):
    def __init__(self, attribute: AttributeEditor, parent=None):
        super().__init__(parent)
        self.viewport_mode = ViewportMode.Materials
        self.settings = SettingsManager()
        self.attribute = attribute
        self.init_widgets()
        self.init_layouts()

    def init_widgets(self):
        self.material_vp = MaterialsViewport(self.attribute)
        self.model_vp = ModelsViewport(self.attribute)
        self.hdri_vp = HdriViewport(self.attribute)
        self.lightsets_vp = LightsetsViewport(self.attribute)

        self.utility_vp = UtilityVieport()
        self.help_vp = HelpViewport()
        self.about_vp = AboutViewport()
        self.settings_vp = SettingsViewport()

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

        mat_name, _ = self.material_vp.get_current_project()
        self.settings.material_settings.current_pool = mat_name
        model_name, _ = self.model_vp.get_current_project()
        self.settings.model_settings.current_pool = model_name
        hdri_name, _ = self.hdri_vp.get_current_project()
        self.settings.hdri_settings.current_pool = hdri_name
        lightset_name, _ = self.lightsets_vp.get_current_project()

        self.settings.lightset_settings.current_pool = lightset_name
        self.settings_vp.write_to_settings_manager()
        Logger.debug("updated settings manager values.")

    def read_from_settings_manager(self, initial=False):
        self.settings_vp.read_from_settings_manager()

        self.material_vp.load_pools()
        self.model_vp.load_pools()
        self.hdri_vp.load_pools()
        self.lightsets_vp.load_pools()

        current_vp = self.settings.window_settings.current_viewport
        self.set_mode(ViewportMode(current_vp), initial=initial)

    def set_mode(self, mode: ViewportMode, initial=False):
        curr = self.currentWidget()
        if mode == ViewportMode.Materials:
            if initial:
                self.material_vp.draw_objects()
                return
            if curr == self.material_vp:
                return
            self.setCurrentWidget(self.material_vp)
            self.material_vp.draw_objects()

        elif mode == ViewportMode.Models:
            if curr == self.model_vp:
                return
            self.setCurrentWidget(self.model_vp)
            self.model_vp.draw_objects()

        elif mode == ViewportMode.Hdri:
            if curr == self.hdri_vp:
                return
            self.setCurrentWidget(self.hdri_vp)
            self.hdri_vp.draw_objects()

        elif mode == ViewportMode.Lightsets:
            if curr == self.lightsets_vp:
                return
            self.setCurrentWidget(self.lightsets_vp)
            self.lightsets_vp.draw_objects()

        elif mode == ViewportMode.Utility:
            if curr == self.utility_vp:
                return
            self.setCurrentWidget(self.utility_vp)
            self.utility_vp.draw_objects()

        elif mode == ViewportMode.Help:
            self.setCurrentWidget(self.help_vp)
        elif mode == ViewportMode.About:
            self.setCurrentWidget(self.about_vp)
        elif mode == ViewportMode.Settings:
            self.setCurrentWidget(self.settings_vp)

        self.viewport_mode = mode
