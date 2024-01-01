import time
from functools import partial
from pathlib import Path
import json
from PySide2.QtCore import QCoreApplication, Qt, QThread
from PySide2.QtWidgets import QAction, QLineEdit, QMenu, QPushButton

from ....controller import (
    DCCHandler,
    Logger,
    MayaThreadWorker,
    ModelPoolHandler,
    SettingsManager,
    core,
)
from ..buttons import IconButton, ViewportButton
from ..attribute_editor import AttributeEditor
from ..dialogs import ArchiveViewerDialog, ExportModelDialog
from ..screenshot import ScreenshotFrame
from ..separator import VLine
from .base_viewport import AssetViewport


class ModelsViewport(AssetViewport):
    def __init__(
        self,
        settings: SettingsManager,
        attribute: AttributeEditor,
        pool_handler: ModelPoolHandler,
        dcc_handler: DCCHandler,
        parent=None,
    ):
        self.settings = settings
        self.attribute = attribute
        self.pool_handler = pool_handler
        self.dcc_handler = dcc_handler
        super().__init__(parent)

    def init_widgets(self):
        super().init_widgets()

        self.label.setText("Models")

        size = self.toolbar_btn_size

        self.export_selected = IconButton(size)
        self.export_selected.set_icon(":icons/tabler-icon-package-export.png", size)
        self.export_selected.set_tooltip("Export selected Model from Maya")

        self.archive_viewer = IconButton(size)
        self.archive_viewer.set_icon(":icons/tabler-icon-archive.png", size)
        self.archive_viewer.set_tooltip("View Model Archive")

        self.reload = IconButton(size)
        self.reload.set_icon(":icons/tabler-icon-reload.png", size)
        self.reload.set_tooltip("Reload the current Pool")

        self.search_bar = QLineEdit(placeholderText="Search")
        self.search_bar.setFixedHeight(20 * self.ui_scale)

    def init_layouts(self):
        super().init_layouts()
        self.toolbar.main_layout.addWidget(self.export_selected)
        self.toolbar.main_layout.addWidget(self.archive_viewer)
        self.toolbar.main_layout.addWidget(VLine())
        self.toolbar.main_layout.addWidget(self.reload)
        self.toolbar.main_layout.addWidget(VLine())
        self.toolbar.main_layout.addWidget(self.search_bar)
        self.toolbar.main_layout.addStretch()

    def init_signals(self):
        super().init_signals()
        self.export_selected.clicked.connect(self.open_export_model_dialog)
        self.reload.clicked.connect(lambda: self.draw_objects(force=True))
        self.archive_viewer.clicked.connect(self.open_archive_viewer)
        self.search_bar.textChanged.connect(self.search)
        self.attribute.tag_selected.connect(self.filter_tags)

    def filter_tags(self, clicked_tag: QPushButton):
        text, checked = clicked_tag.text(), clicked_tag.isChecked()
        if not checked:
            self.draw_objects()
            return

        _, path = self.get_current_project()
        path = Path(path)
        metadata_path = path / "ModelPool" / "Metadata"
        if not metadata_path.exists():
            metadata_path.mkdir()

        tags = (file for file in metadata_path.iterdir() if file.suffix == ".json")

        self.clear_layout()

        for file in tags:
            with open(file, "r") as f:
                data = json.load(f)
                tags = data.get("tags", [])
                file_path = Path(data.get("path", ""))

                if text in tags:
                    self.flow_layout.addWidget(self._button_cache[file_path])

    def load_pools(self):
        self.pool_box.blockSignals(True)
        self.pools = self.settings.model_settings.pools
        super().load_pools()
        current_pool = self.settings.model_settings.current_pool
        if current_pool:
            self.pool_box.setCurrentText(current_pool)
        self.pool_box.blockSignals(False)

    def open_export_model_dialog(self):
        _, path = self.get_current_project()
        if not path:
            Logger.error("no existing project")
            return
        path = Path(path, "ModelPool", "Models")

        self.export_model_dialog = ExportModelDialog(self.dcc_handler, path)
        self.export_model_dialog.model_exported.connect(self.draw_objects)
        self.export_model_dialog.repath.connect(self.repath_material_textures)
        self.export_model_dialog.exec_()

    def open_archive_viewer(self):
        _, path = self.get_current_project()
        if not path:
            Logger.error("no existing project")
            return
        path = Path(path, "ModelPool", "Archive")

        if not path.exists():
            try:
                path.mkdir()
            except Exception as e:
                Logger.exception(e)

        viewer = ArchiveViewerDialog(self.pool_handler, self.dcc_handler, path)
        viewer.exec_()

    def draw_objects(self, force=False):
        _, path = self.get_current_project()
        if not path:
            return

        width = self.settings.window_settings.asset_button_size

        self.clear_layout()
        assets = self.pool_handler.get_assets_and_thumbnails(path)
        for model, model_path, thumb, size in assets:
            if not force and model_path in self._button_cache:
                self.flow_layout.addWidget(self._button_cache[model_path])
                continue

            btn = ViewportButton(
                model, (width, width), size, model_path.suffix, checkable=True
            )
            btn.icon.set_icon(
                thumb or ":icons/tabler-icon-photo.png", (width - 20, width - 20)
            )
            btn.icon.clicked.connect(partial(self.attribute.display_asset, model_path))

            btn.setContextMenuPolicy(Qt.CustomContextMenu)
            btn.customContextMenuRequested.connect(
                partial(self.on_context_menu, btn, model_path)
            )
            self.flow_layout.addWidget(btn)
            self._button_cache[model_path] = btn

        if not self.attribute.current_asset:
            self.attribute.display_asset(next(iter(self._button_cache)))

        super().draw_objects(force=force)

    def on_context_menu(self, button: ViewportButton, path: Path, point):
        selected = [
            path for path, btn in self._button_cache.items() if btn.icon.isChecked()
        ]

        multi_path = selected or path
        tooltip = button.toolTip()

        open_btn = QAction("Open Scene", self)
        open_btn.triggered.connect(lambda: self.dcc_handler.open_scene(path))

        import_btn = QAction("Import Model", self)
        import_btn.triggered.connect(lambda: self.dcc_handler.import_model(multi_path))

        reference_btn = QAction("Reference Model", self)
        reference_btn.triggered.connect(
            lambda: self.dcc_handler.reference_model(multi_path)
        )

        delete_btn = QAction("Delete Model", self)
        delete_btn.triggered.connect(lambda: self.delete_asset(path, button))

        render_btn = QAction("Create Thumbnail", self)
        render_btn.triggered.connect(lambda: self.show_screenshot_frame(tooltip, path))

        archive = QAction("Archive and Replace", self)
        archive.triggered.connect(lambda: self.archive_and_replace(path))

        pop_menu = QMenu(self)

        pop_menu.addAction(open_btn)
        pop_menu.addSeparator()
        pop_menu.addAction(import_btn)
        pop_menu.addAction(reference_btn)
        pop_menu.addSeparator()
        pop_menu.addAction(archive)
        pop_menu.addSeparator()
        pop_menu.addAction(render_btn)
        pop_menu.addSeparator()
        pop_menu.addAction(delete_btn)

        pop_menu.exec_(button.mapToGlobal(point))

    def take_screenshot(self, data):
        geometry, model_name, model_path = data
        self.screenshot_frame.setVisible(False)
        QCoreApplication.processEvents()

        _, path = self.get_current_project()
        if not path:
            return
        time.sleep(0.2)
        screen_path = Path(path, "ModelPool", "Thumbnails", f"{model_name}.jpg")

        core.take_screenshot(screen_path, geometry)
        self.refresh_thumbnail(str(screen_path), model_path)

    def refresh_thumbnail(self, screen_path: str, model_path: str):
        width = self.settings.window_settings.asset_button_size
        btn = self._button_cache.get(model_path)
        if not btn:
            return

        btn.icon.set_icon(screen_path, (width - 20, width - 20))
        btn.update()

    def show_screenshot_frame(self, model_name, path):
        self.screenshot_frame = ScreenshotFrame(model_name, path)
        self.screenshot_frame.take_screenshot.connect(self.take_screenshot)
        self.screenshot_frame.exec_()

    def repath_material_textures(self, model):
        name, extension = model
        _, path = self.get_current_project()
        if not path:
            return
        model_path = str(Path(path, "ModelPool", "Models", f"{name}.{extension}"))

        command = self.dcc_handler.repath_textures_cmd(
            path, materials="None", model=model_path, mode=1
        )
        self.repath_thread = QThread(self)
        self.repath_worker = MayaThreadWorker(command)

        self.repath_worker.operation_ended.connect(self.repath_worker_ended)

        self.repath_thread.started.connect(self.repath_worker.run)
        self.repath_thread.finished.connect(self.repath_thread.deleteLater)

        self.repath_worker.moveToThread(self.repath_thread)
        self.repath_thread.start()

    def repath_worker_ended(self):
        self.repath_worker.deleteLater()
        self.repath_thread.quit()

    def archive_and_replace(self, path: Path):
        self.pool_handler.archive_asset(path)
        self.dcc_handler.save_scene_as(path)
