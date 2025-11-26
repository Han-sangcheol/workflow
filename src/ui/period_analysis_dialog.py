"""
기간별 성과 분석 다이얼로그
주간/월간/연간 단위로 팀원별, 프로젝트별 성과를 분석합니다.
"""

import logging
from datetime import date, timedelta
from typing import Optional, List, Dict

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QComboBox, QDateEdit,
    QTextEdit, QTableWidget, QTableWidgetItem,
    QGroupBox, QRadioButton, QButtonGroup, QWidget,
    QHeaderView, QMessageBox, QSplitter, QProgressBar
)
from PySide6.QtCore import Qt, Slot, QDate, QThread, Signal
from PySide6.QtGui import QFont

from ..database.db_manager import get_db_manager
from ..ai.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class PeriodAnalysisWorker(QThread):
    """기간별 AI 분석 워커"""
    
    progress = Signal(str)
    result_ready = Signal(str)
    error = Signal(str)
    finished = Signal()
    
    def __init__(self, tasks_text: str, period_info: str, model: str = "llama3.2:latest"):
        super().__init__()
        self.tasks_text = tasks_text
        self.period_info = period_info
        self.model = model
    
    def run(self):
        try:
            self.progress.emit("AI 분석 중...")
            
            client = OllamaClient(model=self.model)
            if not client.is_available():
                self.error.emit("Ollama 서버에 연결할 수 없습니다.")
                return
            
            result = client.generate_period_analysis(
                self.tasks_text,
                self.period_info
            )
            
            if result:
                self.result_ready.emit(result)
            else:
                self.error.emit("AI 분석에 실패했습니다.")
                
        except Exception as e:
            logger.error(f"기간별 분석 오류: {e}")
            self.error.emit(f"분석 오류: {str(e)}")
        finally:
            self.finished.emit()


class PeriodAnalysisDialog(QDialog):
    """기간별 성과 분석 다이얼로그"""
    
    # 기간 프리셋
    PERIOD_PRESETS = {
        "이번 주": lambda: (
            date.today() - timedelta(days=date.today().weekday()),
            date.today()
        ),
        "지난 주": lambda: (
            date.today() - timedelta(days=date.today().weekday() + 7),
            date.today() - timedelta(days=date.today().weekday() + 1)
        ),
        "이번 달": lambda: (
            date.today().replace(day=1),
            date.today()
        ),
        "지난 달": lambda: (
            (date.today().replace(day=1) - timedelta(days=1)).replace(day=1),
            date.today().replace(day=1) - timedelta(days=1)
        ),
        "최근 3개월": lambda: (
            date.today() - timedelta(days=90),
            date.today()
        ),
        "올해": lambda: (
            date(date.today().year, 1, 1),
            date.today()
        ),
        "직접 선택": None
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = get_db_manager()
        self.worker = None
        self.current_tasks = []
        
        self._init_ui()
        self._load_statistics()
    
    def _init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("기간별 성과 분석")
        self.setMinimumSize(900, 700)
        self.resize(1000, 750)
        
        layout = QVBoxLayout(self)
        
        # 상단: 기간 선택 및 분석 유형
        layout.addWidget(self._create_filter_area())
        
        # 중앙: 결과 표시 (탭)
        layout.addWidget(self._create_result_area(), stretch=1)
        
        # 하단: 버튼
        layout.addWidget(self._create_button_area())
    
    def _create_filter_area(self) -> QWidget:
        """필터 영역 생성"""
        group = QGroupBox("분석 조건")
        layout = QVBoxLayout(group)
        
        # 첫 번째 행: 기간 선택
        period_layout = QHBoxLayout()
        
        period_layout.addWidget(QLabel("기간:"))
        
        self.period_combo = QComboBox()
        self.period_combo.addItems(self.PERIOD_PRESETS.keys())
        self.period_combo.currentTextChanged.connect(self._on_period_changed)
        period_layout.addWidget(self.period_combo)
        
        period_layout.addWidget(QLabel("시작:"))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addDays(-7))
        self.start_date.setEnabled(False)
        period_layout.addWidget(self.start_date)
        
        period_layout.addWidget(QLabel("종료:"))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setEnabled(False)
        period_layout.addWidget(self.end_date)
        
        period_layout.addStretch()
        layout.addLayout(period_layout)
        
        # 두 번째 행: 분석 유형
        type_layout = QHBoxLayout()
        
        type_layout.addWidget(QLabel("분석 유형:"))
        
        self.type_group = QButtonGroup(self)
        self.member_radio = QRadioButton("팀원별")
        self.member_radio.setChecked(True)
        self.project_radio = QRadioButton("프로젝트별")
        
        self.type_group.addButton(self.member_radio)
        self.type_group.addButton(self.project_radio)
        
        type_layout.addWidget(self.member_radio)
        type_layout.addWidget(self.project_radio)
        
        type_layout.addStretch()
        
        # 분석 버튼
        self.analyze_btn = QPushButton("🔍 분석 실행")
        self.analyze_btn.setStyleSheet("font-size: 11pt; padding: 8px 20px;")
        self.analyze_btn.clicked.connect(self._on_analyze)
        type_layout.addWidget(self.analyze_btn)
        
        layout.addLayout(type_layout)
        
        # 통계 표시
        self.stats_label = QLabel("데이터베이스: 로딩 중...")
        self.stats_label.setStyleSheet("color: #666; font-size: 9pt;")
        layout.addWidget(self.stats_label)
        
        return group
    
    def _create_result_area(self) -> QWidget:
        """결과 표시 영역 생성"""
        self.result_tabs = QTabWidget()
        
        # 탭1: 요약
        self.summary_tab = QWidget()
        summary_layout = QVBoxLayout(self.summary_tab)
        
        self.summary_table = QTableWidget()
        self.summary_table.setColumnCount(5)
        self.summary_table.setHorizontalHeaderLabels([
            "팀원/프로젝트", "업무 수", "근무일", "평균 진행률", "완료 건수"
        ])
        self.summary_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        summary_layout.addWidget(self.summary_table)
        
        self.result_tabs.addTab(self.summary_tab, "📊 요약")
        
        # 탭2: 상세 업무
        self.detail_tab = QWidget()
        detail_layout = QVBoxLayout(self.detail_tab)
        
        self.detail_table = QTableWidget()
        self.detail_table.setColumnCount(6)
        self.detail_table.setHorizontalHeaderLabels([
            "날짜", "팀원", "프로젝트", "업무 내용", "진행률", "상태"
        ])
        self.detail_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.detail_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        detail_layout.addWidget(self.detail_table)
        
        self.result_tabs.addTab(self.detail_tab, "📋 상세 업무")
        
        # 탭3: AI 분석
        self.ai_tab = QWidget()
        ai_layout = QVBoxLayout(self.ai_tab)
        
        # AI 분석 버튼
        ai_btn_layout = QHBoxLayout()
        self.ai_analyze_btn = QPushButton("🤖 AI 성과 분석")
        self.ai_analyze_btn.clicked.connect(self._on_ai_analyze)
        self.ai_analyze_btn.setEnabled(False)
        ai_btn_layout.addWidget(self.ai_analyze_btn)
        
        self.ai_progress = QProgressBar()
        self.ai_progress.setVisible(False)
        ai_btn_layout.addWidget(self.ai_progress)
        
        ai_btn_layout.addStretch()
        ai_layout.addLayout(ai_btn_layout)
        
        self.ai_result_text = QTextEdit()
        self.ai_result_text.setReadOnly(True)
        self.ai_result_text.setPlaceholderText(
            "AI 성과 분석 결과가 여기에 표시됩니다.\n"
            "'AI 성과 분석' 버튼을 클릭하세요."
        )
        ai_layout.addWidget(self.ai_result_text)
        
        self.result_tabs.addTab(self.ai_tab, "🤖 AI 분석")
        
        return self.result_tabs
    
    def _create_button_area(self) -> QWidget:
        """버튼 영역 생성"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 10, 0, 0)
        
        layout.addStretch()
        
        self.close_btn = QPushButton("닫기")
        self.close_btn.clicked.connect(self.accept)
        layout.addWidget(self.close_btn)
        
        return widget
    
    def _load_statistics(self):
        """DB 통계 로드"""
        try:
            stats = self.db.get_statistics()
            date_range = self.db.get_date_range()
            
            stats_text = (
                f"📁 저장된 데이터: 팀원 {stats['member_count']}명, "
                f"프로젝트 {stats['project_count']}개, "
                f"업무 {stats['task_count']}건, "
                f"분석 이력 {stats['analysis_count']}건"
            )
            
            if date_range['min_date'] and date_range['max_date']:
                stats_text += f" | 기간: {date_range['min_date']} ~ {date_range['max_date']}"
            
            self.stats_label.setText(stats_text)
            
        except Exception as e:
            logger.error(f"통계 로드 오류: {e}")
            self.stats_label.setText("데이터베이스 연결 오류")
    
    @Slot(str)
    def _on_period_changed(self, preset: str):
        """기간 프리셋 변경"""
        if preset == "직접 선택":
            self.start_date.setEnabled(True)
            self.end_date.setEnabled(True)
        else:
            self.start_date.setEnabled(False)
            self.end_date.setEnabled(False)
            
            # 프리셋 날짜 적용
            preset_func = self.PERIOD_PRESETS.get(preset)
            if preset_func:
                start, end = preset_func()
                self.start_date.setDate(QDate(start.year, start.month, start.day))
                self.end_date.setDate(QDate(end.year, end.month, end.day))
    
    @Slot()
    def _on_analyze(self):
        """분석 실행"""
        # 날짜 범위 가져오기
        start = self.start_date.date().toPython()
        end = self.end_date.date().toPython()
        
        if start > end:
            QMessageBox.warning(self, "경고", "시작일이 종료일보다 클 수 없습니다.")
            return
        
        try:
            # 데이터 조회
            is_member_view = self.member_radio.isChecked()
            
            # 상세 업무 조회
            self.current_tasks = self.db.get_tasks_by_date_range(start, end)
            
            if not self.current_tasks:
                QMessageBox.information(
                    self, "알림", 
                    f"선택한 기간({start} ~ {end})에 저장된 업무가 없습니다.\n"
                    "먼저 일일 업무 분석을 실행하세요."
                )
                return
            
            # 요약 데이터 조회
            if is_member_view:
                summary_data = self.db.get_member_tasks_summary(start, end)
            else:
                summary_data = self.db.get_project_tasks_summary(start, end)
            
            # 테이블 업데이트
            self._update_summary_table(summary_data, is_member_view)
            self._update_detail_table(self.current_tasks)
            
            # AI 분석 버튼 활성화
            self.ai_analyze_btn.setEnabled(True)
            
            # 요약 탭으로 전환
            self.result_tabs.setCurrentIndex(0)
            
            logger.info(f"분석 완료: {len(self.current_tasks)}건")
            
        except Exception as e:
            logger.error(f"분석 오류: {e}")
            QMessageBox.critical(self, "오류", f"분석 중 오류 발생: {str(e)}")
    
    def _update_summary_table(self, data: List[Dict], is_member_view: bool):
        """요약 테이블 업데이트"""
        self.summary_table.setRowCount(len(data))
        
        if is_member_view:
            self.summary_table.setHorizontalHeaderLabels([
                "팀원", "업무 수", "근무일", "평균 진행률", "완료 건수"
            ])
        else:
            self.summary_table.setHorizontalHeaderLabels([
                "프로젝트", "업무 수", "참여 인원", "평균 진행률", "담당자"
            ])
        
        for row, item in enumerate(data):
            if is_member_view:
                self.summary_table.setItem(row, 0, QTableWidgetItem(
                    item.get('member_name', '-')
                ))
                self.summary_table.setItem(row, 1, QTableWidgetItem(
                    str(item.get('task_count', 0))
                ))
                self.summary_table.setItem(row, 2, QTableWidgetItem(
                    str(item.get('work_days', 0))
                ))
                avg_progress = item.get('avg_progress')
                self.summary_table.setItem(row, 3, QTableWidgetItem(
                    f"{avg_progress:.1f}%" if avg_progress else "-"
                ))
                self.summary_table.setItem(row, 4, QTableWidgetItem(
                    str(item.get('completed_count', 0))
                ))
            else:
                self.summary_table.setItem(row, 0, QTableWidgetItem(
                    item.get('project_name') or '미분류'
                ))
                self.summary_table.setItem(row, 1, QTableWidgetItem(
                    str(item.get('task_count', 0))
                ))
                self.summary_table.setItem(row, 2, QTableWidgetItem(
                    str(item.get('member_count', 0))
                ))
                avg_progress = item.get('avg_progress')
                self.summary_table.setItem(row, 3, QTableWidgetItem(
                    f"{avg_progress:.1f}%" if avg_progress else "-"
                ))
                self.summary_table.setItem(row, 4, QTableWidgetItem(
                    item.get('members', '-')
                ))
    
    def _update_detail_table(self, tasks: List[Dict]):
        """상세 업무 테이블 업데이트"""
        self.detail_table.setRowCount(len(tasks))
        
        for row, task in enumerate(tasks):
            self.detail_table.setItem(row, 0, QTableWidgetItem(
                str(task.get('work_date', '-'))
            ))
            self.detail_table.setItem(row, 1, QTableWidgetItem(
                task.get('member_name', '-')
            ))
            self.detail_table.setItem(row, 2, QTableWidgetItem(
                task.get('project_name') or '미분류'
            ))
            
            # 업무 내용 (너무 길면 줄임)
            content = task.get('task_content', '')
            if len(content) > 100:
                content = content[:100] + "..."
            self.detail_table.setItem(row, 3, QTableWidgetItem(content))
            
            self.detail_table.setItem(row, 4, QTableWidgetItem(
                f"{task.get('progress_percent', 0)}%"
            ))
            self.detail_table.setItem(row, 5, QTableWidgetItem(
                task.get('status', '-')
            ))
    
    @Slot()
    def _on_ai_analyze(self):
        """AI 성과 분석"""
        if not self.current_tasks:
            QMessageBox.warning(self, "경고", "먼저 기간별 분석을 실행하세요.")
            return
        
        # 업무 데이터를 텍스트로 변환
        tasks_text = self._tasks_to_text()
        
        # 기간 정보
        start = self.start_date.date().toPython()
        end = self.end_date.date().toPython()
        period_info = f"{start} ~ {end}"
        
        # UI 상태 변경
        self.ai_analyze_btn.setEnabled(False)
        self.ai_progress.setVisible(True)
        self.ai_progress.setRange(0, 0)  # 무한 진행
        
        # 워커 시작
        self.worker = PeriodAnalysisWorker(tasks_text, period_info)
        self.worker.progress.connect(self._on_ai_progress)
        self.worker.result_ready.connect(self._on_ai_result)
        self.worker.error.connect(self._on_ai_error)
        self.worker.finished.connect(self._on_ai_finished)
        self.worker.start()
    
    def _tasks_to_text(self) -> str:
        """업무 데이터를 텍스트로 변환"""
        lines = []
        
        # 팀원별로 그룹화
        member_tasks = {}
        for task in self.current_tasks:
            member = task.get('member_name', '미확인')
            if member not in member_tasks:
                member_tasks[member] = []
            member_tasks[member].append(task)
        
        for member, tasks in member_tasks.items():
            lines.append(f"\n### {member}")
            for task in tasks:
                project = task.get('project_name') or '기타'
                content = task.get('task_content', '')[:200]
                progress = task.get('progress_percent', 0)
                status = task.get('status', '진행중')
                work_date = task.get('work_date', '')
                
                lines.append(f"- [{work_date}] {project}: {content} ({progress}%, {status})")
        
        return "\n".join(lines)
    
    @Slot(str)
    def _on_ai_progress(self, message: str):
        """AI 분석 진행 상황"""
        self.ai_result_text.setPlaceholderText(message)
    
    @Slot(str)
    def _on_ai_result(self, result: str):
        """AI 분석 결과"""
        self.ai_result_text.setPlainText(result)
        self.result_tabs.setCurrentIndex(2)  # AI 분석 탭으로 전환
    
    @Slot(str)
    def _on_ai_error(self, error: str):
        """AI 분석 오류"""
        QMessageBox.critical(self, "AI 분석 오류", error)
    
    @Slot()
    def _on_ai_finished(self):
        """AI 분석 완료"""
        self.ai_analyze_btn.setEnabled(True)
        self.ai_progress.setVisible(False)

