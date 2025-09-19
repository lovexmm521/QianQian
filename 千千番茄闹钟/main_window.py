# main_window.py
import sys
import os
import random
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QApplication, QMessageBox,
    QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, QUrl, QTimer
from PyQt6.QtGui import QFont, QColor, QIcon
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

import qtawesome as qta

from timer_engine import TimerEngine, TimerState, PomodoroPhase
from settings_dialog import SettingsDialog
from config import config


# --- 新增: 用于解决打包后资源路径问题的函数 ---
def resource_path(relative_path):
    """ 获取资源的绝对路径，适用于开发环境和 PyInstaller 打包后 """
    try:
        # PyInstaller 创建一个临时文件夹，并将路径存储在 _MEIPASS 中
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings_dialog = None
        self.work_player = None
        self.break_player = None
        self.long_break_player = None
        self.random_player = None
        self.random_sound_list = []
        self.has_run_once = False
        self.drag_position = None

        self.init_ui()
        self.init_timer_logic()
        self.init_sound()

        # 首次加载，执行一次全部刷新
        self.apply_settings(full_reload=True)

    def init_ui(self):
        self.setWindowTitle("番茄计时器")

        # --- 修改: 使用 resource_path 函数加载图标 ---
        icon_path = resource_path("1.ico")  # 确保您的图标文件名为 1.ico
        self.setWindowIcon(QIcon(icon_path))

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.main_frame = QFrame()
        self.main_frame.setObjectName("mainFrame")

        self.main_layout = QVBoxLayout(self.main_frame)

        outer_layout = QVBoxLayout(central_widget)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(self.main_frame)

        self.timer_label = QLabel()
        self.timer_label.setObjectName("timerLabel")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setFont(QFont("Arial", 52, QFont.Weight.Bold))

        self.timer_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        self.custom_text_label = QLabel()
        self.custom_text_label.setObjectName("customTextLabel")
        self.custom_text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.custom_text_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        self.controls_layout_widget = QWidget()
        controls_layout = QHBoxLayout(self.controls_layout_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        self.start_button = QPushButton("开始")
        self.pause_button = QPushButton("暂停")
        self.reset_button = QPushButton("重置")

        for btn in [self.start_button, self.pause_button, self.reset_button]:
            btn.setObjectName("controlButton")

        controls_layout.addStretch()
        controls_layout.addWidget(self.start_button)
        controls_layout.addWidget(self.pause_button)
        controls_layout.addWidget(self.reset_button)
        controls_layout.addStretch()

        self.bottom_layout_widget = QWidget()
        bottom_layout = QHBoxLayout(self.bottom_layout_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        self.exit_button = QPushButton(qta.icon("fa5s.times", color="white"), "")
        self.exit_button.setObjectName("exitButton")
        self.app_title_label = QLabel("千千番茄闹钟")
        self.app_title_label.setObjectName("appTitleLabel")
        self.app_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.settings_button = QPushButton(qta.icon("fa5s.cog", color="gray"), "")
        self.settings_button.setObjectName("iconButton")

        for btn in [self.exit_button, self.settings_button]:
            btn.setFixedSize(26, 26)

        bottom_layout.addWidget(self.exit_button, 0, Qt.AlignmentFlag.AlignLeft)
        bottom_layout.addStretch(1)
        bottom_layout.addWidget(self.app_title_label)
        bottom_layout.addStretch(1)
        bottom_layout.addWidget(self.settings_button, 0, Qt.AlignmentFlag.AlignRight)

        self.main_layout.addWidget(self.timer_label)
        self.main_layout.addWidget(self.custom_text_label)
        self.main_layout.addWidget(self.controls_layout_widget)
        self.main_layout.addWidget(self.bottom_layout_widget)

        self.exit_button.clicked.connect(QApplication.instance().quit)
        self.settings_button.clicked.connect(self.open_settings)

    def init_timer_logic(self):
        self.timer_engine = TimerEngine()
        self.timer_engine.time_updated.connect(self.update_timer_display)
        self.timer_engine.phase_finished.connect(self.handle_phase_finish)
        self.timer_engine.cycle_finished.connect(self.handle_cycle_finish)
        self.timer_engine.state_changed.connect(self.update_button_states)

        self.start_button.clicked.connect(self.handle_start_click)
        self.pause_button.clicked.connect(self.handle_pause_click)
        self.reset_button.clicked.connect(self.handle_reset_click)

    def init_sound(self):
        self.work_player = self._create_player()
        self.break_player = self._create_player()
        self.long_break_player = self._create_player()
        self.random_player = self._create_player()

    def _create_player(self):
        player = QMediaPlayer()
        audio_output = QAudioOutput()
        player.setAudioOutput(audio_output)
        return player, audio_output

    # --- 修改: 为 apply_settings 添加 full_reload 参数 ---
    def apply_settings(self, full_reload=False):
        """
        应用设置。
        :param full_reload: True 表示重新加载所有设置（包括声音），False 表示仅更新UI。
        """
        is_on_top = config.get("always_on_top")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, is_on_top)

        self.update_ui_visibility()

        self.show()

        # 只有在需要完全重新加载时，才更新计时器和声音配置
        if full_reload:
            self.timer_engine.set_durations(
                work_mins=config.get("work_minutes"),
                break_mins=config.get("break_minutes"),
                long_break_mins=config.get("long_break_minutes"),
                pomos_per_cycle=config.get("pomodoros_per_cycle"),
                is_debug=config.get("developer_debug_mode")
            )

            self.custom_text_label.setText(config.get("custom_text"))

            self._configure_player(self.work_player, config.get("work_sound_path"), config.get("work_sound_volume"))
            self._configure_player(self.break_player, config.get("break_sound_path"), config.get("break_sound_volume"))
            self._configure_player(self.long_break_player, config.get("long_break_sound_path"),
                                   config.get("long_break_sound_volume"))

            self.load_random_sounds()

        # 每次都更新样式和按钮状态
        self.update_styles()
        self.update_button_states(self.timer_engine.state)
        self.update_timer_display(self.timer_engine.get_formatted_time())

        if not config.get("compact_mode_enabled"):
            QTimer.singleShot(1, self.adjustSize)

    def update_ui_visibility(self):
        is_compact = config.get("compact_mode_enabled")

        self.main_frame.setVisible(True)

        self.custom_text_label.setVisible(not is_compact and config.get("show_custom_text"))
        self.app_title_label.setVisible(not is_compact and config.get("show_app_title"))
        self.controls_layout_widget.setVisible(not is_compact)
        self.bottom_layout_widget.setVisible(not is_compact)

        if is_compact:
            self.timer_label.setMinimumHeight(0)
            self.setMinimumSize(150, 80)
            self.setMaximumSize(16777215, 16777215)
            self.setFixedSize(QSize(0, 0).expandedTo(self.minimumSize()))
            self.resize(250, 150)
            self.main_layout.setContentsMargins(0, 0, 0, 0)
        else:
            self.timer_label.setMinimumHeight(100)
            self.setMinimumSize(340, 100)
            self.setMaximumSize(340, 500)
            self.setFixedWidth(340)
            self.main_layout.setContentsMargins(20, 20, 20, 20)
            self.main_layout.setSpacing(15)

    def _configure_player(self, player_tuple, path, volume):
        player, audio_output = player_tuple
        if path and os.path.exists(path):
            player.setSource(QUrl.fromLocalFile(path))
        else:
            player.setSource(QUrl())

        safe_volume = volume if volume is not None else 80
        audio_output.setVolume(safe_volume / 100.0)

    def load_random_sounds(self):
        self.random_sound_list = []
        folder_path = config.get("random_sound_folder_path")
        if config.get("random_sound_enabled") and folder_path and os.path.isdir(folder_path):
            supported_formats = ('.mp3', '.wav', '.ogg', '.flac')
            for filename in os.listdir(folder_path):
                if filename.lower().endswith(supported_formats):
                    self.random_sound_list.append(os.path.join(folder_path, filename))

    def update_styles(self):
        phase_colors = {
            PomodoroPhase.WORK: config.get("work_color"),
            PomodoroPhase.BREAK: config.get("break_color"),
            PomodoroPhase.LONG_BREAK: config.get("long_break_color")
        }
        current_bg_color = phase_colors.get(self.timer_engine.phase, "#000000")

        current_text_color = config.get("timer_text_color")
        custom_text_color = config.get("custom_text_color")
        custom_text_font_size = config.get("custom_text_font_size")
        custom_text_font_family = config.get("custom_text_font_family")
        self.custom_text_label.setFont(QFont(custom_text_font_family, custom_text_font_size))

        is_compact = config.get("compact_mode_enabled")

        if is_compact:
            main_frame_bg = current_bg_color
            main_frame_border = "none"
            timer_label_bg = "transparent"
            timer_padding = "0px"
        else:
            main_frame_bg = "white"
            main_frame_border = "1px solid #E0E0E0"
            timer_label_bg = current_bg_color
            timer_padding = "10px"

        style = f"""
            #mainFrame {{
                background-color: {main_frame_bg};
                border-radius: 15px;
                border: {main_frame_border};
            }}
            #timerLabel {{
                color: {current_text_color};
                background-color: {timer_label_bg};
                border-radius: 10px;
                padding: {timer_padding};
            }}
            #customTextLabel {{ color: {custom_text_color}; }}
            #appTitleLabel {{ color: black; font-size: 19px; font-weight: bold; }}
            #controlButton {{ background-color: {current_bg_color}; color: white; border: none; padding: 8px 16px; font-size: 14px; border-radius: 5px; }}
            #controlButton:hover {{ background-color: {QColor(current_bg_color).darker(110).name()}; }}
            #iconButton {{ border: none; background-color: transparent; border-radius: 13px; }}
            #iconButton:hover {{ background-color: #f0f0f0; }}
            #exitButton {{ background-color: #ff5f57; border: none; border-radius: 13px; }}
            #exitButton:hover {{ background-color: #e0443e; }}
        """
        self.setStyleSheet(style)

    def update_timer_display(self, time_str):
        self.timer_label.setText(time_str)

    def show_notification(self, title, text):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        screen = QApplication.primaryScreen()
        if screen:
            center_point = screen.geometry().center()
            hint_size = msg_box.sizeHint()
            msg_box.move(int(center_point.x() - hint_size.width() / 2), int(center_point.y() - hint_size.height() / 2))

        msg_box.exec()

        if config.get("auto_cycle_enabled"):
            QTimer.singleShot(500, self.start_button.click)

    def stop_all_sounds(self):
        self.work_player[0].stop()
        self.break_player[0].stop()
        self.long_break_player[0].stop()
        self.random_player[0].stop()

    def play_notification_sound(self, phase):
        if not config.get("sound_notification"):
            return

        self.stop_all_sounds()

        if config.get("random_sound_enabled") and self.random_sound_list:
            player_to_play, audio_output = self.random_player
            random_sound_path = random.choice(self.random_sound_list)
            player_to_play.setSource(QUrl.fromLocalFile(random_sound_path))
            random_volume = config.get("random_sound_volume")
            safe_random_volume = random_volume if random_volume is not None else 80
            audio_output.setVolume(safe_random_volume / 100.0)
            player_to_play.play()
        else:
            player_tuple_to_play = None
            if phase == PomodoroPhase.WORK:
                player_tuple_to_play = self.work_player
            elif phase == PomodoroPhase.BREAK:
                player_tuple_to_play = self.break_player
            elif phase == PomodoroPhase.LONG_BREAK:
                player_tuple_to_play = self.long_break_player

            if player_tuple_to_play:
                player, _ = player_tuple_to_play
                if not player.source().isEmpty():
                    player.play()

    def handle_phase_finish(self, phase):
        self.play_notification_sound(phase)

        if config.get("desktop_notification"):
            text_map = {
                PomodoroPhase.WORK: config.get("work_finish_text"),
                PomodoroPhase.BREAK: config.get("break_finish_text"),
            }
            title_map = {
                PomodoroPhase.WORK: "工作完成！",
                PomodoroPhase.BREAK: "休息结束！",
            }
            text = text_map.get(phase)
            title = title_map.get(phase)
            if text and title:
                self.show_notification(title, text)
        elif config.get("auto_cycle_enabled"):
            QTimer.singleShot(500, self.start_button.click)

    def handle_cycle_finish(self):
        self.play_notification_sound(PomodoroPhase.LONG_BREAK)

        if config.get("desktop_notification"):
            title = "一轮完成！"
            text = config.get("long_break_finish_text")
            self.show_notification(title, text)
        elif config.get("auto_cycle_enabled"):
            pass

    def update_button_states(self, state):
        is_pristine_state = not self.has_run_once

        self.start_button.setEnabled(state != TimerState.RUNNING)
        self.pause_button.setEnabled(not is_pristine_state)
        self.reset_button.setEnabled(not is_pristine_state)
        self.update_styles()

    def handle_start_click(self):
        self.has_run_once = True
        self.timer_engine.start_timer()

    def handle_pause_click(self):
        self.timer_engine.pause_timer()
        self.stop_all_sounds()

    def handle_reset_click(self):
        self.has_run_once = False
        self.timer_engine.reset_timer()
        self.stop_all_sounds()

    # --- 修改: 修改 open_settings ---
    def open_settings(self):
        if self.settings_dialog is None:
            self.settings_dialog = SettingsDialog(self)
            # 当设置改变时，执行一次“全部刷新”
            self.settings_dialog.settings_changed.connect(lambda: self.apply_settings(full_reload=True))
        self.settings_dialog.load_settings()
        self.settings_dialog.exec()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.drag_position is not None and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_position = None
        event.accept()

    # --- 修改: 修改 mouseDoubleClickEvent ---
    def mouseDoubleClickEvent(self, event):
        is_compact = config.get("compact_mode_enabled")

        if not is_compact and self.timer_label.underMouse():
            config.set("compact_mode_enabled", True)
            # 只刷新UI，不重新加载声音等配置
            self.apply_settings(full_reload=False)
        elif is_compact:
            config.set("compact_mode_enabled", False)
            # 只刷新UI，不重新加载声音等配置
            self.apply_settings(full_reload=False)

        super().mouseDoubleClickEvent(event)

    def resizeEvent(self, event):
        if config.get("compact_mode_enabled"):
            font_size = max(12, int(min(self.width(), self.height()) / 2.2))
            self.timer_label.setFont(QFont("Arial", font_size, QFont.Weight.Bold))
        else:
            self.timer_label.setFont(QFont("Arial", 52, QFont.Weight.Bold))
        return super().resizeEvent(event)