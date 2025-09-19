import tkinter as tk
from tkinter import messagebox, Label, Entry, Button, Frame, Scrollbar, Canvas, Text, filedialog, Scale, Checkbutton, BooleanVar
import os
import json
import sys # 导入 sys 模块

# --- 辅助函数：获取资源的绝对路径 ---
# 无论是在开发环境运行还是打包成exe后运行，此函数都能正确定位文件路径
def resource_path(relative_path):
    """
    获取资源的绝对路径，适用于开发环境和 PyInstaller 打包后的 --onefile 模式。
    当程序被打包后，资源文件会被解压到一个临时的文件夹中，
    这个函数能找到那个临时文件夹的路径。
    """
    try:
        # PyInstaller 创建一个临时文件夹，并将路径存储在 sys._MEIPASS 中
        base_path = sys._MEIPASS
    except Exception:
        # 在开发模式下或未被打包时，获取脚本所在的绝对路径
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class ConfessionApp:
    def __init__(self, master):
        self.master = master
        self.master.title("千千表白软件")

        # --- 设置窗口图标 ---
        # 使用 resource_path 函数确保在任何情况下都能找到图标文件
        try:
            icon_path = resource_path('1.ico')
            self.master.iconbitmap(icon_path)
        except tk.TclError:
            print("错误: 图标文件 '1.ico' 未找到。")
            print("请确保 '1.ico' 文件与脚本或打包后的.exe文件在同一目录下，")
            print("并且在打包时已正确包含它。")

        self.master.geometry("1200x750")

        self.config_file = "config.json"
        self.popups_config = []
        self.html_texts = ['亲爱的', '节日快乐', '我爱你']
        self.heart_text = '我会永远\n陪着你'
        self.music_file = ""
        self.volume = 0.5
        self.delay = 0
        self.final_rejection_text = "好吧，看来你真的不喜欢我..."

        self.load_config()

        # --- UI ---
        main_frame = Frame(master)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        top_frame = Frame(main_frame)
        top_frame.pack(fill=tk.BOTH, expand=True)

        # --- 左侧面板：HTML 内容设置 ---
        left_panel = Frame(top_frame, relief=tk.GROOVE, borderwidth=2, padx=5, pady=5)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        Label(left_panel, text="成功后显示的文字:", font=("Helvetica", 12, "bold")).pack(anchor="w", padx=5, pady=5)
        html_canvas_frame = Frame(left_panel, height=150)
        html_canvas_frame.pack(fill=tk.X, expand=False, padx=5, pady=5)
        html_canvas_frame.pack_propagate(False)
        self.html_canvas = Canvas(html_canvas_frame)
        html_scrollbar = Scrollbar(html_canvas_frame, orient="vertical", command=self.html_canvas.yview)
        self.html_scrollable_frame = Frame(self.html_canvas)
        self.html_scrollable_frame.bind("<Configure>",
                                        lambda e: self.html_canvas.configure(scrollregion=self.html_canvas.bbox("all")))
        self.html_canvas.create_window((0, 0), window=self.html_scrollable_frame, anchor="nw")
        self.html_canvas.configure(yscrollcommand=html_scrollbar.set)
        self.html_canvas.pack(side="left", fill="both", expand=True)
        html_scrollbar.pack(side="right", fill="y")
        self.html_entries = []
        self.update_html_entries()
        html_button_frame = Frame(left_panel)
        html_button_frame.pack(fill=tk.X, padx=5, pady=5)
        Button(html_button_frame, text="添加一行文字", command=self.add_html_text).pack(side=tk.LEFT, padx=5)
        Button(html_button_frame, text="移除最后一行", command=self.remove_html_text).pack(side=tk.LEFT, padx=5)
        Label(left_panel, text="心形中间的文字 (可换行):", font=("Helvetica", 12, "bold")).pack(anchor="w", padx=5,
                                                                                                pady=(10, 5))
        self.heart_text_widget = Text(left_panel, height=4, font=("Helvetica", 10))
        self.heart_text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.heart_text_widget.insert(tk.END, self.heart_text)

        # --- 右侧面板：弹窗设置 ---
        right_panel = Frame(top_frame, relief=tk.GROOVE, borderwidth=2, padx=5, pady=5)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        Label(right_panel, text="自定义弹窗内容:", font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(5, 0))
        popup_canvas_frame = Frame(right_panel)
        popup_canvas_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.popup_canvas = Canvas(popup_canvas_frame)
        popup_scrollbar = Scrollbar(popup_canvas_frame, orient="vertical", command=self.popup_canvas.yview)
        self.popup_scrollable_frame = Frame(self.popup_canvas)
        self.popup_scrollable_frame.bind("<Configure>", lambda e: self.popup_canvas.configure(
            scrollregion=self.popup_canvas.bbox("all")))
        self.popup_canvas.create_window((0, 0), window=self.popup_scrollable_frame, anchor="nw")
        self.popup_canvas.configure(yscrollcommand=popup_scrollbar.set)
        self.popup_canvas.pack(side="left", fill="both", expand=True)
        popup_scrollbar.pack(side="right", fill="y")
        self.popup_widgets = []
        self.update_popup_widgets()
        control_frame = Frame(right_panel)
        control_frame.pack(fill=tk.X, pady=(5, 0))
        Button(control_frame, text="添加一个弹窗", command=self.add_popup_config).pack(side=tk.LEFT, padx=5)
        Button(control_frame, text="移除最后一个弹窗", command=self.remove_popup_config).pack(side=tk.LEFT, padx=5)

        # --- 底部面板：通用设置 ---
        general_settings_frame = Frame(main_frame, relief=tk.GROOVE, borderwidth=2)
        general_settings_frame.pack(fill=tk.X, pady=10)
        Label(general_settings_frame, text="通用设置:", font=("Helvetica", 12, "bold")).pack(anchor="w", padx=5, pady=5)

        rejection_frame = Frame(general_settings_frame)
        rejection_frame.pack(fill=tk.X, padx=10, pady=5)
        Label(rejection_frame, text="最终拒绝信息:").pack(side=tk.LEFT)
        self.rejection_entry = Entry(rejection_frame)
        self.rejection_entry.insert(0, self.final_rejection_text)
        self.rejection_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        delay_frame = Frame(general_settings_frame)
        delay_frame.pack(fill=tk.X, padx=10, pady=5)
        Label(delay_frame, text="弹窗前延迟(秒):").pack(side=tk.LEFT)
        self.delay_entry = Entry(delay_frame, width=10)
        self.delay_entry.insert(0, str(self.delay))
        self.delay_entry.pack(side=tk.LEFT, padx=5)
        music_frame = Frame(general_settings_frame)
        music_frame.pack(fill=tk.X, padx=10, pady=5)
        Label(music_frame, text="背景音乐:").pack(side=tk.LEFT)
        self.music_entry = Entry(music_frame, width=40)
        self.music_entry.insert(0, self.music_file)
        self.music_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        Button(music_frame, text="选择...", command=self.select_music_file).pack(side=tk.LEFT)
        volume_frame = Frame(general_settings_frame)
        volume_frame.pack(fill=tk.X, padx=10, pady=5)
        Label(volume_frame, text="音量大小:").pack(side=tk.LEFT)
        self.volume_slider = Scale(volume_frame, from_=0, to=1, resolution=0.01, orient=tk.HORIZONTAL, length=300)
        self.volume_slider.set(self.volume)
        self.volume_slider.pack(side=tk.LEFT, padx=5)

        # --- 底部按钮 ---
        bottom_frame = Frame(master)
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=10)
        Button(bottom_frame, text="保存配置", command=self.save_and_generate, bg="#4CAF50", fg="white",
               font=("Helvetica", 12, "bold")).pack(fill=tk.X)

    def select_music_file(self):
        filepath = filedialog.askopenfilename(
            title="选择一个音乐文件",
            filetypes=[("音频文件", "*.mp3 *.wav *.ogg"), ("所有文件", "*.*")]
        )
        if filepath:
            self.music_file = filepath
            self.music_entry.delete(0, tk.END)
            self.music_entry.insert(0, self.music_file)

    def update_html_entries(self):
        for widget in self.html_scrollable_frame.winfo_children():
            widget.destroy()
        self.html_entries = []
        for i, text in enumerate(self.html_texts):
            row_frame = Frame(self.html_scrollable_frame)
            row_frame.pack(fill=tk.X, pady=2, padx=5)
            Label(row_frame, text=f"第 {i + 1} 行:").pack(side=tk.LEFT, padx=5)
            entry = Entry(row_frame, width=40)
            entry.insert(0, text)
            entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
            self.html_entries.append(entry)

    def add_html_text(self):
        self.html_texts.append("新的一行")
        self.update_html_entries()

    def remove_html_text(self):
        if self.html_texts:
            self.html_texts.pop()
            self.update_html_entries()

    def update_popup_widgets(self):
        for widget_dict in self.popup_widgets:
            widget_dict["frame"].destroy()
        self.popup_widgets = []

        for i, config in enumerate(self.popups_config):
            frame = Frame(self.popup_scrollable_frame, relief=tk.RIDGE, borderwidth=2, padx=5, pady=5)
            frame.pack(fill=tk.X, pady=5, padx=5)

            Label(frame, text=f"--- 弹窗 {i + 1} ---", font=("Helvetica", 10, "bold")).grid(row=0, column=0,
                                                                                            columnspan=2, sticky="w")
            Label(frame, text="标题:").grid(row=1, column=0, sticky="w")
            title_entry = Entry(frame, width=50)
            title_entry.insert(0, config.get("title", ""))
            title_entry.grid(row=1, column=1, sticky="ew")
            Label(frame, text="内容:").grid(row=2, column=0, sticky="w")
            content_entry = Entry(frame, width=50)
            content_entry.insert(0, config.get("content", ""))
            content_entry.grid(row=2, column=1, sticky="ew")

            widget_dict = {
                "frame": frame, "title": title_entry, "content": content_entry,
            }

            is_last_popup = (i == len(self.popups_config) - 1)
            if is_last_popup:
                mandatory_var = BooleanVar()
                mandatory_var.set(config.get("is_mandatory", False))
                mandatory_check = Checkbutton(frame, text="终极强制 (此弹窗将无法关闭，点击确认后直接成功)",
                                              variable=mandatory_var)
                mandatory_check.grid(row=5, column=0, columnspan=2, sticky="w", pady=(5, 0))
                widget_dict["mandatory_var"] = mandatory_var

            frame.columnconfigure(1, weight=1)
            self.popup_widgets.append(widget_dict)

    def add_popup_config(self):
        new_config = {
            "title": f"问题 {len(self.popups_config) + 1}", "content": "你喜欢我吗？",
            "is_mandatory": False
        }
        if self.popups_config:
            self.popups_config[-1]['is_mandatory'] = False
        self.popups_config.append(_config)
        self.update_popup_widgets()
        self.popup_canvas.update_idletasks()
        self.popup_canvas.yview_moveto(1.0)

    def remove_popup_config(self):
        if self.popups_config:
            self.popups_config.pop()
            self.update_popup_widgets()

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.popups_config = config.get("popups", [])
                    self.html_texts = config.get("html_texts", [])
                    self.heart_text = config.get("heart_text", '我会永远\n陪着你')
                    self.music_file = config.get("music_file", "")
                    self.volume = config.get("volume", 0.5)
                    self.delay = config.get("delay", 0)
                    self.final_rejection_text = config.get("final_rejection_text", "好吧，看来你真的不喜欢我...")
            except (json.JSONDecodeError, KeyError):
                self.set_default_config()
        else:
            self.set_default_config()

    def set_default_config(self):
        self.popups_config = [
            {"title": "我喜欢你", "content": "做我女朋友好吗？", "is_mandatory": False},
            {"title": "求求你了", "content": "我真的很喜欢你，给我个机会吧", "is_mandatory": False},
        ]
        self.html_texts = ['亲爱的', '节日快乐', '我爱你']
        self.heart_text = '我会永远\n陪着你'
        self.music_file = ""
        self.volume = 0.5
        self.delay = 0
        self.final_rejection_text = "好吧，看来你真的不喜欢我..."

    def save_and_generate(self):
        # 从UI控件收集最新的配置
        self.popups_config = []
        for i, widgets in enumerate(self.popup_widgets):
            config = {
                "title": widgets["title"].get(), "content": widgets["content"].get(),
            }
            if "mandatory_var" in widgets:
                config["is_mandatory"] = widgets["mandatory_var"].get()
            else:
                config["is_mandatory"] = False
            self.popups_config.append(config)

        self.html_texts = [entry.get() for entry in self.html_entries]
        self.heart_text = self.heart_text_widget.get("1.0", tk.END).strip()
        self.music_file = self.music_entry.get()
        self.volume = self.volume_slider.get()
        try:
            self.delay = int(self.delay_entry.get())
        except ValueError:
            self.delay = 0
        self.final_rejection_text = self.rejection_entry.get()

        # 组合所有配置到一个字典中
        config_data = {
            "popups": self.popups_config,
            "html_texts": self.html_texts,
            "heart_text": self.heart_text,
            "music_file": self.music_file,
            "volume": self.volume,
            "delay": self.delay,
            "final_rejection_text": self.final_rejection_text
        }

        # 将配置写入 config.json 文件
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("成功", f"配置已成功保存到 {self.config_file}")
        except Exception as e:
            messagebox.showerror("保存失败", f"无法写入配置文件: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ConfessionApp(root)
    root.mainloop()
