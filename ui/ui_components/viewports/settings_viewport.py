from PySide2.QtGui import QIcon
from PySide2.QtWidgets import (
    QAbstractSpinBox,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
)

from ....controller import SettingsManager
from .base_viewport import DataViewport


class SettingsViewport(DataViewport):
    def __init__(self, settings: SettingsManager, parent=None):
        super().__init__(parent)
        self.settings = settings

    def init_widgets(self):
        super().init_widgets()
        self.label = QLabel("Settings")
        self.label.setContentsMargins(10, 0, 0, 0)

        self.general_settings = QGroupBox("General Settings")
        self.button_resolution = QSpinBox()
        self.button_resolution.setRange(0, 5000)
        self.button_resolution.setButtonSymbols(QAbstractSpinBox.NoButtons)

        self.ui_scale = QDoubleSpinBox()
        self.ui_scale.setRange(0, 10)
        self.ui_scale.setButtonSymbols(QAbstractSpinBox.NoButtons)

        self.material_settings = QGroupBox("Material Settings")
        self.material_renderer = QComboBox()
        self.material_renderer.addItems(("Default", "V-Ray", "Arnold", "Redshift"))
        self.render_scene = QLineEdit("Path/To/Render/Scene")
        self.browse_render_scene = QPushButton(
            QIcon(":icons/tabler-icon-folder-open.png"), ""
        )
        self.render_object = QLineEdit("Name of shaderball Object")
        self.render_cam = QLineEdit("Render Camera")
        self.render_resolution_x = QSpinBox()
        self.render_resolution_x.setRange(0, 5000)
        self.render_resolution_x.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.render_resolution_y = QSpinBox()
        self.render_resolution_y.setRange(0, 5000)
        self.render_resolution_y.setButtonSymbols(QAbstractSpinBox.NoButtons)

        self.model_settings = QGroupBox("Model Settings")
        self.screenshot_opacity = QDoubleSpinBox()
        self.screenshot_opacity.setRange(0, 5000)
        self.screenshot_opacity.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.screenshot_opacity.setRange(0, 1)

        self.hdri_settings = QGroupBox("HDRI Settings")
        self.hdri_renderer = QComboBox()
        self.hdri_renderer.addItems(("Default", "V-Ray", "Arnold", "Redshift"))
        self.auto_generate_thumb = QCheckBox()

        self.save = QPushButton("Save")

    def init_layouts(self):
        super().init_layouts()
        self.toolbar.main_layout.addWidget(self.label)

        self.general_settings_layout = QFormLayout(self.general_settings)
        self.general_settings_layout.addRow(
            "Asset Button Size (px)", self.button_resolution
        )
        self.general_settings_layout.addRow("UI Scale", self.ui_scale)
        self.render_scene_layout = QHBoxLayout()
        self.render_scene_layout.addWidget(self.render_scene)
        self.render_scene_layout.addWidget(self.browse_render_scene)

        self.resolution_layout = QHBoxLayout()
        self.resolution_layout.addWidget(self.render_resolution_x)
        self.resolution_layout.addWidget(self.render_resolution_y)

        self.material_settings_layout = QFormLayout(self.material_settings)
        self.material_settings_layout.addRow(QLabel("Renderer"), self.material_renderer)
        self.material_settings_layout.addRow(
            QLabel("Render Scene"), self.render_scene_layout
        )
        self.material_settings_layout.addRow(
            QLabel("Render Object"), self.render_object
        )
        self.material_settings_layout.addRow(QLabel("Render Camera"), self.render_cam)
        self.material_settings_layout.addRow(
            QLabel("Render Resolution"), self.resolution_layout
        )

        self.model_settings_layout = QFormLayout(self.model_settings)
        self.model_settings_layout.addRow(
            QLabel("Screenshot Widget Opacity"), self.screenshot_opacity
        )

        self.hdri_settings_layout = QFormLayout(self.hdri_settings)
        self.hdri_settings_layout.addRow(QLabel("Renderer"), self.hdri_renderer)
        self.hdri_settings_layout.addRow(
            QLabel("Auto Generate Thumbnails"), self.auto_generate_thumb
        )

        self.save_layout = QHBoxLayout()
        self.save_layout.addStretch()
        self.save_layout.addWidget(self.save)

        self.settings_groups_layout.addWidget(self.general_settings)
        self.settings_groups_layout.addWidget(self.material_settings)
        self.settings_groups_layout.addWidget(self.model_settings)
        self.settings_groups_layout.addWidget(self.hdri_settings)
        self.settings_groups_layout.addLayout(self.save_layout)
        self.settings_groups_layout.addStretch()

    def init_signals(self):
        self.browse_render_scene.clicked.connect(self.open_render_scene)

    def open_render_scene(self):
        file, _ = QFileDialog().getOpenFileName(
            self, "Browse Render Scene", filter="Maya Files (*.ma *.mb)"
        )
        if not file:
            return

        self.render_scene.setText(file)

    def read_from_settings_manager(self):
        self.button_resolution.setValue(self.settings.window_settings.asset_button_size)
        self.ui_scale.setValue(self.settings.window_settings.ui_scale)

        self.material_renderer.setCurrentIndex(
            self.settings.material_settings.material_renderer
        )
        self.render_scene.setText(self.settings.material_settings.render_scene)
        self.render_object.setText(self.settings.material_settings.render_object)
        self.render_cam.setText(self.settings.material_settings.render_cam)
        self.render_resolution_x.setValue(
            self.settings.material_settings.render_resolution_x
        )
        self.render_resolution_y.setValue(
            self.settings.material_settings.render_resolution_y
        )

        self.screenshot_opacity.setValue(
            self.settings.model_settings.screenshot_opacity
        )
        self.hdri_renderer.setCurrentIndex(self.settings.hdri_settings.hdri_renderer)
        self.auto_generate_thumb.setChecked(
            self.settings.hdri_settings.auto_generate_thumbnails
        )

    def write_to_settings_manager(self):
        self.settings.window_settings.asset_button_size = self.button_resolution.value()
        self.settings.window_settings.ui_scale = self.ui_scale.value()

        self.settings.material_settings.render_resolution_x = (
            self.render_resolution_x.value()
        )
        self.settings.material_settings.render_resolution_y = (
            self.render_resolution_y.value()
        )
        self.settings.material_settings.render_object = self.render_object.text()
        self.settings.material_settings.render_scene = self.render_scene.text()
        self.settings.material_settings.render_cam = self.render_cam.text()
        self.settings.material_settings.material_renderer = (
            self.material_renderer.currentIndex()
        )

        self.settings.model_settings.screenshot_opacity = (
            self.screenshot_opacity.value()
        )

        self.settings.hdri_settings.hdri_renderer = self.hdri_renderer.currentIndex()
        self.settings.hdri_settings.auto_generate_thumbnails = (
            self.auto_generate_thumb.isChecked()
        )
