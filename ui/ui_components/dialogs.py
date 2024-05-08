from pathlib import Path
import json
from PySide2.QtCore import Qt, Signal
from PySide2.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ...controller import DCCHandler, Logger, PoolHandler
from .buttons import IconButton


class CreatePoolDialog(QDialog):
    pool_created = Signal(tuple)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Create new Pool")
        # self.setStyleSheet(dialog_style)
        # self.setWindowFlag(Qt.WindowStaysOnTopHint, True)

        self.init_widgets()
        self.init_layouts()
        self.init_signals()

    def init_widgets(self):
        self.name_edit = QLineEdit("")
        self.name_edit.setFixedHeight(30)

        self.folder_edit = QLineEdit("")
        self.folder_edit.setFixedHeight(30)

        self.open_file_dialog = IconButton((27, 27))
        self.open_file_dialog.set_icon(":icons/tabler-icon-folder-open.png", (27, 27))
        self.open_file_dialog.set_tooltip("Open Folder")

        buttons = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.button_box = QDialogButtonBox(buttons)

    def init_layouts(self):
        self.main_layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()
        self.folder_layout = QHBoxLayout()
        self.folder_layout.setAlignment(Qt.AlignTop)
        self.buttons_layout = QHBoxLayout()

        self.folder_layout.addWidget(self.folder_edit)
        self.folder_layout.addWidget(self.open_file_dialog)

        self.form_layout.addRow(QLabel("Pool Name"), self.name_edit)
        self.form_layout.addRow(QLabel("Pool Path"), self.folder_layout)

        self.main_layout.addLayout(self.form_layout)
        self.main_layout.addWidget(self.button_box)

    def init_signals(self):
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.open_file_dialog.clicked.connect(self.browse_folder)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Pool Folder")
        if not folder:
            return
        self.folder_edit.setText(folder)

    def accept(self) -> None:
        data = (self.name_edit.text(), self.folder_edit.text())
        self.pool_created.emit(data)
        super().accept()


class DeletePoolDialog(QDialog):
    pool_deleted = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Delete current Pool")
        # self.setStyleSheet(dialog_style)
        # self.setWindowFlag(Qt.WindowStaysOnTopHint, True)

        self.init_widgets()
        self.init_layouts()
        self.init_signals()

    def init_widgets(self):
        self.label = QLabel("Do you want to delete the current Pool?")

        buttons = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.button_box = QDialogButtonBox(buttons)

    def init_layouts(self):
        self.main_layout = QVBoxLayout(self)
        self.buttons_layout = QHBoxLayout()

        self.buttons_layout.addStretch()
        self.buttons_layout.addWidget(self.button_box)

        self.main_layout.addWidget(self.label)
        self.main_layout.addLayout(self.buttons_layout)

    def init_signals(self):
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def accept(self) -> None:
        self.pool_deleted.emit()
        super().accept()


class ExportModelDialog(QDialog):
    model_exported = Signal()
    repath = Signal(tuple)

    SAVE = "Save current Scene"
    EXPORT = "Export selected"

    def __init__(self, dcc_handler: DCCHandler, path: Path, parent=None):
        super().__init__(parent)
        self.dcc_handler = dcc_handler
        self.path = path

        self.setWindowTitle("Export Model")
        # self.setStyleSheet(dialog_style)
        # self.setWindowFlag(Qt.WindowStaysOnTopHint, True)

        self.init_widgets()
        self.init_layouts()
        self.init_signals()

    def init_widgets(self):
        self.name_edit = QLineEdit("")
        self.name_edit.setFixedHeight(30)

        self.export_options = QComboBox()
        self.export_options.addItems([self.EXPORT, self.SAVE])

        self.file_ext_box = QComboBox()
        self.file_ext_box.addItems(["mb", "ma"])

        self.copy_textues_check = QCheckBox("")

        buttons = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.button_box = QDialogButtonBox(buttons)

    def init_layouts(self):
        self.main_layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        self.form_layout.addRow("Model Name", self.name_edit)
        self.form_layout.addRow("Export Options", self.export_options)
        self.form_layout.addRow("File Extension", self.file_ext_box)
        self.form_layout.addRow("Copy Textures and Repath", self.copy_textues_check)

        self.main_layout.addLayout(self.form_layout)
        self.main_layout.addWidget(self.button_box)

    def init_signals(self):
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def accept(self) -> None:
        super().accept()
        opt = self.export_options.currentText()
        name, ext = (self.name_edit.text(), self.file_ext_box.currentText())

        if opt == self.SAVE:
            self.dcc_handler.save_scene_as(self.path / f"{name}.{ext}")
        elif opt == self.EXPORT:
            self.dcc_handler.export_model(self.path, name, ext)

        self.model_exported.emit()
        if self.copy_textues_check.isChecked():
            self.repath.emit((name, ext))


class ExportMaterialsDialog(QDialog):
    materials_exported = Signal()
    repath = Signal(list)

    def __init__(self, dcc_handler: DCCHandler, export_path: Path, parent=None):
        super().__init__(parent)
        self.dcc_handler = dcc_handler
        self.export_path = export_path
        self.materials = []

        self.setWindowTitle("Export Materials")
        # self.setStyleSheet(dialog_style)
        # self.setWindowFlag(Qt.WindowStaysOnTopHint, True)

        self.init_widgets()
        self.init_layouts()
        self.init_signals()

    def init_widgets(self):
        self.copy_textues_check = QCheckBox("Copy Textures and Repath")

        self.select_all = QPushButton("Select All")
        self.deselect_all = QPushButton("Deselect All")

        self.scroll_widget = QWidget()
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setFocusPolicy(Qt.NoFocus)
        self.scroll_area.setWidgetResizable(True)

        buttons = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.button_box = QDialogButtonBox(buttons)

    def init_layouts(self):
        self.main_layout = QVBoxLayout(self)
        self.select_layout = QHBoxLayout()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)

        materials = self.dcc_handler.get_non_default_materials()
        for mtl in materials:
            layout = self.add_material_row(mtl)
            self.scroll_layout.addLayout(layout)
        self.scroll_layout.addStretch()

        self.select_layout.addStretch()
        self.select_layout.addWidget(self.select_all)
        self.select_layout.addWidget(self.deselect_all)

        self.main_layout.addWidget(self.scroll_area)
        self.main_layout.addWidget(self.copy_textues_check, alignment=Qt.AlignRight)
        self.main_layout.addLayout(self.select_layout)
        self.main_layout.addWidget(self.button_box)

    def init_signals(self):
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.select_all.clicked.connect(self.select_all_materials)
        self.deselect_all.clicked.connect(self.deselect_all_materials)

    def add_material_row(self, name: str):
        layout = QHBoxLayout()
        checkbox = QCheckBox("")
        label = QLabel(name)

        layout.setSpacing(10)
        layout.addWidget(checkbox)
        layout.addWidget(label, 0, Qt.AlignLeft)
        layout.addStretch()

        self.materials.append((checkbox, label))
        return layout

    def accept(self) -> None:
        super().accept()
        materials = self.get_selected_materials()
        self.dcc_handler.export_materials(self.export_path, materials)
        self.materials_exported.emit()

        if self.copy_textues_check.isChecked():
            self.repath.emit(materials)

    def get_selected_materials(self):
        materials = []
        for check, label in self.materials:
            if not check.isChecked():
                continue

            materials.append(label.text())
        return materials

    def select_all_materials(self):
        for check, _ in self.materials:
            check.setChecked(True)

    def deselect_all_materials(self):
        for check, _ in self.materials:
            check.setChecked(False)


class ArchiveViewerDialog(QDialog):
    def __init__(
        self,
        pool_handler: PoolHandler,
        dcc_handler: DCCHandler,
        archive_path: Path,
        parent=None,
    ):
        super().__init__(parent)
        self.pool_handler = pool_handler
        self.dcc_handler = dcc_handler
        self.archive_path = archive_path
        self.elements = []

        self.get_archives()

        self.setWindowTitle("Archive Viewer")

        self.init_widgets()
        self.init_layouts()
        self.init_signals()

    def init_widgets(self):
        self.open_model = QPushButton("Open")
        self.import_model = QPushButton("Import")
        self.reference_model = QPushButton("Reference")

        self.tree_widget = QTreeWidget(self)
        self.tree_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tree_widget.setHeaderLabels(["Archive"])

        for archive, versions in self.get_archives().items():
            archive_item = QTreeWidgetItem(self.tree_widget, [archive])
            for version_info in versions:
                version_name, _ = list(version_info.items())[0]
                item = QTreeWidgetItem(archive_item, [version_name])
                self.elements.append(item)

    def init_layouts(self):
        self.main_layout = QVBoxLayout(self)
        self.select_layout = QHBoxLayout()

        self.select_layout.addStretch()
        self.select_layout.addWidget(self.open_model)
        self.select_layout.addWidget(self.import_model)
        self.select_layout.addWidget(self.reference_model)

        self.main_layout.addWidget(self.tree_widget)
        self.main_layout.addLayout(self.select_layout)

    def init_signals(self):
        self.import_model.clicked.connect(lambda: self.import_selection())
        self.reference_model.clicked.connect(lambda: self.reference_selection())
        self.open_model.clicked.connect(lambda: self.open_selection())

    def import_selection(self):
        path = self.get_selected_path()
        if not path:
            Logger.error(f"can't import model, path is: {path}")
            return
        self.dcc_handler.import_model(path)
        self.close()

    def reference_selection(self):
        path = self.get_selected_path()
        if not path:
            Logger.error(f"can't reference model, path is: {path}")
            return
        self.dcc_handler.reference_model(path)
        self.close()

    def open_selection(self):
        path = self.get_selected_path()
        if not path:
            Logger.error(f"can't open model, path is: {path}")
            return
        self.dcc_handler.open_scene(path)
        self.close()

    def get_archives(self) -> dict:
        archives = self.archive_path.iterdir()
        versions = {}
        for a in archives:
            if a.is_dir():
                version_files = [{b.name: b} for b in a.iterdir()]
                versions[a.stem] = version_files
        return versions

    def get_item_level(self, item):
        level = 0
        while item.parent() is not None:
            item = item.parent()
            level += 1
        return level

    def get_selected_path(self):
        selected = self.tree_widget.selectedItems()[0]
        item_name = selected.text(0)

        if not self.get_item_level(selected) == 1:
            Logger.error("select an archived version instead of the group")
            return

        parent_name = selected.parent().text(0)
        import_path = self.archive_path / parent_name / item_name
        return import_path


class CreateTagDialog(QDialog):
    tag_created = Signal(str)

    def __init__(self, pool_path: Path, parent=None):
        super().__init__(parent)
        self.pool_path = pool_path
        self.setWindowTitle("Add new Tag")

        self._button_cache = {}

        self.init_widgets()
        self.init_layouts()
        self.init_signals()

        self.add_tags(self.load_tags())

    def init_widgets(self):
        self.name_edit = QLineEdit("")
        self.name_edit.setFixedHeight(30)

        self.scroll_widget = QWidget()
        self.scroll_area = QScrollArea()
        self.scroll_area.setFocusPolicy(Qt.NoFocus)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setWidget(self.scroll_widget)

        buttons = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.button_box = QDialogButtonBox(buttons)

    def init_layouts(self):
        self.tag_layout = QVBoxLayout()
        self.main_layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        self.form_layout.addRow(QLabel("Tag Name"), self.name_edit)

        self.scroll_widget.setLayout(self.tag_layout)

        self.main_layout.addWidget(self.scroll_area)
        self.main_layout.addLayout(self.form_layout)
        self.main_layout.addWidget(self.button_box)

    def init_signals(self):
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def accept(self) -> None:
        for tag, btn in self._button_cache.items():
            if not btn.isChecked():
                continue
            self.tag_created.emit(tag)

        if (t := self.name_edit.text()) and t not in self._button_cache.keys():
            self.tag_created.emit(self.name_edit.text())
        super().accept()

    def load_tags(self) -> set[str]:
        metadata_path = self.pool_path / "Metadata"
        print(metadata_path)
        if not metadata_path.exists():
            return

        metadata_files = (
            file for file in metadata_path.iterdir() if file.suffix == ".json"
        )

        pool_tags = set()

        for file in metadata_files:
            with open(file, "r") as f:
                data = json.load(f)
                tags = data.get("tags", [])
                for i in tags:
                    pool_tags.add(i)

        return pool_tags

    def add_tags(self, tags: set[str]):
        for tag in tags:
            btn = QPushButton(tag)
            btn.setCheckable(True)
            self._button_cache[tag] = btn
            self.tag_layout.addWidget(btn)
