from pathlib import Path

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QComboBox, QLabel, QScrollArea, QVBoxLayout, QWidget
import time

from ....controller import DCCHandler, Logger, PoolHandler, SettingsManager
from ...qss import toolbar_style
from ...ui_components import (
    FlowLayout,
    IconButton,
    Toolbar,
    ToolbarDirection,
    ViewportButton,
)
from typing import Callable

from ..dialogs import CreatePoolDialog, DeletePoolDialog
from ..separator import VLine


def benchmark(func: Callable) -> Callable:
    def wrapper(*args, **kwargs) -> None:
        start = time.perf_counter()
        func(*args, **kwargs)
        stop = time.perf_counter()
        Logger.debug(f"executed {func.__qualname__} in {stop-start:.3f}s")

    return wrapper


class AssetViewport(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui_scale = SettingsManager.window_settings.ui_scale
        self.toolbar_btn_size = (20 * self.ui_scale, 20 * self.ui_scale)
        self.dcc_handler: DCCHandler
        self.pool_handler: PoolHandler
        self.pools = {}
        self._button_cache: dict[Path, ViewportButton] = {}

        self.init_widgets()
        self.init_layouts()
        self.init_signals()

    def init_widgets(self):
        self.toolbar = Toolbar(ToolbarDirection.Horizontal, 25 * self.ui_scale)
        self.toolbar.setStyleSheet(toolbar_style)

        self.label = QLabel("Base Label")
        self.label.setContentsMargins(0, 0, 0, 0)

        self.pool_box = QComboBox()
        # self.pool_box.setFixedWidth(125 * self.ui_scale)
        self.pool_box.setFixedHeight(self.toolbar_btn_size[0])

        self.add_project = IconButton(self.toolbar_btn_size)
        self.add_project.set_icon(
            ":icons/tabler-icon-folder-plus.png", self.toolbar_btn_size
        )
        self.remove_project = IconButton(self.toolbar_btn_size)
        self.remove_project.set_icon(
            ":icons/tabler-icon-folder-minus.png", self.toolbar_btn_size
        )
        self.open_folder = IconButton(self.toolbar_btn_size)
        self.open_folder.set_icon(
            ":icons/tabler-icon-folder-open.png", self.toolbar_btn_size
        )

        self.grid_widget = QWidget()
        self.grid_widget.setContentsMargins(5, 5, 5, 5)
        self.scroll_area = QScrollArea()
        self.scroll_area.setFocusPolicy(Qt.NoFocus)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setWidget(self.grid_widget)

    def init_layouts(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.toolbar.main_layout.addWidget(self.label)
        self.toolbar.main_layout.addWidget(VLine())
        self.toolbar.main_layout.addWidget(self.pool_box)
        self.toolbar.main_layout.addWidget(self.add_project)
        self.toolbar.main_layout.addWidget(self.remove_project)
        self.toolbar.main_layout.addWidget(self.open_folder)
        self.toolbar.main_layout.addWidget(VLine())

        self.flow_layout = FlowLayout(self.grid_widget)
        self.flow_layout.setSpacing(0)

        self.main_layout.addWidget(self.toolbar)
        self.main_layout.addWidget(self.scroll_area)

    def init_signals(self):
        self.add_project.clicked.connect(self.open_new_pool_dialog)
        self.remove_project.clicked.connect(self.open_delete_pool_dialog)
        self.open_folder.clicked.connect(self.open_pool_directory)
        self.pool_box.currentIndexChanged.connect(
            lambda: self.draw_objects(force=False)
        )

    def clear_layout(self):
        while self.flow_layout.count():
            widget = self.flow_layout.takeAt(0).widget()
            widget.icon.setChecked(False)
            widget.setParent(None)

    def draw_objects(self, force=False):
        Logger.debug(
            f"{'force ' if force else ''}reloaded {self.label.text()} pool: {self.pool_box.currentText()}"
        )

    def search(self, input):
        if not input:
            self.draw_objects()

        _, path = self.get_current_project()
        path = str(Path(path))

        for k, v in self._button_cache.items():
            if not path in str(k):
                continue
            if input.lower() in k.stem.lower():
                if not v.parent():
                    self.flow_layout.addWidget(v)
                continue

            v.setParent(None)

    def open_new_pool_dialog(self):
        create_pool_dialog = CreatePoolDialog()
        create_pool_dialog.pool_created.connect(self.create_new_pool)
        create_pool_dialog.exec_()

    def open_delete_pool_dialog(self):
        delete_pool_dialog = DeletePoolDialog()
        delete_pool_dialog.pool_deleted.connect(self.delete_pool)
        delete_pool_dialog.exec_()

    def create_new_pool(self, pool: tuple):
        name, path = pool
        if not name or not path:
            return

        self.pool_handler.create_pool(name, path)

        self.pool_box.addItem(name)
        self.pool_box.setCurrentText(name)
        self.pools[name] = path
        self.draw_objects()

    def delete_pool(self):
        if not self.pools:
            return

        self.clear_layout()

        current_pool = self.pool_box.currentIndex()
        current_pool_text = self.pool_box.currentText()
        self.pool_box.removeItem(current_pool)

        path = self.pools.get(current_pool_text, "")
        self.pool_handler.delete_pool(current_pool_text, path)

        Logger.info(f"deleting current pool {current_pool_text}")
        self.pools.pop(current_pool_text)

    def open_pool_directory(self):
        _, path = self.get_current_project()
        if not path:
            return

        self.pool_handler.open_pool_dir(path)

    def get_current_project(self) -> tuple:
        name = self.pool_box.currentText()
        if not name:
            return None, None

        path = self.pools.get(name)
        return name, path

    def load_pools(self):
        if not self.pools:
            return

        # self.pool_box.blockSignals(True)
        self.pool_box.clear()
        for name, _ in self.pools.items():
            self.pool_box.addItem(name)

        # self.pool_box.blockSignals(False)

    def delete_asset(self, path: Path, btn: ViewportButton):
        btn.deleteLater()
        self.pool_handler.delete_asset(path)
        self._button_cache.pop(path)


class DataViewport(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui_scale = SettingsManager.window_settings.ui_scale
        self.setFocusPolicy(Qt.NoFocus)

        self.init_widgets()
        self.init_layouts()
        self.init_signals()

    def init_widgets(self):
        self.toolbar = Toolbar(ToolbarDirection.Horizontal, 25 * self.ui_scale)
        self.toolbar.setStyleSheet(toolbar_style)
        self.settings_widget = QWidget()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.settings_widget)

    def init_layouts(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.settings_groups_layout = QVBoxLayout(self.settings_widget)

        self.main_layout.addWidget(self.toolbar)
        self.main_layout.addWidget(self.scroll_area)

    def init_signals(self):
        pass

    def draw_objects(self):
        pass
