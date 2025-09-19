import logging
import os
from PyQt6.QtWidgets import (QDialog, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QSlider, QSpinBox, QCheckBox, QFormLayout, QLabel,
                             QDialogButtonBox, QGroupBox)
from PyQt6.QtCore import Qt, QSize, QUrl, QPoint
from PyQt6.QtGui import QPixmap, QTransform, QPainter
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget


class ItemSettingsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings.copy()  # Work on a copy
        self.is_image = any(
            self.settings['path'].lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.bmp', '.gif'])
        self.media_player = None
        self.audio_output = None
        self.original_pixmap = None  # 确保属性始终存在

        self.setWindowTitle("自定义设置")
        self.setMinimumSize(800, 500)

        self.setup_ui()
        self.load_settings_to_ui()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)

        # --- Left Side (Preview) ---
        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        self.preview_area = QLabel("预览区")
        self.preview_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_area.setFixedSize(480, 270)
        self.preview_area.setStyleSheet("background-color: #333; color: white; border-radius: 5px;")

        self.video_widget_container = QWidget()
        self.video_widget_container.setFixedSize(480, 270)
        video_container_layout = QVBoxLayout(self.video_widget_container)
        video_container_layout.setContentsMargins(0, 0, 0, 0)
        self.video_widget = QVideoWidget()
        video_container_layout.addWidget(self.video_widget)

        preview_layout.addWidget(self.preview_area)
        preview_layout.addWidget(self.video_widget_container)

        # --- Right Side (Controls) ---
        controls_container = QWidget()
        controls_layout = QVBoxLayout(controls_container)

        adjustments_group = QGroupBox("调整")
        adjustments_layout = QFormLayout(adjustments_group)

        # Size
        size_layout = QHBoxLayout()
        self.width_spin = QSpinBox();
        self.width_spin.setRange(10, 5000)
        self.height_spin = QSpinBox();
        self.height_spin.setRange(10, 5000)
        self.aspect_check = QCheckBox("保持宽高比");
        self.aspect_check.setChecked(True)
        size_layout.addWidget(self.width_spin);
        size_layout.addWidget(QLabel("x"));
        size_layout.addWidget(self.height_spin)
        adjustments_layout.addRow("尺寸 (宽 x 高):", size_layout)
        adjustments_layout.addRow("", self.aspect_check)

        # Rotation (Image only)
        self.rotation_spin = QSpinBox();
        self.rotation_spin.setRange(0, 359);
        self.rotation_spin.setSuffix(" °")
        self.rotation_label = QLabel("旋转:")
        adjustments_layout.addRow(self.rotation_label, self.rotation_spin)

        # Scale (Image only)
        self.scale_slider = QSlider(Qt.Orientation.Horizontal);
        self.scale_slider.setRange(10, 300)  # 10% to 300%
        self.scale_label_widget = QLabel("缩放:")
        scale_display_layout = QHBoxLayout()
        self.scale_value_label = QLabel("100 %")
        scale_display_layout.addWidget(self.scale_slider)
        scale_display_layout.addWidget(self.scale_value_label)
        adjustments_layout.addRow(self.scale_label_widget, scale_display_layout)

        # Volume (Video only)
        self.volume_slider = QSlider(Qt.Orientation.Horizontal);
        self.volume_slider.setRange(0, 100)
        self.volume_label = QLabel("音量:")
        volume_display_layout = QHBoxLayout()
        self.volume_value_label = QLabel("75 %")
        volume_display_layout.addWidget(self.volume_slider)
        volume_display_layout.addWidget(self.volume_value_label)
        self.mute_check = QCheckBox("静音")
        adjustments_layout.addRow(self.volume_label, volume_display_layout)
        adjustments_layout.addRow("", self.mute_check)

        # Keyframe Animation
        keyframe_group = QGroupBox("关键帧动画")
        keyframe_layout = QFormLayout(keyframe_group)
        self.enable_keyframe_check = QCheckBox("启用关键帧移动")

        self.start_pos_widget = QWidget()
        start_pos_layout = QHBoxLayout(self.start_pos_widget);
        start_pos_layout.setContentsMargins(0, 0, 0, 0)
        self.start_x_spin = QSpinBox();
        self.start_x_spin.setRange(-10000, 10000)
        self.start_y_spin = QSpinBox();
        self.start_y_spin.setRange(-10000, 10000)
        start_pos_layout.addWidget(QLabel("X:"));
        start_pos_layout.addWidget(self.start_x_spin)
        start_pos_layout.addWidget(QLabel("Y:"));
        start_pos_layout.addWidget(self.start_y_spin)
        start_pos_layout.addStretch()

        self.end_pos_widget = QWidget()
        end_pos_layout = QHBoxLayout(self.end_pos_widget);
        end_pos_layout.setContentsMargins(0, 0, 0, 0)
        self.end_x_spin = QSpinBox();
        self.end_x_spin.setRange(-10000, 10000)
        self.end_y_spin = QSpinBox();
        self.end_y_spin.setRange(-10000, 10000)
        end_pos_layout.addWidget(QLabel("X:"));
        end_pos_layout.addWidget(self.end_x_spin)
        end_pos_layout.addWidget(QLabel("Y:"));
        end_pos_layout.addWidget(self.end_y_spin)
        end_pos_layout.addStretch()

        self.duration_spin = QSpinBox();
        self.duration_spin.setRange(1, 300);
        self.duration_spin.setSuffix(" 秒")

        keyframe_layout.addRow(self.enable_keyframe_check)
        keyframe_layout.addRow("起始坐标:", self.start_pos_widget)
        keyframe_layout.addRow("结束坐标:", self.end_pos_widget)
        keyframe_layout.addRow("动画时长:", self.duration_spin)

        # Dialog Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        controls_layout.addWidget(adjustments_group)
        controls_layout.addWidget(keyframe_group)
        controls_layout.addStretch()
        controls_layout.addWidget(self.button_box)

        main_layout.addWidget(preview_container)
        main_layout.addWidget(controls_container)

        # Connect signals
        self.width_spin.valueChanged.connect(self.width_changed)
        self.height_spin.valueChanged.connect(self.height_changed)
        self.scale_slider.valueChanged.connect(self.update_previews)
        self.rotation_spin.valueChanged.connect(self.update_previews)
        self.volume_slider.valueChanged.connect(self.set_video_volume)
        self.mute_check.toggled.connect(self.toggle_mute)
        self.enable_keyframe_check.toggled.connect(self.toggle_keyframe_controls)

    def load_settings_to_ui(self):
        # Universal settings
        w = self.settings.get('width')
        h = self.settings.get('height')
        self.width_spin.setValue(w if w else self.preview_area.width())
        self.height_spin.setValue(h if h else self.preview_area.height())

        # Keyframe settings
        self.enable_keyframe_check.setChecked(self.settings.get('keyframe_enabled', False))
        start_pos = self.settings.get('keyframe_start_pos', [0, 0])
        self.start_x_spin.setValue(start_pos[0])
        self.start_y_spin.setValue(start_pos[1])
        end_pos = self.settings.get('keyframe_end_pos', [100, 100])
        self.end_x_spin.setValue(end_pos[0])
        self.end_y_spin.setValue(end_pos[1])
        self.duration_spin.setValue(self.settings.get('keyframe_duration', 5))
        self.toggle_keyframe_controls(self.enable_keyframe_check.isChecked())

        if self.is_image:
            self.video_widget_container.hide()
            self.preview_area.show()

            # Hide video-specific controls
            self.volume_label.hide()
            self.volume_slider.hide()
            self.volume_value_label.hide()
            self.mute_check.hide()

            # Show image-specific controls
            self.rotation_label.show()
            self.rotation_spin.show()
            self.scale_label_widget.show()
            self.scale_slider.show()
            self.scale_value_label.show()

            self.original_pixmap = QPixmap(self.settings['path'])
            self.rotation_spin.setValue(self.settings.get('rotation', 0))
            self.scale_slider.setValue(int(self.settings.get('scale', 1.0) * 100))
        else:  # Is video
            self.preview_area.hide()
            self.video_widget_container.show()

            # Hide image-specific controls
            self.rotation_label.hide()
            self.rotation_spin.hide()
            self.scale_label_widget.hide()
            self.scale_slider.hide()
            self.scale_value_label.hide()

            # Show video-specific controls
            self.volume_label.show()
            self.volume_slider.show()
            self.volume_value_label.show()
            self.mute_check.show()

            self.media_player = QMediaPlayer()
            self.audio_output = QAudioOutput()
            self.media_player.setAudioOutput(self.audio_output)
            self.media_player.setVideoOutput(self.video_widget)
            self.media_player.setSource(QUrl.fromLocalFile(self.settings['path']))
            self.media_player.mediaStatusChanged.connect(
                lambda s: self.media_player.play() if s == QMediaPlayer.MediaStatus.EndOfMedia else None)

            vol_float = self.settings.get('volume', 0.75)
            self.volume_slider.setValue(int(vol_float * 100))
            self.audio_output.setVolume(vol_float)
            self.media_player.play()

        self.update_previews()

    def toggle_keyframe_controls(self, enabled):
        self.start_pos_widget.setEnabled(enabled)
        self.end_pos_widget.setEnabled(enabled)
        self.duration_spin.setEnabled(enabled)

    def width_changed(self, value):
        if self.aspect_check.isChecked():
            ratio = self.settings.get('aspect_ratio', 1.0)
            if ratio > 0:
                self.height_spin.blockSignals(True)
                self.height_spin.setValue(int(value / ratio))
                self.height_spin.blockSignals(False)
        self.update_previews()

    def height_changed(self, value):
        if self.aspect_check.isChecked():
            ratio = self.settings.get('aspect_ratio', 1.0)
            self.width_spin.blockSignals(True)
            self.width_spin.setValue(int(value * ratio))
            self.width_spin.blockSignals(False)
        self.update_previews()

    def update_previews(self, *args):
        if not self.is_image or not self.original_pixmap or self.original_pixmap.isNull():
            return

        scale = self.scale_slider.value() / 100.0
        rotation = self.rotation_spin.value()
        self.scale_value_label.setText(f"{int(scale * 100)} %")

        base_pixmap = self.original_pixmap
        preview_box_size = self.preview_area.size()

        # Scale pixmap to fit the preview box (100% scale = fit box)
        scaled_pixmap = base_pixmap.scaled(preview_box_size, Qt.AspectRatioMode.KeepAspectRatio,
                                           Qt.TransformationMode.SmoothTransformation)

        # Apply user scale and rotation
        transform = QTransform().rotate(rotation)
        final_pixmap = scaled_pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)

        # Create a canvas to draw on, allowing parts of the image to be outside the bounds
        canvas = QPixmap(preview_box_size)
        canvas.fill(Qt.GlobalColor.transparent)

        painter = QPainter(canvas)
        target_size = QSize(int(scaled_pixmap.width() * scale), int(scaled_pixmap.height() * scale))

        final_pixmap_scaled = final_pixmap.scaled(target_size, Qt.AspectRatioMode.IgnoreAspectRatio,
                                                  Qt.TransformationMode.SmoothTransformation)

        # Center the final pixmap on the canvas
        x = (preview_box_size.width() - final_pixmap_scaled.width()) / 2
        y = (preview_box_size.height() - final_pixmap_scaled.height()) / 2

        painter.drawPixmap(int(x), int(y), final_pixmap_scaled)
        painter.end()

        self.preview_area.setPixmap(canvas)

    def set_video_volume(self, value):
        if self.audio_output:
            self.audio_output.setMuted(False)
            self.mute_check.setChecked(False)
            vol_float = value / 100.0
            self.audio_output.setVolume(vol_float)
            self.volume_value_label.setText(f"{value} %")

    def toggle_mute(self, checked):
        if self.audio_output:
            self.audio_output.setMuted(checked)

    def get_settings(self):
        self.settings['width'] = self.width_spin.value()
        self.settings['height'] = self.height_spin.value()
        if self.is_image:
            self.settings['rotation'] = self.rotation_spin.value()
            self.settings['scale'] = self.scale_slider.value() / 100.0
        else:  # is video
            self.settings['volume'] = self.volume_slider.value() / 100.0 if not self.mute_check.isChecked() else 0.0

        self.settings['keyframe_enabled'] = self.enable_keyframe_check.isChecked()
        self.settings['keyframe_start_pos'] = [self.start_x_spin.value(), self.start_y_spin.value()]
        self.settings['keyframe_end_pos'] = [self.end_x_spin.value(), self.end_y_spin.value()]
        self.settings['keyframe_duration'] = self.duration_spin.value()

        return self.settings

    def reject(self):
        if self.media_player:
            self.media_player.stop()
        super().reject()

    def accept(self):
        if self.media_player:
            self.media_player.stop()
        super().accept()

    def closeEvent(self, event):
        if self.media_player:
            self.media_player.stop()
        super().closeEvent(event)
