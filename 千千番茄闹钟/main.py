# main.py
import sys
from PyQt6.QtWidgets import QApplication

# 我们将很快创建 main_window.py 文件，这里先导入
# 在实际运行前，请确保 main_window.py 文件存在且其中定义了 MainWindow 类
from main_window import MainWindow

def main():
    """
    应用程序主函数。
    初始化并运行PyQt6应用程序。
    """
    # 1. 创建 QApplication 实例
    # sys.argv 允许你从命令行传递参数给应用
    app = QApplication(sys.argv)

    # 2. 创建主窗口实例
    # MainWindow 类将是我们应用的UI和核心交互界面
    window = MainWindow()

    # 3. 显示窗口
    window.show()

    # 4. 运行应用程序的事件循环
    # app.exec() 会启动事件循环，等待用户交互，直到窗口关闭
    # sys.exit() 确保程序在退出时能将状态码返回给父进程
    sys.exit(app.exec())

if __name__ == '__main__':
    # 这是Python脚本的标准入口点
    # 确保只有在直接运行此脚本时，main()函数才会被调用
    main()
    # 打包用下面指令
    # pyinstaller --onefile --windowed --name "番茄闹钟" --icon="1.ico" --add-data="1.ico;." main.py