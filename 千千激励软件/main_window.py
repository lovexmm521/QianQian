import os
import random
import logging
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QFileDialog, QMessageBox, QFrame,
    QGroupBox, QSpinBox, QCheckBox, QSizePolicy, QMenu, QTabWidget, QFormLayout,
    QSystemTrayIcon, QStyle
)
from PyQt6.QtCore import Qt, QSize, QUrl, QPoint, pyqtSignal, QTimer, QPropertyAnimation, QSettings
from PyQt6.QtGui import (QIcon, QDesktopServices, QAction, QPixmap,
                         QTransform, QMouseEvent, QCloseEvent, QScreen)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget

from settings_window import SettingsTab
from item_settings_dialog import ItemSettingsDialog


# --- 桌面悬浮窗 ---
class DesktopWidget(QWidget):
    widget_closed = pyqtSignal(QWidget)
    video_finished = pyqtSignal()

    def __init__(self, main_window_ref, file_settings, global_settings, playback_settings, parent=None):
        super().__init__(parent)
        self.main_window_ref = main_window_ref
        self.file_settings = file_settings
        self.global_settings = global_settings
        self.playback_settings = playback_settings
        self.offset = QPoint()
        self.animation = None
        self.pos_animation = None
        self.is_closing = False

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.media_player = None
        self.audio_output = None
        self.image_label = None
        self.original_pixmap = None

        self.setup_media()
        self.apply_transformations()
        self.setup_animation()

    def setup_media(self):
        file_path = self.file_settings['path']
        is_image = any(file_path.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.bmp', '.gif'])

        if is_image:
            self.image_label = QLabel()
            self.original_pixmap = QPixmap(file_path)
            self.image_label.setPixmap(self.original_pixmap)
            self.main_layout.addWidget(self.image_label)
        else:
            video_widget = QVideoWidget()
            self.media_player = QMediaPlayer()
            self.audio_output = QAudioOutput()
            saved_volume = self.file_settings.get('volume', 0.75)
            self.audio_output.setVolume(saved_volume)
            self.media_player.setAudioOutput(self.audio_output)
            self.media_player.setVideoOutput(video_widget)
            self.media_player.setSource(QUrl.fromLocalFile(file_path))
            self.media_player.mediaStatusChanged.connect(self.handle_media_status)
            self.main_layout.addWidget(video_widget)
            self.media_player.play()

    def handle_media_status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia and self.media_player:
            logging.info("Video finished playback.")
            self.video_finished.emit()

    def setup_animation(self):
        if self.file_settings.get('keyframe_enabled', False):
            start_pos_list = self.file_settings.get('keyframe_start_pos', [0, 0])
            end_pos_list = self.file_settings.get('keyframe_end_pos', [100, 100])
            duration_sec = self.file_settings.get('keyframe_duration', 5)

            start_pos = QPoint(start_pos_list[0], start_pos_list[1])
            end_pos = QPoint(end_pos_list[0], end_pos_list[1])

            self.move(start_pos)

            self.pos_animation = QPropertyAnimation(self, b"pos")
            self.pos_animation.setDuration(duration_sec * 1000)
            self.pos_animation.setStartValue(start_pos)
            self.pos_animation.setEndValue(end_pos)

    def apply_transformations(self):
        use_global = self.global_settings['enabled']
        rotation = self.file_settings['rotation']
        is_image = self.image_label is not None
        scale = self.file_settings['scale'] if is_image else 1.0

        if is_image and self.original_pixmap and not self.original_pixmap.isNull():
            temp_pixmap = self.original_pixmap
            if use_global:
                is_landscape = temp_pixmap.width() > temp_pixmap.height()
                target_size = self.global_settings['landscape_size'] if is_landscape else self.global_settings[
                    'portrait_size']
            elif self.file_settings.get('width') and self.file_settings.get('height'):
                target_size = QSize(self.file_settings['width'], self.file_settings['height'])
            else:
                is_landscape = temp_pixmap.width() > temp_pixmap.height()
                target_size = self.global_settings['landscape_size'] if is_landscape else self.global_settings[
                    'portrait_size']

            scaled_size = QSize(int(target_size.width() * scale), int(target_size.height() * scale))
            transform = QTransform().rotate(rotation)
            final_pixmap = temp_pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
            final_pixmap = final_pixmap.scaled(scaled_size, Qt.AspectRatioMode.KeepAspectRatio,
                                               Qt.TransformationMode.SmoothTransformation)
            self.image_label.setPixmap(final_pixmap)
            self.setFixedSize(final_pixmap.size())
        elif self.media_player:
            if use_global:
                is_landscape = self.file_settings['aspect_ratio'] > 1
                target_size = self.global_settings['landscape_size'] if is_landscape else self.global_settings[
                    'portrait_size']
            elif self.file_settings.get('width'):
                target_size = QSize(self.file_settings['width'], self.file_settings['height'])
            else:
                is_landscape = self.file_settings['aspect_ratio'] > 1
                target_size = self.global_settings['landscape_size'] if is_landscape else self.global_settings[
                    'portrait_size']

            scaled_size = QSize(int(target_size.width() * scale), int(target_size.height() * scale))
            self.setFixedSize(scaled_size)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.addAction("删除此窗口", self.close)
        menu.exec(self.mapToGlobal(event.pos()))

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.offset = event.pos()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.move(self.pos() + event.pos() - self.offset)

    def showEvent(self, event):
        if self.playback_settings.get('use_fade_effect', False):
            self.setWindowOpacity(0.0)
            self.animation = QPropertyAnimation(self, b"windowOpacity", self)
            self.animation.setDuration(500)
            self.animation.setStartValue(0.0)
            self.animation.setEndValue(1.0)
            self.animation.start()

        if self.pos_animation:
            self.pos_animation.start()

        super().showEvent(event)

    def close(self):
        if self.playback_settings.get('use_fade_effect', False) and not self.is_closing:
            self.is_closing = True
            self.animation = QPropertyAnimation(self, b"windowOpacity", self)
            self.animation.setDuration(500)
            self.animation.setStartValue(self.windowOpacity())
            self.animation.setEndValue(0.0)
            self.animation.finished.connect(self.perform_cleanup_and_close)
            self.animation.start()
        else:
            self.perform_cleanup_and_close()

    def perform_cleanup_and_close(self):
        if self.media_player:
            self.media_player.stop()
            self.media_player.setVideoOutput(None)
            self.media_player.setAudioOutput(None)
            self.media_player.setSource(QUrl())
            self.media_player = None
        self.widget_closed.emit(self)
        super().close()


# --- 主应用窗口 ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("千千激励软件")
        self.media_files = []
        self.active_desktop_widgets = []
        self.playback_settings = {}
        self.is_playing = False
        self.current_playback_index = -1
        self.shuffled_playlist = []
        self.music_files_in_folder = []
        self.playback_timer = QTimer(self)
        self.playback_timer.timeout.connect(self.show_next_item)
        self.bg_music_player = QMediaPlayer()
        self.bg_audio_output = QAudioOutput()
        self.bg_music_player.setAudioOutput(self.bg_audio_output)
        self.setStyleSheet("""
            QPushButton {
                background-color: #AFEEEE; border: 1px solid #9AC0CD;
                padding: 6px 12px; border-radius: 5px;
            }
            QPushButton:hover { background-color: #98E0E0; }
            QListWidget {
                background-color: #FFFFFF; border: 1px solid #B0C4DE;
                border-radius: 5px;
            }
            QGroupBox { border: 1px solid #B0C4DE; border-radius: 5px; margin-top: 1ex; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px; }
            QSpinBox { padding: 4px; }
        """)
        self.setup_tabs()
        self.setup_shortcuts()
        self.setup_tray_icon()
        self.load_settings()

    def setup_shortcuts(self):
        close_all_action = QAction(self)
        close_all_action.setShortcut(Qt.Key.Key_Escape)
        close_all_action.triggered.connect(self.close_all_desktop_widgets)
        self.addAction(close_all_action)

    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        default_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray_icon.setIcon(default_icon)
        self.tray_icon.setToolTip("千千激励软件")

        tray_menu = QMenu()
        show_action = tray_menu.addAction("显示主界面")
        show_action.triggered.connect(self.show)
        quit_action = tray_menu.addAction("退出")
        quit_action.triggered.connect(self.close)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()

    def set_tray_icon(self, icon):
        self.tray_icon.setIcon(icon)

    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.showNormal()

    def setup_tabs(self):
        tab_widget = QTabWidget()
        self.setCentralWidget(tab_widget)
        main_tab = QWidget()
        self.setup_main_tab(main_tab)
        tab_widget.addTab(main_tab, "主界面")
        self.settings_tab = SettingsTab()
        self.settings_tab.settings_changed.connect(self.update_playback_settings)
        tab_widget.addTab(self.settings_tab, "设置")

    def setup_main_tab(self, main_tab):
        layout = QVBoxLayout(main_tab)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        self.file_list_widget = QListWidget()
        self.file_list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_list_widget.customContextMenuRequested.connect(self.show_list_context_menu)

        buttons_layout = QHBoxLayout()
        add_file_btn = QPushButton("添加文件")
        add_file_btn.clicked.connect(self.add_files)
        add_folder_btn = QPushButton("添加文件夹")
        add_folder_btn.clicked.connect(self.add_folder)
        remove_btn = QPushButton("删除选中")
        remove_btn.clicked.connect(lambda: self.remove_file())
        buttons_layout.addWidget(add_file_btn)
        buttons_layout.addWidget(add_folder_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(remove_btn)

        self.setup_global_settings(layout)

        self.play_pause_button = QPushButton("🚀 开始播放")
        self.play_pause_button.setStyleSheet("padding: 12px; font-size: 14pt; background-color: #90EE90;")
        self.play_pause_button.clicked.connect(self.toggle_playback)

        layout.addWidget(QLabel("媒体文件列表:"))
        layout.addWidget(self.file_list_widget)
        layout.addLayout(buttons_layout)
        layout.addWidget(self.play_pause_button)

    def update_playback_settings(self, settings):
        self.playback_settings = settings

        bg_volume = settings.get('bg_volume', 100) / 100.0
        self.bg_audio_output.setVolume(bg_volume)

        use_folder = settings.get('use_music_folder', False)

        try:
            self.bg_music_player.mediaStatusChanged.disconnect()
        except TypeError:
            pass

        if use_folder:
            folder_path = settings.get('music_folder_path', "")
            self.load_music_from_folder(folder_path)
            self.bg_music_player.mediaStatusChanged.connect(self.handle_bg_music_status)
        else:
            self.music_files_in_folder.clear()
            music_path = settings.get('music_path', "")
            if music_path and os.path.exists(music_path):
                self.bg_music_player.setSource(QUrl.fromLocalFile(music_path))
                self.bg_music_player.mediaStatusChanged.connect(
                    lambda s: self.bg_music_player.play() if s == QMediaPlayer.MediaStatus.EndOfMedia else None
                )
            else:
                self.bg_music_player.setSource(QUrl())

    def load_music_from_folder(self, folder_path):
        self.music_files_in_folder.clear()
        if folder_path and os.path.isdir(folder_path):
            supported_exts = ['.mp3', '.wav', '.ogg']
            for filename in os.listdir(folder_path):
                if any(filename.lower().endswith(ext) for ext in supported_exts):
                    self.music_files_in_folder.append(os.path.join(folder_path, filename))
            logging.info(f"从文件夹 '{folder_path}' 加载了 {len(self.music_files_in_folder)} 个音乐文件。")
        else:
            logging.warning(f"音乐文件夹路径无效或不存在: '{folder_path}'")

    def handle_bg_music_status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            logging.info("背景音乐播放结束，准备播放下一首随机歌曲。")
            self.play_next_random_song()

    def play_next_random_song(self):
        if self.music_files_in_folder and self.is_playing:
            song_path = random.choice(self.music_files_in_folder)
            self.bg_music_player.setSource(QUrl.fromLocalFile(song_path))
            self.bg_music_player.play()
            logging.info(f"正在播放随机背景音乐: {os.path.basename(song_path)}")
        else:
            self.bg_music_player.stop()

    def toggle_playback(self):
        if self.is_playing:
            self.stop_playback()
        else:
            self.start_playback()

    def start_playback(self):
        if not self.media_files:
            QMessageBox.warning(self, "提示", "请先添加至少一个媒体文件！")
            return
        self.is_playing = True
        self.play_pause_button.setText("⏹️ 停止播放")
        self.play_pause_button.setStyleSheet("padding: 12px; font-size: 14pt; background-color: #F08080;")

        if self.playback_settings.get('is_random_order', True):
            self.shuffled_playlist = list(range(len(self.media_files)))
            random.shuffle(self.shuffled_playlist)
        else:
            self.current_playback_index = -1

        use_folder = self.playback_settings.get('use_music_folder', False)
        if use_folder:
            if self.music_files_in_folder:
                self.play_next_random_song()
        elif self.playback_settings.get('music_path'):
            self.bg_music_player.play()

        self.show_next_item()
        self.hide()

    def stop_playback(self):
        self.is_playing = False
        self.play_pause_button.setText("🚀 开始播放")
        self.play_pause_button.setStyleSheet("padding: 12px; font-size: 14pt; background-color: #90EE90;")
        self.playback_timer.stop()
        self.bg_music_player.stop()
        if self.bg_music_player.audioOutput():
            self.bg_music_player.audioOutput().setMuted(False)
        self.close_all_desktop_widgets()
        self.showNormal()

    def get_next_item_index(self):
        if self.playback_settings.get('is_random_order', True):
            if not self.shuffled_playlist:
                if self.playback_settings.get('loop_playback', True):
                    self.shuffled_playlist = list(range(len(self.media_files)))
                    random.shuffle(self.shuffled_playlist)
                else:
                    return None
            return self.shuffled_playlist.pop(0)
        else:
            next_index = self.current_playback_index + 1
            if next_index >= len(self.media_files):
                if self.playback_settings.get('loop_playback', True):
                    return 0
                else:
                    return None
            return next_index

    def show_next_item(self):
        self.close_all_desktop_widgets()

        if not self.is_playing or not self.media_files:
            self.stop_playback()
            return

        self.playback_timer.stop()

        next_index = self.get_next_item_index()

        if next_index is None:
            self.stop_playback()
            return

        self.current_playback_index = next_index

        file_settings = self.media_files[self.current_playback_index]
        is_image = any(file_settings['path'].lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.bmp', '.gif'])

        if self.playback_settings.get('mute_on_video', True):
            if is_image:
                self.bg_music_player.audioOutput().setMuted(False)
            else:
                self.bg_music_player.audioOutput().setMuted(True)
        else:
            self.bg_music_player.audioOutput().setMuted(False)

        global_settings = {
            'enabled': self.global_enabled_check.isChecked(),
            'landscape_size': QSize(self.ls_width_spin.value(), self.ls_height_spin.value()),
            'portrait_size': QSize(self.pt_width_spin.value(), self.pt_height_spin.value())
        }

        widget = DesktopWidget(self, file_settings, global_settings, self.playback_settings)
        widget.widget_closed.connect(self.remove_widget_from_list)

        if not file_settings.get('keyframe_enabled', False):
            if self.playback_settings.get('position_mode') == 'fixed':
                widget.move(self.playback_settings.get('fixed_pos', QPoint(100, 100)))
            else:
                screen = QApplication.primaryScreen().availableGeometry()
                x = random.randint(screen.left(), max(screen.left(), screen.right() - widget.width()))
                y = random.randint(screen.top(), max(screen.top(), screen.bottom() - widget.height()))
                widget.move(x, y)

        widget.show()
        self.active_desktop_widgets.append(widget)

        if is_image:
            interval = self.playback_settings.get('interval', 5) * 1000
            self.playback_timer.start(interval)
        else:
            widget.video_finished.connect(self.show_next_item)

    def close_all_desktop_widgets(self):
        for widget in list(self.active_desktop_widgets):
            widget.close()

    def closeEvent(self, event: QCloseEvent):
        self.save_settings()
        self.stop_playback()
        self.tray_icon.hide()
        super().closeEvent(event)

    def setup_global_settings(self, parent_layout):
        group_box = QGroupBox("全局尺寸设置")
        group_layout = QVBoxLayout(group_box)

        self.global_enabled_check = QCheckBox("启用全局尺寸 (覆盖所有自定义尺寸)")

        form_layout = QFormLayout()
        self.ls_width_spin = QSpinBox()
        self.ls_width_spin.setRange(100, 5000)
        self.ls_width_spin.setValue(640)
        self.ls_height_spin = QSpinBox()
        self.ls_height_spin.setRange(100, 5000)
        self.ls_height_spin.setValue(360)

        self.pt_width_spin = QSpinBox()
        self.pt_width_spin.setRange(100, 5000)
        self.pt_width_spin.setValue(300)
        self.pt_height_spin = QSpinBox()
        self.pt_height_spin.setRange(100, 5000)
        self.pt_height_spin.setValue(500)

        ls_layout = QHBoxLayout()
        ls_layout.addWidget(self.ls_width_spin);
        ls_layout.addWidget(QLabel("x"));
        ls_layout.addWidget(self.ls_height_spin)
        pt_layout = QHBoxLayout()
        pt_layout.addWidget(self.pt_width_spin);
        pt_layout.addWidget(QLabel("x"));
        pt_layout.addWidget(self.pt_height_spin)

        form_layout.addRow("横图/视频 (宽 x 高):", ls_layout)
        form_layout.addRow("竖图/视频 (宽 x 高):", pt_layout)

        group_layout.addWidget(self.global_enabled_check)
        group_layout.addLayout(form_layout)
        parent_layout.addWidget(group_box)

    def add_files(self, *args):
        files, _ = QFileDialog.getOpenFileNames(self, "选择图片或视频文件", "",
                                                "媒体文件 (*.png *.jpg *.jpeg *.gif *.bmp *.mp4 *.avi *.mov *.mkv)")
        for file_path in files: self.add_file_item(file_path)

    def add_folder(self, *args):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            for filename in os.listdir(folder):
                if any(filename.lower().endswith(ext) for ext in
                       ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.mp4', '.avi', '.mov', '.mkv']):
                    self.add_file_item(os.path.join(folder, filename))

    def add_file_item(self, file_path):
        if any(f['path'] == file_path for f in self.media_files): return
        pixmap = QPixmap(file_path)
        aspect = pixmap.width() / pixmap.height() if not pixmap.isNull() and pixmap.height() > 0 else 16.0 / 9.0
        settings = {
            'path': file_path, 'width': None, 'height': None, 'rotation': 0,
            'scale': 1.0, 'aspect_ratio': aspect, 'volume': 0.75,
            'keyframe_enabled': False, 'keyframe_start_pos': [0, 0],
            'keyframe_end_pos': [100, 100], 'keyframe_duration': 5
        }
        self.media_files.append(settings)
        item = QListWidgetItem(self.file_list_widget)
        widget = self.create_file_item_widget(file_path, len(self.media_files) - 1)
        item.setSizeHint(widget.sizeHint())
        self.file_list_widget.addItem(item)
        self.file_list_widget.setItemWidget(item, widget)

    def rebuild_list_from_data(self):
        self.file_list_widget.clear()
        for i, file_data in enumerate(self.media_files):
            item = QListWidgetItem(self.file_list_widget)
            widget = self.create_file_item_widget(file_data['path'], i)
            item.setSizeHint(widget.sizeHint())
            self.file_list_widget.addItem(item)
            self.file_list_widget.setItemWidget(item, widget)

    def create_file_item_widget(self, file_path, index):
        widget = QWidget()
        layout = QHBoxLayout(widget);
        layout.setContentsMargins(5, 5, 5, 5)
        label = QLabel(os.path.basename(file_path));
        label.setToolTip(file_path)
        button = QPushButton("自定义");
        button.setFixedSize(70, 28)
        button.clicked.connect(lambda: self.open_item_settings(index))
        layout.addWidget(label);
        layout.addStretch();
        layout.addWidget(button)
        return widget

    def open_item_settings(self, index):
        if not (0 <= index < len(self.media_files)): return
        dialog = ItemSettingsDialog(self.media_files[index], self)
        if dialog.exec():
            self.media_files[index] = dialog.get_settings()
            QMessageBox.information(self, "成功", "自定义设置已保存！")

    def remove_file(self, row=None):
        row = self.file_list_widget.currentRow() if row is None else row
        if row < 0: return
        self.file_list_widget.takeItem(row)
        del self.media_files[row]
        self.rebuild_list_from_data()

    def clear_all_files(self):
        if QMessageBox.question(self, "确认", "确定要清空所有文件吗？") == QMessageBox.StandardButton.Yes:
            self.media_files.clear()
            self.file_list_widget.clear()

    def remove_widget_from_list(self, widget):
        if widget in self.active_desktop_widgets:
            self.active_desktop_widgets.remove(widget)
            widget.deleteLater()

    def show_list_context_menu(self, position):
        menu = QMenu()
        item = self.file_list_widget.itemAt(position)
        if item:
            menu.addAction("删除此文件", lambda: self.remove_file(self.file_list_widget.row(item)))
            menu.addSeparator()
        menu.addAction("添加文件...", self.add_files)
        menu.addAction("添加文件夹...", self.add_folder)
        menu.addSeparator()
        clear_action = menu.addAction("清空所有文件")
        clear_action.setEnabled(bool(self.media_files))
        clear_action.triggered.connect(self.clear_all_files)
        menu.exec(self.file_list_widget.mapToGlobal(position))

    def save_settings(self):
        settings = QSettings("config.ini", QSettings.Format.IniFormat)
        settings.setValue("geometry", self.saveGeometry())

        settings.beginGroup("GlobalSettings")
        settings.setValue("enabled", self.global_enabled_check.isChecked())
        settings.setValue("ls_width", self.ls_width_spin.value())
        settings.setValue("ls_height", self.ls_height_spin.value())
        settings.setValue("pt_width", self.pt_width_spin.value())
        settings.setValue("pt_height", self.pt_height_spin.value())
        settings.endGroup()

        settings.beginGroup("PlaybackSettings")
        for key, value in self.playback_settings.items():
            if isinstance(value, QPoint):
                settings.setValue(key, f"{value.x()},{value.y()}")
            else:
                settings.setValue(key, value)
        settings.endGroup()

        settings.setValue("media_files", json.dumps(self.media_files, ensure_ascii=False))
        logging.info("所有设置已保存到 config.ini。")

    def load_settings(self):
        settings = QSettings("config.ini", QSettings.Format.IniFormat)

        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

        settings.beginGroup("GlobalSettings")
        self.global_enabled_check.setChecked(settings.value("enabled", False, type=bool))
        self.ls_width_spin.setValue(settings.value("ls_width", 640, type=int))
        self.ls_height_spin.setValue(settings.value("ls_height", 360, type=int))
        self.pt_width_spin.setValue(settings.value("pt_width", 300, type=int))
        self.pt_height_spin.setValue(settings.value("pt_height", 500, type=int))
        settings.endGroup()

        loaded_playback_settings = {}
        settings.beginGroup("PlaybackSettings")
        for key in settings.childKeys():
            loaded_playback_settings[key] = settings.value(key)
        settings.endGroup()

        if 'fixed_pos' in loaded_playback_settings and isinstance(loaded_playback_settings['fixed_pos'], str):
            try:
                coords = loaded_playback_settings['fixed_pos'].split(',')
                loaded_playback_settings['fixed_pos'] = QPoint(int(coords[0]), int(coords[1]))
            except:
                loaded_playback_settings['fixed_pos'] = QPoint(100, 100)

        type_map = {
            'interval': int, 'is_random_order': bool,
            'use_fade_effect': bool, 'loop_playback': bool,
            'mute_on_video': bool,
            'bg_volume': int, 'use_music_folder': bool
        }
        for key, t in type_map.items():
            if key in loaded_playback_settings:
                try:
                    val = loaded_playback_settings[key]
                    if t is bool:
                        loaded_playback_settings[key] = val in ['true', True]
                    else:
                        loaded_playback_settings[key] = t(val)
                except (ValueError, TypeError):
                    pass

        if loaded_playback_settings:
            self.settings_tab.apply_settings(loaded_playback_settings)

        try:
            files_json = settings.value("media_files", "[]")
            self.media_files = json.loads(files_json)
            self.rebuild_list_from_data()
        except json.JSONDecodeError:
            logging.error("无法解析已保存的媒体文件列表。")
            self.media_files = []

        logging.info("已从 config.ini 加载设置。")

