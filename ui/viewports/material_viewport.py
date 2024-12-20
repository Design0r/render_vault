from functools import partial
from pathlib import Path

from Qt.QtCore import Qt, QThread
from Qt.QtWidgets import QAction, QLineEdit, QMenu

from ...controller import (
    Logger,
    MaterialPoolHandler,
    MayaHandler,
    MayaThreadWorker,
    SettingsManager,
)
from ...core import utils
from ..ui_components.attribute_editor import AttributeEditor
from ..ui_components.buttons import IconButton, ViewportButton
from ..ui_components.dialogs import ArchiveViewerDialog, ExportMaterialsDialog
from ..ui_components.separator import VLine
from .base_viewport import AssetViewport


class MaterialsViewport(AssetViewport):
    metadata_path = Path("MaterialPool/Metadata")

    def __init__(
        self,
        attribute: AttributeEditor,
        parent=None,
    ):
        super().__init__(attribute=attribute, parent=parent)
        self.settings = SettingsManager()
        self.pool_handler = MaterialPoolHandler()
        self.dcc_handler = MayaHandler()
        self.tag_cache = {}

    def init_widgets(self):
        super().init_widgets()
        self.label.setText("Materials")
        self.label.setContentsMargins(10, 0, 0, 0)

        self.add_project.setToolTip("Create new Material Pool")
        self.remove_project.setToolTip("Delete current Material Pool")
        self.open_folder.setToolTip("Open current Material Pool in the File Explorer")

        size = self.toolbar_btn_size

        self.export_selected = IconButton(size)
        self.export_selected.set_icon(":icons/tabler-icon-file-export.png", size)
        self.export_selected.set_tooltip("Export selected Materials from Maya")

        self.render_materials = IconButton(size)
        self.render_materials.set_icon(":icons/tabler-icon-photo.png", size)
        self.render_materials.set_tooltip(
            "Render Thumbnails for all Materials in the current Pool"
        )

        self.repath = IconButton(size)
        self.repath.set_icon(":icons/tabler-icon-route.png", size)
        self.repath.set_tooltip("Copy and Repath Textures of the current Pool")

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
        self.toolbar.main_layout.addWidget(self.render_materials)
        self.toolbar.main_layout.addWidget(self.repath)
        self.toolbar.main_layout.addWidget(VLine())
        self.toolbar.main_layout.addWidget(self.reload)
        self.toolbar.main_layout.addWidget(VLine())
        self.toolbar.main_layout.addWidget(self.search_bar)
        self.toolbar.main_layout.addStretch()

    def init_signals(self):
        super().init_signals()
        self.export_selected.clicked.connect(self.open_export_materials_dialog)
        self.archive_viewer.clicked.connect(self.open_archive_viewer)
        self.render_materials.clicked.connect(self.render_material_thumbnails)
        self.reload.clicked.connect(lambda: self.draw_objects(force=True))
        self.repath.clicked.connect(self.repath_material_textures)
        self.search_bar.textChanged.connect(self.search)

    def load_pools(self):
        self.pool_box.blockSignals(True)

        self.pools = self.settings.material_settings.pools
        super().load_pools()
        current_pool = self.settings.material_settings.current_pool
        if current_pool:
            self.pool_box.setCurrentText(current_pool)
        self.pool_box.blockSignals(False)

    def open_export_materials_dialog(self):
        _, path = self.get_current_project()
        if not path:
            Logger.error("no existing project")
            return
        path = Path(path, "MaterialPool", "Materials")

        export_materials_dialog = ExportMaterialsDialog(self.dcc_handler, path)
        export_materials_dialog.materials_exported.connect(self.draw_objects)
        export_materials_dialog.repath.connect(self.repath_material_textures)
        export_materials_dialog.exec_()

    def open_archive_viewer(self):
        _, path = self.get_current_project()
        if not path:
            Logger.error("no existing project")
            return
        path = Path(path, "MaterialPool", "Archive")

        if not path.exists():
            try:
                path.mkdir()
            except Exception as e:
                Logger.exception(e)

        viewer = ArchiveViewerDialog(self.pool_handler, self.dcc_handler, path)
        viewer.exec_()

    @utils.benchmark
    def draw_objects(self, force=False):
        _, path = self.get_current_project()
        if not path:
            return

        btn_width = self.settings.window_settings.asset_button_size
        btn_size = btn_width, btn_width
        icon_size = btn_width - 20, btn_width - 20
        self.clear_layout()

        assets = self.pool_handler.get_assets_and_thumbnails(path)
        for mtl, mtl_path, thumb, size in assets:
            if not force and mtl_path in self._button_cache:
                self.flow_layout.addWidget(self._button_cache[mtl_path])
                continue

            suffix = mtl_path.suffix

            btn = ViewportButton(mtl, btn_size, size, suffix, checkable=True)
            btn.icon.set_icon(
                thumb or ":icons/tabler-icon-photo.png",
                icon_size,
            )
            btn.setContextMenuPolicy(Qt.CustomContextMenu)
            btn.customContextMenuRequested.connect(
                partial(self.on_context_menu, btn, mtl_path)
            )
            btn.icon.clicked.connect(partial(self.attribute.display_asset, mtl_path))
            self.flow_layout.addWidget(btn)
            self._button_cache[mtl_path] = btn

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

        import_btn = QAction("Import Shader", self)
        import_btn.triggered.connect(
            lambda: self.dcc_handler.import_material(multi_path, assign=False)
        )

        assign_btn = QAction("Import and assign to Selection", self)
        assign_btn.triggered.connect(
            lambda: self.dcc_handler.import_material(path, assign=True)
        )

        reference_btn = QAction("Reference Shader", self)
        reference_btn.triggered.connect(
            lambda: self.dcc_handler.reference_material(multi_path, assign=False)
        )

        reference_assign_btn = QAction("Reference and assign to Selection", self)
        reference_assign_btn.triggered.connect(
            lambda: self.dcc_handler.reference_material(multi_path, assign=True)
        )

        replace_btn = QAction("Replace Material in Scene", self)
        replace_btn.triggered.connect(
            lambda: self.dcc_handler.replace_material_in_scene(path)
        )

        archive = QAction("Archive and Replace", self)
        archive.triggered.connect(lambda: self.archive_and_replace(path))

        delete_btn = QAction("Delete Shader", self)
        delete_btn.triggered.connect(lambda: self.delete_asset(path, button))

        render_btn = QAction(f"Render {tooltip}", self)
        render_btn.triggered.connect(
            lambda: self.render_material_thumbnails(path=path, single=True)
        )

        pop_menu = QMenu(self)
        pop_menu.addAction(open_btn)
        pop_menu.addSeparator()
        pop_menu.addAction(import_btn)
        pop_menu.addAction(assign_btn)
        pop_menu.addAction(reference_btn)
        pop_menu.addAction(reference_assign_btn)
        pop_menu.addSeparator()
        pop_menu.addAction(replace_btn)
        pop_menu.addAction(archive)
        pop_menu.addSeparator()
        pop_menu.addAction(render_btn)
        pop_menu.addSeparator()
        pop_menu.addAction(delete_btn)

        pop_menu.exec_(button.mapToGlobal(point))

    def render_material_thumbnails(self, path=None, single=False):
        if not path:
            _, path = self.get_current_project()
            if not path:
                return
        if single:
            command = self.dcc_handler.render_single_material_cmd(path)
        else:
            command = self.dcc_handler.render_all_materials_cmd(path)

        self.render_thread = QThread(self)
        self.render_worker = MayaThreadWorker(command)

        self.render_worker.operation_ended.connect(self.render_worker_ended)

        self.render_thread.started.connect(self.render_worker.run)
        self.render_thread.finished.connect(self.render_thread.deleteLater)

        self.render_worker.moveToThread(self.render_thread)
        self.render_thread.start()

    def render_worker_ended(self):
        self.render_worker.deleteLater()
        self.render_thread.quit()
        self.draw_objects(force=True)

    def repath_material_textures(self, materials=None):
        _, path = self.get_current_project()
        if not path:
            return

        if not materials:
            assets = self.pool_handler.get_assets_and_thumbnails(path)
            materials = [mtl_name for mtl_name, _, _, _ in assets]

        command = self.dcc_handler.repath_textures_cmd(
            path, materials, model="None", mode=0
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
