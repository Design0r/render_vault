from functools import partial
from pathlib import Path

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QAction, QMenu

from ....controller import DCCHandler, PoolHandler, SettingsManager
from ..buttons import IconButton, ViewportButton
from ..separator import VLine
from .base_viewport import AssetViewport


class UtilityVieport(AssetViewport):
    def __init__(
        self,
        pool_handler: PoolHandler,
        dcc_handler: DCCHandler,
        settings: SettingsManager,
        parent=None,
    ):
        super().__init__(parent)
        self.settings = settings
        self.pool_handler = pool_handler
        self.dcc_handler = dcc_handler

    def init_widgets(self):
        super().init_widgets()
        self.label.setText("Utilities")

        size = self.toolbar_btn_size

        self.reload = IconButton(size)
        self.reload.set_icon(":icons/tabler-icon-reload.png", size)
        self.reload.set_tooltip("Reload the current Pool")

        self.export_settings = IconButton(size)
        self.export_settings.set_icon(":icons/tabler-icon-file-export.png", size)
        self.export_settings.set_tooltip("Export current Render Settings from Maya")

    def init_layouts(self):
        super().init_layouts()
        self.toolbar.main_layout.addWidget(self.export_settings)
        self.toolbar.main_layout.addWidget(VLine())
        self.toolbar.main_layout.addWidget(self.reload)
        self.toolbar.main_layout.addStretch()

    def init_signals(self):
        super().init_signals()
        self.reload.clicked.connect(self.draw_objects)

    def draw_objects(self, force=False):
        width = self.settings.window_settings.asset_button_size
        self.clear_layout()

        assets = self.pool_handler.get_assets_and_thumbnails("")
        for name, path, _, size in assets:
            btn_size = (width, width)
            suffix = path.suffix

            btn = ViewportButton(name, btn_size, size, suffix)
            btn.icon.set_icon(":icons/tabler-icon-script.png", (width - 20, width - 20))
            btn.setContextMenuPolicy(Qt.CustomContextMenu)
            btn.customContextMenuRequested.connect(
                partial(self.on_context_menu, btn, path)
            )

            self.flow_layout.addWidget(btn)

        super().draw_objects(force=force)

    def on_context_menu(self, button: ViewportButton, path: Path, point):
        tooltip = button.toolTip()

        import_btn = QAction(f"Import {tooltip}", self)
        import_btn.triggered.connect(
            lambda: self.dcc_handler.import_render_settings(path)
        )

        pop_menu = QMenu(self)
        pop_menu.addAction(import_btn)

        pop_menu.exec_(button.mapToGlobal(point))
