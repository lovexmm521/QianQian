# main_window.py
# ----------------------------------------------------------------
# 这是程序的主窗口，所有界面元素都在这里组装。
# 新增功能：启动时加载上次输入的身高体重。
# ----------------------------------------------------------------
import sys
import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel,
                             QDoubleSpinBox, QPushButton, QGroupBox, QMessageBox, QFrame, QGridLayout)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, pyqtSignal
from config import Config
from bmi_calculator import calculate_bmi, get_bmi_info
from data_handler import DataHandler
from visualization import VisualizationTab
from history import HistoryTab


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class ClickableGroupBox(QGroupBox):
    doubleClicked = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit()
        super().mouseDoubleClickEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.unit = 'kg'
        self.data_handler = DataHandler()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("千千小秤日记")
        self.setGeometry(200, 200, 600, 700)
        self.setStyleSheet(Config.STYLESHEET)

        icon_path = resource_path('1.ico')
        self.setWindowIcon(QIcon(icon_path))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.calculator_tab = self.create_calculator_tab()
        self.history_tab = HistoryTab(self.data_handler)
        self.visualization_tab = VisualizationTab(self.data_handler)

        self.tabs.addTab(self.calculator_tab, "测量记录")
        self.tabs.addTab(self.history_tab, "历史数据")
        self.tabs.addTab(self.visualization_tab, "可视化图表")

        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.on_tab_changed(0)

        # --- 新增：加载并设置上次的输入值 ---
        self.load_and_set_last_input()

    def create_calculator_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        input_group = QGroupBox("输入您的身体数据")
        input_layout = QVBoxLayout(input_group)

        height_layout = QHBoxLayout()
        height_layout.addWidget(QLabel("身高:"))
        self.height_input = QDoubleSpinBox()
        self.height_input.setRange(100.0, 250.0)
        self.height_input.setValue(170.0)  # 默认值
        self.height_input.setSuffix(" cm")
        height_layout.addWidget(self.height_input)
        input_layout.addLayout(height_layout)

        weight_layout = QHBoxLayout()
        weight_layout.addWidget(QLabel("体重:"))
        self.weight_input = QDoubleSpinBox()
        self.weight_input.setRange(20.0, 300.0)
        self.weight_input.setValue(70.0)  # 默认值
        self.weight_input.setSuffix(" kg")
        weight_layout.addWidget(self.weight_input)
        input_layout.addLayout(weight_layout)

        layout.addWidget(input_group)

        self.calculate_button = QPushButton("计算并保存记录")
        self.calculate_button.clicked.connect(self.calculate_and_save)
        layout.addWidget(self.calculate_button)

        result_group = ClickableGroupBox("测量结果")
        result_group.doubleClicked.connect(self.toggle_unit)
        result_layout = QVBoxLayout(result_group)
        result_layout.setSpacing(10)
        result_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.bmi_value_label = QLabel("BMI: -")
        self.bmi_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bmi_value_label.setStyleSheet("font-size: 18px; font-weight: bold;")

        initial_text = ("<span style='color:#2E8B57;'>请</span>"
                        "<span style='color:#2E8B57;'>先</span>"
                        "<span style='color:#FFA500;'>测</span>"
                        "<span style='color:#FF6347;'>量</span>")
        self.bmi_category_label = QLabel(initial_text)
        self.bmi_category_label.setObjectName("BMICategoryLabel")
        self.bmi_category_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.bmi_suggestion_label = QLabel("点击上方按钮开始")
        self.bmi_suggestion_label.setObjectName("BMISuggestionLabel")
        self.bmi_suggestion_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bmi_suggestion_label.setWordWrap(True)
        self.bmi_suggestion_label.setMinimumHeight(60)

        result_layout.addWidget(self.bmi_value_label)
        result_layout.addWidget(self.bmi_category_label)
        result_layout.addWidget(self.bmi_suggestion_label)

        layout.addWidget(result_group)

        legend_group = QGroupBox("BMI 标准参考")
        legend_layout = QVBoxLayout(legend_group)
        legend_layout.setSpacing(8)
        legend_layout.setContentsMargins(15, 25, 15, 10)

        grid_layout = QGridLayout()
        grid_layout.setHorizontalSpacing(20)
        grid_layout.setVerticalSpacing(10)

        colors = {
            "underweight": Config.BMI_COLORS["underweight"]["border"],
            "normal": Config.BMI_COLORS["normal"]["border"],
            "overweight": Config.BMI_COLORS["overweight"]["border"],
            "obese": Config.BMI_COLORS["obese"]["border"]
        }

        standards = Config.BMI_STANDARDS_CHINA

        categories = [('underweight', '偏瘦'), ('normal', '正常'), ('overweight', '过重'), ('obese', '肥胖')]
        for i, (key, name) in enumerate(categories):
            label = QLabel(name)
            label.setStyleSheet(f"font-weight: bold; color: {colors[key]};")

            std = standards[key]
            if 'min' in std and 'max' in std:
                range_text = f"{std['min']} ~ {std['max']}"
            elif 'max' in std:
                range_text = f"<= {std['max']}"
            else:
                range_text = f">= {std['min']}"
            range_label = QLabel(range_text)

            grid_layout.addWidget(label, i, 0)
            grid_layout.addWidget(range_label, i, 1)

        legend_layout.addLayout(grid_layout)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        legend_layout.addWidget(line)

        note_label = QLabel("此BMI为中国标准")
        note_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        note_label.setStyleSheet("color: #666; font-size: 12px; padding-top: 5px;")
        legend_layout.addWidget(note_label)

        layout.addWidget(legend_group)
        layout.addStretch()

        return tab

    def load_and_set_last_input(self):
        """加载并设置上次的输入值"""
        last_input = self.data_handler.load_last_input()
        if last_input:
            if 'last_height' in last_input:
                self.height_input.setValue(last_input['last_height'])
            if 'last_weight_kg' in last_input:
                # 根据当前单位设置显示值
                display_weight = last_input['last_weight_kg']
                if self.unit == 'jin':
                    display_weight *= 2
                self.weight_input.setValue(display_weight)

    def toggle_unit(self):
        """切换单位并更新所有相关UI"""
        current_value = self.weight_input.value()
        if self.unit == 'kg':
            self.unit = 'jin'
            self.weight_input.setSuffix(" 斤")
            self.weight_input.setRange(40.0, 600.0)
            self.weight_input.setValue(current_value * 2)
        else:
            self.unit = 'kg'
            self.weight_input.setSuffix(" kg")
            self.weight_input.setRange(20.0, 300.0)
            self.weight_input.setValue(current_value / 2)

        self.history_tab.refresh_data(self.unit)
        self.visualization_tab.refresh_data(self.unit)

    def calculate_and_save(self):
        try:
            height_cm = self.height_input.value()
            weight_display = self.weight_input.value()

            weight_kg = weight_display / 2 if self.unit == 'jin' else weight_display

            if height_cm <= 0 or weight_kg <= 0:
                QMessageBox.warning(self, "输入错误", "身高和体重必须是正数！")
                return

            bmi = calculate_bmi(weight_kg, height_cm)
            bmi_info = get_bmi_info(bmi)

            category_key = bmi_info['key']
            status_color = Config.BMI_COLORS[category_key]["border"]

            self.bmi_value_label.setText(f"您的 BMI 指数是: {bmi}")
            self.bmi_category_label.setText(bmi_info["label"])
            self.bmi_category_label.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {status_color};")
            self.bmi_suggestion_label.setText(bmi_info["suggestion"])

            if self.data_handler.save_record(weight_kg, height_cm, bmi):
                # --- 新增：保存当前输入的身高和体重 ---
                self.data_handler.save_last_input(height_cm, weight_kg)
                print("记录已保存，用户配置已更新")
                self.history_tab.refresh_data(self.unit)
                self.visualization_tab.refresh_data(self.unit)
            else:
                QMessageBox.critical(self, "保存失败", "无法将记录写入文件！")

        except Exception as e:
            QMessageBox.critical(self, "发生错误", f"计算时出现问题: {e}")

    def on_tab_changed(self, index):
        if index == 1:
            self.history_tab.refresh_data(self.unit)
        elif index == 2:
            self.visualization_tab.refresh_data(self.unit)
