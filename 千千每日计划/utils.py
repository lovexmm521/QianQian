# utils.py
# 存放辅助函数和常量 (已更新)

from PyQt6.QtCore import QDate


def get_week_dates(current_date):
    """
    根据给定日期，获取其所在周的周一到周日的QDate对象列表。
    """
    day_of_week = current_date.dayOfWeek()
    days_to_monday = day_of_week - 1
    start_of_week = current_date.addDays(-days_to_monday)
    week_dates = [start_of_week.addDays(i) for i in range(7)]
    return week_dates


# Font Awesome 5 Free Solid 图标的Unicode
# 需要系统中安装 "Font Awesome 5 Free" 字体
FONT_AWESOME = {
    "plus": "\uf067",
    "cog": "\uf013",
    "chart-pie": "\uf200",
    "calendar-day": "\uf783",
    "trash-alt": "\uf2ed",
    "check-circle": "\uf058",  # 成功
    "times-circle": "\uf057",  # 失败
    "circle": "\uf111",      # 未打卡
    "chevron-left": "\uf053",   # 新增：收起图标
    "chevron-right": "\uf054",  # 新增：展开图标
}
