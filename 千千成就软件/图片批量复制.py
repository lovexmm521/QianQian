import tkinter as tk
from tkinter import filedialog, messagebox
import os
import shutil

# --- 全局变量 ---
# 用于存储用户选择的图片路径
selected_image_path = None


# --- 函数定义 ---

def select_image():
    """
    打开文件对话框让用户选择一个图片文件 (PNG 或 JPG)。
    """
    global selected_image_path
    # 打开文件选择对话框，限制文件类型
    f_path = filedialog.askopenfilename(
        title="请选择一个图片文件",
        filetypes=[("Image Files", "*.png *.jpg"), ("All files", "*.*")]
    )
    # 如果用户选择了文件
    if f_path:
        selected_image_path = f_path
        # 更新界面上的标签，显示已选择的文件路径
        file_label.config(text=f"已选图片: {os.path.basename(f_path)}")
        status_label.config(text="图片已选择，请输入数字范围。")
    else:
        # 如果用户取消选择
        selected_image_path = None
        file_label.config(text="未选择任何图片")


def start_copying():
    """
    执行图片复制和重命名的核心逻辑。
    """
    # 1. 检查是否已选择图片
    if not selected_image_path:
        messagebox.showerror("错误", "请先选择一个图片文件！")
        return

    # 2. 获取并验证输入的数字
    try:
        start_num = int(start_entry.get())
        end_num = int(end_entry.get())
    except ValueError:
        messagebox.showerror("错误", "请输入有效的整数！")
        return

    # 3. 验证数字范围
    if start_num > end_num:
        messagebox.showerror("错误", "起始数字不能大于结束数字！")
        return

    # 4. 执行复制操作
    try:
        # 获取源文件的目录和扩展名
        source_dir = os.path.dirname(selected_image_path)
        _, extension = os.path.splitext(selected_image_path)

        # 计数成功复制的文件数量
        copied_count = 0

        # 循环遍历指定的数字范围
        for i in range(start_num, end_num + 1):
            # 构建目标文件的完整路径
            destination_path = os.path.join(source_dir, f"{i}{extension}")
            # 使用 shutil.copy2 来复制文件，它会同时复制元数据
            shutil.copy2(selected_image_path, destination_path)
            copied_count += 1

        # 5. 显示成功信息
        success_message = f"操作成功！\n\n总共复制了 {copied_count} 个文件。\n文件已保存在原始图片的文件夹下。"
        messagebox.showinfo("完成", success_message)
        status_label.config(text=f"任务完成，成功复制 {copied_count} 个文件。")

    except Exception as e:
        # 捕获可能发生的其他异常（如权限问题）
        messagebox.showerror("操作失败", f"发生了一个错误: {e}")
        status_label.config(text="操作失败，请检查错误信息。")


# --- GUI 界面设置 ---

# 创建主窗口
root = tk.Tk()
root.title("图片批量复制工具")
root.geometry("450x300")  # 设置窗口大小
root.resizable(False, False)  # 禁止调整窗口大小

# 创建一个主框架用于组织控件
main_frame = tk.Frame(root, padx=20, pady=20)
main_frame.pack(expand=True, fill=tk.BOTH)

# 1. 文件选择部分
select_button = tk.Button(main_frame, text="1. 选择图片 (.png 或 .jpg)", command=select_image, font=("Helvetica", 10))
select_button.pack(pady=5, fill=tk.X)

file_label = tk.Label(main_frame, text="未选择任何图片", fg="blue", wraplength=400)
file_label.pack(pady=5)

# 2. 数字输入部分
number_frame = tk.Frame(main_frame)
number_frame.pack(pady=10)

start_label = tk.Label(number_frame, text="起始数字:")
start_label.pack(side=tk.LEFT, padx=5)
start_entry = tk.Entry(number_frame, width=8)
start_entry.pack(side=tk.LEFT)

end_label = tk.Label(number_frame, text="结束数字:")
end_label.pack(side=tk.LEFT, padx=(15, 5))
end_entry = tk.Entry(number_frame, width=8)
end_entry.pack(side=tk.LEFT)

# 3. 执行按钮
copy_button = tk.Button(main_frame, text="2. 开始复制", command=start_copying, font=("Helvetica", 10, "bold"),
                        bg="#4CAF50", fg="white")
copy_button.pack(pady=15, fill=tk.X, ipady=5)

# 4. 状态栏
status_label = tk.Label(root, text="请先选择一张图片", bd=1, relief=tk.SUNKEN, anchor=tk.W)
status_label.pack(side=tk.BOTTOM, fill=tk.X)

# 启动 Tkinter 事件循环
root.mainloop()
