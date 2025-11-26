"""
프로젝트 관리 다이얼로그
프로젝트별 목표 설정, 진행률 관리, AI 추천 기능을 제공합니다.
"""

import logging
from datetime import date, timedelta
from typing import Optional, List, Dict

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QComboBox, QDateEdit,
    QTextEdit, QTableWidget, QTableWidgetItem,
    QGroupBox, QSpinBox, QLineEdit, QWidget,
    QHeaderView, QMessageBox, QSplitter, QProgressBar,
    QFormLayout
)
from PySide6.QtCore import Qt, Slot, QDate, QThread, Signal
from PySide6.QtGui import QFont, QColor

from ..database.db_manager import get_db_manager
from ..ai.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class AIRecommendWorker(QThread):
    """AI 추천 워커"""
    
    progress = Signal(str)
    result_ready = Signal(str)
    error = Signal(str)
    finished = Signal()
    
    def __init__(self, project_data: str, model: str = "llama3.2:latest"):
        super().__init__()
        self.project_data = project_data
        self.model = model
    
    def run(self):
        try:
            self.progress.emit("AI 분석 중...")
            
            client = OllamaClient(model=self.model)
            if not client.is_available():
                self.error.emit("Ollama 서버에 연결할 수 없습니다.")
                return
            
            result = client.generate_project_recommendation(self.project_data)
            
            if result:
                self.result_ready.emit(result)
            else:
                self.error.emit("AI 추천 생성에 실패했습니다.")
                
        except Exception as e:
            logger.error(f"AI 추천 오류: {e}")
            self.error.emit(f"추천 오류: {str(e)}")
        finally:
            self.finished.emit()


class ProjectManagerDialog(QDialog):
    """프로젝트 관리 다이얼로그"""
    
    PRIORITY_OPTIONS = ["높음", "보통", "낮음"]
    STATUS_OPTIONS = ["진행중", "완료", "보류", "계획중"]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = get_db_manager()
        self.worker = None
        self.current_project_id = None
        
        self._init_ui()
        self._load_projects()
    
    def _init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("프로젝트 관리")
        self.setMinimumSize(1000, 700)
        self.resize(1100, 750)
        
        layout = QVBoxLayout(self)
        
        # 탭 위젯
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget, stretch=1)
        
        # 탭1: 프로젝트 목록
        self.tab_widget.addTab(self._create_project_list_tab(), "📋 프로젝트 목록")
        
        # 탭2: 프로젝트 상세/편집
        self.tab_widget.addTab(self._create_project_detail_tab(), "📝 프로젝트 상세")
        
        # 탭3: AI 추천
        self.tab_widget.addTab(self._create_ai_recommend_tab(), "🤖 AI 추천")
        
        # 하단 버튼
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.close_btn = QPushButton("닫기")
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)
        
        layout.addLayout(btn_layout)
    
    def _create_project_list_tab(self) -> QWidget:
        """프로젝트 목록 탭"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 상단 버튼
        btn_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("🔄 새로고침")
        self.refresh_btn.clicked.connect(self._load_projects)
        btn_layout.addWidget(self.refresh_btn)
        
        self.auto_progress_btn = QPushButton("📊 진행률 자동 계산")
        self.auto_progress_btn.setToolTip("최근 30일 업무 기준으로 진행률 자동 계산")
        self.auto_progress_btn.clicked.connect(self._on_auto_calculate)
        btn_layout.addWidget(self.auto_progress_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # 프로젝트 테이블
        self.project_table = QTableWidget()
        self.project_table.setColumnCount(8)
        self.project_table.setHorizontalHeaderLabels([
            "프로젝트명", "카테고리", "진행률", "목표", "목표일", 
            "우선순위", "상태", "담당자"
        ])
        self.project_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.project_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.project_table.doubleClicked.connect(self._on_project_double_click)
        layout.addWidget(self.project_table)
        
        return widget
    
    def _create_project_detail_tab(self) -> QWidget:
        """프로젝트 상세 탭"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 프로젝트 선택
        select_layout = QHBoxLayout()
        select_layout.addWidget(QLabel("프로젝트 선택:"))
        
        self.project_combo = QComboBox()
        self.project_combo.currentIndexChanged.connect(self._on_project_selected)
        select_layout.addWidget(self.project_combo, stretch=1)
        
        layout.addLayout(select_layout)
        
        # 상세 정보 폼
        form_group = QGroupBox("프로젝트 정보")
        form_layout = QFormLayout(form_group)
        
        self.project_name_label = QLabel("-")
        self.project_name_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        form_layout.addRow("프로젝트명:", self.project_name_label)
        
        self.category_label = QLabel("-")
        form_layout.addRow("카테고리:", self.category_label)
        
        # 진행률
        progress_layout = QHBoxLayout()
        self.current_progress_spin = QSpinBox()
        self.current_progress_spin.setRange(0, 100)
        self.current_progress_spin.setSuffix("%")
        progress_layout.addWidget(self.current_progress_spin)
        
        progress_layout.addWidget(QLabel("/"))
        
        self.target_progress_spin = QSpinBox()
        self.target_progress_spin.setRange(0, 100)
        self.target_progress_spin.setValue(100)
        self.target_progress_spin.setSuffix("%")
        progress_layout.addWidget(self.target_progress_spin)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumWidth(200)
        progress_layout.addWidget(self.progress_bar)
        
        progress_layout.addStretch()
        form_layout.addRow("진행률 (현재/목표):", progress_layout)
        
        # 목표일
        self.target_date_edit = QDateEdit()
        self.target_date_edit.setCalendarPopup(True)
        self.target_date_edit.setDate(QDate.currentDate().addMonths(1))
        form_layout.addRow("목표 완료일:", self.target_date_edit)
        
        # 우선순위
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(self.PRIORITY_OPTIONS)
        form_layout.addRow("우선순위:", self.priority_combo)
        
        # 상태
        self.status_combo = QComboBox()
        self.status_combo.addItems(self.STATUS_OPTIONS)
        form_layout.addRow("상태:", self.status_combo)
        
        # 설명
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        form_layout.addRow("설명:", self.description_edit)
        
        layout.addWidget(form_group)
        
        # 저장 버튼
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        
        self.save_btn = QPushButton("💾 저장")
        self.save_btn.setStyleSheet("font-size: 11pt; padding: 8px 20px;")
        self.save_btn.clicked.connect(self._on_save_project)
        save_layout.addWidget(self.save_btn)
        
        layout.addLayout(save_layout)
        layout.addStretch()
        
        return widget
    
    def _create_ai_recommend_tab(self) -> QWidget:
        """AI 추천 탭"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 설명
        info_label = QLabel(
            "📌 AI가 현재 프로젝트 상태를 분석하여 다음 할 일과 우선순위를 추천합니다."
        )
        info_label.setStyleSheet("color: #666; font-size: 10pt; padding: 10px;")
        layout.addWidget(info_label)
        
        # 분석 버튼
        btn_layout = QHBoxLayout()
        
        self.ai_analyze_btn = QPushButton("🤖 AI 분석 및 추천 받기")
        self.ai_analyze_btn.setStyleSheet("font-size: 11pt; padding: 10px 20px;")
        self.ai_analyze_btn.clicked.connect(self._on_ai_recommend)
        btn_layout.addWidget(self.ai_analyze_btn)
        
        self.ai_progress = QProgressBar()
        self.ai_progress.setVisible(False)
        btn_layout.addWidget(self.ai_progress)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # 결과 표시
        self.ai_result_text = QTextEdit()
        self.ai_result_text.setReadOnly(True)
        self.ai_result_text.setPlaceholderText(
            "AI 분석 결과가 여기에 표시됩니다.\n\n"
            "분석 내용:\n"
            "• 프로젝트별 현재 상태 평가\n"
            "• 다음에 해야 할 작업 추천\n"
            "• 우선순위 조정 제안\n"
            "• 일정 위험 분석"
        )
        layout.addWidget(self.ai_result_text)
        
        return widget
    
    def _load_projects(self):
        """프로젝트 목록 로드"""
        try:
            projects = self.db.get_projects_with_stats()
            
            # 테이블 업데이트
            self.project_table.setRowCount(len(projects))
            
            for row, project in enumerate(projects):
                self.project_table.setItem(row, 0, QTableWidgetItem(
                    project.get('name', '-')
                ))
                self.project_table.setItem(row, 1, QTableWidgetItem(
                    project.get('category') or '-'
                ))
                
                # 진행률 (색상 표시)
                current = project.get('current_progress', 0) or 0
                target = project.get('target_progress', 100) or 100
                progress_item = QTableWidgetItem(f"{current}%")
                
                if current >= target:
                    progress_item.setForeground(QColor(76, 175, 80))  # 녹색
                elif current >= target * 0.7:
                    progress_item.setForeground(QColor(255, 152, 0))  # 주황
                else:
                    progress_item.setForeground(QColor(244, 67, 54))  # 빨강
                
                self.project_table.setItem(row, 2, progress_item)
                self.project_table.setItem(row, 3, QTableWidgetItem(f"{target}%"))
                self.project_table.setItem(row, 4, QTableWidgetItem(
                    str(project.get('target_date') or '-')
                ))
                self.project_table.setItem(row, 5, QTableWidgetItem(
                    project.get('priority') or '보통'
                ))
                self.project_table.setItem(row, 6, QTableWidgetItem(
                    project.get('status') or '진행중'
                ))
                
                # 담당자 (task_count 기반)
                member_count = project.get('member_count', 0)
                self.project_table.setItem(row, 7, QTableWidgetItem(
                    f"{member_count}명"
                ))
            
            # 콤보박스 업데이트
            self.project_combo.clear()
            self.project_combo.addItem("-- 선택하세요 --", None)
            for project in projects:
                self.project_combo.addItem(
                    project['name'], 
                    project['id']
                )
            
            logger.info(f"프로젝트 {len(projects)}개 로드 완료")
            
        except Exception as e:
            logger.error(f"프로젝트 로드 오류: {e}")
            QMessageBox.critical(self, "오류", f"프로젝트 로드 실패: {str(e)}")
    
    @Slot()
    def _on_auto_calculate(self):
        """진행률 자동 계산"""
        try:
            projects = self.db.get_all_projects()
            updated = 0
            
            for project in projects:
                progress = self.db.calculate_project_progress(project['id'])
                if progress > 0:
                    self.db.update_project(project['id'], current_progress=progress)
                    updated += 1
            
            self._load_projects()
            QMessageBox.information(
                self, "완료", 
                f"진행률 자동 계산 완료!\n업데이트된 프로젝트: {updated}개"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"계산 실패: {str(e)}")
    
    @Slot()
    def _on_project_double_click(self):
        """프로젝트 더블클릭"""
        row = self.project_table.currentRow()
        if row >= 0:
            project_name = self.project_table.item(row, 0).text()
            # 콤보박스에서 해당 프로젝트 선택
            index = self.project_combo.findText(project_name)
            if index >= 0:
                self.project_combo.setCurrentIndex(index)
                self.tab_widget.setCurrentIndex(1)  # 상세 탭으로 이동
    
    @Slot(int)
    def _on_project_selected(self, index: int):
        """프로젝트 선택"""
        project_id = self.project_combo.currentData()
        
        if not project_id:
            self.current_project_id = None
            self.project_name_label.setText("-")
            self.category_label.setText("-")
            return
        
        self.current_project_id = project_id
        
        try:
            projects = self.db.get_all_projects()
            project = next((p for p in projects if p['id'] == project_id), None)
            
            if project:
                self.project_name_label.setText(project['name'])
                self.category_label.setText(project.get('category') or '-')
                self.current_progress_spin.setValue(project.get('current_progress') or 0)
                self.target_progress_spin.setValue(project.get('target_progress') or 100)
                
                # 진행률 바 업데이트
                current = project.get('current_progress') or 0
                target = project.get('target_progress') or 100
                self.progress_bar.setMaximum(target)
                self.progress_bar.setValue(current)
                
                # 목표일
                target_date = project.get('target_date')
                if target_date:
                    if isinstance(target_date, str):
                        from datetime import datetime
                        target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
                    self.target_date_edit.setDate(QDate(
                        target_date.year, target_date.month, target_date.day
                    ))
                
                # 우선순위
                priority = project.get('priority') or '보통'
                idx = self.priority_combo.findText(priority)
                if idx >= 0:
                    self.priority_combo.setCurrentIndex(idx)
                
                # 상태
                status = project.get('status') or '진행중'
                idx = self.status_combo.findText(status)
                if idx >= 0:
                    self.status_combo.setCurrentIndex(idx)
                
                # 설명
                self.description_edit.setPlainText(
                    project.get('description') or ''
                )
                
        except Exception as e:
            logger.error(f"프로젝트 로드 오류: {e}")
    
    @Slot()
    def _on_save_project(self):
        """프로젝트 저장"""
        if not self.current_project_id:
            QMessageBox.warning(self, "경고", "프로젝트를 선택하세요.")
            return
        
        try:
            self.db.update_project(
                self.current_project_id,
                current_progress=self.current_progress_spin.value(),
                target_progress=self.target_progress_spin.value(),
                target_date=self.target_date_edit.date().toPython(),
                priority=self.priority_combo.currentText(),
                status=self.status_combo.currentText(),
                description=self.description_edit.toPlainText()
            )
            
            self._load_projects()
            QMessageBox.information(self, "저장 완료", "프로젝트 정보가 저장되었습니다.")
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"저장 실패: {str(e)}")
    
    @Slot()
    def _on_ai_recommend(self):
        """AI 추천 요청"""
        try:
            projects = self.db.get_projects_with_stats()
            
            if not projects:
                QMessageBox.warning(
                    self, "알림", 
                    "저장된 프로젝트가 없습니다.\n먼저 일일 업무 분석을 실행하세요."
                )
                return
            
            # 프로젝트 데이터 텍스트 생성
            project_data = self._projects_to_text(projects)
            
            # UI 상태 변경
            self.ai_analyze_btn.setEnabled(False)
            self.ai_progress.setVisible(True)
            self.ai_progress.setRange(0, 0)
            
            # 워커 시작
            self.worker = AIRecommendWorker(project_data)
            self.worker.progress.connect(self._on_ai_progress)
            self.worker.result_ready.connect(self._on_ai_result)
            self.worker.error.connect(self._on_ai_error)
            self.worker.finished.connect(self._on_ai_finished)
            self.worker.start()
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"AI 분석 실패: {str(e)}")
    
    def _projects_to_text(self, projects: List[Dict]) -> str:
        """프로젝트 데이터를 텍스트로 변환"""
        lines = ["## 현재 프로젝트 현황\n"]
        
        for project in projects:
            name = project.get('name', '미분류')
            current = project.get('current_progress') or 0
            target = project.get('target_progress') or 100
            target_date = project.get('target_date') or '미정'
            priority = project.get('priority') or '보통'
            status = project.get('status') or '진행중'
            task_count = project.get('task_count', 0)
            last_activity = project.get('last_activity') or '없음'
            
            lines.append(f"""
### {name}
- 진행률: {current}% / 목표 {target}%
- 목표일: {target_date}
- 우선순위: {priority}
- 상태: {status}
- 업무 수: {task_count}건
- 최근 활동: {last_activity}
""")
        
        return "\n".join(lines)
    
    @Slot(str)
    def _on_ai_progress(self, message: str):
        """AI 분석 진행"""
        self.ai_result_text.setPlaceholderText(message)
    
    @Slot(str)
    def _on_ai_result(self, result: str):
        """AI 분석 결과"""
        self.ai_result_text.setPlainText(result)
    
    @Slot(str)
    def _on_ai_error(self, error: str):
        """AI 분석 오류"""
        QMessageBox.critical(self, "AI 분석 오류", error)
    
    @Slot()
    def _on_ai_finished(self):
        """AI 분석 완료"""
        self.ai_analyze_btn.setEnabled(True)
        self.ai_progress.setVisible(False)

