import requests
import os


def download_images():
    # 基础URL，我们将用数字替换末尾的部分
    base_url = "http://ossweb-img.qq.com/images/cf/web201105/rank/BigClass_{}.jpg"

    # 设置保存图片的文件夹名
    save_dir = 'level'
    # 如果文件夹不存在，就创建它
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    print(f"开始检查并下载缺失的图片到 '{save_dir}' 文件夹...")

    # 循环1到100
    for i in range(1, 101):
        # 构建本地保存的文件路径（包含文件夹）
        file_path = os.path.join(save_dir, f"{i}.jpg")

        # 检查文件是否已经存在，如果存在则跳过
        if os.path.exists(file_path):
            print(f"文件已存在，跳过: {file_path}")
            continue

        # 构建完整的图片URL
        image_url = base_url.format(i)

        try:
            # 发送HTTP GET请求
            print(f"正在下载: {image_url}")
            response = requests.get(image_url, stream=True, timeout=10)

            # 检查请求是否成功 (状态码 200)
            if response.status_code == 200:
                # 以二进制写模式打开文件并保存
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                print(f"成功下载并保存: {file_path}")
            else:
                print(f"下载失败: {image_url} (状态码: {response.status_code})")

        except requests.exceptions.RequestException as e:
            print(f"请求时发生错误: {image_url} ({e})")

    print("\n所有图片检查和下载完成！")


if __name__ == "__main__":
    download_images()

