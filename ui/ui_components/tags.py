from PySide2.QtWidgets import (
    QWidget,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QScrollArea,
)
from PySide2.QtCore import Qt, Signal
from pathlib import Path
from . import FlowLayout
from .dialogs import CreateTagDialog


class TagWidget(QWidget):
    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        self.label = label

        self.setMinimumWidth(100)

        self.init_widgets()
        self.init_layouts()
        self.init_signals()

    def init_widgets(self):
        self.tag = QPushButton(self.label)
        self.tag.setCheckable(True)

        self.delete = QPushButton("X")
        self.delete.setFixedWidth(20)

    def init_layouts(self):
        self.main_layout = QHBoxLayout()
        self.main_layout.setSpacing(0)
        self.main_layout.setMargin(0)

        self.main_layout.addWidget(self.tag)
        self.main_layout.addWidget(self.delete)

        self.setLayout(self.main_layout)

    def init_signals(self):
        pass


class TagCollection(QWidget):
    tag_deleted = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._pool_path: Path = Path()
        self.tag_cache = {}

        self.init_widgets()
        self.init_layouts()
        self.init_signals()

    def init_widgets(self):
        self.new_tag_btn = QPushButton("New")
        self.scroll_widget = QWidget()
        self.scroll_area = QScrollArea()
        self.scroll_area.setFocusPolicy(Qt.NoFocus)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setWidget(self.scroll_widget)

    def init_layouts(self):
        self.flow_layout = FlowLayout()
        self.flow_layout.setSpacing(0)

        self.scroll_widget.setLayout(self.flow_layout)

        self.main_layout = QVBoxLayout()
        self.main_layout.setMargin(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.new_tag_btn)
        self.main_layout.addWidget(self.scroll_area)

        self.setLayout(self.main_layout)

    def init_signals(self):
        self.new_tag_btn.clicked.connect(self.open_tag_dialog)

    def open_tag_dialog(self):
        dialog = CreateTagDialog(self._pool_path)
        dialog.tag_created.connect(self.add_tag)
        dialog.exec()

    def add_tag(self, name: str):
        tag = TagWidget(name)
        tag.delete.clicked.connect(lambda: self.remove_tag(name))
        self.tag_cache[name] = tag
        self.flow_layout.addWidget(tag)

    def remove_tag(self, name: str):
        if name in self.tag_cache:
            tag = self.tag_cache[name]
            tag.deleteLater()
            del self.tag_cache[name]
            self.tag_deleted.emit()

    def load_tags(self, tags: tuple[str]):
        self.tag_cache.clear()
        self.clear_layout()
        for tag in tags:
            self.add_tag(tag)

    def clear_layout(self):
        while self.flow_layout.count():
            widget = self.flow_layout.takeAt(0).widget()
            widget.deleteLater()

    @property
    def pool_path(self):
        return self._pool_path

    @pool_path.setter
    def pool_path(self, value):
        self._pool_path = value
