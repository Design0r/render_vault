from Qt.QtCore import QSize, Qt, Signal
from Qt.QtGui import QIcon
from Qt.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QApplication,
)

from ..qss import viewport_button_style


class IconButton(QPushButton):
    activated = Signal(tuple)

    def __init__(self, size: tuple[int, int], checkable=False, parent=None):
        super().__init__(parent)
        self.setCheckable(checkable)
        self.setFixedSize(*size)
        self.clicked.connect(self.handle_shift)

    def set_icon(self, icon_path: str, icon_size: tuple[int, int]) -> None:
        width, height = icon_size
        self.icon_path = icon_path
        icon = QIcon(icon_path)
        available_sizes = icon.availableSizes()
        if available_sizes and available_sizes[0].width() < width:
            pixmap = icon.pixmap(available_sizes[0])
            scaled_pixmap = pixmap.scaled(
                width, height, Qt.KeepAspectRatio, Qt.FastTransformation
            )
            icon = QIcon(scaled_pixmap)

        self.setIcon(icon)
        self.setIconSize(QSize(width, height))

    def set_tooltip(self, text: str) -> None:
        self.setToolTip(text)

    def handle_shift(self):
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.ShiftModifier and self.isCheckable():
            self.setChecked(True)
            self.activated.emit(self)

        else:
            self.setChecked(False)


class SidebarButton(QPushButton):
    activated = Signal(tuple)

    def __init__(self, size: tuple[int, int], parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedSize(*size)
        self.clicked.connect(lambda: self.activated.emit(self))

    def set_icon(self, icon_path: str, icon_size: tuple[int, int]) -> None:
        width, height = icon_size
        icon = QIcon(icon_path)
        self.setIcon(icon)
        self.setIconSize(QSize(width, height))

    def set_tooltip(self, text: str) -> None:
        self.setToolTip(text)


class ViewportButton(QWidget):
    def __init__(
        self,
        name: str,
        button_size: tuple[int, int],
        filesize: int,
        suffix: str,
        checkable=False,
        parent=None,
    ):
        super().__init__(parent)
        self.button_size = button_size
        self.name = name
        self.filesize = filesize
        self.suffix = suffix.replace(".", "")
        self.checkable = checkable
        self.setMinimumSize(*button_size)
        self.setToolTip(name)
        self.setStyleSheet(viewport_button_style)

        self.init_widgets()
        self.init_layouts()
        self.init_signals()

    def init_widgets(self):
        self.icon = IconButton(self.button_size, self.checkable)
        self.label = QLabel(self.name)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setContentsMargins(0, 3, 0, 5)
        self.label.setMaximumWidth(self.button_size[0])

        self.file_size = QLabel(f"Size: {self.format_filesize()}")
        self.file_size.setAlignment(Qt.AlignCenter)
        self.file_size.setContentsMargins(0, 5, 0, 5)
        self.file_size.setStyleSheet(
            "border-right: none;border-bottom:1px solid black; font-size: 8pt;"
        )
        self.file_type = QLabel(f"Type: {self.suffix}")
        self.file_type.setStyleSheet(
            "border-left: none;border-bottom:1px solid black;font-size: 8pt;"
        )
        self.file_type.setContentsMargins(0, 5, 0, 5)
        self.file_type.setAlignment(Qt.AlignCenter)

    def init_layouts(self):
        self.main_layout = QVBoxLayout(self)
        self.info_layout = QHBoxLayout()

        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.info_layout.addWidget(self.file_size)
        self.info_layout.addWidget(self.file_type)

        self.main_layout.setSpacing(0)
        self.main_layout.addWidget(self.icon)
        self.main_layout.addWidget(self.label)
        self.main_layout.addLayout(self.info_layout)

    def init_signals(self):
        pass

    def format_filesize(self) -> str:
        # bytes

        filesize = f"{self.filesize / 1_000:.2f}KB"
        if self.filesize >= 100_000_000:
            filesize = f"{self.filesize / 1_000_000_000:.2f}GB"
        elif self.filesize >= 100_000:
            filesize = f"{self.filesize / 1_000_000:.2f}MB"

        return filesize
