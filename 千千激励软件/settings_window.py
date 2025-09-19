import logging
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QFileDialog, QGroupBox, QRadioButton, QSpinBox,
                             QCheckBox, QFormLayout, QLabel, QSlider)
from PyQt6.QtCore import pyqtSignal, QPoint, Qt


class SettingsTab(QWidget):
    settings_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)

        music_group = QGroupBox("背景音乐设置")
        music_layout = QVBoxLayout(music_group)

        # Single file widget
        self.single_file_widget = QWidget()
        single_file_layout = QHBoxLayout(self.single_file_widget)
        single_file_layout.setContentsMargins(0, 0, 0, 0)
        self.music_path_label = QLabel("未选择文件")
        self.music_path_label.setWordWrap(True)
        select_music_btn = QPushButton("选择音乐文件...")
        select_music_btn.clicked.connect(self.select_music)
        single_file_layout.addWidget(QLabel("当前音乐:"))
        single_file_layout.addWidget(self.music_path_label)
        single_file_layout.addStretch()
        single_file_layout.addWidget(select_music_btn)

        # Folder mode checkbox
        self.folder_mode_check = QCheckBox("启用音乐文件夹随机播放")

        # Folder selection widget
        self.folder_widget = QWidget()
        folder_layout = QHBoxLayout(self.folder_widget)
        folder_layout.setContentsMargins(0, 0, 0, 0)
        self.folder_path_label = QLabel("未选择文件夹")
        self.folder_path_label.setWordWrap(True)
        select_folder_btn = QPushButton("选择文件夹...")
        select_folder_btn.clicked.connect(self.select_folder)
        folder_layout.addWidget(QLabel("音乐文件夹:"))
        folder_layout.addWidget(self.folder_path_label)
        folder_layout.addStretch()
        folder_layout.addWidget(select_folder_btn)

        # Volume control
        volume_layout = QHBoxLayout()
        self.bg_volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.bg_volume_slider.setRange(0, 100)
        self.bg_volume_label = QLabel("100 %")
        volume_layout.addWidget(QLabel("背景音乐音量:"))
        volume_layout.addWidget(self.bg_volume_slider)
        volume_layout.addWidget(self.bg_volume_label)

        self.mute_on_video_check = QCheckBox("播放视频时静音背景音乐")

        music_layout.addWidget(self.single_file_widget)
        music_layout.addWidget(self.folder_mode_check)
        music_layout.addWidget(self.folder_widget)
        music_layout.addSpacing(10)
        music_layout.addLayout(volume_layout)
        music_layout.addSpacing(10)
        music_layout.addWidget(self.mute_on_video_check)

        playback_group = QGroupBox("播放设置")
        playback_form_layout = QFormLayout(playback_group)
        playback_form_layout.setSpacing(10)

        pos_layout = QVBoxLayout()
        self.random_pos_radio = QRadioButton("随机位置")
        self.fixed_pos_radio = QRadioButton("固定位置")

        self.pos_coords_widget = QWidget()
        pos_coords_layout = QHBoxLayout(self.pos_coords_widget)
        pos_coords_layout.setContentsMargins(0, 0, 0, 0)
        self.pos_x_spin = QSpinBox()
        self.pos_x_spin.setRange(0, 5000)
        self.pos_y_spin = QSpinBox()
        self.pos_y_spin.setRange(0, 5000)
        pos_coords_layout.addWidget(QLabel("X:"))
        pos_coords_layout.addWidget(self.pos_x_spin)
        pos_coords_layout.addWidget(QLabel("Y:"))
        pos_coords_layout.addWidget(self.pos_y_spin)
        pos_coords_layout.addStretch()

        pos_layout.addWidget(self.random_pos_radio)
        pos_layout.addWidget(self.fixed_pos_radio)
        pos_layout.addWidget(self.pos_coords_widget)
        playback_form_layout.addRow("展示位置:", pos_layout)

        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 300)
        self.interval_spin.setSuffix(" 秒")
        playback_form_layout.addRow("图片切换间隔:", self.interval_spin)

        self.random_order_check = QCheckBox("随机顺序播放")
        self.loop_playback_check = QCheckBox("循环播放列表")
        self.fade_effect_check = QCheckBox("使用渐进渐出效果")

        playback_form_layout.addRow(self.random_order_check)
        playback_form_layout.addRow(self.loop_playback_check)
        playback_form_layout.addRow(self.fade_effect_check)

        main_layout.addWidget(music_group)
        main_layout.addWidget(playback_group)
        main_layout.addStretch()

        # 连接信号
        self.mute_on_video_check.stateChanged.connect(self.update_settings)
        self.random_pos_radio.toggled.connect(self.update_settings)
        self.fixed_pos_radio.toggled.connect(self.update_settings)
        self.pos_x_spin.valueChanged.connect(self.update_settings)
        self.pos_y_spin.valueChanged.connect(self.update_settings)
        self.interval_spin.valueChanged.connect(self.update_settings)
        self.random_order_check.stateChanged.connect(self.update_settings)
        self.loop_playback_check.stateChanged.connect(self.update_settings)
        self.fade_effect_check.stateChanged.connect(self.update_settings)
        self.fixed_pos_radio.toggled.connect(self.pos_coords_widget.setEnabled)

        self.folder_mode_check.toggled.connect(self.toggle_music_mode)
        self.bg_volume_slider.valueChanged.connect(self.update_volume_label)
        self.bg_volume_slider.valueChanged.connect(self.update_settings)

        self.toggle_music_mode(False)  # Initialize

    def select_music(self):
        file, _ = QFileDialog.getOpenFileName(self, "选择音乐文件", "", "音频文件 (*.mp3 *.wav *.ogg)")
        if file:
            self.music_path_label.setText(os.path.basename(file))
            self.music_path_label.setToolTip(file)
            self.update_settings()

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择音乐文件夹")
        if folder:
            self.folder_path_label.setText(os.path.basename(folder))
            self.folder_path_label.setToolTip(folder)
            self.update_settings()

    def update_volume_label(self, value):
        self.bg_volume_label.setText(f"{value} %")

    def toggle_music_mode(self, checked):
        self.folder_widget.setEnabled(checked)
        self.single_file_widget.setEnabled(not checked)
        self.update_settings()

    def apply_settings(self, settings):
        """应用从主窗口加载的设置来更新UI"""
        logging.info(f"正在将加载的设置应用到UI: {settings}")
        music_path = settings.get('music_path', '')
        self.music_path_label.setToolTip(music_path)
        self.music_path_label.setText(os.path.basename(music_path) if music_path else "未选择文件")

        folder_path = settings.get('music_folder_path', '')
        self.folder_path_label.setToolTip(folder_path)
        self.folder_path_label.setText(os.path.basename(folder_path) if folder_path else "未选择文件夹")

        self.folder_mode_check.setChecked(settings.get('use_music_folder', False))
        self.bg_volume_slider.setValue(settings.get('bg_volume', 100))
        self.mute_on_video_check.setChecked(settings.get('mute_on_video', True))

        pos_mode = settings.get('position_mode', 'random')
        if pos_mode == 'fixed':
            self.fixed_pos_radio.setChecked(True)
        else:
            self.random_pos_radio.setChecked(True)

        fixed_pos = settings.get('fixed_pos', QPoint(100, 100))
        if isinstance(fixed_pos, QPoint):
            self.pos_x_spin.setValue(fixed_pos.x())
            self.pos_y_spin.setValue(fixed_pos.y())

        self.interval_spin.setValue(settings.get('interval', 5))
        self.random_order_check.setChecked(settings.get('is_random_order', True))
        self.loop_playback_check.setChecked(settings.get('loop_playback', True))
        self.fade_effect_check.setChecked(settings.get('use_fade_effect', True))
        self.update_settings()  # 确保信号在应用后发出

    def update_settings(self):
        """从UI控件读取当前状态并发出信号"""
        current_settings = {}
        music_tooltip = self.music_path_label.toolTip()
        current_settings['music_path'] = music_tooltip if "未选择" not in music_tooltip and music_tooltip else ""

        folder_tooltip = self.folder_path_label.toolTip()
        current_settings[
            'music_folder_path'] = folder_tooltip if "未选择" not in folder_tooltip and folder_tooltip else ""
        current_settings['use_music_folder'] = self.folder_mode_check.isChecked()
        current_settings['bg_volume'] = self.bg_volume_slider.value()

        current_settings['mute_on_video'] = self.mute_on_video_check.isChecked()
        current_settings['position_mode'] = 'fixed' if self.fixed_pos_radio.isChecked() else 'random'
        current_settings['fixed_pos'] = QPoint(self.pos_x_spin.value(), self.pos_y_spin.value())
        current_settings['interval'] = self.interval_spin.value()
        current_settings['is_random_order'] = self.random_order_check.isChecked()
        current_settings['use_fade_effect'] = self.fade_effect_check.isChecked()
        current_settings['loop_playback'] = self.loop_playback_check.isChecked()

        logging.info(f"设置已更新(从UI读取): {current_settings}")
        self.settings_changed.emit(current_settings)

