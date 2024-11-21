# config.py
import os

# 获取 cs 目录的路径（config.py 文件的上一级）
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 定义路径
DOWNLOAD_FOLDER = os.path.join(base_dir, "downloads")
EXTRACT_FOLDER = os.path.join(base_dir, "extracted")
JY_FOLDER = os.path.join(base_dir, "jy")
ZY_FOLDER = os.path.join(base_dir, "zy")
