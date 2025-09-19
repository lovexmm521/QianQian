import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDialog,
                             QMessageBox, QProgressBar, QFrame, QComboBox, QPushButton, QDateEdit, QScrollArea)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, pyqtSignal, QDate


class ClickableLabel(QLabel):
    doubleClicked = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit()
        super().mouseDoubleClickEvent(event)


class SetCountdownDialog(QDialog):
    def __init__(self, current_date_str=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置目标倒计时")
        self.selected_date = None
        self.action = None

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("请选择一个未来的目标日期:"))

        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setMinimumDate(QDate.currentDate().addDays(1))
        if current_date_str:
            current_date = QDate.fromString(current_date_str, "yyyy-MM-dd")
            if current_date.isValid() and current_date > QDate.currentDate():
                self.date_edit.setDate(current_date)

        layout.addWidget(self.date_edit)

        button_box = QHBoxLayout()
        ok_button = QPushButton("确定")
        show_button = QPushButton("显示倒计时")
        clear_button = QPushButton("清除倒计时")
        cancel_button = QPushButton("取消")
        button_box.addStretch()
        button_box.addWidget(ok_button)
        button_box.addWidget(show_button)
        button_box.addWidget(clear_button)
        button_box.addWidget(cancel_button)
        layout.addLayout(button_box)

        ok_button.clicked.connect(self.accept_date)
        show_button.clicked.connect(self.show_and_accept)
        clear_button.clicked.connect(self.clear_date)
        cancel_button.clicked.connect(self.reject)

    def accept_date(self):
        self.selected_date = self.date_edit.date()
        self.action = "accept"
        self.accept()

    def show_and_accept(self):
        self.selected_date = self.date_edit.date()
        self.action = "show"
        self.accept()

    def clear_date(self):
        self.selected_date = None
        self.action = "clear"
        self.accept()

    def get_result(self):
        return self.selected_date, self.action


class SelectLevelDialog(QDialog):
    def __init__(self, level_config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择对比等级")
        self.selected_level = None

        layout = QVBoxLayout(self)
        self.level_combo = QComboBox()
        for level in level_config:
            self.level_combo.addItem(
                f"{level.get('level_name', f'等级 {level.get('level')}')} (需财富: {level.get('wealth_threshold', 0):,})",
                userData=level)

        layout.addWidget(QLabel("请选择一个等级进行对比:"))
        layout.addWidget(self.level_combo)

        button_box = QHBoxLayout()
        ok_button = QPushButton("确定")
        cancel_button = QPushButton("取消")
        button_box.addStretch()
        button_box.addWidget(ok_button)
        button_box.addWidget(cancel_button)
        layout.addLayout(button_box)

        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

    def accept(self):
        self.selected_level = self.level_combo.currentData()
        super().accept()


class MainTab(QWidget):
    comparison_changed = pyqtSignal()
    countdown_date_changed = pyqtSignal(object)
    countdown_visibility_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.comparison_level_data = None
        self.level_config = []
        self.current_wealth = 0
        self.style_config = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.main_card = QFrame(self);
        self.main_card.setObjectName("mainCard")

        main_card_layout = QVBoxLayout(self.main_card)
        top_layout = QHBoxLayout()
        self.level_icon_label = ClickableLabel();
        self.level_icon_label.setObjectName("levelIcon");
        self.level_icon_label.setFixedSize(120, 120);
        self.level_icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.level_icon_label.doubleClicked.connect(self.open_level_select_dialog)

        right_details_layout = QVBoxLayout()
        self.level_name_label = QLabel("---");
        self.level_name_label.setObjectName("levelNameLabel")
        self.wealth_value_label = QLabel("财富: ---");
        self.wealth_value_label.setObjectName("wealthValueLabel")
        self.progress_bar = QProgressBar()

        self.progress_label = ClickableLabel("---");
        self.progress_label.setObjectName("progressLabel");
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.doubleClicked.connect(self.open_countdown_dialog)

        self.countdown_label = ClickableLabel("")
        self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.countdown_label.setStyleSheet("color: #006400; font-weight: bold;")
        self.countdown_label.setVisible(False)
        self.countdown_label.doubleClicked.connect(self.hide_countdown)

        right_details_layout.addWidget(self.level_name_label);
        right_details_layout.addWidget(self.wealth_value_label);
        right_details_layout.addWidget(self.progress_bar);
        right_details_layout.addWidget(self.progress_label)
        right_details_layout.addWidget(self.countdown_label)

        top_layout.addWidget(self.level_icon_label);
        top_layout.addSpacing(20);
        top_layout.addLayout(right_details_layout)

        main_card_layout.addLayout(top_layout)
        layout.addWidget(self.main_card)

        self.comparison_card = QFrame(self);
        self.comparison_card.setObjectName("comparisonCard")
        comparison_layout = QHBoxLayout(self.comparison_card)
        self.comp_icon_label = ClickableLabel();
        self.comp_icon_label.setFixedSize(80, 80)
        self.comp_icon_label.doubleClicked.connect(self.hide_comparison_panel)
        self.comp_icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        comp_details_layout = QVBoxLayout()
        self.comp_name_label = QLabel("对比等级: ---");
        self.comp_name_label.setObjectName("compNameLabel")
        self.comp_progress_bar = QProgressBar()
        self.comp_progress_label = QLabel("---");
        self.comp_progress_label.setObjectName("compProgressLabel");
        self.comp_progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        comp_details_layout.addWidget(self.comp_name_label);
        comp_details_layout.addWidget(self.comp_progress_bar);
        comp_details_layout.addWidget(self.comp_progress_label)
        comparison_layout.addWidget(self.comp_icon_label);
        comparison_layout.addSpacing(15);
        comparison_layout.addLayout(comp_details_layout)
        self.comparison_card.setVisible(False)
        layout.addWidget(self.comparison_card)

        self.reward_card = QFrame();
        self.reward_card.setObjectName("rewardCard")
        reward_layout = QVBoxLayout(self.reward_card);
        reward_layout.setContentsMargins(20, 15, 20, 15)
        self.reward_title_label = QLabel();
        self.reward_title_label.setObjectName("rewardTitleLabel")
        self.reward_text_label = QLabel();
        self.reward_text_label.setObjectName("rewardTextLabel");
        self.reward_text_label.setWordWrap(True)
        reward_layout.addWidget(self.reward_title_label);
        reward_layout.addWidget(self.reward_text_label)
        self.reward_card.setVisible(False)
        layout.addWidget(self.reward_card)

        # 新增：计划展示区域
        plans_container = QWidget()
        plans_layout = QHBoxLayout(plans_container)
        plans_layout.setContentsMargins(0, 0, 0, 0)

        self.daily_plan_card = self.create_plan_card("📅 当天计划")
        self.current_plan_card = self.create_plan_card("🎯 当前计划")

        plans_layout.addWidget(self.daily_plan_card)
        plans_layout.addWidget(self.current_plan_card)
        layout.addWidget(plans_container)

        layout.addStretch()

    def create_plan_card(self, title):
        card = QFrame()
        card.setObjectName("planCard")
        card.setMinimumHeight(211)
        layout = QVBoxLayout(card)
        title_label = QLabel(f"<b>{title}</b>")
        card.title_label = title_label

        content_label = QLabel("暂无计划")
        content_label.setWordWrap(True)
        content_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        content_label.setStyleSheet("background-color: transparent;")

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(content_label)
        scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll_area.viewport().setStyleSheet("background: transparent;")

        layout.addWidget(title_label)
        layout.addWidget(scroll_area)
        card.setVisible(False)
        # 将内容标签附加到卡片对象以便以后引用
        card.content_label = content_label
        return card

    def open_countdown_dialog(self):
        target_date_str = self.style_config.get("countdown_target_date")
        dialog = SetCountdownDialog(target_date_str, self)
        if dialog.exec():
            new_date, action = dialog.get_result()
            if action == "clear":
                self.countdown_date_changed.emit(None)
            elif action == "accept":
                if new_date:
                    self.countdown_date_changed.emit(new_date.toString("yyyy-MM-dd"))
            elif action == "show":
                if new_date:
                    self.countdown_date_changed.emit(new_date.toString("yyyy-MM-dd"))
                self.countdown_visibility_changed.emit(True)

    def hide_countdown(self):
        # 隐藏倒计时并通知主窗口保存状态
        self.countdown_visibility_changed.emit(False)

    def hide_comparison_panel(self):
        self.comparison_level_data = None
        self.update_comparison_display()
        self.comparison_changed.emit()

    def open_level_select_dialog(self):
        if not self.level_config:
            QMessageBox.information(self, "提示", "请先在“等级设置”中定义等级。")
            return
        dialog = SelectLevelDialog(self.level_config, self)
        if dialog.exec():
            self.comparison_level_data = dialog.selected_level
            self.update_comparison_display()
            self.comparison_changed.emit()

    def update_comparison_display(self):
        if not self.comparison_level_data:
            self.comparison_card.setVisible(False)
            return

        level_image_folder = self.style_config.get("level_image_folder", "level")
        target_level = self.comparison_level_data
        target_name = target_level.get("level_name")
        target_wealth = target_level.get("wealth_threshold", 0)
        target_num = target_level.get("level", 0)

        self.comp_name_label.setText(f"对比目标: {target_name}")

        icon_path_jpg = os.path.join(level_image_folder, f"{target_num}.jpg")
        icon_path_png = os.path.join(level_image_folder, f"{target_num}.png")
        icon_path = icon_path_jpg if os.path.exists(icon_path_jpg) else (
            icon_path_png if os.path.exists(icon_path_png) else None)
        if icon_path:
            self.comp_icon_label.setPixmap(
                QPixmap(icon_path).scaled(self.comp_icon_label.size(), Qt.AspectRatioMode.KeepAspectRatio,
                                          Qt.TransformationMode.SmoothTransformation))
        else:
            self.comp_icon_label.setText("无图")

        progress_mode = self.style_config.get("progress_bar_mode", "percentage")
        self.comp_progress_bar.setFormat(f"%p%")

        if target_wealth > 0:
            percentage = min(100, int((self.current_wealth / target_wealth) * 100))
            self.comp_progress_bar.setValue(percentage)
            if progress_mode == "experience":
                self.comp_progress_bar.setFormat(f"{self.current_wealth:,} / {target_wealth:,}")
        else:
            self.comp_progress_bar.setValue(100)
            if progress_mode == "experience":
                self.comp_progress_bar.setFormat("已达成")

        needed = target_wealth - self.current_wealth
        if needed > 0:
            self.comp_progress_label.setText(f"距离目标还需 {needed:,} 财富值")
        else:
            self.comp_progress_label.setText("已达成此目标！")

        self.comparison_card.setVisible(True)

    def update_display(self, total_wealth, current_level_data, next_level_data, sorted_config, current_level_index,
                       style_config, comparison_level_data=None):
        self.level_config = sorted_config
        self.current_wealth = total_wealth
        self.style_config = style_config
        self.comparison_level_data = comparison_level_data

        self.update_comparison_display()

        level_image_folder = self.style_config.get("level_image_folder", "level")
        progress_mode = self.style_config.get("progress_bar_mode", "percentage")
        self.progress_bar.setFormat(f"%p%")

        self.wealth_value_label.setText(f"财富: {total_wealth:,}")
        if current_level_data:
            self.level_name_label.setText(current_level_data.get("level_name", f"等级 {current_level_data['level']}"))
            level_num = current_level_data['level']

            icon_path_jpg = os.path.join(level_image_folder, f"{level_num}.jpg");
            icon_path_png = os.path.join(level_image_folder, f"{level_num}.png")
            icon_path = icon_path_jpg if os.path.exists(icon_path_jpg) else (
                icon_path_png if os.path.exists(icon_path_png) else None)

            if icon_path:
                self.level_icon_label.setPixmap(
                    QPixmap(icon_path).scaled(self.level_icon_label.size(), Qt.AspectRatioMode.KeepAspectRatio,
                                              Qt.TransformationMode.SmoothTransformation))
            else:
                self.level_icon_label.setText("无图")
            if next_level_data:
                prev_threshold = sorted_config[current_level_index]['wealth_threshold']
                next_threshold = next_level_data['wealth_threshold']
                range_total = next_threshold - prev_threshold
                progress_in_range = total_wealth - prev_threshold
                percentage = int((progress_in_range / range_total) * 100) if range_total > 0 else 100
                self.progress_bar.setValue(percentage)
                if progress_mode == "experience":
                    self.progress_bar.setFormat(f"{progress_in_range:,} / {range_total:,}")

                needed = next_threshold - total_wealth
                self.progress_label.setText(f"距离下一级 [{next_level_data.get('level_name')}] 还需 {needed:,} 财富值")
            else:
                self.progress_bar.setValue(100)
                if progress_mode == "experience":
                    self.progress_bar.setFormat("已满级")
                self.progress_label.setText("恭喜！您已达到最高等级！")
        else:
            self.level_name_label.setText("未定级");

            icon_path_jpg = os.path.join(level_image_folder, "0.jpg")
            icon_path_png = os.path.join(level_image_folder, "0.png")
            icon_path = icon_path_jpg if os.path.exists(icon_path_jpg) else (
                icon_path_png if os.path.exists(icon_path_png) else None)

            if icon_path:
                self.level_icon_label.setPixmap(
                    QPixmap(icon_path).scaled(self.level_icon_label.size(), Qt.AspectRatioMode.KeepAspectRatio,
                                              Qt.TransformationMode.SmoothTransformation))
            else:
                self.level_icon_label.setText("?")

            if sorted_config:
                first_level_wealth = sorted_config[0]['wealth_threshold']
                self.progress_bar.setValue(
                    int((total_wealth / first_level_wealth) * 100) if first_level_wealth > 0 else 0)
                if progress_mode == "experience":
                    self.progress_bar.setFormat(f"{total_wealth:,} / {first_level_wealth:,}")
                self.progress_label.setText(f"为达到第一个等级努力吧！还需 {first_level_wealth - total_wealth:,} 财富值")
            else:
                self.progress_bar.setValue(0)
                self.progress_label.setText("请先设置等级")

        # --- 奖励文字显示逻辑 ---
        level_for_text = None
        title = ""

        if comparison_level_data:
            level_for_text = comparison_level_data
            title = f"对比奖励 ({level_for_text.get('level_name')})"
        else:
            text_mode = self.style_config.get("reward_text_display_mode", "current")
            if text_mode == "current":
                level_for_text = current_level_data
                if level_for_text: title = "🎉 恭喜！您已获得奖励！"
            elif text_mode == "next":
                level_for_text = next_level_data
                if level_for_text: title = f"下一个等级奖励 ({level_for_text.get('level_name')})"
            elif text_mode == "next_available":
                for i in range(current_level_index + 1, len(sorted_config)):
                    if sorted_config[i].get("reward_text"):
                        level_for_text = sorted_config[i]
                        title = f"下一个奖励 ({level_for_text.get('level_name')})"
                        break

        if level_for_text and level_for_text.get("reward_text"):
            self.reward_title_label.setText(title)
            self.reward_text_label.setText(level_for_text.get("reward_text"))
            self.reward_card.setVisible(True)
        else:
            self.reward_card.setVisible(False)

        # --- 倒计时显示逻辑 ---
        target_date_str = self.style_config.get("countdown_target_date")
        show_countdown = self.style_config.get("show_countdown", True)

        if show_countdown and next_level_data and target_date_str:
            target_date = QDate.fromString(target_date_str, "yyyy-MM-dd")
            if target_date.isValid():
                today = QDate.currentDate()
                if target_date > today:
                    days_left = today.daysTo(target_date)
                    self.countdown_label.setText(f"离完成目标还剩 {days_left} 天")
                    self.countdown_label.setVisible(True)
                else:
                    self.countdown_label.setText("目标日期已到或已过！")
                    self.countdown_label.setVisible(True)
            else:
                self.countdown_label.setVisible(False)
        else:
            self.countdown_label.setVisible(False)

    def update_rewards_display(self, rewards_data):
        daily_data = rewards_data.get("daily", [])
        current_data = rewards_data.get("current", [])

        daily_html = self.format_plan_to_html(daily_data, self.style_config)
        current_html = self.format_plan_to_html(current_data, self.style_config)

        if daily_html:
            self.daily_plan_card.content_label.setText(daily_html)
            self.daily_plan_card.setVisible(True)
        else:
            self.daily_plan_card.content_label.setText("暂无计划")
            self.daily_plan_card.setVisible(False)

        if current_html:
            self.current_plan_card.content_label.setText(current_html)
            self.current_plan_card.setVisible(True)
        else:
            self.current_plan_card.content_label.setText("暂无计划")
            self.current_plan_card.setVisible(False)

    def format_plan_to_html(self, data, style_config):
        if not data:
            return ""

        plan_style = style_config.get("planContent", {"family": "Microsoft YaHei", "size": 14, "color": "#333333"})
        plan_reward_style = style_config.get("planRewardText",
                                             {"family": "Microsoft YaHei", "size": 14, "color": "#E59866"})

        def build_list(items):
            if not items:
                return ""
            html = "<ul>"
            for item in items:
                reward_part = f" -> <span class='reward'>{item.get('reward')}</span>" if item.get(
                    'reward') else ""
                html += f"<li>{item.get('plan', '')}{reward_part}"
                html += build_list(item.get("children", []))
                html += "</li>"
            html += "</ul>"
            return html

        style = f"""
        <style>
            ul {{ 
                margin: 0; 
                padding-left: 1px; 
                list-style-type: disc; 
                font-family: "{plan_style['family']}";
                font-size: {plan_style['size']}px;
                color: {plan_style['color']};
            }}
            li {{ 
                margin-bottom: 3px; 
            }}
            span.reward {{
                font-family: "{plan_reward_style['family']}";
                font-size: {plan_reward_style['size']}px;
                color: {plan_reward_style['color']};
            }}
        </style>
        """
        return style + build_list(data)
