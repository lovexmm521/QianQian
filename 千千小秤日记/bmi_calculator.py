# bmi_calculator.py
# ----------------------------------------------------------------
# 负责所有和 BMI 相关的计算逻辑。
# ----------------------------------------------------------------
from config import Config

def calculate_bmi(weight_kg, height_cm):
    """根据体重(kg)和身高(cm)计算BMI值"""
    if height_cm <= 0:
        return 0
    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)
    return round(bmi, 1)

def get_bmi_category_key(bmi):
    """根据BMI值返回其分类的键名（例如 'normal'）"""
    standards = Config.BMI_STANDARDS_CHINA
    if bmi <= standards["underweight"]["max"]:
        return "underweight"
    elif standards["normal"]["min"] <= bmi <= standards["normal"]["max"]:
        return "normal"
    elif standards["overweight"]["min"] <= bmi <= standards["overweight"]["max"]:
        return "overweight"
    else: # bmi >= standards["obese"]["min"]
        return "obese"

def get_bmi_info(bmi):
    """根据BMI值返回对应的完整信息，包括分类键名、标签和建议"""
    category_key = get_bmi_category_key(bmi)
    # 使用copy()避免意外修改原始配置字典
    info = Config.BMI_STANDARDS_CHINA[category_key].copy()
    # 将键名也添加到返回的信息字典中，方便UI根据键名查找颜色
    info['key'] = category_key
    return info