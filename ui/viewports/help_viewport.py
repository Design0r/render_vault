from Qt.QtWidgets import QLabel

from .base_viewport import DataViewport


class HelpViewport(DataViewport):
    def __init__(self, parent=None):
        super().__init__(parent)

    def init_widgets(self):
        super().init_widgets()
        self.label = QLabel("Help")
        self.label.setContentsMargins(10, 0, 0, 0)

    def init_layouts(self):
        super().init_layouts()
        self.toolbar.main_layout.addWidget(self.label)
