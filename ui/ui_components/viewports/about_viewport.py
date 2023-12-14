from PySide2.QtCore import Qt, QUrl
from PySide2.QtGui import QCursor, QDesktopServices
from PySide2.QtWidgets import QFormLayout, QLabel

from ...qss import about_viewport
from ...version import get_version
from .base_viewport import DataViewport


class HyperlinkLabel(QLabel):
    def __init__(self, text, url):
        super().__init__(text)
        self.url = url
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setStyleSheet("text-decoration: underline;")

    def mousePressEvent(self, event):
        QDesktopServices.openUrl(QUrl(self.url))


class AboutViewport(DataViewport):
    def __init__(self, parent=None):
        super().__init__(parent)

    def init_widgets(self):
        super().init_widgets()
        self.setStyleSheet(about_viewport)
        self.label = QLabel("About")
        self.label.setContentsMargins(10, 0, 0, 0)

        self.name = QLabel("Render Vault")
        self.version = QLabel(get_version())
        self.repository = HyperlinkLabel(
            "Render Vault GitHub", "https://github.com/Design0r/render_vault"
        )
        self.author = QLabel("Alexander Mors")
        self.email = QLabel("alex.mors@gmx.de")
        self.name.setAlignment(Qt.AlignCenter)

    def init_layouts(self):
        super().init_layouts()
        self.toolbar.main_layout.addWidget(self.label)

        self.form_layout = QFormLayout()
        self.form_layout.addRow("Name: ", self.name)
        self.form_layout.addRow("Version: ", self.version)
        self.form_layout.addRow("Repository: ", self.repository)
        self.form_layout.addRow("Author: ", self.author)
        self.form_layout.addRow("E-Mail: ", self.email)

        self.form_layout.setAlignment(Qt.AlignCenter)
        self.settings_groups_layout.addLayout(self.form_layout)
        self.settings_groups_layout.setAlignment(Qt.AlignCenter)
