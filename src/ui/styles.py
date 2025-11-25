"""
UI 스타일 정의
"""

# 스플리터 스타일
SPLITTER_STYLE = """
QSplitter::handle {
    background-color: #d0d0d0;
}

QSplitter::handle:horizontal {
    width: 4px;
}

QSplitter::handle:vertical {
    height: 4px;
}

QSplitter::handle:hover {
    background-color: #909090;
}

QSplitter::handle:pressed {
    background-color: #606060;
}
"""

# 그룹박스 스타일
GROUPBOX_STYLE = """
QGroupBox {
    font-weight: bold;
    border: 1px solid #c0c0c0;
    border-radius: 5px;
    margin-top: 10px;
    padding-top: 10px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
    color: #303030;
}
"""

# 전체 애플리케이션 스타일
APP_STYLE = SPLITTER_STYLE + GROUPBOX_STYLE

