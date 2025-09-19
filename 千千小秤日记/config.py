# config.py
# ----------------------------------------------------------------
# 这个文件用于存放应用的配置信息，比如样式、颜色、标准等。
# 这样做的好处是方便统一修改和管理，让代码更整洁。
# ----------------------------------------------------------------
class Config:
    # 中国 BMI 标准
    # 适用于18至64岁的人群
    BMI_STANDARDS_CHINA = {
        "underweight": {"max": 18.4, "label": "偏瘦", "suggestion": "身体可能需要更多营养哦，试着均衡饮食吧！"},
        "normal": {"min": 18.5, "max": 23.9, "label": "正常", "suggestion": "非常棒！请继续保持健康的生活方式。"},
        "overweight": {"min": 24.0, "max": 27.9, "label": "过重", "suggestion": "注意一下，可以适当增加运动，调整饮食结构。"},
        "obese": {"min": 28.0, "label": "肥胖", "suggestion": "为了健康，是时候开始制定一个运动和饮食计划了！"}
    }

    # 为不同的BMI等级定义颜色
    BMI_COLORS = {
        "underweight": {"border": "#A9A9A9", "background": "#F5F5F5"}, # 暗灰色 / 白烟色
        "normal":      {"border": "#2E8B57", "background": "#F0FFF0"}, # 海洋绿 / 蜜瓜色
        "overweight":  {"border": "#FFA500", "background": "#FFFACD"}, # 橙色 / 柠檬绸色
        "obese":       {"border": "#FF6347", "background": "#FFF5EE"}  # 红色 / 海贝色
    }


    # UI 样式表 (Stylesheet)
    # 使用了类似 CSS 的语法来美化界面
    STYLESHEET = """
        QWidget {
            font-family: 'Microsoft YaHei', 'Segoe UI', 'Arial';
            font-size: 14px;
        }
        QMainWindow {
            background-color: #F0F8FF; /* 爱丽丝蓝，作为窗口底色 */
        }
        QTabWidget::pane {
            border: 1px solid #B0C4DE; /* 亮钢蓝色边框 */
            border-top: none;
            background-color: #FFFFFF; /* 纯白 */
        }
        QTabBar::tab {
            background: #E6E6FA; /* 淡紫色 */
            border: 1px solid #B0C4DE;
            border-bottom: none;
            padding: 8px 20px;
            margin-right: 2px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
        }
        QTabBar::tab:selected {
            background: #FFFFFF; /* 选中时为纯白 */
            border: 1px solid #B0C4DE;
            border-bottom: 1px solid #FFFFFF; /* 与 pane 融为一体 */
        }
        QTabBar::tab:hover {
            background: #F5F5F5; /* 鼠标悬停时变淡灰色 */
        }
        QGroupBox {
            background-color: #F5FFFA; /* 薄荷奶油色 */
            border: 1px solid #B0E0E6; /* 粉蓝色 */
            border-radius: 8px;
            margin-top: 10px;
            font-weight: bold;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 5px 10px;
            background-color: #B0E0E6;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            color: #2F4F4F; /* 暗瓦灰色 */
        }
        QLabel {
            color: #333333;
        }
        QDoubleSpinBox, QLineEdit {
            padding: 8px;
            border: 1px solid #B0C4DE;
            border-radius: 5px;
            background-color: #FFFFFF;
        }
        QDoubleSpinBox:focus, QLineEdit:focus {
            border: 1px solid #4682B4; /* 钢蓝色 */
        }
        QPushButton {
            background-color: #87CEEB; /* 天蓝色 */
            color: white;
            padding: 10px 15px;
            border-radius: 5px;
            border: none;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #6495ED; /* 矢车菊蓝 */
        }
        QPushButton:pressed {
            background-color: #4169E1; /* 皇家蓝 */
        }
        QScrollArea {
            border: none;
            background-color: #FFFFFF;
        }
        /* 结果展示标签的特定样式 */
        #BMICategoryLabel {
            font-size: 28px;
            font-weight: bold;
            color: #008080; /* 蓝绿色 */
        }
        #BMISuggestionLabel {
            font-size: 16px;
            color: #556B2F; /* 暗橄榄绿 */
            padding-top: 10px;
        }
        /* 删除按钮的特定样式 */
        #DeleteButton {
            background-color: #FF6347; /* 番茄色 */
            color: white;
            font-size: 12px;
            font-weight: bold;
            padding: 5px 8px;
            border-radius: 4px;
            border: none;
        }
        #DeleteButton:hover {
            background-color: #E5533D;
        }
        #DeleteButton:pressed {
            background-color: #CC4A35;
        }
    """
