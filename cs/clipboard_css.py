# clipboard_css.py

# 样式常量
DEFAULT_FRAME_STYLE = """
    QFrame {
        background-color: #FFFFFF;
        border-radius: 15px;
        padding: 10px;
        border: 2px solid transparent;
        margin: 10px;  /* 控制框架与其他元素的间距 */
    }
"""
HIGHLIGHTED_FRAME_STYLE = """
    QFrame {
        background-color: #E6F7FF;
        border-radius: 15px;
        padding: 10px;
        border: 2px solid #1890FF;
        margin: 10px;
    }
"""
LABEL_STYLE = "border: none; padding: 5px; margin: 5px;"  # 设置标签的内外边距
TIME_LABEL_STYLE = "color: #8C8C8C; border: none; padding: 0px; margin: 5px;"
FOOTER_STYLE = "background-color: #1890FF; border-radius: 0px 0px 10px 10px; border: none; padding: 2px;"
SCROLL_AREA_STYLE = "background-color: #F0F2F5; padding: 10px; margin: 0px;"
