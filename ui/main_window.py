from __future__ import annotations
from pathlib import Path
from datetime import datetime

from PySide2.QtWidgets import QMainWindow, QHBoxLayout, QSplitter, QWidget
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
    LOGS = ROOT_PATH / "logs"
    LOGGING_PATH = LOGS / f"{datetime.now().date()}.log"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = SettingsManager()
        self.setWindowTitle(f"Render Vault - {get_version()}")
        self.setWindowIcon(QIcon(":icons/tabler-icon-packages.png"))
        self.setWindowFlag(Qt.WindowType.Window)

        MainWindow.LOGS.mkdir(exist_ok=True)
        Logger.write_to_file(MainWindow.LOGGING_PATH)
        Logger.set_propagate(False)
        Logger.info("starting Render Vault...")

        self.settings.load_settings()
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
        self.sidebar = Sidebar(self.settings)
        self.attribute = AttributeEditor()
        self.vp_container = ViewportContainer(self.settings, self.attribute)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setOpaqueResize(True)
        self.splitter.addWidget(self.vp_container)
        self.splitter.addWidget(self.attribute)

    def init_layouts(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.splitter)

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
        s.settings_btn.clicked.connect(lambda: c.set_mode(ViewportMode.Settings))

        c.settings_vp.save.clicked.connect(self.save_and_update_settings)

    def closeEvent(self, event):
        self.save_settings()

    def hideEvent(self, event):
        self.save_settings()

    def load_settings(self, initial=False):
        if not initial:
            self.settings.load_settings()
        self.read_from_settings_manager(initial=initial)

    def save_settings(self):
        self.write_to_settings_manager()
        self.settings.save_settings()

    def write_to_settings_manager(self):
        self.settings.window_settings.window_geometry = [
            self.x(),
            self.y(),
            self.width(),
            self.height(),
        ]
        self.vp_container.write_to_settings_manager()

    def read_from_settings_manager(self, initial=False):
        x, y, w, h = self.settings.window_settings.window_geometry
        self.resize(w, h)
        self.move(x, y)

        self.vp_container.read_from_settings_manager(initial=initial)

        current_vp = self.settings.window_settings.current_viewport
        self.sidebar.highlight_modes(current_vp)

    def save_and_update_settings(self):
        self.save_settings()
        self.vp_container.read_from_settings_manager()
