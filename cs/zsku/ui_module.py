# ui_module.py
import os
from PySide6.QtCore import QUrl, Qt, QPoint
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget, QSplitter, QProgressBar, \
    QListWidgetItem
from PySide6.QtWebEngineWidgets import QWebEngineView
from .backend_module import DocumentHandler
from .config import EXTRACT_FOLDER


class FloatingSearchResults(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 8px;
                padding: 5px;
            }
        """)
        layout = QVBoxLayout()
        self.results_list = QListWidget()
        layout.addWidget(self.results_list)
        self.setLayout(layout)

    def update_results(self, results):
        self.results_list.clear()
        for result in results:
            item = QListWidgetItem(result["class_name"])
            item.setData(Qt.UserRole, result["path"])
            self.results_list.addItem(item)

    def clear_results(self):
        self.results_list.clear()


class KnowledgeBaseApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.document_handler = DocumentHandler(self.browser)

        # 浮动搜索结果
        self.floating_results = FloatingSearchResults(self)
        self.floating_results.hide()

        # 绑定事件
        self.search_box.textChanged.connect(self.on_search)
        self.floating_results.results_list.itemClicked.connect(self.load_selected_result)
        self.nav_list.currentItemChanged.connect(self.load_content)

    def setup_ui(self):
        main_layout = QVBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search...")
        main_layout.addWidget(self.search_box)

        self.nav_list = QListWidget()
        self.nav_list.addItems(["Java", "MySQL"])
        content_layout = QHBoxLayout()
        content_layout.addWidget(self.nav_list)

        self.browser = QWebEngineView()
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        self.content_area = QVBoxLayout()
        self.content_area.addWidget(self.progress_bar)
        self.content_area.addWidget(self.browser)

        content_widget = QWidget()
        content_widget.setLayout(self.content_area)
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.nav_list)
        splitter.addWidget(content_widget)
        splitter.setSizes([150, 450])

        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

    def load_content(self):
        selected_text = self.nav_list.currentItem().text()
        if selected_text == "Java":
            if not self.document_handler.load_class_index():
                self.start_download()
            else:
                self.document_handler.load_java_content()
        elif selected_text == "MySQL":
            self.document_handler.load_mysql_content()

    def start_download(self):
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        download_thread = self.document_handler.download_jdk8_files()
        download_thread.progress_signal.connect(self.progress_bar.setValue)
        download_thread.finished_signal.connect(self.on_download_finished)
        download_thread.start()

    def on_download_finished(self, success):
        self.progress_bar.hide()
        if success:
            self.document_handler.load_java_content()

    def on_search(self):
        query = self.search_box.text().strip().lower()
        results = self.document_handler.search(query)
        self.floating_results.update_results(results)
        if results:
            self.show_floating_results()
        else:
            self.floating_results.hide()

    def show_floating_results(self):
        search_box_position = self.search_box.mapToGlobal(QPoint(0, self.search_box.height()))
        self.floating_results.move(search_box_position)
        self.floating_results.resize(self.search_box.width(), 200)
        self.floating_results.show()

    def load_selected_result(self, item):
        path = item.data(Qt.UserRole)
        full_path = self.document_handler.get_document_path(path)
        if os.path.exists(full_path):
            self.browser.setUrl(QUrl.fromLocalFile(full_path))
        self.floating_results.hide()
