# bj/bji.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel, QFileDialog, \
    QListWidget
from PySide6.QtCore import Qt
import os


class NotePage(QWidget):
    def __init__(self):
        super().__init__()

        # 主布局
        main_layout = QHBoxLayout()

        # 左侧文件列表区域
        left_layout = QVBoxLayout()
        self.file_list = QListWidget()  # 显示文件夹中的 .txt 文件
        self.file_list.itemClicked.connect(self.display_file_content)  # 绑定点击事件
        left_layout.addWidget(QLabel("文件列表"))
        left_layout.addWidget(self.file_list)

        # 文件夹选择按钮
        folder_button = QPushButton("选择文件夹")
        folder_button.clicked.connect(self.select_folder)
        left_layout.addWidget(folder_button)

        # 新建文件按钮
        new_file_button = QPushButton("新建文件")
        new_file_button.clicked.connect(self.create_new_file)
        left_layout.addWidget(new_file_button)

        # 右侧文本编辑和保存区域
        right_layout = QVBoxLayout()
        self.text_edit = QTextEdit()
        right_layout.addWidget(QLabel("笔记内容"))
        right_layout.addWidget(self.text_edit)

        # 保存按钮
        save_button = QPushButton("保存笔记")
        save_button.clicked.connect(self.save_note)  # 保存笔记
        right_layout.addWidget(save_button)

        # 将左侧和右侧布局添加到主布局
        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)
        self.setLayout(main_layout)

        # 当前文件夹和当前打开文件路径
        self.current_folder = ""
        self.current_file_path = None

    def select_folder(self):
        """选择文件夹并显示其中的 .txt 文件"""
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            self.current_folder = folder
            self.load_txt_files()

    def load_txt_files(self):
        """加载选中文件夹中的 .txt 文件并显示在文件列表中"""
        self.file_list.clear()
        if self.current_folder:
            for file_name in os.listdir(self.current_folder):
                if file_name.endswith(".txt"):
                    self.file_list.addItem(file_name)
        # 清除当前打开的文件
        self.current_file_path = None
        self.text_edit.clear()

    def display_file_content(self, item):
        """显示选中文件的内容到文本编辑器"""
        self.current_file_path = os.path.join(self.current_folder, item.text())
        with open(self.current_file_path, "r", encoding="utf-8") as file:
            content = file.read()
            self.text_edit.setPlainText(content)

    def save_note(self):
        """保存当前编辑内容到文件。如果当前文件存在则覆盖，否则弹出对话框保存新文件"""
        if self.current_file_path:
            # 直接覆盖当前文件
            with open(self.current_file_path, "w", encoding="utf-8") as file:
                file.write(self.text_edit.toPlainText())
            print(f"已保存到 {self.current_file_path}")
        else:
            # 没有选择文件时，作为新文件保存
            self.save_as_new_file()

    def save_as_new_file(self):
        """弹出文件选择对话框，保存当前文本内容到新文件"""
        file_path, _ = QFileDialog.getSaveFileName(self, "保存笔记", self.current_folder, "Text Files (*.txt)")
        if file_path:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(self.text_edit.toPlainText())
            self.current_file_path = file_path  # 更新当前文件路径
            self.load_txt_files()  # 刷新文件列表

    def create_new_file(self):
        """创建新文件，并自动添加到文件列表中"""
        new_file_path, _ = QFileDialog.getSaveFileName(self, "新建文件", self.current_folder, "Text Files (*.txt)")
        if new_file_path:
            # 创建空文件
            with open(new_file_path, "w", encoding="utf-8") as file:
                file.write("")
            self.current_file_path = new_file_path  # 更新当前文件路径
            self.text_edit.clear()  # 清空编辑器
            self.load_txt_files()  # 刷新文件列表

