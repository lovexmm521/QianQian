# data_handler.py
# ----------------------------------------------------------------
# 负责数据的读取、存储、修改和删除。
# 新增功能：保存和加载用户最后输入的身高体重。
# ----------------------------------------------------------------
import json
import os
from datetime import datetime


class DataHandler:
    def __init__(self, records_filename="bmi_records.json", settings_filename="user_settings.json"):
        self.records_filename = records_filename
        self.settings_filename = settings_filename
        self.records = self.load_records()

    # --- 用户设置相关 ---
    def save_last_input(self, height, weight_kg):
        """保存最后输入的身高和体重(kg)"""
        settings = {"last_height": height, "last_weight_kg": weight_kg}
        try:
            with open(self.settings_filename, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)
            return True
        except IOError:
            return False

    def load_last_input(self):
        """加载最后输入的身高和体重"""
        if not os.path.exists(self.settings_filename):
            return None  # 如果文件不存在，返回None
        try:
            with open(self.settings_filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    # --- BMI 记录相关 ---
    def _save_to_file(self):
        """将当前记录列表保存到JSON文件（私有方法）"""
        try:
            self.records.sort(key=lambda x: x['date'], reverse=True)
            with open(self.records_filename, 'w', encoding='utf-8') as f:
                json.dump(self.records, f, indent=4, ensure_ascii=False)
            return True
        except IOError:
            return False

    def load_records(self):
        """从JSON文件加载记录"""
        if not os.path.exists(self.records_filename):
            return []
        try:
            with open(self.records_filename, 'r', encoding='utf-8') as f:
                records = json.load(f)
                records.sort(key=lambda x: x['date'], reverse=True)
                return records
        except (json.JSONDecodeError, IOError):
            return []

    def save_record(self, weight_kg, height_cm, bmi):
        """保存一条新的记录"""
        new_record = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "weight": weight_kg,
            "height": height_cm,
            "bmi": bmi
        }
        self.records.insert(0, new_record)
        return self._save_to_file()

    def update_record(self, original_record_date, new_record_data):
        """根据原始日期更新一条记录的全部内容"""
        for i, record in enumerate(self.records):
            if record['date'] == original_record_date:
                self.records[i] = new_record_data
                return self._save_to_file()
        return False

    def delete_record(self, record_date):
        """根据日期删除一条记录"""
        original_length = len(self.records)
        self.records = [rec for rec in self.records if rec['date'] != record_date]

        if len(self.records) < original_length:
            return self._save_to_file()
        return False

    def get_all_records(self):
        """获取所有记录"""
        return self.records
