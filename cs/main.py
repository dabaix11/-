from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, \
    QStackedWidget, QWidget, QLabel
from PySide6.QtGui import QIcon, QPalette, QColor
from PySide6.QtCore import QThread, Signal, Qt
import os
import sys
import keyboard
from zsku.ui_module import KnowledgeBaseApp
from clipboard_manager import ClipboardWindow
from settings import SettingsPage
from bj.bji import NotePage


class GlobalShortcutListener(QThread):
    """线程类，用于监听全局快捷键"""
    triggered = Signal()  # 自定义信号，用于唤出剪贴板

    def __init__(self, shortcut="ctrl+k"):
        super().__init__()
        self.shortcut = shortcut

    def run(self):
        """线程运行时启动快捷键监听"""
        keyboard.add_hotkey(self.shortcut, self.triggered.emit)  # 绑定全局快捷键
        keyboard.wait()  # 保持线程运行

    def update_shortcut(self, new_shortcut):
        """更新全局快捷键"""
        keyboard.remove_hotkey(self.shortcut)  # 移除旧快捷键
        self.shortcut = new_shortcut  # 更新快捷键
        keyboard.add_hotkey(self.shortcut, self.triggered.emit)  # 绑定新快捷键


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("剪切助手 v0.0.8")
        self.setGeometry(100, 100, 1200, 800)  # 调整窗口大小

        # 图标文件路径
        icon_dir = os.path.join(os.path.dirname(__file__), 'ioc')  # 图标目录
        icon_clipboard = os.path.join(icon_dir, 'jtb.png')  # 剪贴板图标
        icon_knowledge = os.path.join(icon_dir, 'zsk.png')  # 知识库图标
        icon_note = os.path.join(icon_dir, 'bj.png')  # 笔记图标

        # 设置整体背景颜色
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("#F8F5FF"))  # 使用淡紫色背景
        self.setPalette(palette)

        # 初始化剪贴板窗口
        self.clipboard_window = ClipboardWindow()

        # 左侧导航栏
        self.navbar = QListWidget()
        self.navbar.setFixedWidth(200)  # 调整宽度
        self.navbar.setStyleSheet("""
            QListWidget {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #A892FF, stop: 1 #7358FF
                );
                border-radius: 15px;
                padding: 10px;
            }
            QListWidget::item {
                padding: 20px;
                margin: 10px 0;  /* 设置每个图标的间距 */
                color: white;
                text-align: center;
                border-radius: 10px;
            }
            QListWidget::item:selected {
                background-color: #5B42D1;  /* 深紫色选中效果 */
                border: 2px solid #FFFFFF; /* 添加选中边框 */
            }
            QListWidget::item:hover {
                background-color: #B59BFF;  /* 浅紫色悬停效果 */
            }
        """)

        # 添加带图标的导航项
        item_clipboard = QListWidgetItem(QIcon(icon_clipboard), "剪贴板")
        item_clipboard.setTextAlignment(Qt.AlignHCenter)  # 文字居中
        item_knowledge = QListWidgetItem(QIcon(icon_knowledge), "知识库")
        item_knowledge.setTextAlignment(Qt.AlignHCenter)
        item_note = QListWidgetItem(QIcon(icon_note), "笔记")
        item_note.setTextAlignment(Qt.AlignHCenter)

        self.navbar.addItem(item_clipboard)
        self.navbar.addItem(item_knowledge)
        self.navbar.addItem(item_note)

        # 中央内容区域11
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("""
            QStackedWidget {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #FFFFFF, stop: 1 #F8F5FF
                );
                border-radius: 15px;
                padding: 20px;
                border: 1px solid #E6E6E6;
                box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.1); /* 添加阴影 */
            }
        """)

        # 各个页面
        self.settings_page = SettingsPage()
        self.knowledge_base = KnowledgeBaseApp()
        self.note_page = NotePage()

        # 添加到堆叠窗口中
        self.stacked_widget.addWidget(self.settings_page)
        self.stacked_widget.addWidget(self.knowledge_base)
        self.stacked_widget.addWidget(self.note_page)

        # 主布局
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.navbar)
        main_layout.addWidget(self.stacked_widget)
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # 绑定导航栏点击事件
        self.navbar.currentRowChanged.connect(self.display_page)

        # 启动全局快捷键监听线程
        self.global_shortcut = GlobalShortcutListener("ctrl+k")
        self.global_shortcut.triggered.connect(self.toggle_clipboard_visibility)
        self.global_shortcut.start()

        # 将 SettingsPage 中的快捷键信号连接到 update_shortcut 方法
        self.settings_page.shortcut_changed.connect(self.update_shortcut)

    def display_page(self, index):
        self.stacked_widget.setCurrentIndex(index)

    def toggle_clipboard_visibility(self):
        """切换剪贴板窗口的显示/隐藏"""
        if self.clipboard_window.isVisible():
            self.clipboard_window.hide()
        else:
            self.clipboard_window.show()

    def update_shortcut(self, new_shortcut):
        """更新全局快捷键"""
        shortcut_str = new_shortcut.lower()
        self.global_shortcut.update_shortcut(shortcut_str)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
