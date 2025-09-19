import sys
import math
import random
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QAbstractItemView,
    QHeaderView, QColorDialog, QDialog, QTimeEdit,
    QDialogButtonBox, QLabel, QSplitter, QFontDialog, QFontComboBox, QSpinBox, QMessageBox
)
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QPolygonF, QIcon
)
from PyQt6.QtCore import (
    Qt, QTimer, QTime, QPointF, QRect, QRectF, QSettings, QTranslator, QLibraryInfo,
    pyqtSignal
)


# --- 核心修改：定义资源路径函数，以支持PyInstaller打包 ---
def resource_path(relative_path):
    """ 获取资源的绝对路径，适用于开发环境和PyInstaller环境 """
    try:
        # PyInstaller 创建一个临时文件夹，并将其路径存储在 _MEIPASS 中
        base_path = sys._MEIPASS
    except Exception:
        # 在开发环境中，使用脚本所在的目录
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# --- 新增：简化的字体选择对话框 ---
class SimpleFontDialog(QDialog):
    """一个只用于选择字体和大小的自定义对话框。"""

    def __init__(self, current_font, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择字体和大小")

        self.fontComboBox = QFontComboBox()
        self.fontComboBox.setCurrentFont(current_font)

        self.sizeSpinBox = QSpinBox()
        self.sizeSpinBox.setRange(6, 72)
        self.sizeSpinBox.setValue(current_font.pointSize())
        self.sizeSpinBox.setSuffix(" pt")

        layout = QVBoxLayout(self)
        form_layout = QHBoxLayout()
        form_layout.addWidget(QLabel("字体:"))
        form_layout.addWidget(self.fontComboBox)
        form_layout.addWidget(QLabel("大小:"))
        form_layout.addWidget(self.sizeSpinBox)
        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_font(self):
        """获取用户选择的字体。"""
        font = self.fontComboBox.currentFont()
        font.setPointSize(self.sizeSpinBox.value())
        return font


# --- 自定义时间段编辑对话框 (已升级) ---
class TimeEditDialog(QDialog):
    """一个用于编辑开始和结束时间的弹出对话框。"""

    def __init__(self, start_time, end_time, parent=None):
        super().__init__(parent)
        self.setWindowTitle("修改时间段")
        self.to_be_deleted = False  # 新增：删除标记

        self.startTimeEdit = QTimeEdit(start_time)
        self.endTimeEdit = QTimeEdit(end_time)
        self.startTimeEdit.setDisplayFormat("HH:mm")
        self.endTimeEdit.setDisplayFormat("HH:mm")

        layout = QVBoxLayout(self)
        form_layout = QHBoxLayout()
        form_layout.addWidget(QLabel("开始时间:"))
        form_layout.addWidget(self.startTimeEdit)
        form_layout.addWidget(QLabel("结束时间:"))
        form_layout.addWidget(self.endTimeEdit)
        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

        # 新增：添加删除按钮
        delete_button = buttons.addButton("删除此时间段", QDialogButtonBox.ButtonRole.DestructiveRole)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        delete_button.clicked.connect(self.mark_for_deletion)  # 连接信号
        layout.addWidget(buttons)

    def mark_for_deletion(self):
        """标记此项待删除并关闭对话框"""
        self.to_be_deleted = True
        self.accept()

    def get_times(self):
        return self.startTimeEdit.time(), self.endTimeEdit.time()


# --- 可视化时钟控件 (已升级) ---
class ClockWidget(QWidget):
    """
    显示一个12小时周期的模拟时钟，支持滚轮缩放和双击切换视图。
    """
    # 新增：双击信号
    doubleClicked = pyqtSignal()

    def __init__(self, time_period, parent=None):
        super().__init__(parent)
        if time_period not in ['AM', 'PM']:
            raise ValueError("time_period must be 'AM' or 'PM'")
        self.time_period = time_period
        self.schedule_data = []
        self.zoom_factor = 1.0
        self.text_font = QFont("Arial", 8)
        # 修改：缩小了时钟的最小尺寸
        self.setMinimumSize(200, 200)

        timer = QTimer(self)
        timer.timeout.connect(self.update)
        timer.start(1000)

    # 新增：处理双击事件
    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit()
        super().mouseDoubleClickEvent(event)

    def set_schedule_data(self, data):
        self.schedule_data = data
        self.update()

    def set_text_font(self, font):
        self.text_font = font
        self.update()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta > 0:
            self.zoom_factor *= 1.1
        else:
            self.zoom_factor *= 0.9

        self.zoom_factor = max(0.5, min(self.zoom_factor, 3.0))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        side = min(self.width(), self.height())
        painter.translate(self.width() / 2, self.height() / 2)
        scale = (side / 220.0) * self.zoom_factor
        painter.scale(scale, scale)

        self.draw_schedule_arcs(painter)
        self.draw_clock_face(painter)
        self.draw_hands(painter)
        painter.end()

    def draw_schedule_arcs(self, painter):
        painter.save()

        is_day_clock = self.time_period == 'AM'

        for item in self.schedule_data:
            start_time = item['start_time']
            end_time = item['end_time']

            item_start_min = start_time.hour() * 60 + start_time.minute()
            item_end_min = end_time.hour() * 60 + end_time.minute()

            # --- PART 1: Draw all relevant ARC segments on this clock ---
            item_segments = []
            if item_end_min <= item_start_min:  # Cross-midnight event
                item_segments.append({'start': item_start_min, 'end': 24 * 60})
                item_segments.append({'start': 0, 'end': item_end_min})
            else:  # Normal event
                item_segments.append({'start': item_start_min, 'end': item_end_min})

            for segment in item_segments:
                seg_start_min = segment['start']
                seg_end_min = segment['end']

                # Determine this clock's time range in minutes
                clock_ranges = []
                if is_day_clock:  # Day clock: 06:00 to 18:00
                    clock_ranges.append((6 * 60, 18 * 60))
                else:  # Night clock: 18:00 to 06:00
                    clock_ranges.append((18 * 60, 24 * 60))
                    clock_ranges.append((0, 6 * 60))

                for clock_start_min, clock_end_min in clock_ranges:
                    # Find intersection between event segment and clock range
                    draw_start_min = max(seg_start_min, clock_start_min)
                    draw_end_min = min(seg_end_min, clock_end_min)
                    duration = draw_end_min - draw_start_min

                    if duration > 0:
                        # Draw just the arc
                        radius = 90
                        current_color = item['color']
                        start_minutes_on_face = draw_start_min % 720
                        start_angle = 90 - (start_minutes_on_face * 0.5)
                        span_angle = -(duration * 0.5)
                        pen = QPen(current_color, 12, Qt.PenStyle.SolidLine)
                        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
                        painter.setPen(pen)
                        rect = QRectF(-radius, -radius, 2 * radius, 2 * radius)
                        painter.drawArc(rect, int(start_angle * 16), int(span_angle * 16))

            # --- PART 2: Calculate true midpoint and draw a SINGLE guideline if it's on this clock ---
            total_duration_min = 0
            if item_end_min <= item_start_min:  # Cross-midnight
                total_duration_min = (24 * 60 - item_start_min) + item_end_min
            else:
                total_duration_min = item_end_min - item_start_min

            if total_duration_min <= 10:
                continue

            midpoint_offset = total_duration_min / 2
            midpoint_min_abs = (item_start_min + midpoint_offset) % (24 * 60)

            # Check if this midpoint falls in the current clock's range
            should_draw_guideline = False
            if is_day_clock:  # Day clock range
                if 6 * 60 <= midpoint_min_abs < 18 * 60:
                    should_draw_guideline = True
            else:  # Night clock range
                if midpoint_min_abs >= 18 * 60 or midpoint_min_abs < 6 * 60:
                    should_draw_guideline = True

            if should_draw_guideline:
                # Draw the guideline
                try:
                    radius = 90
                    current_color = item['color']
                    mid_minutes_on_face = midpoint_min_abs % 720
                    mid_angle_deg = 90 - (mid_minutes_on_face * 0.5)
                    mid_angle_rad = math.radians(mid_angle_deg)

                    line_start = QPointF((radius + 6) * math.cos(mid_angle_rad),
                                         -(radius + 6) * math.sin(mid_angle_rad))
                    line_end = QPointF((radius + 15) * math.cos(mid_angle_rad),
                                       -(radius + 15) * math.sin(mid_angle_rad))

                    painter.setPen(QPen(current_color, 1))
                    painter.drawLine(line_start, line_end)

                    painter.setFont(self.text_font)
                    fm = painter.fontMetrics()
                    text_bounding_rect = fm.boundingRect(QRect(0, 0, 70, 100), Qt.TextFlag.TextWordWrap, item['task'])

                    is_right_side = math.cos(mid_angle_rad) >= 0
                    if is_right_side:
                        final_text_rect = QRectF(
                            line_end.x(),
                            line_end.y() - text_bounding_rect.height() / 2,
                            text_bounding_rect.width(),
                            text_bounding_rect.height()
                        )
                    else:
                        final_text_rect = QRectF(
                            line_end.x() - text_bounding_rect.width(),
                            line_end.y() - text_bounding_rect.height() / 2,
                            text_bounding_rect.width(),
                            text_bounding_rect.height()
                        )

                    painter.setPen(current_color)
                    painter.drawText(final_text_rect, Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignCenter,
                                     item['task'])
                except Exception as e:
                    print(f"绘制引导线时出错: {e}")

        painter.restore()

    def draw_clock_face(self, painter):
        painter.save()
        painter.setPen(Qt.GlobalColor.black)
        for i in range(60):
            if (i % 5) == 0:
                painter.setPen(QPen(Qt.GlobalColor.black, 2))
                painter.drawLine(88, 0, 96, 0)
            else:
                painter.setPen(QPen(Qt.GlobalColor.darkGray, 1))
                painter.drawLine(92, 0, 96, 0)
            painter.rotate(6.0)

        painter.setFont(QFont("Arial", 10))
        for i in range(1, 13):
            angle_rad = math.radians(i * 30 - 90)
            x = 78 * math.cos(angle_rad)
            y = 78 * math.sin(angle_rad)

            # --- 核心修改：统一将两个时钟的刻度都显示为1-12 ---
            hour_label = str(i)

            painter.drawText(QRectF(x - 10, y - 10, 20, 20), Qt.AlignmentFlag.AlignCenter, hour_label)
        painter.restore()

    def draw_hands(self, painter):
        time = QTime.currentTime()
        current_hour = time.hour()

        # --- 核心逻辑修改: 根据新的时间范围决定是否绘制指针 ---
        should_draw_hands = False
        if self.time_period == 'AM':  # 白天时钟 06:00 - 17:59
            if 6 <= current_hour < 18:
                should_draw_hands = True
        else:  # 夜晚时钟 18:00 - 05:59
            if current_hour >= 18 or current_hour < 6:
                should_draw_hands = True

        if not should_draw_hands:
            return

        hour_hand = QPolygonF([QPointF(-3, 8), QPointF(3, 8), QPointF(0, -50)])
        minute_hand = QPolygonF([QPointF(-2, 8), QPointF(2, 8), QPointF(0, -70)])

        painter.setPen(Qt.PenStyle.NoPen)

        painter.save()
        painter.setBrush(QColor(0, 0, 0, 200))
        display_hour = time.hour() % 12
        painter.rotate(30.0 * (display_hour + time.minute() / 60.0))
        painter.drawPolygon(hour_hand)
        painter.restore()

        painter.save()
        painter.setBrush(QColor(50, 50, 50, 220))
        painter.rotate(6.0 * (time.minute() + time.second() / 60.0))
        painter.drawPolygon(minute_hand)
        painter.restore()

        painter.save()
        painter.setPen(QPen(QColor(255, 0, 0, 150), 1))
        painter.rotate(6.0 * time.second())
        painter.drawLine(0, 10, 0, -80)
        painter.restore()

        painter.setBrush(Qt.GlobalColor.black)
        painter.drawEllipse(-4, -4, 8, 8)


# --- 主窗口 (已升级) ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("千千每日计划钟")

        # --- 核心修改：设置窗口图标 ---
        # 这会同时设置窗口左上角的图标和任务栏图标
        try:
            icon_path = resource_path("1.ico")
            self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            print(f"无法加载图标 '1.ico': {e}")  # 如果找不到图标，则打印错误但程序继续运行

        self.setGeometry(100, 100, 1200, 900)
        self.schedule_data = []
        self.clock_text_font = QFont("Arial", 8)
        self.single_view_mode = False
        self.predefined_colors = [
            QColor("#F44336"), QColor("#E91E63"), QColor("#9C27B0"),
            QColor("#673AB7"), QColor("#3F51B5"), QColor("#2196F3"),
            QColor("#03A9F4"), QColor("#00BCD4"), QColor("#009688"),
            QColor("#4CAF50"), QColor("#8BC34A"), QColor("#CDDC39"),
            QColor("#FFEB3B"), QColor("#FFC107"), QColor("#FF9800"),
            QColor("#FF5722"), QColor("#795548"), QColor("#607D8B")
        ]
        self.init_ui()
        self.load_settings()
        self.update_all_views()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        splitter = QSplitter(Qt.Orientation.Vertical)

        top_container = QWidget()
        top_layout = QHBoxLayout(top_container)

        self.clock_splitter = QSplitter(Qt.Orientation.Horizontal)

        # --- 核心修改：移除标题，但保留容器结构以便双击功能正常工作 ---
        am_container = QWidget()
        am_layout = QVBoxLayout(am_container)
        am_layout.setContentsMargins(0, 0, 0, 0)
        self.am_clock = ClockWidget('AM')
        am_layout.addWidget(self.am_clock)

        pm_container = QWidget()
        pm_layout = QVBoxLayout(pm_container)
        pm_layout.setContentsMargins(0, 0, 0, 0)
        self.pm_clock = ClockWidget('PM')
        pm_layout.addWidget(self.pm_clock)

        self.am_clock.doubleClicked.connect(self.toggle_clock_view)
        self.pm_clock.doubleClicked.connect(self.toggle_clock_view)

        self.clock_splitter.addWidget(am_container)
        self.clock_splitter.addWidget(pm_container)
        top_layout.addWidget(self.clock_splitter)

        self.bottom_container = QWidget()
        bottom_layout = QVBoxLayout(self.bottom_container)

        self.table_widget = QTableWidget()
        bottom_layout.addWidget(self.table_widget)

        button_layout = QHBoxLayout()
        add_button = QPushButton("➕ 添加时间段")
        delete_button = QPushButton("➖ 删除选中项")
        button_layout.addWidget(add_button)
        button_layout.addWidget(delete_button)
        bottom_layout.addLayout(button_layout)

        splitter.addWidget(top_container)
        splitter.addWidget(self.bottom_container)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        splitter.setSizes([600, 300])
        main_layout.addWidget(splitter)

        bottom_buttons_layout = QHBoxLayout()
        bottom_buttons_layout.addStretch()

        self.toggle_button = QPushButton("🔽 最小化")
        self.toggle_button.clicked.connect(self.toggle_bottom_panel)
        bottom_buttons_layout.addWidget(self.toggle_button)

        settings_button = QPushButton("⚙️ 设置")
        settings_button.clicked.connect(self.open_settings_dialog)
        bottom_buttons_layout.addWidget(settings_button)

        bottom_buttons_layout.addStretch()
        main_layout.addLayout(bottom_buttons_layout)

        self.setup_table()
        add_button.clicked.connect(self.add_item)
        delete_button.clicked.connect(self.delete_item)

    def toggle_clock_view(self):
        sender_clock = self.sender()
        if not self.single_view_mode:
            self.single_view_mode = True
            if sender_clock == self.am_clock:
                self.pm_clock.parentWidget().hide()
            else:
                self.am_clock.parentWidget().hide()
        else:
            self.single_view_mode = False
            self.am_clock.parentWidget().show()
            self.pm_clock.parentWidget().show()
            sizes = [self.clock_splitter.width() // 2, self.clock_splitter.width() // 2]
            self.clock_splitter.setSizes(sizes)

    def open_settings_dialog(self):
        dialog = SimpleFontDialog(self.clock_text_font, self)
        if dialog.exec():
            self.clock_text_font = dialog.get_font()
            self.am_clock.set_text_font(self.clock_text_font)
            self.pm_clock.set_text_font(self.clock_text_font)
            self.save_settings()

    def toggle_bottom_panel(self):
        if self.bottom_container.isVisible():
            self.bottom_container.hide()
            self.toggle_button.setText("🔼 恢复")
        else:
            self.bottom_container.show()
            self.toggle_button.setText("🔽 最小化")

    def setup_table(self):
        self.table_widget.setColumnCount(3)
        self.table_widget.setHorizontalHeaderLabels(["时间段", "事件内容", "颜色"])
        self.table_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table_widget.setColumnWidth(0, 150)
        self.table_widget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_widget.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table_widget.setColumnWidth(2, 80)
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_widget.cellDoubleClicked.connect(self.edit_time)
        self.table_widget.itemChanged.connect(self.edit_task)

    def load_default_data(self):
        self.schedule_data = [
            {'start_time': QTime(6, 0), 'end_time': QTime(7, 30), 'task': '起床 & 早餐', 'color': QColor("#4CAF50")},
            {'start_time': QTime(8, 0), 'end_time': QTime(12, 0), 'task': '上午工作',
             'color': QColor("#2196F3")},
            {'start_time': QTime(11, 30), 'end_time': QTime(13, 0), 'task': '午餐', 'color': QColor("#FFC107")},
            {'start_time': QTime(13, 0), 'end_time': QTime(17, 30), 'task': '下午工作', 'color': QColor("#03A9F4")},
            {'start_time': QTime(18, 0), 'end_time': QTime(19, 0), 'task': '晚餐', 'color': QColor("#FF9800")},
            {'start_time': QTime(23, 0), 'end_time': QTime(0, 0), 'task': '准备睡觉休息', 'color': QColor("#673AB7")},
        ]

    def rebuild_table_view(self):
        self.table_widget.blockSignals(True)
        self.table_widget.setRowCount(len(self.schedule_data))
        for row, item in enumerate(self.schedule_data):
            time_str = f"{item['start_time'].toString('HH:mm')} - {item['end_time'].toString('HH:mm')}"
            time_item = QTableWidgetItem(time_str)
            time_item.setFlags(time_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_widget.setItem(row, 0, time_item)
            self.table_widget.setItem(row, 1, QTableWidgetItem(item['task']))

            color_button = QPushButton()
            color_button.setStyleSheet(f"background-color: {item['color'].name()}; border: 1px solid #ccc;")
            color_button.clicked.connect(lambda checked, r=row: self.change_color(r))
            self.table_widget.setCellWidget(row, 2, color_button)
        self.table_widget.blockSignals(False)

    def update_all_views(self):
        self.schedule_data.sort(key=lambda x: x['start_time'])
        self.rebuild_table_view()
        self.am_clock.set_schedule_data(self.schedule_data)
        self.pm_clock.set_schedule_data(self.schedule_data)
        self.am_clock.set_text_font(self.clock_text_font)
        self.pm_clock.set_text_font(self.clock_text_font)
        self.save_settings()

    # --- 新增：时间冲突检测逻辑 ---
    def check_for_conflict(self, new_start_time, new_end_time, editing_row_index):
        new_start_min = new_start_time.hour() * 60 + new_start_time.minute()
        new_end_min = new_end_time.hour() * 60 + new_end_time.minute()

        new_segments = []
        if new_end_min <= new_start_min:  # 跨天事件
            new_segments.append((new_start_min, 24 * 60))
            new_segments.append((0, new_end_min))
        else:
            new_segments.append((new_start_min, new_end_min))

        for i, item in enumerate(self.schedule_data):
            if i == editing_row_index:
                continue

            exist_start_min = item['start_time'].hour() * 60 + item['start_time'].minute()
            exist_end_min = item['end_time'].hour() * 60 + item['end_time'].minute()

            exist_segments = []
            if exist_end_min <= exist_start_min:  # 跨天事件
                exist_segments.append((exist_start_min, 24 * 60))
                exist_segments.append((0, exist_end_min))
            else:
                exist_segments.append((exist_start_min, exist_end_min))

            for ns_start, ns_end in new_segments:
                for es_start, es_end in exist_segments:
                    if max(ns_start, es_start) < min(ns_end, es_end):
                        return True  # 发现冲突
        return False  # 未发现冲突

    # --- 修改：添加项目的逻辑 ---
    def add_item(self):
        new_start_time = QTime(0, 0)
        if self.schedule_data:
            last_item = max(self.schedule_data,
                            key=lambda x: (x['end_time'].hour() + (24 if x['end_time'] < x['start_time'] else 0),
                                           x['end_time'].minute()))
            last_end_time = last_item['end_time']

            if last_end_time.minute() > 0 or last_end_time.second() > 0:
                new_hour = (last_end_time.hour() + 1) % 24
                new_start_time = QTime(new_hour, 0)
            else:
                new_start_time = last_end_time

        new_end_time = new_start_time.addSecs(3600)

        if self.check_for_conflict(new_start_time, new_end_time, -1):
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setText("无法添加时间段")
            msg_box.setInformativeText("新的一小时时间段与现有计划冲突，或已排满24小时。")
            msg_box.setWindowTitle("警告")
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.exec()
            return

        new_item = {
            'start_time': new_start_time,
            'end_time': new_end_time,
            'task': '新事件',
            'color': random.choice(self.predefined_colors)
        }
        self.schedule_data.append(new_item)
        self.update_all_views()

        try:
            new_row_index = self.schedule_data.index(new_item)
            self.table_widget.selectRow(new_row_index)
        except ValueError:
            if self.table_widget.rowCount() > 0:
                self.table_widget.selectRow(self.table_widget.rowCount() - 1)

    # --- 修改：删除项目的逻辑 ---
    def delete_item(self):
        if self.schedule_data:
            self.schedule_data.pop()  # 从列表末尾删除
            self.update_all_views()
            if self.table_widget.rowCount() > 0:
                self.table_widget.selectRow(self.table_widget.rowCount() - 1)

    # --- 修改：编辑时间的逻辑 ---
    def edit_time(self, row, column):
        if column == 0:
            if not (0 <= row < len(self.schedule_data)):
                return

            item = self.schedule_data[row]
            dialog = TimeEditDialog(item['start_time'], item['end_time'], self)
            if dialog.exec():
                if dialog.to_be_deleted:
                    # 如果用户点击了删除
                    del self.schedule_data[row]
                    self.update_all_views()
                    # 删除后，智能选择下一行
                    if self.table_widget.rowCount() > 0:
                        new_selection_row = min(row, self.table_widget.rowCount() - 1)
                        self.table_widget.selectRow(new_selection_row)
                else:
                    # 如果用户点击了OK
                    new_start, new_end = dialog.get_times()

                    if self.check_for_conflict(new_start, new_end, row):
                        msg_box = QMessageBox(self)
                        msg_box.setIcon(QMessageBox.Icon.Warning)
                        msg_box.setText("时间冲突！")
                        msg_box.setInformativeText("您设置的时间段与现有计划重叠，请重新设置。")
                        msg_box.setWindowTitle("警告")
                        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
                        msg_box.exec()
                    else:
                        self.schedule_data[row]['start_time'] = new_start
                        self.schedule_data[row]['end_time'] = new_end
                        self.update_all_views()

    def edit_task(self, item):
        row, column = item.row(), item.column()
        if column == 1 and row < len(self.schedule_data):
            self.schedule_data[row]['task'] = item.text()
            self.update_all_views()

    def change_color(self, row):
        if 0 <= row < len(self.schedule_data):
            initial_color = self.schedule_data[row]['color']
            new_color = QColorDialog.getColor(initial_color, self)
            if new_color.isValid():
                self.schedule_data[row]['color'] = new_color
                self.update_all_views()

    def save_settings(self):
        settings_path = "clock_schedule.ini"
        settings = QSettings(settings_path, QSettings.Format.IniFormat)

        settings.setValue("font/family", self.clock_text_font.family())
        settings.setValue("font/pointSize", self.clock_text_font.pointSize())

        serializable_data = []
        for item in self.schedule_data:
            serializable_data.append({
                'start_time': item['start_time'].toString("HH:mm"),
                'end_time': item['end_time'].toString("HH:mm"),
                'task': item['task'],
                'color': item['color'].name()
            })
        settings.setValue("schedule", serializable_data)

    def load_settings(self):
        settings_path = "clock_schedule.ini"
        settings = QSettings(settings_path, QSettings.Format.IniFormat)

        family = settings.value("font/family", "Arial")
        try:
            pointSize = int(settings.value("font/pointSize", 8))
        except (ValueError, TypeError):
            pointSize = 8
        self.clock_text_font = QFont(family, pointSize)

        saved_schedule = settings.value("schedule", [])

        if not isinstance(saved_schedule, list):
            self.load_default_data()
            return

        try:
            new_schedule_data = []
            for item in saved_schedule:
                if not isinstance(item, dict):
                    continue

                start_time_str = item.get('start_time', '00:00')
                end_time_str = item.get('end_time', '01:00')
                task_str = str(item.get('task', ''))
                color_str = item.get('color', '#808080')

                start_time = QTime.fromString(start_time_str, "HH:mm")
                end_time = QTime.fromString(end_time_str, "HH:mm")
                color = QColor(color_str)

                if start_time.isValid() and end_time.isValid() and color.isValid():
                    new_schedule_data.append({
                        'start_time': start_time,
                        'end_time': end_time,
                        'task': task_str,
                        'color': color
                    })
            self.schedule_data = new_schedule_data

            if not self.schedule_data:
                self.load_default_data()

        except Exception as e:
            print(f"解析设置文件失败: {e}. 加载默认数据。")
            self.load_default_data()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    translator = QTranslator()
    path = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    if translator.load("qt_zh_CN", path):
        app.installTranslator(translator)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
