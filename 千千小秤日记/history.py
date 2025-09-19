# history.py
# ----------------------------------------------------------------
# 历史记录标签页。
# 新增功能：支持显示不同重量单位（kg/斤）。
# ----------------------------------------------------------------
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QScrollArea, QLabel, QFrame, QHBoxLayout,
                             QPushButton, QMessageBox, QDialog, QFormLayout, QDoubleSpinBox,
                             QDialogButtonBox, QDateTimeEdit)
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QMouseEvent
from datetime import datetime
from config import Config
from bmi_calculator import get_bmi_category_key, calculate_bmi


class EditRecordDialog(QDialog):
    def __init__(self, record, unit, parent=None):
        super().__init__(parent)
        self.setWindowTitle("修改或删除记录")
        self.delete_requested = False
        self.unit = unit

        self.datetime_input = QDateTimeEdit(self)
        self.datetime_input.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        initial_datetime = QDateTime.fromString(record['date'], "yyyy-MM-dd HH:mm:ss")
        self.datetime_input.setDateTime(initial_datetime)

        self.weight_input = QDoubleSpinBox()
        display_weight = record['weight']
        if self.unit == 'jin':
            display_weight *= 2
            self.weight_input.setSuffix(" 斤")
            self.weight_input.setRange(40.0, 600.0)
        else:
            self.weight_input.setSuffix(" kg")
            self.weight_input.setRange(20.0, 300.0)
        self.weight_input.setValue(display_weight)

        self.height_input = QDoubleSpinBox()
        self.height_input.setRange(100.0, 250.0)
        self.height_input.setValue(record['height'])
        self.height_input.setSuffix(" cm")

        button_box = QDialogButtonBox(self)
        button_box.setStandardButtons(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.button(QDialogButtonBox.StandardButton.Ok).setText("确认")
        button_box.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        delete_button = button_box.addButton("删除此记录", QDialogButtonBox.ButtonRole.DestructiveRole)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        delete_button.clicked.connect(self._request_delete)

        layout = QFormLayout(self)
        layout.addRow("记录时间:", self.datetime_input)
        layout.addRow("新的体重:", self.weight_input)
        layout.addRow("新的身高:", self.height_input)
        layout.addWidget(button_box)

    def _request_delete(self):
        self.delete_requested = True
        self.accept()

    def get_data(self):
        weight_display = self.weight_input.value()
        weight_kg = weight_display / 2 if self.unit == 'jin' else weight_display
        return {
            "weight_kg": weight_kg,
            "height": self.height_input.value(),
            "date": self.datetime_input.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        }


class RecordRow(QFrame):
    def __init__(self, record, previous_record, data_handler, parent_tab, unit):
        super().__init__()
        self.record = record
        self.previous_record = previous_record
        self.data_handler = data_handler
        self.parent_tab = parent_tab
        self.unit = unit
        self.init_ui()

    def init_ui(self):
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFixedHeight(50)

        category_key = get_bmi_category_key(self.record['bmi'])
        colors = Config.BMI_COLORS.get(category_key, {"border": "#E0E0E0", "background": "#FFFFFF"})
        self.setStyleSheet(f"""
            RecordRow {{
                background-color: {colors['background']};
                border: 1px solid {colors['border']};
                border-radius: 6px;
            }}
            RecordRow:hover {{
                background-color: #E8F5E9;
            }}
        """)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 5, 10, 5)

        date_obj = datetime.strptime(self.record['date'], "%Y-%m-%d %H:%M:%S")
        date_label = QLabel(date_obj.strftime('%Y-%m-%d %H:%M'))
        date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        display_weight = self.record['weight']
        display_unit = 'kg'
        prev_display_weight = self.previous_record['weight'] if self.previous_record else None
        if self.unit == 'jin':
            display_weight *= 2
            display_unit = '斤'
            if prev_display_weight is not None:
                prev_display_weight *= 2
        weight_widget = self.create_value_with_arrow_widget(
            round(display_weight, 1), display_unit, prev_display_weight
        )

        bmi_widget = self.create_value_with_arrow_widget(
            self.record['bmi'], '', self.previous_record and self.previous_record['bmi']
        )

        height_label = QLabel(f"{self.record['height']} cm")
        height_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        category_label = QLabel(Config.BMI_STANDARDS_CHINA[category_key]['label'])
        category_label.setStyleSheet("font-weight: bold;")
        category_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        main_layout.addWidget(date_label, 3)
        main_layout.addWidget(weight_widget, 2)
        main_layout.addWidget(bmi_widget, 2)
        main_layout.addWidget(height_label, 2)
        main_layout.addWidget(category_label, 2)

    def create_value_with_arrow_widget(self, value, unit, previous_value):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        value_label = QLabel(f"<b>{value}</b> {unit}")
        arrow_label = QLabel()
        arrow_label.setFixedWidth(15)
        arrow_label.setStyleSheet("font-weight: bold; font-size: 16px;")

        if previous_value is not None:
            if value > previous_value:
                arrow_label.setText("<span style='color:red;'>↑</span>")
            elif value < previous_value:
                arrow_label.setText("<span style='color:green;'>↓</span>")
            else:
                arrow_label.setText("<span style='color:#888;'>-</span>")

        layout.addWidget(value_label)
        layout.addWidget(arrow_label)
        return widget

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        dialog = EditRecordDialog(self.record, self.unit, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if dialog.delete_requested:
                self._delete_record()
            else:
                original_date = self.record['date']
                new_data = dialog.get_data()
                new_bmi = calculate_bmi(new_data['weight_kg'], new_data['height'])

                updated_record_data = {
                    "date": new_data['date'],
                    "weight": new_data['weight_kg'],
                    "height": new_data['height'],
                    "bmi": new_bmi
                }
                self.data_handler.update_record(original_date, updated_record_data)
                self.parent_tab.refresh_data(self.unit)

    def _delete_record(self):
        reply = QMessageBox()
        reply.setWindowTitle('确认删除')
        reply.setText(f"您确定要删除 {self.record['date']} 的这条记录吗？")
        reply.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        reply.button(QMessageBox.StandardButton.Yes).setText('确认')
        reply.button(QMessageBox.StandardButton.No).setText('取消')
        reply.setIcon(QMessageBox.Icon.Question)
        reply.setDefaultButton(reply.button(QMessageBox.StandardButton.No))

        if reply.exec() == QMessageBox.StandardButton.Yes:
            self.data_handler.delete_record(self.record['date'])
            self.parent_tab.refresh_data(self.unit)


class HistoryTab(QWidget):
    def __init__(self, data_handler):
        super().__init__()
        self.data_handler = data_handler
        self.current_unit = 'kg'
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        header = self.create_header()
        main_layout.addWidget(header)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")

        scroll_content = QWidget()
        self.records_layout = QVBoxLayout(scroll_content)
        self.records_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.records_layout.setSpacing(8)
        self.records_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

    def create_header(self):
        header_widget = QWidget()
        layout = QHBoxLayout(header_widget)
        layout.setContentsMargins(10, 5, 10, 5)

        style = "font-weight: bold; color: #333;"
        headers = ["时间", "体重", "BMI", "身高", "结果"]
        proportions = [3, 2, 2, 2, 2]

        for text, prop in zip(headers, proportions):
            label = QLabel(text)
            label.setStyleSheet(style)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label, prop)

        return header_widget

    def refresh_data(self, unit='kg'):
        self.current_unit = unit
        while self.records_layout.count():
            child = self.records_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        records = self.data_handler.get_all_records()
        if not records:
            no_record_label = QLabel("暂无记录，快去测量第一次吧！")
            no_record_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_record_label.setStyleSheet("color: #999; margin-top: 50px;")
            self.records_layout.addWidget(no_record_label)
            return

        for i, record in enumerate(records):
            previous_record = records[i + 1] if i + 1 < len(records) else None
            record_row = RecordRow(record, previous_record, self.data_handler, self, self.current_unit)
            self.records_layout.addWidget(record_row)