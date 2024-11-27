import os
import requests
import subprocess
import json
import logging
from PySide6.QtCore import QThread, Signal, QUrl
from PySide6.QtWidgets import QMessageBox
from .config import ZY_FOLDER, DOWNLOAD_FOLDER, EXTRACT_FOLDER, JY_FOLDER

# 配置日志格式
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


class DownloadThread(QThread):
    progress = Signal(int)  # 信号：用于更新进度条
    finished = Signal(str, str)  # 信号：下载完成（解压路径或错误消息）

    def __init__(self, key, download_links):
        super().__init__()
        self.key = key
        self.download_links = download_links
        self._is_running = True

    def run(self):
        try:
            temp_dir = DOWNLOAD_FOLDER
            os.makedirs(temp_dir, exist_ok=True)

            # 下载所有文件
            for i, link in enumerate(self.download_links):
                if not self._is_running:
                    logging.info("下载线程已停止")
                    return
                file_name = os.path.join(temp_dir, os.path.basename(link))
                if not os.path.exists(file_name):  # 避免重复下载
                    self.download_file(link, file_name)
                self.progress.emit(int((i + 1) / len(self.download_links) * 100))  # 更新进度条

            # 解压主 ZIP 文件
            main_zip = os.path.join(temp_dir, [f for f in self.download_links if f.endswith(".zip")][0].split("/")[-1])
            self.extract_with_7z(main_zip, EXTRACT_FOLDER)
            self.finished.emit(EXTRACT_FOLDER, None)  # 解压成功，返回解压路径
        except Exception as e:
            logging.error(f"下载或解压失败: {e}")
            self.finished.emit(None, str(e))  # 返回错误消息

    def stop(self):
        """停止线程"""
        self._is_running = False

    def download_file(self, url, save_path):
        """下载文件"""
        logging.info(f"下载文件: {url}")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(save_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                if not self._is_running:
                    logging.info("下载线程中止，文件未完成: {url}")
                    return
                file.write(chunk)

    def extract_with_7z(self, zip_file_path, output_folder):
        """使用 7-Zip 解压分割文件"""
        seven_zip_exe = os.path.join(JY_FOLDER, "7z.exe")
        if not os.path.exists(seven_zip_exe):
            raise FileNotFoundError(f"7z.exe 未找到，请检查路径: {seven_zip_exe}")

        logging.info(f"使用 7-Zip 解压文件: {zip_file_path}")
        command = [
            seven_zip_exe,
            "x",  # 解压命令
            zip_file_path,  # 要解压的主文件
            f"-o{output_folder}",  # 输出路径
            "-mmt",  # 启用多线程
            "-y"  # 自动回答 "yes"
        ]

        process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if process.returncode != 0:
            raise RuntimeError(f"7-Zip 解压失败: {process.stderr}")
        logging.info(f"解压完成: {output_folder}")


class DocumentHandler:
    def __init__(self, browser, progress_bar):
        self.browser = browser
        self.progress_bar = progress_bar
        self.resources = self.load_luj_json()
        self.download_links = self.load_wd_json()
        self.download_thread = None  # 初始化线程对象

    def load_luj_json(self):
        """加载 luj.json 文件并解析路径为绝对路径"""
        json_path = os.path.join(ZY_FOLDER, "luj.json")
        logging.info(f"加载 luj.json 文件，路径: {json_path}")
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # 遍历资源并将相对路径转换为绝对路径
                for category, subcategories in data.get("资源", {}).items():
                    for subcategory, links in subcategories.items():
                        if isinstance(links, list):
                            # 将所有相对路径转为基于 EXTRACT_FOLDER 的绝对路径
                            data["资源"][category][subcategory] = [
                                os.fspath(os.path.abspath(os.path.join(EXTRACT_FOLDER, link))) for link in links
                            ]
                logging.info("成功加载并解析 luj.json 文件")
                return data
        else:
            logging.error("luj.json 文件未找到")
            return {}

    def load_wd_json(self):
        """加载 wd.json 文件"""
        json_path = os.path.join(ZY_FOLDER, "wd.json")
        logging.info(f"加载 wd.json 文件，路径: {json_path}")
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                logging.info("成功加载 wd.json 文件")
                return json.load(f)
        else:
            logging.error("wd.json 文件未找到")
            return {}

    def load_content(self, path, key=None):
        """加载文档内容"""
        absolute_path = os.path.join(EXTRACT_FOLDER, path)
        logging.info(f"当前工作目录: {os.getcwd()}")
        logging.info(f"尝试加载文档路径: {absolute_path}")

        if os.path.exists(absolute_path):
            logging.info(f"加载本地文档: {absolute_path}")
            content = self.read_file(absolute_path)
            if content.strip():  # 检查内容是否为空
                self.browser.setHtml(content, baseUrl=QUrl.fromLocalFile(absolute_path))
            else:
                self.browser.setHtml("<h1>文档内容为空</h1>")
        else:
            logging.warning(f"文档未找到: {absolute_path}")
            self.browser.setHtml("<h1>文件未找到，尝试下载中...</h1>")
            if key:
                self.download_and_extract(key)
            else:
                self.browser.setHtml("<h1>文档未找到</h1>")

    def read_file(self, path):
        """读取文件内容"""
        try:
            with open(path, "r", encoding="utf-8") as file:
                content = file.read()
                logging.info(f"读取文件内容: {content[:500]}")  # 仅打印前500字符，避免日志过长
                return content
        except Exception as e:
            logging.error(f"读取文件出错: {path}, 错误: {e}")
            return f"<h1>无法加载文档: {path}</h1>"

    def download_and_extract(self, key):
        """异步下载并解压资源"""
        if key not in self.download_links.get("resources", {}):
            logging.error(f"资源 {key} 的下载链接未找到。")
            self.browser.setHtml(f"<h1>资源未找到: {key}</h1>")
            return

        links = self.download_links["resources"][key]
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.browser.setHtml("<h1>下载中，请稍后...</h1>")

        self.download_thread = DownloadThread(key, links)
        self.download_thread.progress.connect(self.progress_bar.setValue)
        self.download_thread.finished.connect(self.on_download_finished)
        self.download_thread.start()

    def on_download_finished(self, extract_path, error):
        """处理下载完成"""
        self.progress_bar.hide()
        if error:
            logging.error(f"下载失败: {error}")
            self.browser.setHtml(f"<h1>下载失败: {error}</h1>")
        else:
            logging.info(f"下载完成，解压路径: {extract_path}")
            self.browser.setHtml("<h1>解压完成，加载内容中...</h1>")
            self.load_content(self.resources["资源"]["Java"]["Java_8"][0])

    def cleanup(self):
        """释放资源"""
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.stop()
            self.download_thread.wait()
        logging.info("清理完成，安全退出")
