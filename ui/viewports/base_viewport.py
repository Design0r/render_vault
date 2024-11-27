import json
from pathlib import Path

from Qt.QtCore import Qt
from Qt.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ...controller.settings import SettingsManager
from ...core import Logger
from ..qss import toolbar_style
from ..ui_components import (
    FlowLayout,
    IconButton,
    Status,
    Statusbar,
    Toolbar,
    ToolbarDirection,
    ViewportButton,
)
from ..ui_components.dialogs import CreatePoolDialog, DeletePoolDialog
from ..ui_components.separator import VLine


class AssetViewport(QWidget):
    _register = []
    metadata_path: Path

    def __new__(cls, *args, **kwargs):
        if cls not in cls._register:
            cls._register.append(cls)

        return super().__new__(cls, *args, **kwargs)

    def __init__(self, attribute, parent=None):
        super().__init__(parent)

        self.attribute = attribute
        self.ui_scale = SettingsManager().window_settings.ui_scale
        self.toolbar_btn_size = (20 * self.ui_scale, 20 * self.ui_scale)
        self.pools = {}
        self._button_cache: dict[Path, ViewportButton] = {}
        self.settings = SettingsManager()

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

        self.statusbar = Statusbar(20 * self.ui_scale)

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

        self.infobar_layout = QHBoxLayout(self.statusbar)

        self.main_layout.addWidget(self.toolbar)
        self.main_layout.addWidget(self.scroll_area)
        self.main_layout.addWidget(self.statusbar)

    def init_signals(self):
        self.add_project.clicked.connect(self.open_new_pool_dialog)
        self.remove_project.clicked.connect(self.open_delete_pool_dialog)
        self.open_folder.clicked.connect(self.open_pool_directory)
        self.pool_box.currentIndexChanged.connect(
            lambda: self.draw_objects(force=False)
        )
        self.attribute.tag_selected.connect(self.filter_tags)

    def clear_layout(self):
        while self.flow_layout.count():
            widget = self.flow_layout.takeAt(0).widget()
            widget.icon.setChecked(False)
            widget.setParent(None)

    def draw_objects(self, force=False):
        text = f"{'force ' if force else ''}reloaded {self.label.text()} pool: {self.pool_box.currentText()}"
        Logger.info(text)
        self.statusbar.update_status(Status.Idle)

    def search(self, input: str):
        if not input:
            self.draw_objects()

        _, path = self.get_current_project()
        path = str(Path(path))

        for k, v in self._button_cache.items():
            if path not in str(k):
                continue
            if input.lower() in k.stem.lower():
                if v.parent():
                    continue
                self.flow_layout.addWidget(v)

            v.setParent(None)

    def filter_tags(self, clicked_tag: QPushButton):
        curr_vp_idx = self.settings.window_settings.current_viewport - 1

        if not isinstance(self, self._register[curr_vp_idx]):
            return

        text, checked = clicked_tag.text(), clicked_tag.isChecked()
        if not checked:
            self.draw_objects()
            return

        _, path = self.get_current_project()
        if not path:
            return
        metadata_path = Path(path) / self.metadata_path
        print(metadata_path)
        metadata_path.mkdir(exist_ok=True)

        self.clear_layout()

        for file in metadata_path.glob("*.json"):
            with open(file, "r") as f:
                data = json.load(f)

            tags = data.get("tags", [])
            file_path = Path(data.get("path", ""))

            if text not in tags:
                continue

            self.flow_layout.addWidget(self._button_cache[file_path])

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

        max_item_width = max(
            self.pool_box.fontMetrics().horizontalAdvance(item)
            for item in [
                self.pool_box.itemText(i) for i in range(self.pool_box.count())
            ]
        )
        self.pool_box.setMinimumWidth(max_item_width + 50)
        # self.pool_box.blockSignals(False)

    def delete_asset(self, path: Path, btn: ViewportButton):
        self.pool_handler.delete_asset(path)
        self._button_cache.pop(path)
        btn.deleteLater()


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
