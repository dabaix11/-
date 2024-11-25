import os
import json
import requests
import subprocess
import logging
from PySide6.QtCore import QThread, Signal, QUrl
from .config import ZY_FOLDER, EXTRACT_FOLDER, DOWNLOAD_FOLDER, JY_FOLDER

# 设置日志记录
logging.basicConfig(
    filename="logs.txt",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

class DownloadAndExtractThread(QThread):
    progress_signal = Signal(int)
    finished_signal = Signal(bool)

    def __init__(self, urls, target_folder):
        super().__init__()
        self.urls = urls
        self.target_folder = target_folder
        self.seven_zip_path = os.path.join(JY_FOLDER, "7z.exe")

    def run(self):
        try:
            self.download_files(self.urls)
            self.extract_files()
            self.finished_signal.emit(True)
        except Exception as e:
            logging.error(f"下载或解压错误: {e}")
            self.finished_signal.emit(False)

    def download_files(self, urls):
        """从给定的 URL 列表下载文件"""
        if not os.path.exists(DOWNLOAD_FOLDER):
            os.makedirs(DOWNLOAD_FOLDER)

        for i, url in enumerate(urls):
            file_name = os.path.join(DOWNLOAD_FOLDER, url.split("/")[-1])
            if not os.path.exists(file_name):
                response = requests.get(url, stream=True)
                total_size = int(response.headers.get("content-length", 0))
                downloaded_size = 0
                with open(file_name, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        progress = int((downloaded_size / total_size) * 50)  # 下载占 50%
                        self.progress_signal.emit(progress)
                logging.info(f"文件已下载: {file_name}")
            else:
                logging.info(f"文件已存在: {file_name}")

    def extract_files(self):
        """解压文件到目标目录"""
        if not os.path.exists(self.target_folder):
            os.makedirs(self.target_folder)

        for file_name in os.listdir(DOWNLOAD_FOLDER):
            file_path = os.path.join(DOWNLOAD_FOLDER, file_name)
            if file_name.endswith(('.zip', '.7z')):
                try:
                    subprocess.run([self.seven_zip_path, "x", file_path, f"-o{self.target_folder}", "-aoa"], check=True)
                    self.progress_signal.emit(100)
                except subprocess.CalledProcessError as e:
                    logging.error(f"解压失败: {file_name}, 错误: {e}")


class DocumentHandler:
    def __init__(self, browser):
        self.browser = browser
        self.resources = self.load_resources("luj.json")
        self.download_urls = self.load_resources("wd.json")
        logging.info(f"当前工作目录: {os.getcwd()}")  # 打印运行时的工作目录

    def load_resources(self, filename):
        """加载 JSON 配置"""
        json_path = os.path.join(ZY_FOLDER, filename)
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        logging.error(f"{filename} 文件未找到")
        return {}

    def process_path(self, path):
        """
        动态处理路径：
        - 如果是网络路径，直接返回
        - 如果是相对路径，基于 EXTRACT_FOLDER 解析为绝对路径
        """
        if path.startswith("http://") or path.startswith("https://"):
            return path  # 保留网络链接
        # 修改基准路径为 EXTRACT_FOLDER，而非 ZY_FOLDER
        absolute_path = os.path.abspath(os.path.join(EXTRACT_FOLDER, path.lstrip("./")))
        if not os.path.exists(absolute_path):
            logging.error(f"文件路径无效: {absolute_path}")
        return absolute_path

    def ensure_resource(self, category, subcategory):
        """确保资源路径存在"""
        resource_paths = self.resources.get("资源", {}).get(category, {}).get(subcategory, [])
        for resource_path in resource_paths:
            absolute_path = self.process_path(resource_path)  # 转换为绝对路径
            if os.path.exists(absolute_path):
                logging.info(f"资源已找到: {absolute_path}")
                return absolute_path
        logging.warning(f"资源路径无效，尝试下载: {subcategory}")
        self.download_resources(subcategory)
        return None

    def load_content(self, resource_path):
        """加载资源到浏览器"""
        resource_path = self.process_path(resource_path)  # 动态处理路径
        if resource_path.startswith("http://") or resource_path.startswith("https://"):
            logging.info(f"加载在线资源: {resource_path}")
            self.browser.setUrl(QUrl(resource_path))
        elif os.path.exists(resource_path):
            logging.info(f"加载本地文件: {resource_path}")
            self.browser.setUrl(QUrl.fromLocalFile(resource_path))
        else:
            logging.error(f"文件路径无效: {resource_path}")
            self.browser.setHtml("<h1>资源未找到</h1>")
