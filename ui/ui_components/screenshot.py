from Qt.QtCore import QPoint, Qt, Signal
from Qt.QtGui import QCursor
from Qt.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout

from ...controller import SettingsManager


class ScreenshotFrame(QDialog):
    take_screenshot = Signal(tuple)

    def __init__(self, model_name: str, model_path, parent=None):
        super().__init__(parent)

        self.setWindowFlags(Qt.FramelessWindowHint)

        # self.setAttribute(Qt.WA_TranslucentBackground)

        self.setStyleSheet("border: 2px solid black;")

        self.setWindowOpacity(SettingsManager.model_settings.screenshot_opacity)

        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)

        self.resize(300, 300)

        self.model_name = model_name
        self.model_path = model_path

        self._dragPos = QPoint()

        self._resize = False

        self.init_widgets()

        self.init_layouts()
        self.init_signals()

    def init_widgets(self):
        buttons = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.button_group = QDialogButtonBox(buttons)

    def init_layouts(self):
        self.main_layout = QVBoxLayout(self)

        self.main_layout.setAlignment(Qt.AlignRight)

        self.main_layout.addStretch()

        self.main_layout.addWidget(self.button_group)

    def init_signals(self):
        self.button_group.accepted.connect(self.accept)

        self.button_group.rejected.connect(self.reject)

    def accept(self):
        self.take_screenshot.emit(
            (
                (self.x(), self.y(), self.width(), self.height()),
                self.model_name,
                self.model_path,
            )
        )

        super().accept()

    def mousePressEvent(self, event):
        # Enable resizing if the mouse is at the border of the window

        if (abs(event.x() - self.width()) < 10) or (
            abs(event.y() - self.height()) < 10
        ):
            self._resize = True

        else:
            self._dragPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if (abs(event.x() - self.width()) < 10) or (
            abs(event.y() - self.height()) < 10
        ):
            self.setCursor(QCursor(Qt.SizeFDiagCursor))

        else:
            self.setCursor(QCursor(Qt.ArrowCursor))

        if event.buttons() == Qt.LeftButton:
            if self._resize:
                # Perform window resize

                self.resize(event.x(), event.x())

            else:
                # Perform window move

                diff = event.globalPos() - self._dragPos

                new_pos = self.pos() + diff

                self.move(new_pos)

                self._dragPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self._resize = False

        self.setCursor(QCursor(Qt.ArrowCursor))
