# config.py
import json

CONFIG_FILE = "config.json"


class ConfigManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ConfigManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True

        self.defaults = {
            "work_minutes": 25,
            "break_minutes": 5,
            "long_break_minutes": 15,
            "pomodoros_per_cycle": 4,

            "custom_text": "考研加油",
            "custom_text_color": "#888888",
            "custom_text_font_family": "Microsoft YaHei",
            "custom_text_font_size": 12,

            "work_color": "#FF6B6B",
            "break_color": "#4ECDC4",
            "long_break_color": "#487EB0",
            "timer_text_color": "#FFFFFF",

            "sound_notification": True,
            "desktop_notification": True,
            "always_on_top": False,

            "work_sound_path": "",
            "break_sound_path": "",
            "long_break_sound_path": "",
            "work_sound_volume": 80,
            "break_sound_volume": 80,
            "long_break_sound_volume": 80,

            "random_sound_enabled": False,
            "random_sound_folder_path": "",
            "random_sound_volume": 80,

            "work_finish_text": "干得漂亮！休息一下吧。",
            "break_finish_text": "休息结束，准备好开始下一个番茄钟了吗？",
            "long_break_finish_text": "完成一轮！可以进行一次长时间休息了。",

            "developer_debug_mode": False,
            "auto_cycle_enabled": False,

            # **新增**: UI 元素显隐开关
            "show_custom_text": True,
            "show_app_title": True,

            # **新增**: 精简模式开关
            "compact_mode_enabled": False
        }
        self.settings = self.defaults.copy()
        self.load_settings()

    def load_settings(self):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                loaded_settings = json.load(f)
                self.settings.update(loaded_settings)
                for key in self.defaults:
                    if key not in self.settings:
                        self.settings[key] = self.defaults[key]
        except (FileNotFoundError, json.JSONDecodeError):
            self.save_settings()

    def save_settings(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
        except IOError as e:
            print(f"Error saving settings: {e}")

    def get(self, key):
        return self.settings.get(key, self.defaults.get(key))

    def set(self, key, value):
        self.settings[key] = value
        self.save_settings()


config = ConfigManager()