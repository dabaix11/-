from PySide6.QtCore import Qt, QUrl, QMimeData, QPoint, QByteArray, QBuffer, QIODevice
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QScrollArea, QFrame, QLabel, QHBoxLayout
)
from PySide6.QtGui import QFont, QPixmap, QIcon, QDrag
from urllib.parse import unquote
from datetime import datetime
import os
import requests
from tempfile import gettempdir
import mimetypes
import base64
import re

# 从 clipboard_css.py 导入样式常量
from clipboard_css import (
    DEFAULT_FRAME_STYLE,
    HIGHLIGHTED_FRAME_STYLE,
    LABEL_STYLE,
    TIME_LABEL_STYLE,
    FOOTER_STYLE,
    SCROLL_AREA_STYLE
)


class ClipboardItem(QFrame):
    def __init__(self, content, timestamp, clipboard_window, file_type=None, display_name=None):
        super().__init__()
        self.content = content
        self.clipboard_window = clipboard_window
        self.file_type = file_type
        self.display_name = display_name or content
        self.setFixedSize(388, 388)
        self.setStyleSheet(DEFAULT_FRAME_STYLE)  # 设置样式表
        self.init_ui(timestamp)

    def init_ui(self, timestamp):
        # 主布局
        main_layout = QVBoxLayout(self)

        # 头部布局
        header_layout = QHBoxLayout()

        # 图标
        icon_label = QLabel()
        icon_label.setPixmap(QIcon("icon.png").pixmap(24, 24))
        icon_label.setStyleSheet(LABEL_STYLE)
        header_layout.addWidget(icon_label)

        # 时间标签
        time_label = QLabel(timestamp)
        time_label.setFont(QFont("Arial", 8))
        time_label.setStyleSheet(TIME_LABEL_STYLE)
        header_layout.addWidget(time_label)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # 分隔线
        separator = QLabel()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #E8E8E8;")
        main_layout.addWidget(separator)

        # 内容显示
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setStyleSheet(LABEL_STYLE + "font-size: 14px;")
        self.display_content()
        main_layout.addWidget(self.label, alignment=Qt.AlignCenter)

        # 底部
        footer = QWidget()
        footer.setFixedHeight(5)
        footer.setStyleSheet(FOOTER_STYLE)
        main_layout.addWidget(footer)

    def display_content(self):
        if self.file_type == "image":
            self.label.setPixmap(self.content.scaled(350, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        elif self.file_type == "text":
            self.label.setText(self.content)
        else:
            self.label.setText(f"{self.file_type.capitalize()} 文件: {self.display_name}")

    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        if self.file_type == "image":
            image = self.content.toImage()
            clipboard.setImage(image)
        elif self.file_type == "text":
            clipboard.setText(self.content)
        else:
            mime_data = QMimeData()
            mime_data.setUrls([QUrl.fromLocalFile(self.content)])
            clipboard.setMimeData(mime_data)
        self.clipboard_window.block_add = True

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
        self.clipboard_window.clear_selection()
        self.setStyleSheet(HIGHLIGHTED_FRAME_STYLE)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not self.drag_start_position:
            return
        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return
        if self.file_type == "image":
            drag = QDrag(self)
            mime_data = QMimeData()

            # 检查是否是 QPixmap 实例，如果是，则保存为临时文件
            if isinstance(self.content, QPixmap):
                temp_dir = gettempdir()
                temp_file_path = os.path.join(temp_dir, "clipboard_image.png")
                self.content.save(temp_file_path, "PNG")  # 将图片保存为 PNG 文件
                mime_data.setUrls([QUrl.fromLocalFile(temp_file_path)])  # 设置文件路径

            elif isinstance(self.content, str) and os.path.isfile(self.content):  # 如果是文件路径
                mime_data.setUrls([QUrl.fromLocalFile(self.content)])  # 使用文件路径

            drag.setMimeData(mime_data)

            # 设置图标，用于拖拽效果
            if isinstance(self.content, QPixmap):
                pixmap = self.content.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            else:
                pixmap = QPixmap(self.content).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)

            drag.setPixmap(pixmap)
            drag.exec(Qt.CopyAction)
        super().mouseMoveEvent(event)

    def mouseDoubleClickEvent(self, event):
        # 双击复制内容
        self.copy_to_clipboard()
        super().mouseDoubleClickEvent(event)


class ClipboardWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("剪贴板内容")
        self.resize(420, 800)
        self.block_add = False
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)
        self.init_ui()

        # 监听剪贴板
        self.clipboard = QApplication.clipboard()
        self.clipboard.dataChanged.connect(self.update_clipboard_content)

        # 将窗口移动到右侧
        self.move_to_right()
        self.drag_start_position = None  # 用于窗口拖拽的起始位置

    def init_ui(self):
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll_area.setStyleSheet(SCROLL_AREA_STYLE)

        # 滚动内容
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(15)
        self.scroll_layout.setContentsMargins(10, 10, 10, 10)
        scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(scroll_area)

    def add_clipboard_item(self, content, file_type=None, display_name=None):
        if self.block_add:
            self.block_add = False
            return
        timestamp = datetime.now().strftime("%H:%M")
        item = ClipboardItem(content, timestamp, self, file_type=file_type, display_name=display_name)
        self.scroll_layout.addWidget(item)

    def clear_selection(self):
        for i in range(self.scroll_layout.count()):
            widget = self.scroll_layout.itemAt(i).widget()
            widget.setStyleSheet(DEFAULT_FRAME_STYLE)

    def update_clipboard_content(self):
        mime_data = self.clipboard.mimeData()
        if mime_data.hasText():
            text = mime_data.text()
            if self.handle_base64_image(text):
                return
            elif text.startswith("file:///"):
                self.handle_file_url(text)
            elif text.startswith("http"):
                self.handle_http_url(text)
            else:
                self.add_clipboard_item(text, "text")
        elif mime_data.hasImage():
            image = self.clipboard.image()
            pixmap = QPixmap.fromImage(image)
            self.add_clipboard_item(pixmap, "image")

    def handle_base64_image(self, text):
        base64_pattern = r"^data:image/([a-zA-Z]*);base64,([^\"]*)$"
        match = re.match(base64_pattern, text)
        if match:
            image_data = match.group(2)
            image_bytes = base64.b64decode(image_data)
            pixmap = QPixmap()
            if pixmap.loadFromData(image_bytes):
                self.add_clipboard_item(pixmap, "image")
                return True
        return False

    def handle_file_url(self, text):
        local_path = unquote(text[8:])
        file_type, _ = mimetypes.guess_type(local_path)
        if file_type:
            if file_type.startswith("image"):
                pixmap = QPixmap(local_path)
                if not pixmap.isNull():
                    self.add_clipboard_item(pixmap, "image")
            else:
                display_name = os.path.basename(local_path)
                self.add_clipboard_item(local_path, file_type.split('/')[0], display_name)

    def handle_http_url(self, url):
        image_path = self.download_image(url)
        if image_path:
            pixmap = QPixmap(image_path)
            self.add_clipboard_item(pixmap, "image")

    def download_image(self, url):
        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                temp_dir = gettempdir()
                file_extension = os.path.splitext(url)[1] or ".jpg"
                file_path = os.path.join(temp_dir, f"clipboard_image{file_extension}")
                with open(file_path, "wb") as f:
                    f.write(response.content)
                return file_path
        except Exception as e:
            print("下载图片失败:", e)
        return None

    def move_to_right(self):
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        x = screen_geometry.width() - self.width() - 10  # 距离右边缘10像素
        y = screen_geometry.y() + 10  # 距离顶部10像素
        self.move(QPoint(x, y))

    def showEvent(self, event):
        self.move_to_right()
        super().showEvent(event)

    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
