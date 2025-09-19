# main.py
# 应用程序的主入口 (已更新)

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from main_window import MainWindow


def resource_path(relative_path):
    """ 获取资源的绝对路径，无论是开发环境还是PyInstaller环境。 """
    try:
        # PyInstaller 创建一个临时文件夹并将路径存储在 _MEIPASS 中
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def main():
    """
    主函数，用于启动应用程序。
    """
    app = QApplication(sys.argv)

    # --- 设置应用程序图标 ---
    # 这会同时影响EXE文件和窗口左上角的图标
    icon_path = resource_path("1.ico")
    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)
    else:
        print(f"警告：未找到图标文件 '{icon_path}'。")

    # --- 加载样式表 ---
    # 使用 resource_path 确保打包后能找到文件
    qss_path = resource_path("style.qss")
    try:
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print(f"警告：未找到样式文件 '{qss_path}'。将使用默认样式。")
    except Exception as e:
        print(f"加载样式时出错: {e}")

    main_window = MainWindow()
    # 主窗口也设置一下图标，确保一致性
    if 'app_icon' in locals():
        main_window.setWindowIcon(app_icon)

    main_window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
