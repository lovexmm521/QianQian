from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class AboutTab(QWidget):
    """
    一个显示祝福语和软件信息的“关于”页面。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        # 主布局，内容居中对齐
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 使用一个带样式的 QFrame 作为内容的容器卡片
        container = QFrame()
        container.setObjectName("aboutCard")
        container.setStyleSheet("""
            #aboutCard { 
                background-color: #FFFFFF; 
                border-radius: 15px; 
                padding: 40px; 
                border: 1px solid #E0E0E0;
            }
        """)

        # 容器内的布局
        layout = QVBoxLayout(container)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 标题
        title_label = QLabel("💌 致每一位努力的朋友 💌")
        title_font = QFont("Microsoft YaHei", 28, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #4A90E2; background-color: transparent;")
        layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # 祝福语列表
        messages = [
            "✨ 愿你的每一份付出，都如星辰闪耀，终将汇成璀璨银河。",
            "🌱 愿你的每一个梦想，都如种子破土，迎着阳光茁壮成长。",
            "☀️ 愿你的每一天，都充满阳光与希望，温暖且明亮。",
            "🚀 愿你的每一步前行，都充满力量与勇气，无畏亦无惧。",
            "💖 愿你的每一次回首，都充满感恩与喜悦，不负韶华。",
            "🌈 生活或许偶有风雨，但请相信，雨后总会有绚烂的彩虹。",
            "💪 这款小小的软件，希望能成为你追梦路上的一盏灯，一个温暖的陪伴。",
            "--- 千千"
        ]

        # 循环创建并添加祝福语标签
        for msg in messages:
            label = QLabel(msg)
            msg_font = QFont("Microsoft YaHei", 16)

            # 对签名行做特殊处理
            if "---" in msg:
                msg_font.setItalic(True)
                label.setAlignment(Qt.AlignmentFlag.AlignRight)
                label.setStyleSheet("color: #777777; margin-top: 20px; background-color: transparent;")
            else:
                label.setStyleSheet("color: #333333; background-color: transparent;")

            label.setFont(msg_font)
            layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.addWidget(container)
