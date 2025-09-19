import sys
import os
import json
import logging
import traceback
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QPushButton, QTabWidget, QMessageBox)
from PyQt6.QtGui import QPixmap, QFont, QIcon, QColor, QTransform, QPainter
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QSize, QRectF

from PIL import Image, ImageDraw, ImageFont

# 导入拆分后的模块
from main_tab import MainTab
from settings_tab import SettingsTab, ImagePreviewDialog
from wealth_log_tab import WealthLogTab
from style_settings_dialog import StyleSettingsDialog
from qianqian_rewards_tab import RewardsTab
from wealth_rules_tab import WealthRulesTab
from about_tab import AboutTab

# --- 全局配置 ---
APP_TITLE = "千千成就软件"
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 750
CONFIG_FILE = "config.json"
WEALTH_LOG_FILE = "wealth_log.json"
ERROR_LOG_FILE = "app_errors.log"
REWARDS_DIR = "rewards"


# --- 日志记录设置 ---
def setup_logging():
    logging.basicConfig(
        level=logging.ERROR,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename=ERROR_LOG_FILE,
        filemode='w'
    )


def handle_exception(exc_type, exc_value, exc_traceback):
    """全局异常处理器"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logging.error("未捕获的异常:\n%s", error_msg)

    # 显示一个用户友好的错误对话框
    error_box = QMessageBox()
    error_box.setIcon(QMessageBox.Icon.Critical)
    error_box.setText("程序遇到了一个意外错误并需要关闭。")
    error_box.setInformativeText(f"详细信息已记录在 {ERROR_LOG_FILE} 文件中。")
    error_box.setWindowTitle("程序错误")
    error_box.setStandardButtons(QMessageBox.StandardButton.Ok)
    error_box.exec()

    QApplication.quit()


# --- PyInstaller 资源路径辅助函数 ---
def resource_path(relative_path):
    """ 获取资源的绝对路径，无论是开发环境还是打包后 """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# --- 清新风格的样式表 ---
STYLESHEET = """
QWidget {
    font-family: 'Microsoft YaHei', 'Segoe UI', Arial, sans-serif;
    font-size: 14px;
    background-color: #F0F8FF;
    color: #333;
}
QMainWindow {
    background-color: #F0F8FF;
}
QTabWidget::pane {
    border: 1px solid #B0C4DE;
    border-radius: 5px;
}
QTabBar::tab {
    background: #E0FFFF;
    border: 1px solid #B0C4DE;
    border-bottom-color: #C0C0C0;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    min-width: 10ex;
    padding: 10px;
    margin-right: 2px;
    font-weight: bold;
}
QTabBar::tab:selected {
    background: #ADD8E6;
    border-color: #909090;
    border-bottom-color: #ADD8E6;
}
QLineEdit, QDateEdit, QSpinBox, QFontComboBox, QComboBox {
    border: 1px solid #B0C4DE;
    border-radius: 5px;
    padding: 8px;
    background-color: #FFF;
}
QLineEdit:focus, QDateEdit:focus, QSpinBox:focus, QFontComboBox:focus, QComboBox:focus {
    border: 1px solid #4682B4;
}
QPushButton {
    background-color: #87CEFA;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 5px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #4682B4;
}
QPushButton:pressed {
    background-color: #4169E1;
}
#toggleButton {
    font-size: 18px;
    padding: 0;
    font-weight: bold;
    background-color: #B0C4DE;
}
#toggleButton:hover {
    background-color: #778899;
}
QTableWidget {
    border: 1px solid #B0C4DE;
    gridline-color: #D3D3D3;
}
QHeaderView::section {
    background-color: #ADD8E6;
    padding: 4px;
    border: 1px solid #B0C4DE;
    font-size: 14px;
}
#tableButton {
    padding: 5px 8px;
    font-size: 12px;
}
QProgressBar {
    border: 1px solid #B0C4DE;
    border-radius: 5px;
    text-align: center;
    background-color: #FFFFFF;
    height: 24px;
}
QProgressBar::chunk {
    background-color: #87CEFA;
    border-radius: 4px;
}
#mainCard {
    background-color: #FFFFFF;
    border-radius: 15px;
    border: 1px solid #E0E0E0;
    padding: 20px;
}
#comparisonCard {
    background-color: #FFFFFF;
    border-radius: 10px;
    border: 1px dashed #B0C4DE;
    margin-top: 15px;
    padding: 15px;
}
#levelIcon {
    border-radius: 10px;
    border: 3px solid #87CEFA;
}
#levelNameLabel, #wealthValueLabel, #progressLabel, #compNameLabel, #compProgressLabel {
    background-color: transparent;
}
#levelNameLabel {
    font-size: 28px;
    font-weight: bold;
    color: #4682B4;
}
#wealthValueLabel {
    font-size: 20px;
    color: #FFA500;
    font-weight: bold;
}
#progressLabel {
    font-size: 14px;
    color: #555;
}
#planCard {
    background-color: #FFFFFF;
    border-radius: 10px;
    border: 1px solid #E0E0E0;
    margin-top: 10px;
    padding: 10px;
}
#planCard QLabel {
    background-color: transparent;
}
"""


class ClickableLabel(QLabel):
    doubleClicked = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit()
        super().mouseDoubleClickEvent(event)


class CroppedPreviewLabel(ClickableLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pixmap_to_draw = None
        self.image_settings = {}

    def set_view(self, pixmap, settings):
        self.pixmap_to_draw = pixmap
        self.image_settings = settings
        self.update()

    def clear_view(self):
        self.pixmap_to_draw = None
        self.image_settings = {}
        self.setPixmap(QPixmap())
        self.update()

    def paintEvent(self, event):
        if not self.pixmap_to_draw or self.pixmap_to_draw.isNull():
            super().paintEvent(event)
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        view_rect = self.contentsRect()

        zoom = self.image_settings.get("zoom", 1.0)
        rotation = self.image_settings.get("rotation", 0)
        center_x = self.image_settings.get("pos_x", self.pixmap_to_draw.width() / 2)
        center_y = self.image_settings.get("pos_y", self.pixmap_to_draw.height() / 2)

        is_default = (
                abs(zoom - 1.0) < 1e-6 and
                rotation % 360 == 0 and
                abs(center_x - self.pixmap_to_draw.width() / 2) < 1e-6 and
                abs(center_y - self.pixmap_to_draw.height() / 2) < 1e-6
        )

        transform = QTransform().rotate(rotation)
        rotated_pixmap = self.pixmap_to_draw.transformed(transform, Qt.TransformationMode.SmoothTransformation)

        if is_default:
            scaled_pix = rotated_pixmap.scaled(view_rect.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                               Qt.TransformationMode.SmoothTransformation)  # 修复
            crop_x = (scaled_pix.width() - view_rect.width()) / 2
            crop_y = (scaled_pix.height() - view_rect.height()) / 2
            cropped_final = scaled_pix.copy(int(crop_x), int(crop_y), view_rect.width(), view_rect.height())
            painter.drawPixmap(view_rect.topLeft(), cropped_final)
        else:
            src_view_w = view_rect.width() / zoom
            src_view_h = view_rect.height() / zoom
            src_top_left_x = center_x - (src_view_w / 2)
            src_top_left_y = center_y - (src_view_h / 2)

            source_rect = QRectF(src_top_left_x, src_top_left_y, src_view_w, src_view_h)
            painter.drawPixmap(QRectF(view_rect), rotated_pixmap, source_rect)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)

        icon_path = resource_path("1.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            self.setWindowIcon(QIcon(QPixmap(64, 64)))

        self.style_config = {}
        self.level_config_data = []
        self.current_reward_level_data = None
        self._is_refreshing = False

        self.setStyleSheet(STYLESHEET)
        self.init_ui()
        self.post_init_connect()

        self.load_app_config()
        self.scan_for_image_conflicts()

        self.settings_tab.load_from_data(self.level_config_data)
        self.wealth_log_tab.update_level_config(self.level_config_data)

        self.apply_all_settings()

        self.wealth_log_tab.refresh_table_and_emit_update()

        self.rewards_tab.load_data()
        self.wealth_rules_tab.load_data()

        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)

    @property
    def term(self):
        return self.style_config.get("term_display_mode", "财富")

    def init_ui(self):
        main_widget = QWidget()
        self.main_layout = QHBoxLayout(main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.main_tab = MainTab()
        self.settings_tab = SettingsTab()
        self.wealth_log_tab = WealthLogTab()
        self.rewards_tab = RewardsTab()
        self.wealth_rules_tab = WealthRulesTab()
        self.about_tab = AboutTab()
        self.tabs.addTab(self.main_tab, "🏆 主界面")
        self.tabs.addTab(self.settings_tab, "🚀 等级设置")
        self.tabs.addTab(self.wealth_log_tab, f"💰 {self.term}日志")
        self.tabs.addTab(self.rewards_tab, "🎁 千千奖励")
        self.tabs.addTab(self.wealth_rules_tab, f"📜 {self.term}规则")
        self.tabs.addTab(self.about_tab, "💖 关于")

        self.side_panel_container = QWidget()
        side_panel_layout = QHBoxLayout(self.side_panel_container)
        side_panel_layout.setContentsMargins(0, 0, 0, 0)
        side_panel_layout.setSpacing(0)

        self.reward_image_display = CroppedPreviewLabel("没有图片")
        self.reward_image_display.doubleClicked.connect(self.open_current_reward_preview)
        self.reward_image_display.setStyleSheet(
            "background-color: transparent; border-left: 1px solid #B0C4DE; padding: 0px;")
        self.reward_image_display.setAlignment(Qt.AlignmentFlag.AlignCenter)

        side_panel_layout.addWidget(self.reward_image_display)
        self.side_panel_container.hide()

        self.toggle_button = QPushButton("◀")
        self.toggle_button.setObjectName("toggleButton")
        self.toggle_button.setFixedSize(25, 80)
        self.toggle_button.clicked.connect(self.toggle_reward_panel)

        self.main_layout.addWidget(self.tabs, 1)
        self.main_layout.addWidget(self.side_panel_container)
        self.setCentralWidget(main_widget)

        self.toggle_button.setParent(self)
        self.toggle_button.raise_()
        self.toggle_button.hide()

    def _update_button_position(self):
        button_x = self.width() - self.toggle_button.width() - 5
        if self.side_panel_container.isVisible():
            button_x -= self.side_panel_container.width()
        button_y = self.height() - self.toggle_button.height() - 25
        self.toggle_button.move(button_x, button_y)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_button_position()

    def open_current_reward_preview(self):
        if not self.current_reward_level_data: return

        image_settings = self.current_reward_level_data.get("reward_image")
        if not image_settings or not image_settings.get("path") or not os.path.exists(image_settings.get("path")):
            return

        dialog = ImagePreviewDialog(image_settings, self, initial_size=self.reward_image_display.size())
        if dialog.exec():
            new_settings = dialog.get_settings()
            self.current_reward_level_data["reward_image"] = new_settings

            for i, level in enumerate(self.level_config_data):
                if level.get("level") == self.current_reward_level_data.get("level"):
                    self.level_config_data[i] = self.current_reward_level_data
                    break

            self.save_app_config()
            self.settings_tab.load_from_data(self.level_config_data)
            self.refresh_main_display()

    def scan_for_image_conflicts(self):
        folder = self.style_config.get("level_image_folder", "level")
        if not os.path.isdir(folder):
            return

        files = os.listdir(folder)
        conflicts = set()
        stems = {}
        for f in files:
            name, ext = os.path.splitext(f)
            ext_lower = ext.lower()
            if ext_lower in ['.jpg', '.png'] and name.isdigit():
                if name in stems:
                    if stems[name] != ext_lower:
                        conflicts.add(name)
                else:
                    stems[name] = ext_lower

        if conflicts:
            sorted_conflicts = sorted(list(conflicts), key=int)
            message = "发现以下等级同时存在 .jpg 和 .png 图片：\n\n"
            message += ", ".join(sorted_conflicts)
            message += "\n\n程序将优先使用 .jpg 图片。"
            QMessageBox.information(self, "图片冲突提示", message)

    def load_app_config(self):
        default_styles = {
            "levelName": {"family": "Microsoft YaHei", "size": 28, "color": "#4682B4"},
            "wealthValue": {"family": "Microsoft YaHei", "size": 20, "color": "#FFA500"},
            "rewardTitle": {"family": "Microsoft YaHei", "size": 18, "color": "#CD5C5C"},
            "rewardText": {"family": "Microsoft YaHei", "size": 16, "color": "#444444"},
            "planTitle": {"family": "Microsoft YaHei", "size": 14, "color": "#333333"},
            "planContent": {"family": "Microsoft YaHei", "size": 14, "color": "#333333"},
            "planRewardText": {"family": "Microsoft YaHei", "size": 14, "color": "#E59866"},
            "rewardCardBackground": "#FFFACD",
            "auto_expand_reward_panel": True,
            "reward_image_display_mode": "current",
            "reward_text_display_mode": "current",
            "progress_bar_mode": "percentage",
            "show_trend_column": False,
            "level_image_folder": "level",
            "countdown_target_date": None,
            "show_countdown": True,
            "show_wealth_rules_tab": True,
            "term_display_mode": "财富"
        }
        default_levels = [
            {"level": 1, "level_name": "初出茅庐", "wealth_threshold": 1000, "reward_text": "解锁【新手上路】称号",
             "reward_image": {"path": ""}},
            {"level": 2, "level_name": "小有成就", "wealth_threshold": 5000, "reward_text": "获得【初入江湖】礼包",
             "reward_image": {"path": ""}},
            {"level": 3, "level_name": "崭露头角", "wealth_threshold": 10000, "reward_text": "奖励【铜质徽章】一枚",
             "reward_image": {"path": ""}},
        ]
        if not os.path.exists(CONFIG_FILE):
            self.level_config_data = default_levels
            self.style_config = default_styles
            self.save_app_config()
            return

        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if isinstance(data, list):
                self.level_config_data = data
                self.style_config = default_styles
            elif isinstance(data, dict):
                self.level_config_data = data.get("levels", default_levels)
                self.style_config = data.get("styles", default_styles)

            # 迁移旧的 "planText" 配置
            if "planText" in self.style_config:
                if "planTitle" not in self.style_config:
                    self.style_config["planTitle"] = self.style_config["planText"]
                if "planContent" not in self.style_config:
                    self.style_config["planContent"] = self.style_config["planText"]
                del self.style_config["planText"]

            for level in self.level_config_data:
                reward_image = level.get("reward_image")
                if isinstance(reward_image, str):
                    level["reward_image"] = {"path": reward_image, "zoom": 1.0, "rotation": 0, "pos_x": 0, "pos_y": 0}
                elif not isinstance(reward_image, dict):
                    level["reward_image"] = {"path": "", "zoom": 1.0, "rotation": 0, "pos_x": 0, "pos_y": 0}

            for key, value in default_styles.items():
                if key not in self.style_config: self.style_config[key] = value

            self.save_app_config()

        except (json.JSONDecodeError, FileNotFoundError):
            QMessageBox.warning(self, "加载错误", "配置文件损坏或不存在，将创建新的默认配置。")
            self.level_config_data = default_levels;
            self.style_config = default_styles;
            self.save_app_config()

    def save_app_config(self):
        combined_config = {"levels": self.level_config_data, "styles": self.style_config}
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f: json.dump(combined_config, f, ensure_ascii=False, indent=4)

    def apply_styles(self):
        ln_style = self.style_config.get("levelName")
        self.main_tab.level_name_label.setStyleSheet(
            f"font-family: '{ln_style['family']}'; font-size: {ln_style['size']}px; color: {ln_style['color']}; font-weight: bold; background-color: transparent;")
        wv_style = self.style_config.get("wealthValue")
        self.main_tab.wealth_value_label.setStyleSheet(
            f"font-family: '{wv_style['family']}'; font-size: {wv_style['size']}px; color: {wv_style['color']}; font-weight: bold; background-color: transparent;")

        r_title_style = self.style_config.get("rewardTitle")
        self.main_tab.reward_title_label.setStyleSheet(
            f"font-family: '{r_title_style['family']}'; font-size: {r_title_style['size']}px; color: {r_title_style['color']}; font-weight: bold; background-color: transparent; border: none;")

        rt_style = self.style_config.get("rewardText")
        self.main_tab.reward_text_label.setStyleSheet(
            f"font-family: '{rt_style['family']}'; font-size: {rt_style['size']}px; color: {rt_style['color']}; background-color: transparent; border: none;")

        bg_color = self.style_config.get("rewardCardBackground", "#FFFACD")
        border_color = QColor(bg_color).darker(110).name()
        self.main_tab.reward_card.setStyleSheet(f"""
            #rewardCard {{
                background-color: {bg_color};
                border-radius: 10px;
                border: 1px solid {border_color};
                margin-top: 15px;
            }}
        """)

        plan_title_style = self.style_config.get("planTitle")
        plan_style_sheet = f"font-family: '{plan_title_style['family']}'; font-size: {plan_title_style['size']}px; color: {plan_title_style['color']}; font-weight: bold; background-color: transparent;"
        if hasattr(self.main_tab.daily_plan_card, 'title_label'):
            self.main_tab.daily_plan_card.title_label.setStyleSheet(plan_style_sheet)
        if hasattr(self.main_tab.current_plan_card, 'title_label'):
            self.main_tab.current_plan_card.title_label.setStyleSheet(plan_style_sheet)

    def apply_all_settings(self):
        """Applies all style and term settings to all components."""
        self.apply_styles()
        self.tabs.setTabText(2, f"💰 {self.term}日志")
        self.tabs.setTabText(4, f"📜 {self.term}规则")

        # 控制财富规则标签页的可见性
        show_rules_tab = self.style_config.get("show_wealth_rules_tab", True)
        self.tabs.setTabVisible(4, show_rules_tab)  # “财富规则”标签页的索引是4

        self.settings_tab.apply_settings(self.style_config)
        self.wealth_log_tab.apply_settings(self.style_config)
        self.wealth_rules_tab.apply_settings(self.style_config)

        self.refresh_main_display()
        self.main_tab.update_rewards_display(self.rewards_tab.get_data())

    def open_style_settings_dialog(self):
        old_folder = self.style_config.get("level_image_folder", "level")
        dialog = StyleSettingsDialog(self.style_config, self)
        if dialog.exec():
            self.style_config.update(dialog.get_settings())
            self.save_app_config()
            self.apply_all_settings()

            new_folder = self.style_config.get("level_image_folder", "level")
            if old_folder != new_folder:
                self.scan_for_image_conflicts()

    def toggle_reward_panel(self):
        self.set_panel_visibility(not self.side_panel_container.isVisible())

    def set_panel_visibility(self, visible):
        self.side_panel_container.setVisible(visible)
        self.toggle_button.setText("\u25C0" if visible else "\u25B6")
        self._update_button_position()

    def post_init_connect(self):
        self.wealth_log_tab.wealth_updated.connect(self.refresh_main_display)
        self.settings_tab.settings_button.clicked.connect(self.open_style_settings_dialog)
        self.tabs.currentChanged.connect(self.refresh_main_display)
        self.main_tab.comparison_changed.connect(self.refresh_main_display)
        self.main_tab.countdown_date_changed.connect(self.on_countdown_date_changed)
        self.main_tab.countdown_visibility_changed.connect(self.on_countdown_visibility_changed)
        self.rewards_tab.rewards_updated.connect(self.main_tab.update_rewards_display)

        def on_config_update():
            self.level_config_data = self.settings_tab.config_data
            self.save_app_config()
            self.wealth_log_tab.update_level_config(self.level_config_data)
            self.wealth_log_tab.refresh_table_and_emit_update()

        self.settings_tab.config_updated.connect(on_config_update)

    def on_countdown_date_changed(self, date_str_or_none):
        self.style_config["countdown_target_date"] = date_str_or_none
        # 如果用户主动设置或修改日期，则默认显示倒计时
        if date_str_or_none is not None:
            self.style_config["show_countdown"] = True
        self.save_app_config()
        self.refresh_main_display()

    def on_countdown_visibility_changed(self, visible):
        self.style_config["show_countdown"] = visible
        self.save_app_config()
        self.refresh_main_display()

    def refresh_main_display(self, _=None):
        if self._is_refreshing:
            return
        self._is_refreshing = True

        total_wealth = self.wealth_log_tab.get_latest_wealth()
        level_config = self.settings_tab.config_data
        sorted_config = sorted(level_config, key=lambda x: x.get('wealth_threshold', 0))
        current_level_data, next_level_data = None, None
        current_level_index = -1
        for i, level in enumerate(sorted_config):
            if total_wealth >= level['wealth_threshold']:
                current_level_data = level;
                current_level_index = i
            else:
                next_level_data = level;
                break

        comparison_level_data = self.main_tab.comparison_level_data
        self.main_tab.update_display(total_wealth, current_level_data, next_level_data, sorted_config,
                                     current_level_index, self.style_config, comparison_level_data)

        self.update_external_reward_display(current_level_data, current_level_index, sorted_config,
                                            comparison_level_data)

        self._is_refreshing = False

    def update_external_reward_display(self, current_level_data, current_level_index, sorted_config,
                                       comparison_level_data=None):
        level_for_image = None
        if comparison_level_data:
            level_for_image = comparison_level_data
        else:
            img_mode = self.style_config.get("reward_image_display_mode", "current")
            if img_mode == "current":
                level_for_image = current_level_data
            elif img_mode == "next":
                if current_level_index + 1 < len(sorted_config): level_for_image = sorted_config[
                    current_level_index + 1]
            elif img_mode == "next_available":
                for i in range(current_level_index + 1, len(sorted_config)):
                    img_settings = sorted_config[i].get("reward_image", {})
                    if img_settings.get("path") and os.path.exists(img_settings.get("path")):
                        level_for_image = sorted_config[i];
                        break

        self.current_reward_level_data = level_for_image
        image_settings = level_for_image.get("reward_image") if level_for_image else None
        has_image = bool(image_settings and image_settings.get("path") and os.path.exists(image_settings.get("path")))
        should_show_elements = has_image and self.tabs.currentIndex() == 0

        self.toggle_button.setVisible(should_show_elements)

        if should_show_elements:
            auto_expand = self.style_config.get("auto_expand_reward_panel", True)
            if auto_expand and not self.side_panel_container.isVisible():
                self.set_panel_visibility(True)

            try:
                pixmap = QPixmap(image_settings.get("path"))
                if not pixmap.isNull():
                    self.side_panel_container.setFixedWidth(400)
                    self.reward_image_display.set_view(pixmap, image_settings)
                else:
                    raise ValueError("Loaded pixmap is null")
            except Exception as e:
                logging.error(f"Error rendering image preview: {e}\n{traceback.format_exc()}")
                self.reward_image_display.clear_view()
                self.reward_image_display.setText("图片预览错误")
        else:
            self.reward_image_display.clear_view()
            self.reward_image_display.setText("没有图片")
            if self.side_panel_container.isVisible():
                self.set_panel_visibility(False)
            self.side_panel_container.setMinimumWidth(0)
            self.side_panel_container.setMaximumWidth(16777215)
            self.side_panel_container.adjustSize()

        self._update_button_position()


def main():
    # setup_logging()
    # sys.excepthook = handle_exception

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
