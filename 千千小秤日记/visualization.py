# visualization.py
# ----------------------------------------------------------------
# 可视化图表模块。
# 新增功能：支持显示不同重量单位（kg/斤）。
# ----------------------------------------------------------------
import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGroupBox
from PyQt6.QtCore import Qt, pyqtSignal
import time
from datetime import datetime
from bmi_calculator import get_bmi_info
from config import Config


class ChineseDateAxis(pg.DateAxisItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def tickStrings(self, values, scale, spacing):
        strings = super().tickStrings(values, scale, spacing)
        month_map = {
            'Jan': '1月', 'Feb': '2月', 'Mar': '3月', 'Apr': '4月',
            'May': '5月', 'Jun': '6月', 'Jul': '7月', 'Aug': '8月',
            'Sep': '9月', 'Oct': '10月', 'Nov': '11月', 'Dec': '12月'
        }
        new_strings = []
        for s in strings:
            for en, ch in month_map.items():
                s = s.replace(en, ch)
            new_strings.append(s)
        return new_strings


class InteractivePlotWidget(pg.PlotWidget):
    doubleClicked = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit()
        super().mouseDoubleClickEvent(event)


class VisualizationTab(QWidget):
    def __init__(self, data_handler):
        super().__init__()
        self.data_handler = data_handler
        self.show_colored_dots = False
        self.current_days_filter = None
        self.unit = 'kg'
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        button_layout = QHBoxLayout()
        self.btn_7_days = QPushButton("近7天")
        self.btn_30_days = QPushButton("近1个月")
        self.btn_3_months = QPushButton("近3个月")
        self.btn_all = QPushButton("全部")

        self.btn_7_days.clicked.connect(lambda: self.update_plot(7))
        self.btn_30_days.clicked.connect(lambda: self.update_plot(30))
        self.btn_3_months.clicked.connect(lambda: self.update_plot(90))
        self.btn_all.clicked.connect(lambda: self.update_plot(None))

        button_layout.addWidget(self.btn_7_days)
        button_layout.addWidget(self.btn_30_days)
        button_layout.addWidget(self.btn_3_months)
        button_layout.addWidget(self.btn_all)
        layout.addLayout(button_layout)

        date_axis = ChineseDateAxis(orientation='bottom')
        self.plot_widget = InteractivePlotWidget(axisItems={'bottom': date_axis})

        self.plot_widget.getPlotItem().getViewBox().setMenuEnabled(False)
        self.plot_widget.doubleClicked.connect(self.toggle_colored_dots)

        self.plot_widget.setBackground('#FFFFFF')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.getAxis('left').setTextPen('k')
        self.plot_widget.getAxis('bottom').setTextPen('k')
        self.plot_widget.setTitle("体重变化趋势", color="k", size="16pt")
        styles = {"color": "k", "font-size": "14px"}
        self.plot_widget.setLabel("left", "体重 (kg)", **styles)
        self.plot_widget.setLabel("bottom", "日期", **styles)

        layout.addWidget(self.plot_widget, 1)

        stats_group = QGroupBox("数据总览")
        stats_layout = QHBoxLayout(stats_group)
        stats_layout.setContentsMargins(10, 25, 10, 15)
        stats_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.start_label_widget = self.create_stats_label("开始值", "-")
        self.current_label_widget = self.create_stats_label("当前值", "-")
        self.change_label_widget = self.create_stats_label("变化值", "-")
        self.bmi_result_widget = self.create_stats_label("当前状态", "-")
        self.advice_widget = self.create_stats_label("健康建议", "-", font_size=16)
        self.advice_widget.value_label.setWordWrap(True)

        stats_layout.addWidget(self.start_label_widget)
        stats_layout.addWidget(self.current_label_widget)
        stats_layout.addWidget(self.change_label_widget)
        stats_layout.addWidget(self.bmi_result_widget)
        stats_layout.addWidget(self.advice_widget)

        layout.addWidget(stats_group)

    def create_stats_label(self, title, value, font_size=20):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 12px; color: #666;")
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setStyleSheet(f"font-size: {font_size}px; font-weight: bold; color: #87CEEB;")
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        widget.value_label = value_label
        return widget

    def toggle_colored_dots(self):
        self.show_colored_dots = not self.show_colored_dots
        self.update_plot(self.current_days_filter)

    def refresh_data(self, unit='kg'):
        self.unit = unit
        self.update_plot(self.current_days_filter)

    def update_plot(self, days=None):
        self.current_days_filter = days

        all_records = self.data_handler.get_all_records()
        if not all_records:
            self.plot_widget.clear()
            self.update_stats_info(None)
            return

        if days is not None:
            now = time.time()
            seconds_in_period = days * 24 * 3600
            filtered_records = [r for r in all_records if
                                now - time.mktime(time.strptime(r['date'], "%Y-%m-%d %H:%M:%S")) <= seconds_in_period]
        else:
            filtered_records = all_records

        multiplier = 2 if self.unit == 'jin' else 1
        unit_str = "斤" if self.unit == 'jin' else "kg"
        self.plot_widget.setLabel("left", f"体重 ({unit_str})")
        self.update_stats_info(filtered_records)
        self.plot_widget.clear()

        if not filtered_records:
            return

        plot_data = sorted(filtered_records, key=lambda x: x['date'])

        dates = [time.mktime(time.strptime(r['date'], "%Y-%m-%d %H:%M:%S")) for r in plot_data]
        weights = [r['weight'] * multiplier for r in plot_data]

        pen = pg.mkPen(color='#87CEEB', width=3)
        self.plot_widget.plot(dates, weights, pen=pen, symbol=None)

        spots = []
        for record in plot_data:
            date = time.mktime(time.strptime(record['date'], "%Y-%m-%d %H:%M:%S"))
            weight = record['weight'] * multiplier

            if self.show_colored_dots:
                bmi_info = get_bmi_info(record['bmi'])
                category_key = bmi_info['key']
                point_color = Config.BMI_COLORS[category_key]["border"]
            else:
                point_color = '#6495ED'

            spots.append({'pos': (date, weight), 'size': 10, 'brush': pg.mkBrush(point_color), 'pen': None})

        scatter = pg.ScatterPlotItem()
        scatter.setData(spots)
        self.plot_widget.addItem(scatter)

        self.plot_widget.autoRange()

    def update_stats_info(self, records_in_period):
        # ... (rest of the function needs to be updated for units)
        start_value_label = self.start_label_widget.value_label
        current_value_label = self.current_label_widget.value_label
        change_value_label = self.change_label_widget.value_label
        bmi_result_label = self.bmi_result_widget.value_label
        advice_label = self.advice_widget.value_label

        multiplier = 2 if self.unit == 'jin' else 1
        unit_str = "斤" if self.unit == 'jin' else "kg"

        if not records_in_period:
            start_value_label.setText("-")
            current_value_label.setText("-")
            change_value_label.setText("-")
            bmi_result_label.setText("-")
            advice_label.setText("-")
            default_style = "font-size: 20px; font-weight: bold; color: #87CEEB;"
            change_value_label.setStyleSheet(default_style)
            bmi_result_label.setStyleSheet(default_style)
            advice_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #87CEEB;")
            return

        latest_record = records_in_period[0]
        start_weight = records_in_period[-1]['weight'] * multiplier
        current_weight = latest_record['weight'] * multiplier
        change = current_weight - start_weight

        start_value_label.setText(f"{start_weight:.1f} {unit_str}")
        current_value_label.setText(f"{current_weight:.1f} {unit_str}")

        change_text = f"{change:+.1f} {unit_str}"
        arrow_text = ""
        arrow_color = "#87CEEB"
        if change > 0:
            arrow_text = "↑"
            arrow_color = "#FF6347"
        elif change < 0:
            arrow_text = "↓"
            arrow_color = "#32CD32"
        change_value_label.setText(
            f"{change_text} <span style='color:{arrow_color}; font-size: 20px;'>{arrow_text}</span>")

        bmi_info = get_bmi_info(latest_record['bmi'])
        bmi_result_label.setText(bmi_info['label'])
        category_key = bmi_info['key']

        status_color = Config.BMI_COLORS[category_key]["border"]

        height_m = latest_record['height'] / 100
        normal_range = Config.BMI_STANDARDS_CHINA['normal']
        target_low_kg = normal_range['min'] * (height_m ** 2)
        target_high_kg = normal_range['max'] * (height_m ** 2)

        advice_text = "非常棒, 请保持!"
        current_weight_kg = latest_record['weight']
        if current_weight_kg < target_low_kg:
            advice_text = f"需增重 {(target_low_kg - current_weight_kg) * multiplier:.1f} {unit_str}"
        elif current_weight_kg > target_high_kg:
            advice_text = f"需减重 {(current_weight_kg - target_high_kg) * multiplier:.1f} {unit_str}"

        advice_label.setText(advice_text)

        advice_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {status_color};")
        bmi_result_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {status_color};")
