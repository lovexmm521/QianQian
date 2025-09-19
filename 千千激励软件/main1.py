import sys
import os
import logging
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon
import ctypes


def resource_path(relative_path):
    """ 获取资源的绝对路径, 适用于开发环境和PyInstaller打包环境 """
    try:
        # PyInstaller 创建一个临时文件夹, 并将路径存储在 _MEIPASS 中
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def handle_exception(exc_type, exc_value, exc_traceback):
    """全局异常处理器"""
    logging.critical("捕获到未处理的致命异常，程序即将退出。", exc_info=(exc_type, exc_value, exc_traceback))

    error_message = f"发生了一个严重错误:\n\n{exc_value}\n\n详细信息已记录到 app_log.txt 文件中。"
    QMessageBox.critical(None, "程序错误", error_message)

    QApplication.quit()


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename='app_log.txt',
        filemode='w',
        encoding='utf-8'
    )
    sys.excepthook = handle_exception
    logging.info("程序启动...")

    try:
        logging.info("步骤 1/6: 初始化 QApplication...")
        app = QApplication(sys.argv)

        app.setOrganizationName("YourOrganizationName")
        app.setApplicationName("QianQianMotivation")

        logging.info("步骤 1/6: QApplication 初始化成功。")

        logging.info("步骤 2/6: 正在导入 MainWindow...")
        from main_window import MainWindow
        logging.info("步骤 2/6: MainWindow 导入成功。")

        logging.info("步骤 3/6: 创建 MainWindow 实例...")
        myappid = u'mycompany.myproduct.subproduct.version'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

        main_win = MainWindow()

        # --- 设置主窗口和应用程序图标 ---
        # 使用辅助函数获取图标的绝对路径
        icon_path = resource_path('1.ico')
        if os.path.exists(icon_path):
            app_icon = QIcon(icon_path)
            main_win.setWindowIcon(app_icon)
            # 将图标传递给主窗口以设置系统托盘图标
            main_win.set_tray_icon(app_icon)
        else:
            logging.warning("图标文件 '1.ico' 未找到。")

        logging.info("步骤 3/6: MainWindow 实例创建成功。")

        logging.info("步骤 4/6: 显示主窗口...")
        main_win.show()
        logging.info("步骤 4/6: 主窗口显示指令已调用。")

        logging.info("步骤 5/6: 进入主事件循环 (app.exec)...")
        sys.exit(app.exec())

    except Exception as e:
        logging.critical("在主启动流程中发生错误。", exc_info=True)
        handle_exception(type(e), e, e.__traceback__)


if __name__ == '__main__':
    main()

