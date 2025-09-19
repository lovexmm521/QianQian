# settings_window.py
# 应用程序的设置窗口 (已更新)

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QPushButton, QCheckBox, QGroupBox,
                             QRadioButton, QFileDialog, QMessageBox, QDateEdit,
                             QHBoxLayout, QLabel, QLineEdit, QFontComboBox,
                             QSpinBox, QColorDialog, QFrame)
from PyQt6.QtCore import QSettings, QDate
from PyQt6.QtGui import QFont, QColor, QPalette
from collections import defaultdict


class SettingsWindow(QDialog):
    """
    设置窗口类。
    """

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.db_manager = db_manager
        # --- 使用INI文件进行设置 ---
        self.settings = QSettings("settings.ini", QSettings.Format.IniFormat)
        self.setMinimumSize(450, 500)

        layout = QVBoxLayout(self)

        # --- 视图模式设置 ---
        view_groupbox = QGroupBox("默认视图模式")
        view_layout = QVBoxLayout()
        self.week_view_radio = QRadioButton("周视图 (默认显示一周)")
        self.day_view_radio = QRadioButton("单日视图 (默认显示当天)")

        default_view = self.settings.value("default_view_mode", "week", type=str)
        if default_view == "week":
            self.week_view_radio.setChecked(True)
        else:
            self.day_view_radio.setChecked(True)

        self.week_view_radio.toggled.connect(self.save_view_mode_setting)
        self.day_view_radio.toggled.connect(self.save_view_mode_setting)

        view_layout.addWidget(self.week_view_radio)
        view_layout.addWidget(self.day_view_radio)
        view_groupbox.setLayout(view_layout)
        layout.addWidget(view_groupbox)

        # --- 界面元素设置 ---
        ui_groupbox = QGroupBox("界面元素显示")
        ui_layout = QVBoxLayout()

        self.show_delete_check = QCheckBox("在时间段上显示删除图标")
        show_delete = self.settings.value("show_delete_button", False, type=bool)
        self.show_delete_check.setChecked(show_delete)
        self.show_delete_check.toggled.connect(
            lambda checked: self.settings.setValue("show_delete_button", checked)
        )
        ui_layout.addWidget(self.show_delete_check)

        self.show_status_icon_check = QCheckBox("在计划上显示打卡图标")
        # 默认设置为 True
        show_status_icon = self.settings.value("show_status_icon", True, type=bool)
        self.show_status_icon_check.setChecked(show_status_icon)
        self.show_status_icon_check.toggled.connect(
            lambda checked: self.settings.setValue("show_status_icon", checked)
        )
        ui_layout.addWidget(self.show_status_icon_check)

        self.show_date_in_header_check = QCheckBox("在表头中显示日期 (例如 '周一 08-25')")
        show_date_in_header = self.settings.value("show_date_in_header", False, type=bool)
        self.show_date_in_header_check.setChecked(show_date_in_header)
        self.show_date_in_header_check.toggled.connect(
            lambda checked: self.settings.setValue("show_date_in_header", checked)
        )
        ui_layout.addWidget(self.show_date_in_header_check)

        ui_groupbox.setLayout(ui_layout)
        layout.addWidget(ui_groupbox)

        # --- 自定义标题设置 ---
        title_groupbox = QGroupBox("自定义标题")
        title_groupbox.setCheckable(True)
        use_custom_title = self.settings.value("title/custom_enabled", False, type=bool)
        title_groupbox.setChecked(use_custom_title)
        title_groupbox.toggled.connect(lambda checked: self.settings.setValue("title/custom_enabled", checked))

        title_layout = QVBoxLayout()

        # 标题文本
        text_layout = QHBoxLayout()
        text_layout.addWidget(QLabel("标题文本:"))
        self.title_text_edit = QLineEdit(self.settings.value("title/text", "", type=str))
        self.title_text_edit.textChanged.connect(lambda text: self.settings.setValue("title/text", text))
        text_layout.addWidget(self.title_text_edit)
        title_layout.addLayout(text_layout)

        # 字体和字号
        font_layout = QHBoxLayout()
        self.font_combo = QFontComboBox()
        current_font_family = self.settings.value("title/font_family", "Microsoft YaHei UI", type=str)
        self.font_combo.setCurrentFont(QFont(current_font_family))
        self.font_combo.currentFontChanged.connect(self.save_font_family)
        font_layout.addWidget(self.font_combo)

        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 72)
        self.font_size_spin.setValue(self.settings.value("title/font_size", 24, type=int))
        self.font_size_spin.valueChanged.connect(lambda size: self.settings.setValue("title/font_size", size))
        font_layout.addWidget(self.font_size_spin)
        title_layout.addLayout(font_layout)

        # 颜色
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("颜色:"))
        self.color_preview = QFrame()
        self.color_preview.setFrameShape(QFrame.Shape.StyledPanel)
        self.color_preview.setFixedSize(24, 24)
        self.update_color_preview(self.settings.value("title/color", "#2c3e50", type=str))

        color_button = QPushButton("选择颜色")
        color_button.clicked.connect(self.choose_color)
        color_layout.addWidget(color_button)
        color_layout.addWidget(self.color_preview)
        color_layout.addStretch()
        title_layout.addLayout(color_layout)

        title_groupbox.setLayout(title_layout)
        layout.addWidget(title_groupbox)

        # --- 导出数据设置 ---
        export_groupbox = QGroupBox("导出数据")
        export_layout = QVBoxLayout()

        dates_layout = QHBoxLayout()
        dates_layout.addWidget(QLabel("从:"))
        self.start_date_edit = QDateEdit(QDate.currentDate())
        self.start_date_edit.setCalendarPopup(True)
        dates_layout.addWidget(self.start_date_edit)
        dates_layout.addWidget(QLabel("到:"))
        self.end_date_edit = QDateEdit(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        dates_layout.addWidget(self.end_date_edit)
        export_layout.addLayout(dates_layout)

        export_button = QPushButton("导出为文件...")
        export_button.clicked.connect(self.export_data)
        export_layout.addWidget(export_button)

        export_groupbox.setLayout(export_layout)
        layout.addWidget(export_groupbox)

        layout.addStretch()

        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

    def save_font_family(self, font):
        self.settings.setValue("title/font_family", font.family())

    def choose_color(self):
        initial_color = self.settings.value("title/color", "#2c3e50", type=str)
        color = QColorDialog.getColor(QColor(initial_color), self, "选择标题颜色")
        if color.isValid():
            self.settings.setValue("title/color", color.name())
            self.update_color_preview(color.name())

    def update_color_preview(self, color_hex):
        palette = self.color_preview.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(color_hex))
        self.color_preview.setPalette(palette)
        self.color_preview.setAutoFillBackground(True)

    def save_view_mode_setting(self, checked):
        # 确保只有选中的那个按钮会触发保存
        if checked:
            if self.sender() == self.week_view_radio:
                self.settings.setValue("default_view_mode", "week")
            elif self.sender() == self.day_view_radio:
                self.settings.setValue("default_view_mode", "day")

    def export_data(self):
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")

        if self.start_date_edit.date() > self.end_date_edit.date():
            QMessageBox.warning(self, "日期错误", "开始日期不能晚于结束日期。")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存计划", "", "Markdown 文件 (*.md);;文本文档 (*.txt)"
        )

        if not file_path:
            return

        plans = self.db_manager.get_plans_for_export(start_date, end_date)

        if not plans:
            QMessageBox.information(self, "无内容", "选定的日期范围内没有可导出的计划内容。")
            return

        # 按日期对计划进行分组
        grouped_plans = defaultdict(list)
        for plan_date, start_time, end_time, plan_text in plans:
            grouped_plans[plan_date].append((start_time, end_time, plan_text))

        weekdays_map_export = {1: "周一", 2: "周二", 3: "周三", 4: "周四", 5: "周五", 6: "周六", 7: "周日"}

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                sorted_dates = sorted(grouped_plans.keys())

                for i, date_str in enumerate(sorted_dates):
                    q_date = QDate.fromString(date_str, "yyyy-MM-dd")
                    date_header = f"【{q_date.month()}.{q_date.day()} {weekdays_map_export[q_date.dayOfWeek()]}】"
                    f.write(date_header + "\n")

                    for start_time, end_time, text in sorted(grouped_plans[date_str]):
                        # 替换换行符，使其在同一行内
                        cleaned_text = text.replace('\n', ' ').replace('\r', '')
                        f.write(f"{start_time}-{end_time}      {cleaned_text}\n")

                    # 在日期之间添加空行
                    if i < len(sorted_dates) - 1:
                        f.write("\n")

            QMessageBox.information(self, "导出成功", f"计划已成功导出到:\n{file_path}")

        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出过程中发生错误:\n{e}")

