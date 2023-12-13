from __future__ import annotations
from pathlib import Path
from datetime import datetime

from PySide2.QtWidgets import QMainWindow, QHBoxLayout, QWidget
from PySide2.QtGui import QIcon
from maya import OpenMayaUI
from shiboken2 import wrapInstance
from PySide2.QtCore import Qt

from .ui_components import Sidebar, AttributeEditor
from .viewport_container import ViewportContainer, ViewportMode
from ..controller import Logger, SettingsManager
from .version import get_version


def get_maya_main_window():
    main_window_ptr = OpenMayaUI.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QMainWindow)


class MainWindow(QWidget):
    win_instance = None

    ROOT_PATH = Path(__file__).parent.parent
    LOGGING_PATH = str(ROOT_PATH / f"logs/{datetime.now().date()}.log")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = SettingsManager()
        self.setWindowTitle(f"Render Vault - {get_version()}")
        self.setWindowIcon(QIcon(":icons/tabler-icon-packages.png"))
        self.setWindowFlag(Qt.WindowType.Window)
        # self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        Logger.write_to_file(MainWindow.LOGGING_PATH)
        Logger.set_propagate(False)
        Logger.info("starting Render Vault...")

        self.init_widgets()
        self.init_layouts()
        self.init_signals()

        self.load_settings(initial=True)

    @classmethod
    def show_window(cls) -> MainWindow:
        if not cls.win_instance:
            cls.win_instance = MainWindow(parent=get_maya_main_window())
            cls.win_instance.show()
        elif cls.win_instance.isHidden():
            cls.win_instance.show()
            cls.win_instance.load_settings()
        else:
            cls.win_instance.showNormal()
            cls.win_instance.load_settings()

        return cls.win_instance

    def init_widgets(self):
        self.sidebar = Sidebar()
        self.attribute = AttributeEditor()
        self.vp_container = ViewportContainer(self.settings, self.attribute)

    def init_layouts(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.vp_container)
        self.main_layout.addWidget(self.attribute)

    def init_signals(self):
        s = self.sidebar
        c = self.vp_container

        s.materials.clicked.connect(lambda: c.set_mode(ViewportMode.Materials))
        s.models.clicked.connect(lambda: c.set_mode(ViewportMode.Models))
        s.hdris.clicked.connect(lambda: c.set_mode(ViewportMode.Hdri))
        s.lightsets.clicked.connect(lambda: c.set_mode(ViewportMode.Lightsets))
        s.utilities.clicked.connect(lambda: c.set_mode(ViewportMode.Utility))
        s.help.clicked.connect(lambda: c.set_mode(ViewportMode.Help))
        s.about.clicked.connect(lambda: c.set_mode(ViewportMode.About))
        s.settings.clicked.connect(lambda: c.set_mode(ViewportMode.Settings))

        c.settings_vp.save.clicked.connect(self.save_and_update_settings)

    def closeEvent(self, event):
        self.save_settings()

    def load_settings(self, initial=False):
        self.settings.load_settings()
        self.read_from_settings_manager(initial=initial)

    def save_settings(self):
        self.write_to_settings_manager()
        self.settings.save_settings()

    def write_to_settings_manager(self):
        self.settings.window_settings.window_geometry = [
            self.geometry().x(),
            self.geometry().y(),
            self.width(),
            self.height(),
        ]
        self.vp_container.write_to_settings_manager()

    def read_from_settings_manager(self, initial=False):
        x, y, w, h = tuple(self.settings.window_settings.window_geometry)
        self.resize(w, h)
        self.move(x, y)

        self.vp_container.read_from_settings_manager(initial=initial)
        self.attribute.update_size(self.settings.window_settings.attribute_width)

        current_vp = self.settings.window_settings.current_viewport
        self.sidebar.highlight_modes(current_vp)

    def save_and_update_settings(self):
        self.save_settings()
        self.vp_container.read_from_settings_manager()
