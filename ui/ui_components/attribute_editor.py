from dataclasses import dataclass
from pathlib import Path
from functools import partial
from PySide2.QtCore import Qt, Signal
from PySide2.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ...controller import MetadataHandler
from . import IconButton
from .tags import TagCollection


class Asset:
    __slots__ = (
        "_path",
        "asset_name",
        "ext",
        "size",
        "renderer",
        "tags",
        "notes",
        "icon",
    )

    def __init__(self, path: Path):
        self._path = path
        self.asset_name: str = ""
        self.ext: str = ""
        self.size: str = ""
        self.renderer: str = ""
        self.tags: tuple = ("",)
        self.notes: str = ""
        self.icon: str = ":icons/tabler-icon-photo.png"

    @property
    def path(self):
        return str(self._path)

    @path.setter
    def path(self, value: Path):
        self._path = value

    def load(self):
        self._path = self._path
        self.asset_name = self._path.name
        self.ext = self._path.suffix
        self.size = self.format_filesize()
        self.icon = str(
            self._path.parent.parent / "Thumbnails" / f"{self._path.stem}.jpg"
        )
        self._load_metadata()

    def save(self):
        metadata = {
            "name": self.asset_name,
            "extension": self.ext,
            "size": self.size,
            "path": self.path,
            "renderer": self.renderer,
            "tags": self.tags,
            "notes": self.notes,
        }
        MetadataHandler.save_metadata(
            self._path.parent.parent / "Metadata" / f"{self._path.stem}.json", metadata
        )

    def _load_metadata(self):
        try:
            (self._path.parent.parent / "Metadata").mkdir(exist_ok=True)
        except:
            pass

        metadata = MetadataHandler.load_metadata(
            self._path.parent.parent / "Metadata" / f"{self._path.stem}.json"
        )
        self.renderer = metadata.get("renderer", "")
        self.tags = metadata.get("tags", "")
        self.notes = metadata.get("notes", "")

    def format_filesize(self) -> str:
        # bytes
        filesize = self._path.stat().st_size
        formatted_size = f"{filesize / 1_000:.3f}KB"
        if filesize >= 100_000_000:
            formatted_size = f"{filesize / 1_000_000_000:.3f}GB"
        elif filesize >= 100_000:
            formatted_size = f"{filesize / 1_000_000:.3f}MB"

        return formatted_size


class AttributeEditor(QWidget):
    tag_selected = Signal(QPushButton)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_asset: Asset = Asset(Path(""))

        self.icon_size = (300 - 20, 300 - 20)

        self.init_widgets()
        self.init_layouts()
        self.init_signals()

    def init_widgets(self):
        self.banner = QWidget()
        self.banner.setFixedHeight(52)

        self.label = QLabel("Metadata")
        self.label.setFixedHeight(52)
        self.label.setStyleSheet(
            "background-color: rgb(50,50,50);font-size: 16pt; color: white;"
        )
        self.label.setContentsMargins(10, 0, 0, 0)

        self.icon = IconButton(self.icon_size)
        self.icon.set_icon(":icons/tabler-icon-photo.png", self.icon_size)

        self.asset_name = QLineEdit("Asset Name")
        self.asset_name.setReadOnly(True)
        self.asset_ext = QLineEdit(".mb")
        self.asset_ext.setReadOnly(True)
        self.asset_size = QLineEdit("10MB")
        self.asset_size.setReadOnly(True)
        self.asset_path = QLineEdit("/path/to/asset.mb")
        self.asset_path.setReadOnly(True)
        self.asset_renderer = QLineEdit("V-Ray")
        self.asset_tags = TagCollection()
        self.asset_notes = QTextEdit("notes about asset...")

        self.save_btn = QPushButton("Save")
        self.save_btn.setFixedWidth(self.icon_size[1] // 2)

    def update_size(self, size: int):
        margin_size = size - 20
        self.icon_size = (margin_size, margin_size)
        self.icon.setFixedSize(*self.icon_size)
        self.icon.set_icon(self.icon.icon_path, self.icon_size)
        self.setFixedWidth(size)

    def init_layouts(self):
        self.another_layout = QVBoxLayout()
        self.banner_layout = QVBoxLayout()
        self.main_layout = QVBoxLayout()
        self.form_layout = QFormLayout()

        self.banner_layout.addWidget(self.label)

        self.form_layout.addRow("Name", self.asset_name)
        self.form_layout.addRow("Extension", self.asset_ext)
        self.form_layout.addRow("Size", self.asset_size)
        self.form_layout.addRow("Path", self.asset_path)
        self.form_layout.addRow("Renderer", self.asset_renderer)
        self.form_layout.addRow("Tags", self.asset_tags)
        self.form_layout.addRow("Notes", self.asset_notes)

        self.button_layout = QHBoxLayout()
        self.button_layout.addStretch()
        self.button_layout.addWidget(self.save_btn)

        self.another_layout.addLayout(self.banner_layout)
        self.another_layout.addLayout(self.main_layout)
        self.another_layout.setMargin(0)

        self.main_layout.setAlignment(Qt.AlignHCenter)
        self.main_layout.setMargin(0)
        self.main_layout.setContentsMargins(10, 0, 10, 10)

        self.main_layout.addLayout(self.banner_layout)
        self.main_layout.addWidget(self.icon)
        self.main_layout.addLayout(self.form_layout)
        self.main_layout.addLayout(self.button_layout)

        self.setLayout(self.another_layout)

    def init_signals(self):
        self.save_btn.clicked.connect(self.save_asset)
        self.asset_tags.new_tag_btn.clicked.connect(self.save_asset)
        self.asset_tags.new_tag_btn.clicked.connect(
            lambda: self.display_asset(self.current_asset._path)
        )
        self.asset_tags.tag_deleted.connect(self.save_asset)

    def save_asset(self):
        if self.current_asset:
            self.current_asset.renderer = self.asset_renderer.text()
            self.current_asset.tags = tuple(
                [k for k in self.asset_tags.tag_cache.keys()]
            )
            self.current_asset.notes = self.asset_notes.toPlainText()
            self.current_asset.save()

    def display_asset(self, asset_path: Path):
        self.current_asset._path = asset_path
        self.current_asset.load()

        self.icon.set_icon(self.current_asset.icon, self.icon_size)
        self.asset_name.setText(self.current_asset.asset_name)
        self.asset_ext.setText(self.current_asset.ext)
        self.asset_size.setText(self.current_asset.size)
        self.asset_path.setText(self.current_asset.path)
        self.asset_renderer.setText(self.current_asset.renderer)
        self.asset_tags.load_tags(self.current_asset.tags)
        self.asset_tags.pool_path = self.current_asset._path.parent.parent
        self.asset_notes.setText(self.current_asset.notes)

        for i in self.asset_tags.tag_cache.values():
            i.tag.clicked.connect(partial(self.tag_selected.emit, i.tag))
