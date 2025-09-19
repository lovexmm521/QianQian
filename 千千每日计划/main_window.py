# main_window.py
# 定义应用程序的主窗口 (已更新)

import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QGridLayout, QScrollArea, QPushButton,
                             QCalendarWidget, QTextEdit, QFrame, QTimeEdit,
                             QMessageBox, QDialog, QDialogButtonBox, QMenu, QApplication)
from PyQt6.QtCore import Qt, QDate, QTime, pyqtSignal, QSettings
from PyQt6.QtGui import QAction, QTextCharFormat, QPalette, QColor

from database import DatabaseManager
from settings_window import SettingsWindow
from utils import get_week_dates, FONT_AWESOME


class BlinkingCursorTextEdit(QTextEdit):
    """
    一个自定义的 QTextEdit，它只在获得焦点时显示闪烁的光标。
    """
    lostFocus = pyqtSignal()  # 当小部件失去焦点时发出信号

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setPlaceholderText("输入计划...")

    def focusInEvent(self, event):
        """当获得焦点时，确保光标可见并闪烁。"""
        self.setCursorWidth(1)
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        """当失去焦点时，先发出信号保存数据，然后隐藏光标。"""
        self.lostFocus.emit()
        super().focusOutEvent(event)
        self.setCursorWidth(0)


class PlanWidget(QFrame):
    """单个计划的自定义小部件"""
    plan_updated = pyqtSignal(int, str, int)
    plan_created = pyqtSignal(object, str, int, str, int,
                              str)  # sender_widget, date_str, slot_id, text, status, plan_type
    plan_type_changed = pyqtSignal(int, str)
    merge_up_requested = pyqtSignal(int, int)
    merge_down_requested = pyqtSignal(int, int)
    split_requested = pyqtSignal(int, int)

    def __init__(self, plan_id, text, status, row, col, row_span, plan_type, date_str, slot_id, parent=None):
        super().__init__(parent)
        self.plan_id = plan_id
        self.status = status
        self.grid_row = row
        self.grid_col = col
        self.row_span = row_span
        self.plan_type = plan_type
        self.date_str = date_str
        self.slot_id = slot_id

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(10)

        self.text_edit = BlinkingCursorTextEdit(text)
        self.text_edit.lostFocus.connect(self.on_update)

        self.complete_btn = QPushButton()
        self.complete_btn.setObjectName("CompleteButton")
        self.complete_btn.setFixedSize(30, 30)
        self.complete_btn.clicked.connect(self.cycle_status)

        self.layout.addWidget(self.text_edit)
        self.layout.addWidget(self.complete_btn)

        self.setObjectName("PlanWidget")
        self.update_visual_state()

    def contextMenuEvent(self, event):
        """创建并显示右键上下文菜单。"""
        menu = QMenu(self)

        merge_up_action = QAction("向上合并", self)
        merge_up_action.triggered.connect(lambda: self.merge_up_requested.emit(self.grid_row, self.grid_col))
        menu.addAction(merge_up_action)

        merge_down_action = QAction("向下合并", self)
        merge_down_action.triggered.connect(lambda: self.merge_down_requested.emit(self.grid_row, self.grid_col))
        menu.addAction(merge_down_action)

        if self.row_span > 1:
            split_action = QAction("拆分计划", self)
            split_action.triggered.connect(lambda: self.split_requested.emit(self.grid_row, self.grid_col))
            menu.addAction(split_action)

        menu.addSeparator()
        rest_action = QAction("休息", self)
        rest_action.triggered.connect(lambda: self._change_plan_type("rest"))
        menu.addAction(rest_action)

        empty_action = QAction("无", self)
        empty_action.triggered.connect(lambda: self._change_plan_type("empty"))
        menu.addAction(empty_action)

        if self.plan_type != "normal":
            menu.addSeparator()
            reset_action = QAction("恢复为计划", self)
            reset_action.triggered.connect(lambda: self._change_plan_type("normal"))
            menu.addAction(reset_action)

        menu.exec(event.globalPos())

    def _change_plan_type(self, new_type):
        """内部方法，用于处理右键菜单的类型变更请求。"""
        if self.plan_id is None:
            self.plan_created.emit(self, self.date_str, self.slot_id, "", 0, new_type)
        else:
            self.plan_type_changed.emit(self.plan_id, new_type)

    def cycle_status(self):
        self.status = (self.status + 1) % 3
        self.update_visual_state()
        self.on_update()

    def update_visual_state(self):
        """根据当前状态更新图标和样式，使用直接设置颜色以提高性能。"""
        color = "#c0c4cc"
        icon_text = FONT_AWESOME['circle']

        if self.status == 1:
            icon_text = FONT_AWESOME['check-circle']
            color = "#67c23a"
        elif self.status == 2:
            icon_text = FONT_AWESOME['times-circle']
            color = "#f56c6c"

        self.complete_btn.setText(icon_text)
        self.complete_btn.setStyleSheet(f"background-color: transparent; border: none; color: {color};")

        self.setProperty("plan_type", self.plan_type)
        is_normal = self.plan_type == 'normal'
        self.text_edit.setVisible(is_normal)

        settings = QSettings("settings.ini", QSettings.Format.IniFormat)
        show_status_icons = settings.value("show_status_icon", True, type=bool)
        self.complete_btn.setVisible(is_normal and show_status_icons)

        self.style().unpolish(self)
        self.style().polish(self)

    def on_update(self):
        text = self.text_edit.toPlainText()
        if self.plan_id is None:
            if text.strip() or self.status != 0:
                self.plan_created.emit(self, self.date_str, self.slot_id, text, self.status, self.plan_type)
        else:
            self.plan_updated.emit(self.plan_id, text, self.status)


class TimeSlotWidget(QFrame):
    """自定义时间段小部件，现在内部管理删除按钮的可见性。"""
    doubleClicked = pyqtSignal(int)
    deleteRequested = pyqtSignal(int)
    merge_up_requested = pyqtSignal(int)
    merge_down_requested = pyqtSignal(int)
    split_requested = pyqtSignal(int)

    def __init__(self, slot_id, start_time, end_time, row, row_span, parent=None):
        super().__init__(parent)
        self.slot_id = slot_id
        self.row = row
        self.row_span = row_span
        self.setObjectName("TimeSlotWidget")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)

        time_label = QLabel(f"{start_time} - {end_time}")
        time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.delete_btn = QPushButton(FONT_AWESOME['trash-alt'])
        self.delete_btn.setObjectName("DeleteButton")
        self.delete_btn.setFixedSize(20, 20)
        self.delete_btn.clicked.connect(lambda: self.deleteRequested.emit(self.slot_id))

        layout.addWidget(time_label)
        layout.addWidget(self.delete_btn)

        self.update_visual_state()

    def update_visual_state(self):
        """从设置读取并更新删除按钮的可见性。"""
        settings = QSettings("settings.ini", QSettings.Format.IniFormat)
        show_delete = settings.value("show_delete_button", False, type=bool)
        self.delete_btn.setVisible(show_delete)

    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit(self.slot_id)
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):
        """创建并显示右键上下文菜单以进行合并。"""
        menu = QMenu(self)
        merge_up_action = QAction("向上合并", self)
        merge_up_action.triggered.connect(lambda: self.merge_up_requested.emit(self.row))
        menu.addAction(merge_up_action)

        merge_down_action = QAction("向下合并", self)
        merge_down_action.triggered.connect(lambda: self.merge_down_requested.emit(self.row))
        menu.addAction(merge_down_action)

        if self.row_span > 1:
            split_action = QAction("拆分时间段", self)
            split_action.triggered.connect(lambda: self.split_requested.emit(self.slot_id))
            menu.addAction(split_action)

        menu.exec(event.globalPos())


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.grid_plan_map = {}
        self.time_slots_data = []  # 用于存储当前视图的时间段完整信息
        self.selected_dates = []
        self.clicked_date = QDate.currentDate()
        self._is_first_load = True
        self.init_ui()

    def showEvent(self, event):
        super().showEvent(event)
        if self._is_first_load:
            self.go_to_today()
            self._is_first_load = False

    def init_ui(self):
        self.setWindowTitle("千千每日计划")
        self.setGeometry(100, 100, 1600, 800)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QHBoxLayout(central_widget)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        self.main_layout.addWidget(left_panel, 7)
        self.week_title_label = QLabel("当前周")
        self.week_title_label.setObjectName("WeekTitle")
        self.week_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(self.week_title_label)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        left_layout.addWidget(scroll_area)
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(5)
        scroll_area.setWidget(self.grid_container)
        self.right_panel = QWidget()
        self.right_panel.setObjectName("RightPanel")
        right_layout = QVBoxLayout(self.right_panel)
        self.calendar = QCalendarWidget()
        self.calendar.selectionChanged.connect(self._process_date_selection)
        right_layout.addWidget(self.calendar)

        buttons_layout = QGridLayout()
        add_slot_btn = QPushButton(f"{FONT_AWESOME['plus']} 添加时间段")
        add_slot_btn.clicked.connect(self.add_time_slot)
        settings_btn = QPushButton(f"{FONT_AWESOME['cog']} 设置")
        settings_btn.clicked.connect(self.open_settings)
        stats_btn = QPushButton(f"{FONT_AWESOME['chart-pie']} 统计")
        stats_btn.clicked.connect(self.show_stats)
        today_btn = QPushButton(f"{FONT_AWESOME['calendar-day']} 回到今天")
        today_btn.clicked.connect(self.go_to_today)

        buttons_layout.addWidget(settings_btn, 0, 0)
        buttons_layout.addWidget(add_slot_btn, 0, 1)
        buttons_layout.addWidget(stats_btn, 1, 0)
        buttons_layout.addWidget(today_btn, 1, 1)

        right_layout.addLayout(buttons_layout)
        right_layout.addStretch()
        bottom_bar_layout = QHBoxLayout()
        bottom_bar_layout.setContentsMargins(5, 5, 5, 5)
        self.toggle_sidebar_btn = QPushButton(FONT_AWESOME['chevron-right'])
        self.toggle_sidebar_btn.setObjectName("SidebarToggleButton")
        self.toggle_sidebar_btn.clicked.connect(self.toggle_sidebar)
        bottom_bar_layout.addWidget(self.toggle_sidebar_btn)
        bottom_bar_layout.addStretch()
        right_layout.addLayout(bottom_bar_layout)
        self.collapsed_panel = QFrame()
        self.collapsed_panel.setObjectName("CollapsedPanel")
        self.collapsed_panel.setFixedWidth(40)
        collapsed_layout = QVBoxLayout(self.collapsed_panel)
        collapsed_layout.setContentsMargins(5, 5, 5, 5)
        collapsed_layout.addStretch()
        self.expand_sidebar_btn = QPushButton(FONT_AWESOME['chevron-left'])
        self.expand_sidebar_btn.setObjectName("ExpandButton")
        self.expand_sidebar_btn.clicked.connect(self.toggle_sidebar)
        collapsed_layout.addWidget(self.expand_sidebar_btn)
        self.main_layout.addWidget(self.right_panel, 3)
        self.main_layout.addWidget(self.collapsed_panel)
        self.collapsed_panel.hide()
        self.is_sidebar_collapsed = False

    def toggle_sidebar(self):
        self.is_sidebar_collapsed = not self.is_sidebar_collapsed
        self.right_panel.setVisible(not self.is_sidebar_collapsed)
        self.collapsed_panel.setVisible(self.is_sidebar_collapsed)

    def _update_title(self, default_title_text):
        settings = QSettings("settings.ini", QSettings.Format.IniFormat)
        use_custom = settings.value("title/custom_enabled", False, type=bool)

        if use_custom:
            text = settings.value("title/text", "", type=str)
            family = settings.value("title/font_family", "Microsoft YaHei UI", type=str)
            size = settings.value("title/font_size", 24, type=int)
            color = settings.value("title/color", "#2c3e50", type=str)
            self.week_title_label.setText(text)
            self.week_title_label.setStyleSheet(f"""
                #WeekTitle {{
                    font-size: {size}px;
                    font-family: '{family}';
                    color: {color};
                }}
            """)
        else:
            self.week_title_label.setText(default_title_text)
            self.week_title_label.setStyleSheet("")

    def update_grid_view(self):
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        self.highlight_selected_dates()
        if not self.selected_dates:
            self.week_title_label.setText("请在日历中选择日期")
            return
        dates_to_display = sorted(self.selected_dates)

        default_title = ""
        is_contiguous = True
        if len(dates_to_display) > 1:
            for i in range(len(dates_to_display) - 1):
                if dates_to_display[i].addDays(1) != dates_to_display[i + 1]:
                    is_contiguous = False
                    break

        if len(dates_to_display) == 1:
            default_title = dates_to_display[0].toString("yyyy年MM月dd日 dddd")
        elif is_contiguous:
            start = dates_to_display[0]
            end = dates_to_display[-1]
            default_title = f"{start.toString('yyyy年MM月dd日')} - {end.toString('yyyy年MM月dd日')}"
        else:
            default_title = "多个已选日期"

        self._update_title(default_title)

        first_date = dates_to_display[0]
        week_of_first_date = get_week_dates(first_date)
        start_of_week_str = week_of_first_date[0].toString("yyyy-MM-dd")
        settings = QSettings("settings.ini", QSettings.Format.IniFormat)
        show_date_in_header = settings.value("show_date_in_header", False, type=bool)
        self.grid_plan_map.clear()

        grid_occupancy = set()

        weekdays_map = {1: "周一", 2: "周二", 3: "周三", 4: "周四", 5: "周五", 6: "周六", 7: "周日"}
        headers = ["时间"]
        for d in dates_to_display:
            header_text = weekdays_map[d.dayOfWeek()]
            if show_date_in_header:
                header_text += f"\n{d.toString('MM-dd')}"
            headers.append(header_text)
        for col, header_text in enumerate(headers):
            header_label = QLabel(header_text)
            header_label.setObjectName("GridHeader")
            header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid_layout.addWidget(header_label, 0, col)

        self.time_slots_data = self.db_manager.get_time_slots(start_of_week_str, include_hidden=True)
        if not self.time_slots_data:
            self.db_manager.create_default_time_slots(start_of_week_str)
            self.time_slots_data = self.db_manager.get_time_slots(start_of_week_str, include_hidden=True)

        day_merges = self.get_effective_day_merges()

        row_idx = 1
        slot_list_idx = 0
        while slot_list_idx < len(self.time_slots_data):
            slot_id, start_time, _, weekly_row_span = self.time_slots_data[slot_list_idx]

            row_span = day_merges.get(slot_id, weekly_row_span)

            if row_span > 0:
                end_time_list_index = slot_list_idx + row_span - 1
                if end_time_list_index < len(self.time_slots_data):
                    end_time = self.time_slots_data[end_time_list_index][2]
                else:  # Handle edge case where span goes out of bounds
                    end_time = self.time_slots_data[-1][2]

                time_label_container = TimeSlotWidget(slot_id, start_time, end_time, row_idx, row_span)
                time_label_container.doubleClicked.connect(self.edit_time_slot)
                time_label_container.deleteRequested.connect(self.delete_time_slot)
                time_label_container.merge_up_requested.connect(self.handle_time_slot_merge_up)
                time_label_container.merge_down_requested.connect(self.handle_time_slot_merge_down)
                time_label_container.split_requested.connect(self.handle_time_slot_split)
                self.grid_layout.addWidget(time_label_container, row_idx, 0, row_span, 1)

            effective_span = row_span if row_span > 0 else 1
            for r_offset in range(effective_span):
                current_row = row_idx + r_offset
                current_slot_in_list_idx = slot_list_idx + r_offset
                if current_slot_in_list_idx >= len(self.time_slots_data): continue

                underlying_slot_id = self.time_slots_data[current_slot_in_list_idx][0]

                for col_idx, date in enumerate(dates_to_display, 1):
                    date_str = date.toString("yyyy-MM-dd")
                    if (current_row, col_idx) in grid_occupancy: continue

                    plan_data = self.db_manager.get_plan(date_str, underlying_slot_id)

                    if plan_data:
                        plan_id, text, status, p_row_span, plan_type = plan_data
                        self.grid_plan_map[(current_row, col_idx)] = (plan_id, text, status, p_row_span, date_str,
                                                                      underlying_slot_id, plan_type)
                        plan_widget = PlanWidget(plan_id, text, status, current_row, col_idx, p_row_span, plan_type,
                                                 date_str, underlying_slot_id)
                    else:
                        p_row_span = 1
                        plan_widget = PlanWidget(None, "", 0, current_row, col_idx, p_row_span, "normal", date_str,
                                                 underlying_slot_id)

                    plan_widget.plan_updated.connect(self.db_manager.update_plan_content)
                    plan_widget.plan_created.connect(self.handle_plan_creation)
                    plan_widget.plan_type_changed.connect(self.handle_plan_type_change)
                    plan_widget.merge_up_requested.connect(self.handle_merge_up)
                    plan_widget.merge_down_requested.connect(self.handle_merge_down)
                    plan_widget.split_requested.connect(self.handle_split)
                    self.grid_layout.addWidget(plan_widget, current_row, col_idx, p_row_span, 1)

                    if p_row_span > 1:
                        for i in range(1, p_row_span):
                            grid_occupancy.add((current_row + i, col_idx))

            slot_list_idx += effective_span
            row_idx += effective_span

        for i in range(1, len(dates_to_display) + 1): self.grid_layout.setColumnStretch(i, 1)
        self.grid_layout.setColumnStretch(0, 0)
        self.grid_layout.setRowStretch(self.grid_layout.rowCount(), 1)

    def handle_plan_creation(self, sender_widget, date_str, slot_id, text, status, plan_type):
        new_id = self.db_manager.add_plan(date_str, slot_id, text, status, plan_type)
        if new_id:
            sender_widget.plan_id = new_id
            row, col = sender_widget.grid_row, sender_widget.grid_col
            self.grid_plan_map[(row, col)] = (new_id, text, status, sender_widget.row_span, date_str, slot_id,
                                              plan_type)

            if plan_type != 'normal':
                self.update_grid_view()

    def handle_plan_type_change(self, plan_id, plan_type):
        self.db_manager.update_plan_type(plan_id, plan_type)
        self.update_grid_view()

    def _ensure_plan_in_db(self, widget):
        if widget and widget.plan_id is None:
            new_id = self.db_manager.add_plan(
                widget.date_str,
                widget.slot_id,
                widget.text_edit.toPlainText(),
                widget.status,
                widget.plan_type
            )
            if new_id:
                widget.plan_id = new_id
                row, col = widget.grid_row, widget.grid_col
                self.grid_plan_map[(row, col)] = (new_id, widget.text_edit.toPlainText(), widget.status,
                                                  widget.row_span, widget.date_str, widget.slot_id, widget.plan_type)
                return True
            return False
        return True

    def handle_merge_down(self, row, col):
        source_widget = self.grid_layout.itemAtPosition(row, col).widget()
        if not source_widget: return

        if not self._ensure_plan_in_db(source_widget):
            QMessageBox.warning(self, "合并失败", "无法在数据库中创建源计划。")
            return

        source_id = source_widget.plan_id
        source_text = source_widget.text_edit.toPlainText()
        source_span = source_widget.row_span

        target_row = row + source_span
        target_item = self.grid_layout.itemAtPosition(target_row, col)
        if not target_item or not target_item.widget():
            QMessageBox.warning(self, "无法合并", "下方没有可合并的计划。")
            return
        target_widget = target_item.widget()

        if not self._ensure_plan_in_db(target_widget):
            QMessageBox.warning(self, "合并失败", "无法在数据库中创建目标计划。")
            return

        target_id = target_widget.plan_id
        target_text = target_widget.text_edit.toPlainText()
        target_span = target_widget.row_span

        new_span = source_span + target_span
        new_text = f"{source_text}\n{target_text}".strip() if source_text.strip() and target_text.strip() else source_text.strip() or target_text.strip()
        self.db_manager.update_plan_after_merge(source_id, new_text, new_span)
        self.db_manager.delete_plan_by_id(target_id)
        self.update_grid_view()

    def handle_merge_up(self, row, col):
        source_widget = self.grid_layout.itemAtPosition(row, col).widget()
        if not source_widget: return

        if not self._ensure_plan_in_db(source_widget):
            QMessageBox.warning(self, "合并失败", "无法在数据库中创建源计划。")
            return

        source_id = source_widget.plan_id
        source_text = source_widget.text_edit.toPlainText()
        source_span = source_widget.row_span

        target_source_row = -1
        for r in range(row - 1, 0, -1):
            item = self.grid_layout.itemAtPosition(r, col)
            if item and item.widget():
                target_source_row = r
                break

        if target_source_row == -1:
            QMessageBox.warning(self, "无法合并", "上方没有可合并的计划。")
            return

        target_widget = self.grid_layout.itemAtPosition(target_source_row, col).widget()
        if not target_widget: return

        if not self._ensure_plan_in_db(target_widget):
            QMessageBox.warning(self, "合并失败", "无法在数据库中创建目标计划。")
            return

        target_id = target_widget.plan_id
        target_text = target_widget.text_edit.toPlainText()
        target_span = target_widget.row_span

        new_span = target_span + source_span
        new_text = f"{target_text}\n{source_text}".strip() if target_text.strip() and source_text.strip() else target_text.strip() or source_text.strip()
        self.db_manager.update_plan_after_merge(target_id, new_text, new_span)
        self.db_manager.delete_plan_by_id(source_id)
        self.update_grid_view()

    def handle_split(self, row, col):
        plan_info = self.grid_plan_map.get((row, col))
        if not plan_info:
            return

        source_id, _, _, source_span, _, _, _ = plan_info
        if source_span <= 1:
            return

        self.db_manager.update_plan_span(source_id, 1)
        self.update_grid_view()

    def get_effective_day_merges(self):
        """ 辅助函数，获取当前视图的有效每日合并信息 """
        day_merges = {}
        settings = QSettings("settings.ini", QSettings.Format.IniFormat)
        is_day_mode = settings.value("default_view_mode", "week", type=str) == "day"
        is_single_day_view = len(self.selected_dates) == 1

        if is_day_mode and is_single_day_view:
            date_str = self.selected_dates[0].toString("yyyy-MM-dd")
            day_merges = self.db_manager.get_day_specific_merges(date_str)
        return day_merges

    def handle_time_slot_merge_down(self, row):
        settings = QSettings("settings.ini", QSettings.Format.IniFormat)
        is_day_mode = settings.value("default_view_mode", "week", type=str) == "day"
        is_single_day_view = len(self.selected_dates) == 1

        # --- 每日特定合并逻辑 ---
        if is_day_mode and is_single_day_view:
            date_str = self.selected_dates[0].toString("yyyy-MM-dd")
            day_merges = self.db_manager.get_day_specific_merges(date_str)

            source_index, source_slot = self.find_slot_index_by_row(row, day_merges)
            if source_index == -1: return

            source_id = source_slot[0]
            source_span = day_merges.get(source_id, source_slot[3])

            target_list_index = source_index + source_span
            if target_list_index >= len(self.time_slots_data):
                QMessageBox.warning(self, "无法合并", "下方没有可合并的时间段。")
                return

            target_id = self.time_slots_data[target_list_index][0]
            target_span = day_merges.get(target_id, self.time_slots_data[target_list_index][3])

            new_span = source_span + target_span
            self.db_manager.update_day_specific_merge(date_str, source_id, new_span)
            self.db_manager.split_day_specific_merge(date_str, target_id)  # 移除旧的每日合并（如果有）
            self.update_grid_view()
            return

        # --- 每周默认合并逻辑 ---
        source_index, _ = self.find_slot_index_by_row(row, {})
        target_index = -1
        for i in range(source_index + 1, len(self.time_slots_data)):
            if self.time_slots_data[i][3] > 0:
                target_index = i
                break

        if target_index == -1:
            QMessageBox.warning(self, "无法合并", "下方没有可合并的时间段。")
            return

        source_id = self.time_slots_data[source_index][0]
        target_id = self.time_slots_data[target_index][0]

        if self.db_manager.merge_time_slots_down(source_id, target_id):
            self.update_grid_view()
        else:
            QMessageBox.critical(self, "合并失败", "数据库操作失败。")

    def handle_time_slot_merge_up(self, row):
        settings = QSettings("settings.ini", QSettings.Format.IniFormat)
        is_day_mode = settings.value("default_view_mode", "week", type=str) == "day"
        is_single_day_view = len(self.selected_dates) == 1

        if is_day_mode and is_single_day_view:
            date_str = self.selected_dates[0].toString("yyyy-MM-dd")
            day_merges = self.db_manager.get_day_specific_merges(date_str)

            source_index, _ = self.find_slot_index_by_row(row, day_merges)
            if source_index == -1: return

            target_index, _ = self.find_previous_visible_slot_index(source_index, day_merges)
            if target_index == -1:
                QMessageBox.warning(self, "无法合并", "上方没有可合并的时间段。")
                return

            source_id = self.time_slots_data[source_index][0]
            target_id = self.time_slots_data[target_index][0]
            source_span = day_merges.get(source_id, self.time_slots_data[source_index][3])
            target_span = day_merges.get(target_id, self.time_slots_data[target_index][3])

            new_span = source_span + target_span
            self.db_manager.update_day_specific_merge(date_str, target_id, new_span)
            self.db_manager.split_day_specific_merge(date_str, source_id)
            self.update_grid_view()
            return

        source_index, _ = self.find_slot_index_by_row(row, {})
        target_index, _ = self.find_previous_visible_slot_index(source_index, {})

        if target_index == -1:
            QMessageBox.warning(self, "无法合并", "上方没有可合并的时间段。")
            return

        source_id = self.time_slots_data[source_index][0]
        target_id = self.time_slots_data[target_index][0]

        if self.db_manager.merge_time_slots_up(target_id, source_id):
            self.update_grid_view()
        else:
            QMessageBox.critical(self, "合并失败", "数据库操作失败。")

    def find_previous_visible_slot_index(self, start_index, day_merges):
        # 从 start_index-1 开始向前查找第一个可见的插槽
        i = start_index - 1
        while i >= 0:
            slot_id = self.time_slots_data[i][0]
            weekly_span = self.time_slots_data[i][3]
            effective_span = day_merges.get(slot_id, weekly_span)
            if effective_span > 0:
                return i, self.time_slots_data[i]
            i -= 1
        return -1, None

    def handle_time_slot_split(self, slot_id):
        settings = QSettings("settings.ini", QSettings.Format.IniFormat)
        is_day_mode = settings.value("default_view_mode", "week", type=str) == "day"
        is_single_day_view = len(self.selected_dates) == 1

        # --- 每日特定拆分 ---
        if is_day_mode and is_single_day_view:
            date_str = self.selected_dates[0].toString("yyyy-MM-dd")
            self.db_manager.split_day_specific_merge(date_str, slot_id)
            self.update_grid_view()
            return

        # --- 每周默认拆分 ---
        slot_index = -1
        for i, slot in enumerate(self.time_slots_data):
            if slot[0] == slot_id:
                slot_index = i
                break

        if slot_index == -1: return

        row_span = self.time_slots_data[slot_index][3]
        if row_span <= 1: return

        ids_to_reset = [s[0] for s in self.time_slots_data[slot_index: slot_index + row_span]]

        if self.db_manager.split_time_slot(ids_to_reset):
            self.update_grid_view()
        else:
            QMessageBox.critical(self, "拆分失败", "数据库操作失败。")

    def find_slot_index_by_row(self, target_row, day_merges):
        current_row = 1
        list_index = 0
        while list_index < len(self.time_slots_data):
            slot = self.time_slots_data[list_index]
            slot_id = slot[0]
            weekly_span = slot[3]
            effective_span = day_merges.get(slot_id, weekly_span)

            if effective_span > 0:
                if current_row == target_row:
                    return list_index, slot
                current_row += effective_span

            list_index_increment = effective_span if effective_span > 0 else 1
            list_index += list_index_increment

        return -1, None

    def _process_date_selection(self):
        selected_date = self.calendar.selectedDate()
        modifiers = QApplication.keyboardModifiers()
        settings = QSettings("settings.ini", QSettings.Format.IniFormat)
        default_view = settings.value("default_view_mode", "week", type=str)
        self.clicked_date = selected_date
        is_ctrl_click = (modifiers == Qt.KeyboardModifier.ControlModifier)

        if default_view == "week":
            self.selected_dates = get_week_dates(selected_date)
        else:
            if not is_ctrl_click:
                self.selected_dates = [selected_date]
            else:
                if selected_date in self.selected_dates:
                    if len(self.selected_dates) > 1:
                        self.selected_dates.remove(selected_date)
                elif len(self.selected_dates) < 7:
                    self.selected_dates.append(selected_date)
                else:
                    QMessageBox.information(self, "提示", "最多只能选择7天。")
        self.update_grid_view()

    def highlight_selected_dates(self):
        self.calendar.setDateTextFormat(QDate(), QTextCharFormat())
        selection_format = QTextCharFormat()
        palette = self.palette()
        selection_format.setBackground(palette.brush(QPalette.ColorRole.Highlight))
        selection_format.setForeground(QColor("#2c3e50"))
        settings = QSettings("settings.ini", QSettings.Format.IniFormat)
        default_view = settings.value("default_view_mode", "week", type=str)
        if default_view == 'week':
            if self.clicked_date:
                self.calendar.setDateTextFormat(self.clicked_date, selection_format)
        else:
            for date in self.selected_dates:
                self.calendar.setDateTextFormat(date, selection_format)

    def go_to_today(self):
        today = QDate.currentDate()
        current_calendar_date = self.calendar.selectedDate()
        self.calendar.setSelectedDate(today)
        if current_calendar_date == today:
            self._process_date_selection()

    def open_settings(self):
        settings_dialog = SettingsWindow(self.db_manager, self)
        settings_dialog.exec()
        self.update_grid_view()

    def add_time_slot(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("添加时间段")
        layout = QVBoxLayout(dialog)
        form_layout = QGridLayout()
        start_label = QLabel("开始时间:")
        self.start_time_edit = QTimeEdit()
        self.start_time_edit.setDisplayFormat("HH:mm")
        self.start_time_edit.setTime(QTime(9, 0))
        end_label = QLabel("结束时间:")
        self.end_time_edit = QTimeEdit()
        self.end_time_edit.setDisplayFormat("HH:mm")
        self.end_time_edit.setTime(QTime(10, 0))
        form_layout.addWidget(start_label, 0, 0)
        form_layout.addWidget(self.start_time_edit, 0, 1)
        form_layout.addWidget(end_label, 1, 0)
        form_layout.addWidget(self.end_time_edit, 1, 1)
        layout.addLayout(form_layout)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        if dialog.exec():
            start_time = self.start_time_edit.time().toString("HH:mm")
            end_time = self.end_time_edit.time().toString("HH:mm")
            if self.start_time_edit.time() >= self.end_time_edit.time():
                QMessageBox.warning(self, "时间错误", "结束时间必须晚于开始时间。")
                return
            first_date = sorted(self.selected_dates)[0] if self.selected_dates else QDate.currentDate()
            start_of_week = get_week_dates(first_date)[0].toString("yyyy-MM-dd")
            self.db_manager.add_time_slot(start_time, end_time, start_of_week)
            self.update_grid_view()

    def edit_time_slot(self, slot_id):
        slot_data = self.db_manager.get_time_slot_by_id(slot_id)
        if not slot_data: return
        current_start_str, current_end_str = slot_data[0:2]  # Ensure we only get time
        dialog = QDialog(self)
        dialog.setWindowTitle("编辑时间段")
        layout = QVBoxLayout(dialog)
        form_layout = QGridLayout()
        start_label = QLabel("开始时间:")
        self.start_time_edit = QTimeEdit()
        self.start_time_edit.setDisplayFormat("HH:mm")
        self.start_time_edit.setTime(QTime.fromString(current_start_str, "HH:mm"))
        end_label = QLabel("结束时间:")
        self.end_time_edit = QTimeEdit()
        self.end_time_edit.setDisplayFormat("HH:mm")
        self.end_time_edit.setTime(QTime.fromString(current_end_str, "HH:mm"))
        form_layout.addWidget(start_label, 0, 0)
        form_layout.addWidget(self.start_time_edit, 0, 1)
        form_layout.addWidget(end_label, 1, 0)
        form_layout.addWidget(self.end_time_edit, 1, 1)
        layout.addLayout(form_layout)
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)
        ok_button = QPushButton("确定")
        delete_button = QPushButton("删除时间段")
        cancel_button = QPushButton("取消")
        ok_button.clicked.connect(dialog.accept)
        delete_button.clicked.connect(lambda: self.handle_delete_from_edit_dialog(dialog, slot_id))
        cancel_button.clicked.connect(dialog.reject)
        buttons_layout.addWidget(cancel_button)
        buttons_layout.addWidget(delete_button)
        buttons_layout.addWidget(ok_button)
        layout.addLayout(buttons_layout)
        if dialog.exec():
            new_start_time = self.start_time_edit.time().toString("HH:mm")
            new_end_time = self.end_time_edit.time().toString("HH:mm")
            if self.start_time_edit.time() >= self.end_time_edit.time():
                QMessageBox.warning(self, "时间错误", "结束时间必须晚于开始时间。")
                return
            self.db_manager.update_time_slot(slot_id, new_start_time, new_end_time)
            self.update_grid_view()

    def handle_delete_from_edit_dialog(self, dialog, slot_id):
        self.delete_time_slot(slot_id)
        dialog.reject()

    def delete_time_slot(self, slot_id):
        reply = QMessageBox.question(self, "确认删除",
                                     "确定要删除这个时间段吗？\n与此时间段相关的计划都将被永久删除！",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.db_manager.delete_time_slot(slot_id)
            self.update_grid_view()

    def show_stats(self):
        if not self.selected_dates:
            QMessageBox.information(self, "统计", "请先选择要统计的日期。")
            return
        dates_to_stat = sorted(self.selected_dates)
        total_plans_with_text, success_count, failed_count, not_checked_count = 0, 0, 0, 0
        for date in dates_to_stat:
            plans = self.db_manager.get_plans_for_date(date.toString("yyyy-MM-dd"))
            for plan in plans:
                plan_text, status = plan[2], plan[3]
                if plan_text and plan_text.strip():
                    total_plans_with_text += 1
                    if status == 1:
                        success_count += 1
                    elif status == 2:
                        failed_count += 1
                    else:
                        not_checked_count += 1
        if total_plans_with_text > 0:
            checked_in_total = success_count + failed_count
            rate_text = f"打卡率: {(success_count / checked_in_total) * 100:.2f}%" if checked_in_total > 0 else "打卡率: N/A"
            message = (f"选中日期内的有效计划总数: {total_plans_with_text}\n\n"
                       f"成功打卡: {success_count}\n"
                       f"失败打卡: {failed_count}\n"
                       f"未打卡: {not_checked_count}\n\n"
                       f"{rate_text}")
        else:
            message = "选中的日期内没有任何有效计划。"
        QMessageBox.information(self, "选中日期统计", message)

    def closeEvent(self, event):
        self.db_manager.close()
        event.accept()
