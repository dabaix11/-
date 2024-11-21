from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit
from PySide6.QtCore import Signal, Qt


class SettingsPage(QWidget):
    shortcut_changed = Signal(str)  # 用于发射快捷键变化信号

    def __init__(self):
        super().__init__()

        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #FDEFF9, stop: 1 #F8F5FF
                );
                border-radius: 15px;
                padding: 20px;
            }
            QLabel {
                font-size: 16px;
                color: #4A4A4A;  /* 深灰色字体 */
            }
            QLineEdit {
                background: white;
                border: 1px solid #D6D6D6;
                border-radius: 10px;
                padding: 5px 10px;
                font-size: 16px;
                color: #333333;
            }
        """)

        self.setLayout(QVBoxLayout())
        self.label = QLabel("设置快捷键: Ctrl + 任意按键")
        self.layout().addWidget(self.label)

        # 显示快捷键的框，用户按下快捷键时显示
        self.shortcut_input = QLineEdit()
        self.shortcut_input.setPlaceholderText("请按 Ctrl + 任意键...")
        self.shortcut_input.setReadOnly(True)  # 设置为只读，防止用户手动编辑
        self.shortcut_input.setText("Ctrl + K")  # 设置默认值为 "Ctrl + K"
        self.layout().addWidget(self.shortcut_input)

        # 错误提示标签
        self.error_label = QLabel()
        self.layout().addWidget(self.error_label)

        # 监听按键事件
        self.setFocusPolicy(Qt.StrongFocus)  # 设置控件为可接受焦点，以便捕捉键盘事件

    def keyPressEvent(self, event):
        """监听按键事件"""
        if event.modifiers() == Qt.ControlModifier:  # 判断是否按下了Ctrl键
            key_code = event.key()  # 获取按键的虚拟键码
            key = None

            # 字母键（A-Z）
            if Qt.Key_A <= key_code <= Qt.Key_Z:
                key = chr(key_code)  # 将虚拟键码转化为字符
            # 数字键（0-9）
            elif Qt.Key_0 <= key_code <= Qt.Key_9:
                key = chr(key_code)
            # 空格键
            elif key_code == Qt.Key_Space:
                key = "space"
            # 回车键
            elif key_code == Qt.Key_Enter or key_code == Qt.Key_Return:
                key = "enter"
            # ESC 键
            elif key_code == Qt.Key_Escape:
                key = "escape"
            # Backspace 键
            elif key_code == Qt.Key_Backspace:
                key = "backspace"
            # 特殊符号键通过 text() 获取字符
            else:
                key = event.text()  # 获取按下键的文本字符

            # 如果获取到有效的按键
            if key:
                # 更新快捷键框显示
                shortcut = f"Ctrl + {key}"
                self.shortcut_input.setText(shortcut)
                # 发射信号更新快捷键
                self.shortcut_changed.emit(shortcut)
                self.error_label.setText("")  # 清除错误信息
            else:
                # 如果按下的是无效的键（如功能键等），可以不更新快捷键
                self.error_label.setText("只支持：Ctrl + 字母、数字和常见符号键")
        else:
            # 如果没有按下Ctrl，提示用户错误
            self.error_label.setText("只支持：Ctrl + 任意按键")

    def clear_error(self):
        """清除错误信息"""
        self.error_label.setText("")
