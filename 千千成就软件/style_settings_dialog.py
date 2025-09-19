from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QFormLayout, QRadioButton, QFontComboBox, QSpinBox,
                             QColorDialog, QWidget, QLineEdit, QFileDialog)
from PyQt6.QtGui import QFont, QColor


class StyleSettingsDialog(QDialog):
    def __init__(self, current_config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("显示设置")
        self.config = current_config

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.widgets = {}
        for key, name in [
            ("levelName", "等级名称"),
            ("wealthValue", "财富/分数值"),
            ("rewardTitle", "奖励文字标题"),
            ("rewardText", "奖励文字"),
            ("planTitle", "计划标题"),
            ("planContent", "计划内容"),
            ("planRewardText", "计划奖励文字")
        ]:
            font_combo = QFontComboBox()
            font_size_spin = QSpinBox();
            font_size_spin.setRange(8, 72)
            color_swatch = QLabel();
            color_swatch.setFixedSize(24, 24);
            color_swatch.setAutoFillBackground(True)
            color_button = QPushButton("选择颜色")

            cfg = self.config.get(key, {})
            font_combo.setCurrentFont(QFont(cfg.get("family", "Microsoft YaHei")))

            default_sizes = {"levelName": 28, "wealthValue": 20, "rewardTitle": 18, "rewardText": 16, "planTitle": 14,
                             "planContent": 14, "planRewardText": 14}
            font_size_spin.setValue(cfg.get("size", default_sizes.get(key, 14)))

            default_colors = {
                "levelName": "#4682B4",
                "wealthValue": "#FFA500",
                "rewardTitle": "#CD5C5C",
                "rewardText": "#444444",
                "planTitle": "#333333",
                "planContent": "#333333",
                "planRewardText": "#E59866"
            }
            initial_color = cfg.get("color", default_colors.get(key, "#000000"))
            color_swatch.setStyleSheet(f"background-color: {initial_color}; border: 1px solid grey;")
            color_button.clicked.connect(lambda _, s=color_swatch: self.choose_color(s))

            row_layout = QHBoxLayout()
            row_layout.addWidget(font_combo);
            row_layout.addWidget(font_size_spin);
            row_layout.addSpacing(10)
            row_layout.addWidget(color_swatch);
            row_layout.addWidget(color_button)

            form_layout.addRow(f"{name}:", row_layout)
            self.widgets[key] = (font_combo, font_size_spin, color_swatch)

        self.reward_bg_swatch = QLabel()
        self.reward_bg_swatch.setFixedSize(24, 24)
        self.reward_bg_swatch.setAutoFillBackground(True)
        reward_bg_button = QPushButton("选择颜色")
        initial_reward_bg = self.config.get("rewardCardBackground", "#FFFACD")
        self.reward_bg_swatch.setStyleSheet(f"background-color: {initial_reward_bg}; border: 1px solid grey;")
        reward_bg_button.clicked.connect(lambda: self.choose_color(self.reward_bg_swatch))

        reward_bg_layout = QHBoxLayout()
        reward_bg_layout.addWidget(self.reward_bg_swatch)
        reward_bg_layout.addWidget(reward_bg_button)
        reward_bg_layout.addStretch()
        form_layout.addRow("奖励框背景色:", reward_bg_layout)

        self.folder_path_edit = QLineEdit(self.config.get("level_image_folder", "level"))
        browse_button = QPushButton("浏览...")
        browse_button.clicked.connect(self.browse_folder)
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(self.folder_path_edit)
        folder_layout.addWidget(browse_button)
        form_layout.addRow("等级图片文件夹:", folder_layout)

        self.img_current_radio = QRadioButton("当前等级")
        self.img_next_radio = QRadioButton("下一等级")
        self.img_next_avail_radio = QRadioButton("下一个有效奖励")
        img_mode = self.config.get("reward_image_display_mode", "current")
        if img_mode == "next":
            self.img_next_radio.setChecked(True)
        elif img_mode == "next_available":
            self.img_next_avail_radio.setChecked(True)
        else:
            self.img_current_radio.setChecked(True)

        img_radio_container = QWidget()
        img_radio_layout = QHBoxLayout(img_radio_container);
        img_radio_layout.setContentsMargins(0, 0, 0, 0)
        img_radio_layout.addWidget(self.img_current_radio);
        img_radio_layout.addWidget(self.img_next_radio)
        img_radio_layout.addWidget(self.img_next_avail_radio);
        img_radio_layout.addStretch()
        form_layout.addRow("奖励图片显示:", img_radio_container)

        self.text_current_radio = QRadioButton("当前等级")
        self.text_next_radio = QRadioButton("下一等级")
        self.text_next_avail_radio = QRadioButton("下一个有效奖励")
        text_mode = self.config.get("reward_text_display_mode", "current")
        if text_mode == "next":
            self.text_next_radio.setChecked(True)
        elif text_mode == "next_available":
            self.text_next_avail_radio.setChecked(True)
        else:
            self.text_current_radio.setChecked(True)

        text_radio_container = QWidget()
        text_radio_layout = QHBoxLayout(text_radio_container);
        text_radio_layout.setContentsMargins(0, 0, 0, 0)
        text_radio_layout.addWidget(self.text_current_radio);
        text_radio_layout.addWidget(self.text_next_radio)
        text_radio_layout.addWidget(self.text_next_avail_radio);
        text_radio_layout.addStretch()
        form_layout.addRow("奖励文字显示:", text_radio_container)

        self.auto_expand_radio = QRadioButton("自动")
        self.manual_expand_radio = QRadioButton("手动")
        if self.config.get("auto_expand_reward_panel", True):
            self.auto_expand_radio.setChecked(True)
        else:
            self.manual_expand_radio.setChecked(True)

        expand_radio_container = QWidget()
        expand_radio_layout = QHBoxLayout(expand_radio_container);
        expand_radio_layout.setContentsMargins(0, 0, 0, 0)
        expand_radio_layout.addWidget(self.auto_expand_radio)
        expand_radio_layout.addWidget(self.manual_expand_radio)
        expand_radio_layout.addStretch()
        form_layout.addRow("奖励图片展开方式:", expand_radio_container)

        self.progress_percent_radio = QRadioButton("百分比")
        self.progress_exp_radio = QRadioButton("经验值")
        progress_mode = self.config.get("progress_bar_mode", "percentage")
        if progress_mode == "experience":
            self.progress_exp_radio.setChecked(True)
        else:
            self.progress_percent_radio.setChecked(True)

        progress_radio_container = QWidget()
        progress_radio_layout = QHBoxLayout(progress_radio_container)
        progress_radio_layout.setContentsMargins(0, 0, 0, 0)
        progress_radio_layout.addWidget(self.progress_percent_radio)
        progress_radio_layout.addWidget(self.progress_exp_radio)
        progress_radio_layout.addStretch()
        form_layout.addRow("进度条显示:", progress_radio_container)

        self.trend_show_radio = QRadioButton("显示")
        self.trend_hide_radio = QRadioButton("隐藏")
        if self.config.get("show_trend_column", False):
            self.trend_show_radio.setChecked(True)
        else:
            self.trend_hide_radio.setChecked(True)

        trend_radio_container = QWidget()
        trend_radio_layout = QHBoxLayout(trend_radio_container)
        trend_radio_layout.setContentsMargins(0, 0, 0, 0)
        trend_radio_layout.addWidget(self.trend_show_radio)
        trend_radio_layout.addWidget(self.trend_hide_radio)
        trend_radio_layout.addStretch()
        form_layout.addRow("财富趋势显示:", trend_radio_container)

        # 新增：目标倒计时显示设置
        self.countdown_show_radio = QRadioButton("显示")
        self.countdown_hide_radio = QRadioButton("隐藏")
        if self.config.get("show_countdown", True):
            self.countdown_show_radio.setChecked(True)
        else:
            self.countdown_hide_radio.setChecked(True)

        countdown_radio_container = QWidget()
        countdown_radio_layout = QHBoxLayout(countdown_radio_container)
        countdown_radio_layout.setContentsMargins(0, 0, 0, 0)
        countdown_radio_layout.addWidget(self.countdown_show_radio)
        countdown_radio_layout.addWidget(self.countdown_hide_radio)
        countdown_radio_layout.addStretch()
        form_layout.addRow("目标倒计时显示:", countdown_radio_container)

        # 新增：财富规则标签页显示设置
        self.rules_tab_show_radio = QRadioButton("显示")
        self.rules_tab_hide_radio = QRadioButton("隐藏")
        if self.config.get("show_wealth_rules_tab", True):
            self.rules_tab_show_radio.setChecked(True)
        else:
            self.rules_tab_hide_radio.setChecked(True)

        rules_tab_radio_container = QWidget()
        rules_tab_radio_layout = QHBoxLayout(rules_tab_radio_container)
        rules_tab_radio_layout.setContentsMargins(0, 0, 0, 0)
        rules_tab_radio_layout.addWidget(self.rules_tab_show_radio)
        rules_tab_radio_layout.addWidget(self.rules_tab_hide_radio)
        rules_tab_radio_layout.addStretch()
        form_layout.addRow("积分规则标签页:", rules_tab_radio_container)

        # 修改：术语显示设置
        self.term_wealth_radio = QRadioButton("财富")
        self.term_score_radio = QRadioButton("分数")
        self.term_custom_radio = QRadioButton("自定义:")
        self.term_custom_edit = QLineEdit()

        term_radio_container = QWidget()
        term_radio_layout = QHBoxLayout(term_radio_container)
        term_radio_layout.setContentsMargins(0, 0, 0, 0)
        term_radio_layout.addWidget(self.term_wealth_radio)
        term_radio_layout.addWidget(self.term_score_radio)
        term_radio_layout.addWidget(self.term_custom_radio)
        term_radio_layout.addWidget(self.term_custom_edit)
        term_radio_layout.addStretch()
        form_layout.addRow("术语显示:", term_radio_container)

        # 设置术语控件的初始状态
        term_mode = self.config.get("term_display_mode", "财富")
        if term_mode == "分数":
            self.term_score_radio.setChecked(True)
            self.term_custom_edit.setText("积分")
        elif term_mode == "财富":
            self.term_wealth_radio.setChecked(True)
            self.term_custom_edit.setText("积分")
        else:
            self.term_custom_radio.setChecked(True)
            self.term_custom_edit.setText(term_mode)

        # 连接信号以控制自定义输入框的可用状态
        self.term_custom_edit.setEnabled(self.term_custom_radio.isChecked())
        self.term_custom_radio.toggled.connect(self.term_custom_edit.setEnabled)

        button_box = QHBoxLayout()
        restore_button = QPushButton("恢复默认设置")
        ok_button = QPushButton("确定")
        cancel_button = QPushButton("取消")
        button_box.addWidget(restore_button);
        button_box.addStretch()
        button_box.addWidget(ok_button);
        button_box.addWidget(cancel_button)

        main_layout.addLayout(form_layout)
        main_layout.addLayout(button_box)

        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        restore_button.clicked.connect(self.restore_defaults)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择等级图片所在的文件夹", self.folder_path_edit.text())
        if folder:
            self.folder_path_edit.setText(folder)

    def restore_defaults(self):
        default_styles = {
            "levelName": {"family": "Microsoft YaHei", "size": 28, "color": "#4682B4"},
            "wealthValue": {"family": "Microsoft YaHei", "size": 20, "color": "#FFA500"},
            "rewardTitle": {"family": "Microsoft YaHei", "size": 18, "color": "#CD5C5C"},
            "rewardText": {"family": "Microsoft YaHei", "size": 16, "color": "#444444"},
            "planTitle": {"family": "Microsoft YaHei", "size": 14, "color": "#333333"},
            "planContent": {"family": "Microsoft YaHei", "size": 14, "color": "#333333"},
            "planRewardText": {"family": "Microsoft YaHei", "size": 14, "color": "#E59866"}
        }
        for key, (font_combo, font_size_spin, color_swatch) in self.widgets.items():
            defaults = default_styles[key]
            font_combo.setCurrentFont(QFont(defaults["family"]))
            font_size_spin.setValue(defaults["size"])
            color_swatch.setStyleSheet(f"background-color: {defaults['color']}; border: 1px solid grey;")

        self.reward_bg_swatch.setStyleSheet("background-color: #FFFACD; border: 1px solid grey;")
        self.folder_path_edit.setText("level")
        self.auto_expand_radio.setChecked(True)
        self.img_current_radio.setChecked(True)
        self.text_current_radio.setChecked(True)
        self.progress_percent_radio.setChecked(True)
        self.trend_hide_radio.setChecked(True)
        self.countdown_show_radio.setChecked(True)
        self.rules_tab_show_radio.setChecked(True)
        self.term_wealth_radio.setChecked(True)
        self.term_custom_edit.setText("积分")

    def choose_color(self, swatch_label):
        current_color_hex = swatch_label.styleSheet().split(":")[1].split(";")[0].strip()
        current_color = QColor(current_color_hex)
        color = QColorDialog.getColor(current_color, self, "选择颜色")
        if color.isValid(): swatch_label.setStyleSheet(f"background-color: {color.name()}; border: 1px solid grey;")

    def get_settings(self):
        new_config = {}
        for key, (font_combo, font_size_spin, color_swatch) in self.widgets.items():
            color_hex = color_swatch.styleSheet().split(":")[1].split(";")[0].strip()
            color = QColor(color_hex).name()
            new_config[key] = {"family": font_combo.currentFont().family(), "size": font_size_spin.value(),
                               "color": color}

        bg_color_hex = self.reward_bg_swatch.styleSheet().split(":")[1].split(";")[0].strip()
        new_config["rewardCardBackground"] = QColor(bg_color_hex).name()

        new_config["level_image_folder"] = self.folder_path_edit.text()

        if self.img_next_radio.isChecked():
            new_config["reward_image_display_mode"] = "next"
        elif self.img_next_avail_radio.isChecked():
            new_config["reward_image_display_mode"] = "next_available"
        else:
            new_config["reward_image_display_mode"] = "current"

        if self.text_next_radio.isChecked():
            new_config["reward_text_display_mode"] = "next"
        elif self.text_next_avail_radio.isChecked():
            new_config["reward_text_display_mode"] = "next_available"
        else:
            new_config["reward_text_display_mode"] = "current"

        new_config["auto_expand_reward_panel"] = self.auto_expand_radio.isChecked()

        if self.progress_exp_radio.isChecked():
            new_config["progress_bar_mode"] = "experience"
        else:
            new_config["progress_bar_mode"] = "percentage"

        new_config["show_trend_column"] = self.trend_show_radio.isChecked()
        new_config["show_countdown"] = self.countdown_show_radio.isChecked()
        new_config["show_wealth_rules_tab"] = self.rules_tab_show_radio.isChecked()

        if self.term_score_radio.isChecked():
            new_config["term_display_mode"] = "分数"
        elif self.term_custom_radio.isChecked():
            custom_text = self.term_custom_edit.text().strip()
            new_config["term_display_mode"] = custom_text if custom_text else "积分"
        else:
            new_config["term_display_mode"] = "财富"

        return new_config