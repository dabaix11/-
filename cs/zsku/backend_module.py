# backend_module.py
import os
import json
import requests
import subprocess
import logging
from PySide6.QtCore import QThread, Signal, QUrl
from .config import DOWNLOAD_FOLDER, EXTRACT_FOLDER, JY_FOLDER, ZY_FOLDER

# 设置日志记录
logging.basicConfig(
    filename='logs.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
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
            logging.error(f"Download and extraction error: {e}")
            self.finished_signal.emit(False)

    def download_files(self, urls):
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
                        progress = int((downloaded_size / total_size) * 50)  # 下载占总进度的 50%
                        self.progress_signal.emit(progress)
                logging.info(f"Downloaded {file_name}")

    def extract_files(self):
        if not os.path.exists(EXTRACT_FOLDER):
            os.makedirs(EXTRACT_FOLDER)
        for file_name in os.listdir(DOWNLOAD_FOLDER):
            file_path = os.path.join(DOWNLOAD_FOLDER, file_name)
            if os.path.isfile(file_path) and file_name.endswith(('.zip', '.tar', '.7z')):
                try:
                    subprocess.run([self.seven_zip_path, "x", file_path, f"-o{EXTRACT_FOLDER}"], check=True)
                    logging.info(f"Extracted {file_name}")
                    self.progress_signal.emit(75)
                except subprocess.CalledProcessError as e:
                    logging.error(f"Failed to extract {file_name}: {e}")
        self.progress_signal.emit(100)

class DocumentHandler:
    def __init__(self, browser):
        self.browser = browser
        self.class_index = []
        self.load_class_index()

    def load_class_index(self):
        index_path = os.path.join(EXTRACT_FOLDER, "jdk8", "class_index.json")
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                self.class_index = json.load(f)
            logging.info("Class index loaded successfully")
            return True
        logging.warning("Class index not found, downloading files.")
        return False

    def load_java_content(self):
        java_path = os.path.join(EXTRACT_FOLDER, "jdk8", "doc", "java8", "index00a1.html")
        if os.path.exists(java_path):
            self.browser.setUrl(QUrl.fromLocalFile(java_path))
            logging.info("Java content loaded.")
        else:
            logging.warning("Java documentation not found.")

    def load_mysql_content(self):
        """加载 MySQL 文档的默认页面"""
        mysql_path = os.path.join(EXTRACT_FOLDER, "mysql", "doc", "mysql", "index.html")
        if os.path.exists(mysql_path):
            self.browser.setUrl(QUrl.fromLocalFile(mysql_path))
            logging.info("MySQL content loaded.")
        else:
            logging.warning("MySQL documentation not found.")

    def download_jdk8_files(self):
        json_path = os.path.join(ZY_FOLDER, "wd.json")
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        urls = data.get("urls", [])
        self.download_thread = DownloadAndExtractThread(urls, EXTRACT_FOLDER)
        return self.download_thread

    def search(self, query):
        return [
            item for item in self.class_index
            if query.lower() in item["class_name"].lower()
        ]

    def get_document_path(self, class_path):
        return os.path.join(EXTRACT_FOLDER, class_path)
