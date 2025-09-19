import sys
import os
import logging
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon


# from main_window import MainWindow # This will be imported inside main() to catch import errors

# --- 全局资源路径函数 ---
def resource_path(relative_path):
    """ 获取资源的绝对路径，兼容开发环境和PyInstaller打包环境 """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# --- 日志设置 (已注释) ---
# def setup_logging():
#     """配置日志记录器，输出到文件和控制台"""
#     log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

#     # 文件处理器，记录所有日志
#     try:
#         file_handler = logging.FileHandler("app_log.txt", mode='w', encoding='utf-8')
#         file_handler.setFormatter(log_formatter)
#         # 获取根日志记录器
#         root_logger = logging.getLogger()
#         root_logger.setLevel(logging.INFO)
#         root_logger.addHandler(file_handler)
#     except Exception as e:
#         print(f"无法设置文件日志: {e}")

#     # 控制台处理器
#     # console_handler = logging.StreamHandler()
#     # console_handler.setFormatter(log_formatter)
#     # root_logger.addHandler(console_handler)


#     # --- 全局异常钩子 ---
#     def handle_exception(exc_type, exc_value, exc_traceback):
#         """捕获所有未处理的异常"""
#         # 忽略键盘中断
#         if issubclass(exc_type, KeyboardInterrupt):
#             sys.__excepthook__(exc_type, exc_value, exc_traceback)
#             return

#         # 记录致命错误
#         logging.critical("捕获到未处理的致命异常，程序即将退出。", exc_info=(exc_type, exc_value, exc_traceback))

#         # 显示一个错误弹窗
#         error_msg = f"发生了一个致命错误，详情请见 app_log.txt。\n\n错误类型: {exc_type.__name__}\n错误信息: {exc_value}"
#         QMessageBox.critical(None, "程序错误", error_msg)
#         QApplication.quit()

#     # 设置系统异常钩子
#     sys.excepthook = handle_exception

# --- 主函数 ---
def main():
    # setup_logging() # 暂时禁用日志
    # logging.info("程序启动...")

    try:
        # logging.info("步骤 1/6: 初始化 QApplication...")
        app = QApplication(sys.argv)
        # logging.info("步骤 1/6: QApplication 初始化成功。")

        # logging.info("步骤 2/6: 正在导入 MainWindow...")
        from main_window import MainWindow
        # logging.info("步骤 2/6: MainWindow 导入成功。")

        # logging.info("步骤 3/6: 创建 MainWindow 实例...")
        main_win = MainWindow()
        # logging.info("步骤 3/6: MainWindow 实例创建成功。")

        # 设置图标
        try:
            icon_path = resource_path("1.ico")
            if os.path.exists(icon_path):
                app_icon = QIcon(icon_path)
                main_win.setWindowIcon(app_icon)
                main_win.set_tray_icon(app_icon)  # 传递给主窗口设置托盘图标
                # logging.info("应用程序图标设置成功。")
            else:
                # logging.warning("图标文件 1.ico 未找到。")
                pass
        except Exception as e:
            # logging.error(f"设置图标时出错: {e}")
            pass

        # logging.info("步骤 4/6: 显示主窗口...")
        main_win.show()
        # logging.info("步骤 4/6: 主窗口显示指令已调用。")

        # logging.info("步骤 5/6: 进入主事件循环 (app.exec)...")
        sys.exit(app.exec())

    except Exception as e:
        # logging.critical(f"在主启动流程中发生错误: {e}", exc_info=True)
        # 即使日志系统未启动，也要尝试显示错误
        QMessageBox.critical(None, "启动错误", f"程序启动失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
