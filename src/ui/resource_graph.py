"""
시스템 리소스 그래프 위젯
시간에 따른 CPU/GPU 사용량을 그래프로 표시합니다.
"""

from collections import deque
from typing import List, Tuple

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QPainterPath


class ResourceGraph(QWidget):
    """실시간 리소스 그래프 위젯"""

    def __init__(
        self,
        title: str = "Resource",
        color: str = "#4CAF50",
        max_points: int = 60,
        parent=None
    ):
        """
        Args:
            title: 그래프 제목
            color: 그래프 선 색상
            max_points: 최대 데이터 포인트 수 (시간 범위)
        """
        super().__init__(parent)
        self.title = title
        self.color = QColor(color)
        self.max_points = max_points
        self.data = deque([0.0] * max_points, maxlen=max_points)
        self.setMinimumHeight(80)
        self.setMinimumWidth(200)

    def add_value(self, value: float):
        """새 값 추가 (0-100)"""
        self.data.append(min(100, max(0, value)))
        self.update()

    def paintEvent(self, event):
        """그래프 그리기"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        margin_top = 20
        margin_bottom = 5
        margin_left = 5
        margin_right = 5
        
        graph_height = height - margin_top - margin_bottom
        graph_width = width - margin_left - margin_right

        # 배경
        painter.fillRect(0, 0, width, height, QColor("#1a1a2e"))

        # 제목
        painter.setPen(QPen(QColor("#ffffff")))
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        painter.setFont(font)
        
        # 현재 값
        current_value = self.data[-1] if self.data else 0
        painter.drawText(
            margin_left, 14,
            f"{self.title}: {current_value:.0f}%"
        )

        # 그리드 (수평선)
        painter.setPen(QPen(QColor("#333355"), 1, Qt.PenStyle.DotLine))
        for i in range(1, 4):
            y = margin_top + (graph_height * i // 4)
            painter.drawLine(margin_left, y, width - margin_right, y)

        # 그래프 영역 테두리
        painter.setPen(QPen(QColor("#444466"), 1))
        painter.drawRect(
            margin_left, margin_top,
            graph_width, graph_height
        )

        # 데이터가 없으면 종료
        if not self.data or len(self.data) < 2:
            return

        # 그래프 그리기
        points = []
        data_list = list(self.data)
        
        for i, value in enumerate(data_list):
            x = margin_left + (i * graph_width / (self.max_points - 1))
            y = margin_top + graph_height - (value * graph_height / 100)
            points.append((x, y))

        # 채우기 영역 (그라데이션 효과)
        if points:
            fill_path = QPainterPath()
            fill_path.moveTo(margin_left, margin_top + graph_height)
            
            for x, y in points:
                fill_path.lineTo(x, y)
            
            fill_path.lineTo(points[-1][0], margin_top + graph_height)
            fill_path.closeSubpath()
            
            fill_color = QColor(self.color)
            fill_color.setAlpha(50)
            painter.fillPath(fill_path, fill_color)

        # 선 그리기
        pen = QPen(self.color, 2)
        painter.setPen(pen)
        
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        # 현재 값 점
        if points:
            x, y = points[-1]
            painter.setBrush(self.color)
            painter.drawEllipse(int(x) - 3, int(y) - 3, 6, 6)


class MultiResourceGraph(QWidget):
    """여러 리소스를 하나의 그래프에 표시"""

    def __init__(
        self,
        title: str = "Resources",
        max_points: int = 60,
        parent=None
    ):
        super().__init__(parent)
        self.title = title
        self.max_points = max_points
        self.series: List[Tuple[str, QColor, deque]] = []
        self.setMinimumHeight(100)
        self.setMinimumWidth(200)

    def add_series(self, name: str, color: str):
        """새 데이터 시리즈 추가"""
        self.series.append((
            name,
            QColor(color),
            deque([0.0] * self.max_points, maxlen=self.max_points)
        ))

    def add_value(self, series_index: int, value: float):
        """특정 시리즈에 값 추가"""
        if 0 <= series_index < len(self.series):
            self.series[series_index][2].append(min(100, max(0, value)))
            self.update()

    def paintEvent(self, event):
        """그래프 그리기"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        margin_top = 25
        margin_bottom = 5
        margin_left = 5
        margin_right = 5
        
        graph_height = height - margin_top - margin_bottom
        graph_width = width - margin_left - margin_right

        # 배경
        painter.fillRect(0, 0, width, height, QColor("#1a1a2e"))

        # 제목과 범례
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        painter.setFont(font)
        
        x_offset = margin_left
        for name, color, data in self.series:
            current_value = data[-1] if data else 0
            text = f"{name}: {current_value:.0f}%"
            
            painter.setPen(QPen(color))
            painter.drawText(x_offset, 14, text)
            x_offset += len(text) * 7 + 15

        # 그리드
        painter.setPen(QPen(QColor("#333355"), 1, Qt.PenStyle.DotLine))
        for i in range(1, 4):
            y = margin_top + (graph_height * i // 4)
            painter.drawLine(margin_left, y, width - margin_right, y)

        # 테두리
        painter.setPen(QPen(QColor("#444466"), 1))
        painter.drawRect(margin_left, margin_top, graph_width, graph_height)

        # 각 시리즈 그래프
        for name, color, data in self.series:
            if not data or len(data) < 2:
                continue

            points = []
            data_list = list(data)
            
            for i, value in enumerate(data_list):
                x = margin_left + (i * graph_width / (self.max_points - 1))
                y = margin_top + graph_height - (value * graph_height / 100)
                points.append((x, y))

            # 선 그리기
            pen = QPen(color, 2)
            painter.setPen(pen)
            
            for i in range(len(points) - 1):
                x1, y1 = points[i]
                x2, y2 = points[i + 1]
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))




