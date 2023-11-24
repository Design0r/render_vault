from functools import partial
from pathlib import Path

from PySide2.QtCore import QCoreApplication, Qt, QThread
from PySide2.QtWidgets import QAction, QLabel, QLineEdit, QMenu

from ....controller import DCCHandler, HdrThreadWorker, PoolHandler, SettingsManager
from ..buttons import IconButton, ViewportButton
from ..separator import VLine
from .base_viewport import AssetViewport


class HdriViewport(AssetViewport):
    def __init__(
        self,
        settings: SettingsManager,
        pool_handler: PoolHandler,
        dcc_handler: DCCHandler,
        parent=None,
    ):
        super().__init__(parent)
        self.settings = settings
        self.dcc_handler = dcc_handler
        self.pool_handler = pool_handler

        self.live_mode = False
        self.thread_running = False

    def init_widgets(self):
        super().init_widgets()
        self.label = QLabel("HDRIs")
        self.label.setContentsMargins(10, 0, 0, 0)

        size = (40, 40)

        self.open_folder = IconButton(size)
        self.open_folder.set_icon(":icons/tabler-icon-folder-open.png", size)
        self.export_hdri = IconButton(size)
        self.export_hdri.set_icon(":icons/tabler-icon-file-export.png", size)

        self.import_hdri = IconButton(size)
        self.import_hdri.set_icon(":icons/tabler-icon-file-import.png", size)
        self.start_live = IconButton(size)
        self.start_live.set_icon(":icons/tabler-icon-live-photo.png", size)
        self.stop_live = IconButton(size)
        self.stop_live.set_icon(":icons/tabler-icon-live-photo-off.png", size)

        self.render_thumbnail = IconButton(size)
        self.render_thumbnail.set_icon(":icons/tabler-icon-photo.png", size)
        self.render_thumbnail.set_tooltip(
            "Render Thumbnails for all HDRIs in the current Pool"
        )

        self.reload = IconButton(size)
        self.reload.set_icon(":icons/tabler-icon-reload.png", size)
        self.reload.set_tooltip("Reload the current Pool")

        self.search_bar = QLineEdit(placeholderText="Search")
        self.search_bar.setFixedSize(250, 40)

    def init_layouts(self):
        super().init_layouts()
        self.toolbar.main_layout.addWidget(self.start_live)
        self.toolbar.main_layout.addWidget(self.stop_live)
        self.toolbar.main_layout.addWidget(VLine())
        self.toolbar.main_layout.addWidget(self.render_thumbnail)
        self.toolbar.main_layout.addWidget(VLine())
        self.toolbar.main_layout.addWidget(self.reload)
        self.toolbar.main_layout.addWidget(VLine())
        self.toolbar.main_layout.addWidget(self.search_bar)
        self.toolbar.main_layout.addStretch()

    def init_signals(self):
        super().init_signals()
        self.reload.clicked.connect(lambda: self.draw_objects(force=True))
        self.render_thumbnail.clicked.connect(self.create_hdr_thumbnails)
        self.search_bar.textChanged.connect(self.search)

    def load_pools(self):
        self.pools = self.settings.hdri_settings.pools
        super().load_pools()

    def draw_objects(self, force=False):
        _, path = self.get_current_project()
        if not path:
            return

        self.clear_layout()

        width = self.settings.window_settings.asset_button_size
        assets = self.pool_handler.get_assets_and_thumbnails(path)

        for hdr_name, hdr_path, thumb, hdr_size in assets:
            if not force and hdr_path in self._button_cache:
                self.flow_layout.addWidget(self._button_cache[hdr_path])
                continue

            btn_size = (width, (width // 2) + 10)
            suffix = hdr_path.suffix

            btn = ViewportButton(hdr_name, btn_size, hdr_size, suffix)
            btn.icon.set_icon(
                thumb or ":icons/tabler-icon-photo.png",
                (width - 20, (width // 2)),
            )

            btn.setContextMenuPolicy(Qt.CustomContextMenu)
            btn.customContextMenuRequested.connect(
                partial(self.on_context_menu, btn, hdr_path)
            )

            self.flow_layout.addWidget(btn)
            self._button_cache[hdr_path] = btn

        super().draw_objects(force=force)
        if force:
            self.create_hdr_thumbnails()

    def on_context_menu(self, button: ViewportButton, path: Path, point):
        import_dome = QAction("Import as Domelight", self)
        import_dome.triggered.connect(lambda: self.dcc_handler.create_domelight(path))
        import_area = QAction("Import as Arealight", self)
        import_area.triggered.connect(lambda: self.dcc_handler.create_arealight(path))
        import_file = QAction("Import as File Node", self)
        import_file.triggered.connect(lambda: self.dcc_handler.create_file_node(path))

        delete_btn = QAction("Delete HDRI", self)
        delete_btn.triggered.connect(lambda: self.delete_asset(path, button))

        pop_menu = QMenu(self)
        pop_menu.addAction(import_dome)
        pop_menu.addAction(import_area)
        pop_menu.addAction(import_file)
        pop_menu.addSeparator()
        pop_menu.addAction(delete_btn)

        pop_menu.exec_(button.mapToGlobal(point))

    def refresh_thumbnail(self, data: tuple[Path, Path]):
        hdr_path, thumbnail_path = data
        width = self.settings.window_settings.asset_button_size

        btn = self._button_cache.get(hdr_path)
        if not btn:
            return

        btn.icon.set_icon(str(thumbnail_path), (width - 20, (width // 2)))
        btn.update()
        QCoreApplication.processEvents()

    def create_hdr_thumbnails(self):
        if self.thread_running:
            return

        self.thread_running = True
        self.hdr_thread = QThread(self)

        _, path = self.get_current_project()
        if not path:
            return

        width = self.settings.window_settings.asset_button_size

        self.hdr_worker = HdrThreadWorker(self.pool_handler, path, width)

        self.hdr_worker.operation_ended.connect(self.render_worker_ended)
        self.hdr_worker.refresh_thumb.connect(self.refresh_thumbnail)
        self.hdr_thread.started.connect(self.hdr_worker.run)
        self.hdr_thread.finished.connect(self.hdr_thread.deleteLater)

        self.hdr_worker.moveToThread(self.hdr_thread)
        self.hdr_thread.start()

    def render_worker_ended(self):
        self.hdr_worker.deleteLater()
        self.hdr_thread.quit()
        self.thread_running = False

    def start_live_mode(self):
        pass

    def stop_live_mode(self):
        pass
