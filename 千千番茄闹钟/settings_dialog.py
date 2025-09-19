# settings_dialog.py
import sys
import os
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QTabWidget, QLabel, QSpinBox, QLineEdit, QPushButton,
    QCheckBox, QFileDialog, QApplication, QGroupBox, QSlider,
    QColorDialog, QFontComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette

from config import config


class SettingsDialog(QDialog):
    settings_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumSize(500, 550)
        self.init_ui()
        self.load_settings()
        self.toggle_sound_controls()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_basic_tab(), "基础")
        self.tabs.addTab(self._create_notifications_tab(), "通知")
        self.tabs.addTab(self._create_theme_tab(), "主题")
        self.tabs.addTab(self._create_advanced_tab(), "高级")

        main_layout.addWidget(self.tabs)

        button_layout = QHBoxLayout()
        self.save_button = QPushButton("保存并关闭")
        self.save_button.clicked.connect(self.save_and_close)
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)

        main_layout.addLayout(button_layout)

    def _create_basic_tab(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)

        self.work_minutes_spinbox = QSpinBox()
        self.work_minutes_spinbox.setRange(1, 120)
        self.break_minutes_spinbox = QSpinBox()
        self.break_minutes_spinbox.setRange(1, 60)
        self.long_break_minutes_spinbox = QSpinBox()
        self.long_break_minutes_spinbox.setRange(1, 120)
        self.pomodoros_per_cycle_spinbox = QSpinBox()
        self.pomodoros_per_cycle_spinbox.setRange(1, 10)

        layout.addRow("工作时长 (分钟):", self.work_minutes_spinbox)
        layout.addRow("休息时长 (分钟):", self.break_minutes_spinbox)
        layout.addRow("长休息时长 (分钟):", self.long_break_minutes_spinbox)
        layout.addRow("每轮番茄钟数量:", self.pomodoros_per_cycle_spinbox)

        return widget

    def _create_notifications_tab(self):
        widget = QWidget()
        main_layout = QVBoxLayout(widget)

        general_group = QGroupBox("通用开关")
        general_layout = QVBoxLayout(general_group)
        self.desktop_notify_checkbox = QCheckBox("开启桌面弹窗提醒")
        self.sound_notify_checkbox = QCheckBox("开启音效提醒")
        general_layout.addWidget(self.desktop_notify_checkbox)
        general_layout.addWidget(self.sound_notify_checkbox)
        main_layout.addWidget(general_group)

        text_group = QGroupBox("弹窗提醒文字")
        text_layout = QFormLayout(text_group)
        self.work_finish_text_input = QLineEdit()
        self.break_finish_text_input = QLineEdit()
        self.long_break_finish_text_input = QLineEdit()
        text_layout.addRow("工作结束:", self.work_finish_text_input)
        text_layout.addRow("休息结束:", self.break_finish_text_input)
        text_layout.addRow("长休息结束:", self.long_break_finish_text_input)
        main_layout.addWidget(text_group)

        sound_group = QGroupBox("音效设置")
        sound_layout = QVBoxLayout(sound_group)

        self.specific_sounds_group = QGroupBox("指定音效")
        specific_sounds_layout = QFormLayout(self.specific_sounds_group)
        self.work_sound_controls = self._create_sound_picker("work_sound")
        self.break_sound_controls = self._create_sound_picker("break_sound")
        self.long_break_sound_controls = self._create_sound_picker("long_break_sound")
        specific_sounds_layout.addRow("工作结束:", self.work_sound_controls["layout"])
        specific_sounds_layout.addRow("休息结束:", self.break_sound_controls["layout"])
        specific_sounds_layout.addRow("长休息结束:", self.long_break_sound_controls["layout"])

        self.random_sound_group = QGroupBox("随机音效")
        self.random_sound_group.setCheckable(True)
        random_sound_layout = QFormLayout(self.random_sound_group)
        self.random_sound_controls = self._create_sound_picker("random_sound", is_folder=True)
        random_sound_layout.addRow("音效文件夹:", self.random_sound_controls["layout"])

        sound_layout.addWidget(self.specific_sounds_group)
        sound_layout.addWidget(self.random_sound_group)
        main_layout.addWidget(sound_group)

        self.random_sound_group.toggled.connect(self.toggle_sound_controls)

        return widget

    def _create_theme_tab(self):
        widget = QWidget()

        visibility_group = QGroupBox("界面元素显示")
        visibility_layout = QVBoxLayout(visibility_group)
        self.show_custom_text_checkbox = QCheckBox("显示主界面文字")
        # **修改**: 修正复选框文字
        self.show_app_title_checkbox = QCheckBox("显示标题")
        visibility_layout.addWidget(self.show_custom_text_checkbox)
        visibility_layout.addWidget(self.show_app_title_checkbox)

        text_group = QGroupBox("主界面文字")
        text_layout = QFormLayout(text_group)

        self.custom_text_input = QLineEdit()
        text_layout.addRow("显示文字:", self.custom_text_input)

        self.custom_text_font_combo = QFontComboBox()
        text_layout.addRow("字体:", self.custom_text_font_combo)

        self.custom_text_font_size_spinbox = QSpinBox()
        self.custom_text_font_size_spinbox.setRange(8, 30)
        self.custom_text_color_button = self._create_color_picker_button('custom_text_color')
        self.custom_text_color_preview = self._create_color_preview_label()

        style_layout = QHBoxLayout()
        style_layout.addWidget(QLabel("字号:"))
        style_layout.addWidget(self.custom_text_font_size_spinbox)
        style_layout.addWidget(QLabel("颜色:"))
        style_layout.addWidget(self.custom_text_color_button)
        style_layout.addWidget(self.custom_text_color_preview)
        style_layout.addStretch()
        text_layout.addRow("文字样式:", style_layout)

        color_group = QGroupBox("颜色设置")
        color_layout = QFormLayout(color_group)

        self.work_color_button = self._create_color_picker_button('work_color')
        self.work_color_preview = self._create_color_preview_label()
        color_layout.addRow("工作时钟背景:", self._create_color_layout(self.work_color_button, self.work_color_preview))

        self.break_color_button = self._create_color_picker_button('break_color')
        self.break_color_preview = self._create_color_preview_label()
        color_layout.addRow("休息时钟背景:",
                            self._create_color_layout(self.break_color_button, self.break_color_preview))

        self.long_break_color_button = self._create_color_picker_button('long_break_color')
        self.long_break_color_preview = self._create_color_preview_label()
        color_layout.addRow("长休息时钟背景:",
                            self._create_color_layout(self.long_break_color_button, self.long_break_color_preview))

        self.timer_text_color_button = self._create_color_picker_button('timer_text_color')
        self.timer_text_color_preview = self._create_color_preview_label()
        color_layout.addRow("时钟时间颜色:",
                            self._create_color_layout(self.timer_text_color_button, self.timer_text_color_preview))

        main_v_layout = QVBoxLayout(widget)
        main_v_layout.addWidget(visibility_group)
        main_v_layout.addWidget(text_group)
        main_v_layout.addWidget(color_group)
        main_v_layout.addStretch()

        return widget

    def _create_advanced_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        mode_group = QGroupBox("显示模式")
        mode_layout = QVBoxLayout(mode_group)
        self.compact_mode_checkbox = QCheckBox("开启精简模式 (双击时间自由切换模式)")
        mode_layout.addWidget(self.compact_mode_checkbox)

        general_group = QGroupBox("通用")
        general_layout = QVBoxLayout(general_group)
        self.always_on_top_checkbox = QCheckBox("窗口总在最前")
        self.auto_cycle_checkbox = QCheckBox("时间自动循环")
        general_layout.addWidget(self.always_on_top_checkbox)
        general_layout.addWidget(self.auto_cycle_checkbox)

        debug_group = QGroupBox("开发者选项")
        debug_layout = QVBoxLayout(debug_group)
        self.debug_mode_checkbox = QCheckBox("开启调试模式 (所有计时变为1秒)")
        debug_layout.addWidget(self.debug_mode_checkbox)

        layout.addWidget(mode_group)
        layout.addWidget(general_group)
        layout.addWidget(debug_group)
        layout.addStretch()

        return widget

    def _create_sound_picker(self, name, is_folder=False):
        controls = {}
        layout = QHBoxLayout()
        controls["path_label"] = QLabel("未选择")
        controls["path_label"].setWordWrap(True)
        button_text = "选择文件夹" if is_folder else "选择文件"
        controls["button"] = QPushButton(button_text)
        if is_folder:
            controls["button"].clicked.connect(lambda: self.select_folder(controls["path_label"]))
        else:
            controls["button"].clicked.connect(lambda: self.select_file(controls["path_label"]))
        controls["slider"] = QSlider(Qt.Orientation.Horizontal)
        controls["slider"].setRange(0, 100)
        controls["volume_label"] = QLabel("80%")
        controls["slider"].valueChanged.connect(lambda val: controls["volume_label"].setText(f"{val}%"))
        layout.addWidget(controls["button"])
        layout.addWidget(controls["path_label"], 1)
        layout.addWidget(controls["slider"])
        layout.addWidget(controls["volume_label"])
        controls["layout"] = layout
        return controls

    def _create_color_picker_button(self, config_key):
        button = QPushButton("选择颜色")
        button.clicked.connect(lambda: self._pick_color(config_key))
        return button

    def _create_color_preview_label(self):
        label = QLabel()
        label.setFixedSize(50, 20)
        label.setAutoFillBackground(True)
        return label

    def _create_color_layout(self, button, preview_label):
        layout = QHBoxLayout()
        layout.addWidget(button)
        layout.addWidget(preview_label)
        layout.addStretch()
        return layout

    def _pick_color(self, config_key):
        preview_widgets = {
            'custom_text_color': self.custom_text_color_preview,
            'work_color': self.work_color_preview,
            'break_color': self.break_color_preview,
            'long_break_color': self.long_break_color_preview,
            'timer_text_color': self.timer_text_color_preview,
        }
        preview_widget = preview_widgets.get(config_key)

        current_color_hex = getattr(self, f"_{config_key}_hex", config.get(config_key))
        color = QColorDialog.getColor(QColor(current_color_hex), self, "选择颜色")

        if color.isValid():
            setattr(self, f"_{config_key}_hex", color.name())
            if preview_widget:
                self.update_color_preview(preview_widget, color.name())

    def update_color_preview(self, label, color_hex):
        label.setStyleSheet(f"background-color: {color_hex}; border: 1px solid #AAAAAA; border-radius: 3px;")

    def select_file(self, label):
        filepath, _ = QFileDialog.getOpenFileName(self, "选择音效文件", "", "音频文件 (*.wav *.mp3 *.ogg *.flac)")
        if filepath:
            label.setText(os.path.basename(filepath))
            label.setToolTip(filepath)

    def select_folder(self, label):
        folderpath = QFileDialog.getExistingDirectory(self, "选择音效文件夹")
        if folderpath:
            label.setText(os.path.basename(folderpath))
            label.setToolTip(folderpath)

    def toggle_sound_controls(self):
        is_random = self.random_sound_group.isChecked()
        self.specific_sounds_group.setEnabled(not is_random)

    def load_settings(self):
        # Basic
        self.work_minutes_spinbox.setValue(config.get("work_minutes"))
        self.break_minutes_spinbox.setValue(config.get("break_minutes"))
        self.long_break_minutes_spinbox.setValue(config.get("long_break_minutes"))
        self.pomodoros_per_cycle_spinbox.setValue(config.get("pomodoros_per_cycle"))

        # Notifications
        self.desktop_notify_checkbox.setChecked(config.get("desktop_notification"))
        self.sound_notify_checkbox.setChecked(config.get("sound_notification"))
        self.work_finish_text_input.setText(config.get("work_finish_text"))
        self.break_finish_text_input.setText(config.get("break_finish_text"))
        self.long_break_finish_text_input.setText(config.get("long_break_finish_text"))

        # Sounds
        self._load_sound_control(self.work_sound_controls, "work_sound")
        self._load_sound_control(self.break_sound_controls, "break_sound")
        self._load_sound_control(self.long_break_sound_controls, "long_break_sound")
        self._load_sound_control(self.random_sound_controls, "random_sound", is_folder=True)
        self.random_sound_group.setChecked(config.get("random_sound_enabled"))

        # Theme
        self.show_custom_text_checkbox.setChecked(config.get("show_custom_text"))
        self.show_app_title_checkbox.setChecked(config.get("show_app_title"))
        self.custom_text_input.setText(config.get("custom_text"))
        font_family = config.get("custom_text_font_family")
        self.custom_text_font_combo.setCurrentFont(QFont(font_family))
        self.custom_text_font_size_spinbox.setValue(config.get("custom_text_font_size"))
        for key in ['custom_text_color', 'work_color', 'break_color', 'long_break_color', 'timer_text_color']:
            color_hex = config.get(key)
            setattr(self, f"_{key}_hex", color_hex)
            preview_widget = getattr(self, f"{key.replace('_color', '')}_color_preview", None)
            if preview_widget:
                self.update_color_preview(preview_widget, color_hex)

        # Advanced
        self.compact_mode_checkbox.setChecked(config.get("compact_mode_enabled"))
        self.always_on_top_checkbox.setChecked(config.get("always_on_top"))
        self.auto_cycle_checkbox.setChecked(config.get("auto_cycle_enabled"))
        self.debug_mode_checkbox.setChecked(config.get("developer_debug_mode"))

    def _load_sound_control(self, controls, name, is_folder=False):
        path = config.get(f"{name}_folder_path" if is_folder else f"{name}_path")
        volume = config.get(f"{name}_volume")
        if path:
            controls["path_label"].setText(os.path.basename(path))
            controls["path_label"].setToolTip(path)
        else:
            controls["path_label"].setText("未选择")
            controls["path_label"].setToolTip("")
        controls["slider"].setValue(volume if volume is not None else 80)

    def save_and_close(self):
        # Basic
        config.set("work_minutes", self.work_minutes_spinbox.value())
        config.set("break_minutes", self.break_minutes_spinbox.value())
        config.set("long_break_minutes", self.long_break_minutes_spinbox.value())
        config.set("pomodoros_per_cycle", self.pomodoros_per_cycle_spinbox.value())

        # Notifications
        config.set("desktop_notification", self.desktop_notify_checkbox.isChecked())
        config.set("sound_notification", self.sound_notify_checkbox.isChecked())
        config.set("work_finish_text", self.work_finish_text_input.text())
        config.set("break_finish_text", self.break_finish_text_input.text())
        config.set("long_break_finish_text", self.long_break_finish_text_input.text())

        # Sounds
        self._save_sound_control(self.work_sound_controls, "work_sound")
        self._save_sound_control(self.break_sound_controls, "break_sound")
        self._save_sound_control(self.long_break_sound_controls, "long_break_sound")
        self._save_sound_control(self.random_sound_controls, "random_sound", is_folder=True)
        config.set("random_sound_enabled", self.random_sound_group.isChecked())

        # Theme
        config.set("show_custom_text", self.show_custom_text_checkbox.isChecked())
        config.set("show_app_title", self.show_app_title_checkbox.isChecked())
        config.set("custom_text", self.custom_text_input.text())
        config.set("custom_text_font_family", self.custom_text_font_combo.currentFont().family())
        config.set("custom_text_font_size", self.custom_text_font_size_spinbox.value())
        for key in ['custom_text_color', 'work_color', 'break_color', 'long_break_color', 'timer_text_color']:
            config.set(key, getattr(self, f"_{key}_hex"))

        # Advanced
        config.set("compact_mode_enabled", self.compact_mode_checkbox.isChecked())
        config.set("always_on_top", self.always_on_top_checkbox.isChecked())
        config.set("auto_cycle_enabled", self.auto_cycle_checkbox.isChecked())
        config.set("developer_debug_mode", self.debug_mode_checkbox.isChecked())

        self.settings_changed.emit()
        self.accept()

    def _save_sound_control(self, controls, name, is_folder=False):
        path = controls["path_label"].toolTip()
        volume = controls["slider"].value()
        config.set(f"{name}_folder_path" if is_folder else f"{name}_path", path)
        config.set(f"{name}_volume", volume)
