from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QTreeWidget, QTreeWidgetItem,
    QSplitter, QProgressBar
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from .backend_module import DocumentHandler
import logging

class KnowledgeBaseApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.document_handler = DocumentHandler(self.browser)
        self.populate_nav_tree()

    def setup_ui(self):
        """设置界面布局"""
        main_layout = QVBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("搜索知识库内容...")
        self.search_box.textChanged.connect(self.on_search)
        main_layout.addWidget(self.search_box)

        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.itemClicked.connect(self.on_item_clicked)

        self.browser = QWebEngineView()
        self.browser.setHtml("<h1>欢迎使用知识库助手</h1>")

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.hide()

        content_layout = QVBoxLayout()
        content_layout.addWidget(self.progress_bar)
        content_layout.addWidget(self.browser)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.tree_widget)
        content_widget = QWidget()
        content_widget.setLayout(content_layout)
        splitter.addWidget(content_widget)
        splitter.setSizes([200, 600])

        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

    def populate_nav_tree(self):
        """填充导航树"""
        resources = self.document_handler.resources.get("资源", {})
        for category, subcategories in resources.items():
            category_item = QTreeWidgetItem([category])
            self.tree_widget.addTopLevelItem(category_item)
            self.add_subcategories(category_item, subcategories)

    def add_subcategories(self, parent_item, subcategories):
        """递归添加子分类"""
        for subcategory, links in subcategories.items():
            if isinstance(links, dict):
                subcategory_item = QTreeWidgetItem([subcategory])
                parent_item.addChild(subcategory_item)
                self.add_subcategories(subcategory_item, links)
            else:
                link_item = QTreeWidgetItem([subcategory])
                link_item.setData(0, Qt.UserRole, links[0])
                parent_item.addChild(link_item)

    def on_item_clicked(self, item, column):
        """处理点击事件"""
        resource_path = item.data(0, Qt.UserRole)
        if resource_path:
            self.document_handler.load_content(resource_path)

    def on_search(self):
        """搜索功能"""
        query = self.search_box.text().strip().lower()
        self.tree_widget.collapseAll()
        if query:
            self.search_tree(query, self.tree_widget.invisibleRootItem())

    def search_tree(self, query, parent_item):
        """递归搜索树"""
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            if query in child.text(0).lower():
                child.setExpanded(True)
            self.search_tree(query, child)
