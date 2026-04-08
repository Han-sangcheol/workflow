"""
메인 윈도우
업무일지 AI 분석 시스템의 메인 GUI입니다.
"""

import logging
from pathlib import Path
from typing import List

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QTextEdit, QProgressBar,
    QLabel, QFileDialog, QCheckBox, QTabWidget,
    QMessageBox, QComboBox, QGroupBox, QSplitter,
    QMenuBar, QMenu
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, Slot, QTimer, QElapsedTimer

from .worker import AnalysisWorker
from .system_monitor import SystemMonitor
from .prompt_editor import PromptEditorDialog
from .help_dialog import HelpDialog
from .period_analysis_dialog import PeriodAnalysisDialog
from .project_manager_dialog import ProjectManagerDialog
from .styles import APP_STYLE
from ..utils.file_selector import FileSelector
from ..utils.output_generator import OutputGenerator
from ..utils.ollama_manager import OllamaManager
from ..utils.settings_manager import get_settings, AI_PROVIDERS
from ..utils.task_parser import TaskParser
from ..ai.ollama_client import OllamaClient
from ..database.db_manager import get_db_manager

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """메인 윈도우 클래스"""

    def __init__(self):
        super().__init__()
        self.file_selector = FileSelector()
        self.output_generator = OutputGenerator()
        self.ollama_manager = OllamaManager()
        self.settings = get_settings()  # 설정 관리자
        self.worker = None
        self.current_summary = ""
        self.current_thanks = ""
        self.current_documents_text = ""
        self.current_cleaned_text = ""
        self.selected_cleaning_model = self.settings.cleaning_model
        self.selected_writing_model = self.settings.writing_model
        self.current_devstatus = ""  # 개발 현황 저장
        
        # 타이머 관련 변수
        self.elapsed_timer = QElapsedTimer()  # 경과 시간 측정
        self.display_timer = QTimer()  # UI 업데이트용 타이머
        self.display_timer.timeout.connect(self._update_elapsed_time)
        
        # 스텝별 시간 저장
        self.step_times = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0}
        
        self._init_ui()
        self._setup_logging()
        self._apply_saved_settings()  # 저장된 설정 적용
        self._check_and_start_ollama()
        self._load_available_models()
        self._restore_file_list()  # 저장된 파일 목록 복원

    def _init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("업무일지 AI 분석 시스템")
        self.setMinimumSize(1100, 750)
        
        # 애플리케이션 스타일 적용
        self.setStyleSheet(APP_STYLE)
        
        # 메뉴바 생성
        self._create_menu_bar()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # 메인 수평 스플리터 (좌/우 분할) - 멤버 변수로 저장하여 상태 저장/복원 가능
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # === 왼쪽: 메인 작업 영역 ===
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # 상단 영역 (파일 선택 + 모델 선택 + 진행 상황)
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(5, 5, 5, 5)
        
        top_layout.addWidget(self._create_file_selection_area())
        top_layout.addWidget(self._create_model_selection_area())
        top_layout.addWidget(self._create_progress_area())
        
        # 하단 영역 (결과 표시)
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(5, 5, 5, 5)
        
        bottom_layout.addWidget(self._create_result_area())
        bottom_layout.addWidget(self._create_save_button())
        
        # 상/하 스플리터 (상단 고정 영역 / 결과 영역) - 멤버 변수로 저장
        self.vertical_splitter = QSplitter(Qt.Orientation.Vertical)
        self.vertical_splitter.addWidget(top_widget)
        self.vertical_splitter.addWidget(bottom_widget)
        
        # 초기 비율 설정 (상단: 30%, 하단: 70%)
        self.vertical_splitter.setStretchFactor(0, 3)
        self.vertical_splitter.setStretchFactor(1, 7)
        
        left_layout.addWidget(self.vertical_splitter)
        
        # === 오른쪽: 시스템 모니터 + AI 생성 표시 ===
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 5, 5, 5)
        
        self.system_monitor = SystemMonitor()
        right_layout.addWidget(self.system_monitor)
        
        # AI 실시간 생성 표시 영역 (크기 확대: 150px → 350px)
        ai_thinking_group = QGroupBox("🧠 AI 생성 중...")
        ai_thinking_layout = QVBoxLayout(ai_thinking_group)
        ai_thinking_layout.setContentsMargins(5, 5, 5, 5)
        
        self.ai_thinking_text = QTextEdit()
        self.ai_thinking_text.setReadOnly(True)
        self.ai_thinking_text.setMinimumHeight(350)  # 최소 높이 350px로 확대
        self.ai_thinking_text.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a2e;
                color: #00ff88;
                font-family: 'Consolas', 'D2Coding', monospace;
                font-size: 10pt;
                border: 1px solid #16213e;
                border-radius: 4px;
                line-height: 1.4;
            }
        """)
        self.ai_thinking_text.setPlaceholderText("AI가 생성하는 내용이 여기에 표시됩니다...")
        ai_thinking_layout.addWidget(self.ai_thinking_text)
        
        right_layout.addWidget(ai_thinking_group, stretch=1)  # stretch 추가로 공간 확보
        
        # 메인 스플리터에 추가
        self.main_splitter.addWidget(left_widget)
        self.main_splitter.addWidget(right_widget)
        
        # 초기 비율 설정 (왼쪽: 75%, 오른쪽: 25%)
        self.main_splitter.setStretchFactor(0, 75)
        self.main_splitter.setStretchFactor(1, 25)
        
        # 스플리터 스타일링
        self.main_splitter.setHandleWidth(4)
        self.vertical_splitter.setHandleWidth(4)
        
        main_layout.addWidget(self.main_splitter)

    def _create_file_selection_area(self) -> QGroupBox:
        """파일 선택 영역 생성"""
        group = QGroupBox("📁 업무일지 파일 선택")
        group.setStyleSheet("QGroupBox { font-size: 11pt; font-weight: bold; }")
        layout = QVBoxLayout(group)
        
        # 버튼 행
        button_layout = QHBoxLayout()
        
        self.folder_btn = QPushButton("폴더 선택")
        self.folder_btn.clicked.connect(self._on_folder_select)
        button_layout.addWidget(self.folder_btn)
        
        self.manual_btn = QPushButton("파일 직접 선택")
        self.manual_btn.clicked.connect(self._on_manual_select)
        button_layout.addWidget(self.manual_btn)
        
        self.auto_check = QCheckBox("오늘 날짜로 자동 검색")
        self.auto_check.setChecked(True)
        button_layout.addWidget(self.auto_check)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # PDF 추출 모드 선택
        pdf_mode_layout = QHBoxLayout()
        pdf_mode_label = QLabel("📄 PDF 추출 모드:")
        pdf_mode_layout.addWidget(pdf_mode_label)
        
        self.pdf_mode_combo = QComboBox()
        self.pdf_mode_combo.addItems([
            "smart (블록 정렬 - 권장)",
            "layout (레이아웃 보존)",
            "simple (기본 추출)"
        ])
        self.pdf_mode_combo.setCurrentIndex(0)  # smart 기본값
        self.pdf_mode_combo.setToolTip(
            "smart: 표 형식 문서에 최적화\n"
            "layout: 복잡한 레이아웃 보존\n"
            "simple: 빠른 기본 추출"
        )
        pdf_mode_layout.addWidget(self.pdf_mode_combo)
        
        pdf_mode_info = QLabel("(표 형식 문서는 smart 권장)")
        pdf_mode_info.setStyleSheet("color: gray; font-size: 9pt;")
        pdf_mode_layout.addWidget(pdf_mode_info)
        
        pdf_mode_layout.addStretch()
        layout.addLayout(pdf_mode_layout)
        
        # 파일 목록 관리 버튼
        file_manage_layout = QHBoxLayout()
        
        self.delete_selected_btn = QPushButton("🗑️ 선택 삭제")
        self.delete_selected_btn.setToolTip("선택된 파일을 목록에서 삭제합니다")
        self.delete_selected_btn.clicked.connect(self._on_delete_selected_files)
        self.delete_selected_btn.setEnabled(False)
        file_manage_layout.addWidget(self.delete_selected_btn)
        
        self.clear_list_btn = QPushButton("🔄 목록 초기화")
        self.clear_list_btn.setToolTip("파일 목록을 모두 지웁니다")
        self.clear_list_btn.clicked.connect(self._on_clear_file_list)
        self.clear_list_btn.setEnabled(False)
        file_manage_layout.addWidget(self.clear_list_btn)
        
        file_manage_layout.addStretch()
        
        self.file_count_label = QLabel("")
        self.file_count_label.setStyleSheet("color: gray; font-size: 9pt;")
        file_manage_layout.addWidget(self.file_count_label)
        
        layout.addLayout(file_manage_layout)
        
        # 파일 목록 (다중 선택 가능)
        self.file_list = QListWidget()
        self.file_list.setMinimumHeight(60)
        self.file_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.file_list.itemSelectionChanged.connect(self._on_file_selection_changed)
        layout.addWidget(self.file_list)
        
        return group

    def _create_model_selection_area(self) -> QWidget:
        """AI 모델 선택 영역 생성 (각 단계별 제공자+모델 선택)"""
        group = QGroupBox("🤖 AI 설정 (단계별 제공자 선택)")
        layout = QVBoxLayout(group)
        
        # 제공자별 모델 캐시 (제공자 변경 시 재사용)
        self._provider_models_cache = {}
        
        # === 모델 선택 레이아웃 (2x2 그리드 형태로 배치) ===
        model_grid = QHBoxLayout()
        
        # 왼쪽 컬럼: 정리, 회의록
        left_col = QVBoxLayout()
        
        # 1. 텍스트 정리
        cleaning_layout = QHBoxLayout()
        cleaning_label = QLabel("1️⃣ 텍스트 정리:")
        cleaning_label.setMinimumWidth(95)
        cleaning_layout.addWidget(cleaning_label)
        
        self.cleaning_provider_combo = QComboBox()
        self.cleaning_provider_combo.setMinimumWidth(85)
        for key, info in AI_PROVIDERS.items():
            self.cleaning_provider_combo.addItem(info["name"], key)
        self.cleaning_provider_combo.currentIndexChanged.connect(
            lambda: self._on_step_provider_changed("cleaning")
        )
        cleaning_layout.addWidget(self.cleaning_provider_combo)
        
        self.cleaning_model_combo = QComboBox()
        self.cleaning_model_combo.setMinimumWidth(150)
        self.cleaning_model_combo.currentTextChanged.connect(
            lambda t: self._on_step_model_changed("cleaning", t)
        )
        cleaning_layout.addWidget(self.cleaning_model_combo)
        cleaning_layout.addStretch()
        left_col.addLayout(cleaning_layout)
        
        # 2. 회의록 생성
        summary_layout = QHBoxLayout()
        summary_label = QLabel("2️⃣ 회의록 생성:")
        summary_label.setMinimumWidth(95)
        summary_layout.addWidget(summary_label)
        
        self.summary_provider_combo = QComboBox()
        self.summary_provider_combo.setMinimumWidth(85)
        for key, info in AI_PROVIDERS.items():
            self.summary_provider_combo.addItem(info["name"], key)
        self.summary_provider_combo.currentIndexChanged.connect(
            lambda: self._on_step_provider_changed("summary")
        )
        summary_layout.addWidget(self.summary_provider_combo)
        
        self.summary_model_combo = QComboBox()
        self.summary_model_combo.setMinimumWidth(150)
        self.summary_model_combo.currentTextChanged.connect(
            lambda t: self._on_step_model_changed("summary", t)
        )
        summary_layout.addWidget(self.summary_model_combo)
        summary_layout.addStretch()
        left_col.addLayout(summary_layout)
        
        model_grid.addLayout(left_col)
        
        # 오른쪽 컬럼: 감사인사, 개발현황
        right_col = QVBoxLayout()
        
        # 3. 감사인사 생성
        thanks_layout = QHBoxLayout()
        thanks_label = QLabel("3️⃣ 감사 인사:")
        thanks_label.setMinimumWidth(95)
        thanks_layout.addWidget(thanks_label)
        
        self.thanks_provider_combo = QComboBox()
        self.thanks_provider_combo.setMinimumWidth(85)
        for key, info in AI_PROVIDERS.items():
            self.thanks_provider_combo.addItem(info["name"], key)
        self.thanks_provider_combo.currentIndexChanged.connect(
            lambda: self._on_step_provider_changed("thanks")
        )
        thanks_layout.addWidget(self.thanks_provider_combo)
        
        self.thanks_model_combo = QComboBox()
        self.thanks_model_combo.setMinimumWidth(150)
        self.thanks_model_combo.currentTextChanged.connect(
            lambda t: self._on_step_model_changed("thanks", t)
        )
        thanks_layout.addWidget(self.thanks_model_combo)
        thanks_layout.addStretch()
        right_col.addLayout(thanks_layout)
        
        # 4. 개발현황 생성
        devstatus_layout = QHBoxLayout()
        devstatus_label = QLabel("4️⃣ 개발 현황:")
        devstatus_label.setMinimumWidth(95)
        devstatus_layout.addWidget(devstatus_label)
        
        self.devstatus_provider_combo = QComboBox()
        self.devstatus_provider_combo.setMinimumWidth(85)
        for key, info in AI_PROVIDERS.items():
            self.devstatus_provider_combo.addItem(info["name"], key)
        self.devstatus_provider_combo.currentIndexChanged.connect(
            lambda: self._on_step_provider_changed("devstatus")
        )
        devstatus_layout.addWidget(self.devstatus_provider_combo)
        
        self.devstatus_model_combo = QComboBox()
        self.devstatus_model_combo.setMinimumWidth(150)
        self.devstatus_model_combo.currentTextChanged.connect(
            lambda t: self._on_step_model_changed("devstatus", t)
        )
        devstatus_layout.addWidget(self.devstatus_model_combo)
        devstatus_layout.addStretch()
        right_col.addLayout(devstatus_layout)
        
        model_grid.addLayout(right_col)
        layout.addLayout(model_grid)
        
        # 컨트롤 행: 새로고침 버튼, 프롬프트 편집, 정보
        control_layout = QHBoxLayout()
        
        self.refresh_models_btn = QPushButton("🔄 모델 새로고침")
        self.refresh_models_btn.clicked.connect(self._load_available_models)
        control_layout.addWidget(self.refresh_models_btn)
        
        self.edit_prompt_btn = QPushButton("📝 프롬프트 편집")
        self.edit_prompt_btn.setToolTip("AI 프롬프트를 직접 수정합니다")
        self.edit_prompt_btn.clicked.connect(self._on_edit_prompts)
        control_layout.addWidget(self.edit_prompt_btn)
        
        self.model_info_label = QLabel("")
        self.model_info_label.setStyleSheet("color: gray; font-size: 9pt;")
        control_layout.addWidget(self.model_info_label)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        return group

    def _create_progress_area(self) -> QGroupBox:
        """진행 상황 영역 생성"""
        group = QGroupBox("⚙️ 실행 및 진행 상황")
        group.setStyleSheet("QGroupBox { font-size: 11pt; font-weight: bold; }")
        layout = QVBoxLayout(group)
        
        # 단계별 실행 선택 체크박스
        step_select_layout = QHBoxLayout()
        step_select_label = QLabel("📋 실행할 단계:")
        step_select_label.setStyleSheet("font-size: 10pt; font-weight: normal;")
        step_select_layout.addWidget(step_select_label)
        
        self.step2_check = QCheckBox("2️⃣ 텍스트 정리")
        self.step2_check.setChecked(True)
        self.step2_check.setToolTip("원본 텍스트를 AI가 구조화된 형태로 정리")
        step_select_layout.addWidget(self.step2_check)
        
        self.step3_check = QCheckBox("3️⃣ 회의록")
        self.step3_check.setChecked(True)
        self.step3_check.setToolTip("정리된 텍스트로 통합 회의록 생성")
        step_select_layout.addWidget(self.step3_check)
        
        self.step4_check = QCheckBox("4️⃣ 감사인사")
        self.step4_check.setChecked(True)
        self.step4_check.setToolTip("정리된 텍스트로 감사 인사 생성")
        step_select_layout.addWidget(self.step4_check)
        
        self.step5_check = QCheckBox("5️⃣ 개발현황")
        self.step5_check.setChecked(True)
        self.step5_check.setToolTip("정리된 텍스트로 개발 현황 생성")
        step_select_layout.addWidget(self.step5_check)
        
        # 전체 선택/해제 버튼
        self.select_all_btn = QPushButton("전체")
        self.select_all_btn.setMaximumWidth(50)
        self.select_all_btn.clicked.connect(self._on_select_all_steps)
        step_select_layout.addWidget(self.select_all_btn)
        
        step_select_layout.addStretch()
        layout.addLayout(step_select_layout)
        
        # 분석 시작/정지 버튼 레이아웃
        button_layout = QHBoxLayout()
        
        # 분석 시작 버튼
        self.analyze_btn = QPushButton("🚀 분석 시작")
        self.analyze_btn.setStyleSheet(
            "font-size: 12pt; padding: 10px;"
        )
        self.analyze_btn.clicked.connect(self._on_analyze)
        self.analyze_btn.setEnabled(False)
        button_layout.addWidget(self.analyze_btn)
        
        # AI 정지 버튼
        self.stop_btn = QPushButton("⏹️ 정지")
        self.stop_btn.setStyleSheet(
            "font-size: 12pt; padding: 10px; background-color: #dc3545; color: white;"
        )
        self.stop_btn.setToolTip("AI 분석을 중단합니다")
        self.stop_btn.clicked.connect(self._on_stop_analysis)
        self.stop_btn.setEnabled(False)  # 초기에는 비활성화
        self.stop_btn.setMaximumWidth(100)
        button_layout.addWidget(self.stop_btn)
        
        # GPU 프로세스 종료 버튼
        self.gpu_kill_btn = QPushButton("🔧 GPU 정리")
        self.gpu_kill_btn.setStyleSheet(
            "font-size: 12pt; padding: 10px; background-color: #ff9800; color: white;"
        )
        self.gpu_kill_btn.setToolTip("GPU를 점유하는 불필요한 프로세스를 종료합니다\n(Chrome, ChatGPT, Claude 등)")
        self.gpu_kill_btn.clicked.connect(self._on_gpu_kill)
        self.gpu_kill_btn.setMaximumWidth(120)
        button_layout.addWidget(self.gpu_kill_btn)
        
        layout.addLayout(button_layout)
        
        # 진행률 및 시간 표시 행
        progress_time_layout = QHBoxLayout()
        
        # 진행률 표시
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 5)
        self.progress_bar.setValue(0)
        progress_time_layout.addWidget(self.progress_bar, stretch=3)
        
        # 경과 시간 표시
        self.time_label = QLabel("⏱️ 00:00")
        self.time_label.setStyleSheet(
            "font-size: 11pt; font-weight: bold; color: #2196F3; "
            "padding: 5px 10px; background: #E3F2FD; border-radius: 4px;"
        )
        self.time_label.setMinimumWidth(80)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_time_layout.addWidget(self.time_label)
        
        layout.addLayout(progress_time_layout)
        
        # 스텝별 시간 표시 (실제 소요 시간)
        self.step_times_label = QLabel("Step 1: --:-- | Step 2: --:-- | Step 3: --:-- | Step 4: --:-- | Step 5: --:--")
        self.step_times_label.setStyleSheet(
            "font-size: 9pt; color: #666; background: #F5F5F5; "
            "padding: 4px 8px; border-radius: 3px;"
        )
        self.step_times_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.step_times_label)
        
        # 예상 시간 표시
        self.estimate_label = QLabel("📊 예상 시간: (이전 분석 이력 없음)")
        self.estimate_label.setStyleSheet(
            "font-size: 9pt; color: #1976D2; background: #E3F2FD; "
            "padding: 4px 8px; border-radius: 3px;"
        )
        self.estimate_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.estimate_label)
        
        # 진행 상황 텍스트
        self.status_label = QLabel("파일을 선택하세요")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        return group

    def _create_result_area(self) -> QWidget:
        """결과 표시 영역 생성"""
        result_container = QWidget()
        result_layout = QVBoxLayout(result_container)
        result_layout.setContentsMargins(0, 0, 0, 0)
        result_layout.setSpacing(5)
        
        # 편집 모드 토글 영역
        edit_control_layout = QHBoxLayout()
        
        self.edit_mode_check = QCheckBox("✏️ 편집 모드")
        self.edit_mode_check.setToolTip(
            "체크하면 각 탭의 텍스트를 직접 편집할 수 있습니다.\n"
            "편집 후 재분석 버튼으로 다음 단계를 실행하세요."
        )
        self.edit_mode_check.stateChanged.connect(self._on_edit_mode_changed)
        edit_control_layout.addWidget(self.edit_mode_check)
        
        self.apply_edit_btn = QPushButton("📥 편집 내용 적용")
        self.apply_edit_btn.setToolTip("편집한 내용을 현재 데이터에 반영합니다")
        self.apply_edit_btn.clicked.connect(self._on_apply_edit)
        self.apply_edit_btn.setEnabled(False)
        self.apply_edit_btn.setMaximumWidth(130)
        edit_control_layout.addWidget(self.apply_edit_btn)
        
        self.edit_status_label = QLabel("")
        self.edit_status_label.setStyleSheet("color: #666; font-size: 9pt;")
        edit_control_layout.addWidget(self.edit_status_label)
        
        edit_control_layout.addStretch()
        result_layout.addLayout(edit_control_layout)
        
        # 탭 위젯
        self.tab_widget = QTabWidget()
        
        # 탭1: 원본 텍스트
        self.documents_text = QTextEdit()
        self.documents_text.setReadOnly(True)
        self.documents_text.setPlaceholderText(
            "Step 1: 파일에서 추출된 원본 텍스트\n"
            "(편집 모드에서 수정 가능)"
        )
        self.tab_widget.addTab(self.documents_text, "1️⃣ 원본 텍스트")
        
        # 탭2: 정리된 텍스트
        self.cleaned_text = QTextEdit()
        self.cleaned_text.setReadOnly(True)
        self.cleaned_text.setPlaceholderText(
            "Step 2: AI가 정리한 구조화된 텍스트\n"
            "(편집 모드에서 수정 후 재분석 가능)"
        )
        self.tab_widget.addTab(self.cleaned_text, "2️⃣ 정리된 텍스트")
        
        # 탭3: 통합 회의록
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setPlaceholderText(
            "Step 3: AI가 생성한 통합 회의록\n"
            "(편집 모드에서 수정 가능)"
        )
        self.tab_widget.addTab(self.summary_text, "3️⃣ 통합 회의록")
        
        # 탭4: 감사 인사
        self.thanks_text = QTextEdit()
        self.thanks_text.setReadOnly(True)
        self.thanks_text.setPlaceholderText(
            "Step 4: AI가 생성한 감사 인사\n"
            "(편집 모드에서 수정 가능)"
        )
        self.tab_widget.addTab(self.thanks_text, "4️⃣ 감사 인사")
        
        # 탭5: 개발 현황
        self.devstatus_text = QTextEdit()
        self.devstatus_text.setReadOnly(True)
        self.devstatus_text.setPlaceholderText(
            "Step 5: AI가 생성한 오전/오후 개발 현황\n"
            "(편집 모드에서 수정 가능)"
        )
        self.tab_widget.addTab(self.devstatus_text, "5️⃣ 개발 현황")
        
        result_layout.addWidget(self.tab_widget)
        
        return result_container

    def _create_save_button(self) -> QWidget:
        """저장 및 재분석 버튼 영역 생성"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 5, 0, 0)
        
        # 개별 재분석 버튼들
        reanalyze_label = QLabel("🔄 재분석:")
        reanalyze_label.setStyleSheet("color: #666; font-size: 9pt;")
        layout.addWidget(reanalyze_label)
        
        self.reanalyze_clean_btn = QPushButton("Step 2: 텍스트 정리")
        self.reanalyze_clean_btn.setToolTip("원본 텍스트를 다시 정리합니다")
        self.reanalyze_clean_btn.clicked.connect(self._on_reanalyze_clean)
        self.reanalyze_clean_btn.setEnabled(False)
        layout.addWidget(self.reanalyze_clean_btn)
        
        self.reanalyze_summary_btn = QPushButton("Step 3: 회의록")
        self.reanalyze_summary_btn.setToolTip("정리된 텍스트로 회의록을 다시 생성합니다")
        self.reanalyze_summary_btn.clicked.connect(self._on_reanalyze_summary)
        self.reanalyze_summary_btn.setEnabled(False)
        layout.addWidget(self.reanalyze_summary_btn)
        
        self.reanalyze_thanks_btn = QPushButton("Step 4: 감사인사")
        self.reanalyze_thanks_btn.setToolTip("정리된 텍스트로 감사인사를 다시 생성합니다")
        self.reanalyze_thanks_btn.clicked.connect(self._on_reanalyze_thanks)
        self.reanalyze_thanks_btn.setEnabled(False)
        layout.addWidget(self.reanalyze_thanks_btn)
        
        self.reanalyze_devstatus_btn = QPushButton("Step 5: 개발현황")
        self.reanalyze_devstatus_btn.setToolTip("정리된 텍스트로 개발 현황을 다시 생성합니다")
        self.reanalyze_devstatus_btn.clicked.connect(self._on_reanalyze_devstatus)
        self.reanalyze_devstatus_btn.setEnabled(False)
        layout.addWidget(self.reanalyze_devstatus_btn)
        
        layout.addStretch()
        
        # 저장 버튼
        self.save_btn = QPushButton("💾 결과 저장")
        self.save_btn.setStyleSheet("font-size: 11pt; padding: 8px;")
        self.save_btn.clicked.connect(self._on_save)
        self.save_btn.setEnabled(False)
        layout.addWidget(self.save_btn)
        
        return container

    @Slot()
    def _on_folder_select(self):
        """폴더 선택 핸들러"""
        # 마지막 사용 폴더에서 시작
        start_folder = self.settings.last_folder_path or ""
        
        folder = QFileDialog.getExistingDirectory(
            self,
            "업무일지 폴더 선택",
            start_folder
        )
        
        if not folder:
            return
        
        # 폴더 경로 저장
        self.settings.last_folder_path = folder
        
        if self.auto_check.isChecked():
            # 오늘 날짜로 자동 검색
            files = self.file_selector.find_files_by_date(folder)
        else:
            # 모든 지원 파일 검색
            files = self._find_all_supported_files(folder)
        
        # 기존 목록에 추가 (중복 제거)
        self._update_file_list(files, append=True)

    @Slot()
    def _on_manual_select(self):
        """파일 직접 선택 핸들러"""
        # 마지막 사용 폴더에서 시작
        start_folder = self.settings.last_folder_path or ""
        
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "업무일지 파일 선택",
            start_folder,
            "문서 파일 (*.pdf *.docx *.doc)"
        )
        
        if files:
            # 선택한 파일의 폴더 저장
            self.settings.last_folder_path = str(Path(files[0]).parent)
            # 기존 목록에 추가 (중복 제거)
            self._update_file_list(files, append=True)

    def _find_all_supported_files(self, folder: str) -> List[str]:
        """폴더에서 지원되는 모든 파일 찾기"""
        files = []
        folder_path = Path(folder)
        
        for ext in FileSelector.SUPPORTED_EXTENSIONS:
            files.extend(
                str(p) for p in folder_path.rglob(f"*{ext}")
            )
        
        return sorted(files)

    def _update_file_list(self, files: List[str], append: bool = False):
        """파일 목록 업데이트
        
        Args:
            files: 추가할 파일 경로 목록
            append: True면 기존 목록에 추가, False면 대체
        """
        valid_files = self.file_selector.validate_files(files)
        
        if append and hasattr(self, '_selected_files'):
            # 기존 파일과 병합 (중복 제거)
            existing_set = set(self._selected_files)
            for f in valid_files:
                if f not in existing_set:
                    self._selected_files.append(f)
        else:
            self._selected_files = valid_files
        
        # UI 업데이트
        self.file_list.clear()
        
        if not self._selected_files:
            self.status_label.setText("유효한 파일이 없습니다")
            self.analyze_btn.setEnabled(False)
            self.clear_list_btn.setEnabled(False)
            self.file_count_label.setText("")
            return
        
        for file_path in self._selected_files:
            self.file_list.addItem(Path(file_path).name)
        
        self.status_label.setText(
            f"{len(self._selected_files)}개 파일 선택됨"
        )
        self.analyze_btn.setEnabled(True)
        self.clear_list_btn.setEnabled(True)
        self.file_count_label.setText(f"총 {len(self._selected_files)}개")
        
        # 설정에 파일 목록 저장
        self.settings.save_file_list(self._selected_files)
    
    @Slot()
    def _on_file_selection_changed(self):
        """파일 목록에서 선택 변경 시 호출"""
        selected_count = len(self.file_list.selectedItems())
        self.delete_selected_btn.setEnabled(selected_count > 0)
    
    @Slot()
    def _on_delete_selected_files(self):
        """선택된 파일을 목록에서 삭제"""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            return
        
        # 선택된 항목의 인덱스를 역순으로 정렬 (뒤에서부터 삭제)
        indices = sorted([self.file_list.row(item) for item in selected_items], reverse=True)
        
        for idx in indices:
            self.file_list.takeItem(idx)
            if hasattr(self, '_selected_files') and idx < len(self._selected_files):
                self._selected_files.pop(idx)
        
        # 상태 업데이트
        remaining = len(self._selected_files) if hasattr(self, '_selected_files') else 0
        
        if remaining > 0:
            self.status_label.setText(f"{remaining}개 파일 선택됨")
            self.file_count_label.setText(f"총 {remaining}개")
            self.settings.save_file_list(self._selected_files)
        else:
            self.status_label.setText("파일을 선택하세요")
            self.file_count_label.setText("")
            self.analyze_btn.setEnabled(False)
            self.clear_list_btn.setEnabled(False)
            self.settings.clear_file_list()
        
        self.delete_selected_btn.setEnabled(False)
    
    @Slot()
    def _on_clear_file_list(self):
        """파일 목록 초기화"""
        reply = QMessageBox.question(
            self,
            "목록 초기화",
            "파일 목록을 모두 지우시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self.file_list.clear()
        self._selected_files = []
        self.status_label.setText("파일을 선택하세요")
        self.file_count_label.setText("")
        self.analyze_btn.setEnabled(False)
        self.clear_list_btn.setEnabled(False)
        self.delete_selected_btn.setEnabled(False)
        self.settings.clear_file_list()

    @Slot()
    def _on_analyze(self):
        """분석 시작 핸들러"""
        if not hasattr(self, '_selected_files'):
            return
        
        # UI 비활성화
        self._set_ui_enabled(False)
        
        # 정지 버튼 활성화
        self.stop_btn.setEnabled(True)
        
        # 타이머 시작
        self.elapsed_timer.start()
        self.display_timer.start(1000)  # 1초마다 업데이트
        self.time_label.setText("⏱️ 00:00")
        self.time_label.setStyleSheet(
            "font-size: 11pt; font-weight: bold; color: #FF9800; "
            "padding: 5px 10px; background: #FFF3E0; border-radius: 4px;"
        )
        
        # 스텝별 시간 초기화
        self.step_times = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0}
        self.step_times_label.setText("Step 1: --:-- | Step 2: --:-- | Step 3: --:-- | Step 4: --:-- | Step 5: --:--")
        
        # 예상 시간 계산 및 표시
        self._update_estimate_display()
        
        # 이전 결과 초기화
        self.documents_text.clear()
        self.cleaned_text.clear()
        self.summary_text.clear()
        self.thanks_text.clear()
        self.devstatus_text.clear()
        self.progress_bar.setValue(0)
        
        # PDF 추출 모드 파싱 (콤보박스 텍스트에서 모드명만 추출)
        pdf_mode_text = self.pdf_mode_combo.currentText()
        pdf_extraction_mode = pdf_mode_text.split(' ')[0]  # "smart", "layout", "simple"
        
        # 선택된 단계 확인
        selected_steps = self._get_selected_steps()
        
        # 최소 하나의 단계가 선택되어 있는지 확인
        if not any(selected_steps.values()):
            QMessageBox.warning(
                self, "경고", 
                "최소 하나의 분석 단계를 선택해주세요."
            )
            self._set_ui_enabled(True)
            self.stop_btn.setEnabled(False)
            return
        
        # 워커 스레드 시작 (단계별 제공자/모델 설정 전달)
        step_configs = self._build_step_configs()
        self.worker = AnalysisWorker(
            self._selected_files,
            pdf_extraction_mode=pdf_extraction_mode,
            selected_steps=selected_steps,
            step_configs=step_configs
        )
        self.worker.progress_updated.connect(self._on_progress)
        self.worker.step_completed.connect(self._on_step_completed)
        self.worker.step_time_recorded.connect(self._on_step_time_recorded)
        self.worker.step_analysis_recorded.connect(self._on_step_analysis_recorded)
        self.worker.documents_parsed.connect(self._on_documents_parsed)
        self.worker.text_cleaned.connect(self._on_text_cleaned)
        self.worker.summary_ready.connect(self._on_summary_ready)
        self.worker.thanks_ready.connect(self._on_thanks_ready)
        self.worker.devstatus_ready.connect(self._on_devstatus_ready)
        self.worker.ai_thinking.connect(self._on_ai_thinking)
        self.worker.error_occurred.connect(self._on_error)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    @Slot(str)
    def _on_progress(self, message: str):
        """진행 상황 업데이트"""
        self.status_label.setText(message)
        # 새로운 단계 시작 시 AI 생성 텍스트 초기화
        if message.startswith("Step"):
            self.ai_thinking_text.clear()
            self._ai_thinking_buffer = ""

    @Slot(str)
    def _on_ai_thinking(self, chunk: str):
        """AI 실시간 생성 텍스트 표시"""
        if not hasattr(self, '_ai_thinking_buffer'):
            self._ai_thinking_buffer = ""
        
        self._ai_thinking_buffer += chunk
        
        # 최근 2000자 표시 (창 크기 확대에 맞춰 증가)
        display_text = self._ai_thinking_buffer
        if len(display_text) > 2000:
            display_text = "..." + display_text[-2000:]
        
        self.ai_thinking_text.setPlainText(display_text)
        # 스크롤을 맨 아래로
        scrollbar = self.ai_thinking_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    @Slot(int)
    def _on_step_completed(self, step: int):
        """단계 완료"""
        self.progress_bar.setValue(step)

    @Slot(int, float)
    def _on_step_time_recorded(self, step: int, elapsed_seconds: float):
        """스텝별 소요 시간 기록"""
        self.step_times[step] = elapsed_seconds
        self._update_step_times_display()
    
    @Slot(int, int, float)
    def _on_step_analysis_recorded(self, step: int, text_length: int, elapsed_seconds: float):
        """분석 이력 저장 (예상 시간 계산용)"""
        self.settings.add_analysis_record(step, text_length, elapsed_seconds)
    
    def _update_estimate_display(self):
        """예상 시간 표시 업데이트"""
        # 현재 텍스트 양 추정 (이전 분석 결과가 있으면 그것 사용, 없으면 파일 수 기반)
        if hasattr(self, 'current_documents_text') and self.current_documents_text:
            text_length = len(self.current_documents_text)
        elif hasattr(self, '_selected_files'):
            # 파일당 평균 약 1000자로 추정
            text_length = len(self._selected_files) * 1000
        else:
            self.estimate_label.setText("📊 예상 시간: (파일 선택 후 표시)")
            return
        
        # 예상 시간 계산
        estimates = self.settings.estimate_total_time(text_length)
        
        if estimates["total"] is None:
            self.estimate_label.setText("📊 예상 시간: (이전 분석 이력 없음 - 첫 분석 후 표시)")
            return
        
        # 스텝별 예상 시간 문자열 생성
        def format_est(seconds):
            if seconds is None:
                return "--:--"
            minutes = int(seconds) // 60
            secs = int(seconds) % 60
            return f"{minutes:02d}:{secs:02d}"
        
        step_estimates = []
        for i in range(1, 6):
            est = estimates.get(f"step_{i}")
            step_estimates.append(f"S{i}:{format_est(est)}")
        
        total_est = format_est(estimates["total"])
        
        self.estimate_label.setText(
            f"📊 예상: {' | '.join(step_estimates)} → 총 {total_est}"
        )
    
    def _update_step_times_display(self):
        """스텝별 시간 표시 업데이트"""
        def format_time(seconds: float) -> str:
            if seconds == 0.0:
                return "--:--"
            minutes = int(seconds) // 60
            secs = int(seconds) % 60
            return f"{minutes:02d}:{secs:02d}"
        
        times_text = " | ".join([
            f"Step {i}: {format_time(self.step_times[i])}"
            for i in range(1, 6)
        ])
        self.step_times_label.setText(times_text)

    @Slot(str)
    def _on_documents_parsed(self, documents_text: str):
        """원본 텍스트 파싱 완료"""
        self.current_documents_text = documents_text
        self.documents_text.setPlainText(documents_text)
        # 원본 텍스트 탭으로 자동 전환
        self.tab_widget.setCurrentIndex(0)
        # 실제 텍스트 양으로 예상 시간 업데이트
        self._update_estimate_display()

    @Slot(str)
    def _on_text_cleaned(self, cleaned_text: str):
        """텍스트 정리 완료"""
        self.current_cleaned_text = cleaned_text
        self.cleaned_text.setPlainText(cleaned_text)
        # 정리된 텍스트 탭으로 자동 전환
        self.tab_widget.setCurrentIndex(1)

    @Slot(str)
    def _on_summary_ready(self, summary: str):
        """회의록 준비 완료"""
        self.current_summary = summary
        self.summary_text.setPlainText(summary)

    @Slot(str)
    def _on_thanks_ready(self, thanks: str):
        """감사 인사 준비 완료"""
        self.current_thanks = thanks
        self.thanks_text.setPlainText(thanks)

    @Slot(str)
    def _on_devstatus_ready(self, devstatus: str):
        """개발 현황 준비 완료"""
        self.current_devstatus = devstatus
        self.devstatus_text.setPlainText(devstatus)

    @Slot()
    def _on_select_all_steps(self):
        """전체 단계 선택/해제 토글"""
        # 현재 모두 선택되어 있으면 해제, 아니면 전체 선택
        all_checked = (
            self.step2_check.isChecked() and 
            self.step3_check.isChecked() and 
            self.step4_check.isChecked() and 
            self.step5_check.isChecked()
        )
        
        new_state = not all_checked
        self.step2_check.setChecked(new_state)
        self.step3_check.setChecked(new_state)
        self.step4_check.setChecked(new_state)
        self.step5_check.setChecked(new_state)
    
    def _get_selected_steps(self) -> dict:
        """선택된 단계 반환"""
        return {
            "step2": self.step2_check.isChecked(),
            "step3": self.step3_check.isChecked(),
            "step4": self.step4_check.isChecked(),
            "step5": self.step5_check.isChecked(),
        }

    @Slot(int)
    def _on_edit_mode_changed(self, state: int):
        """편집 모드 토글"""
        is_editable = state == Qt.CheckState.Checked.value
        
        # 모든 텍스트 영역의 편집 모드 변경
        self.documents_text.setReadOnly(not is_editable)
        self.cleaned_text.setReadOnly(not is_editable)
        self.summary_text.setReadOnly(not is_editable)
        self.thanks_text.setReadOnly(not is_editable)
        self.devstatus_text.setReadOnly(not is_editable)
        
        # 적용 버튼 활성화/비활성화
        self.apply_edit_btn.setEnabled(is_editable)
        
        # 상태 표시
        if is_editable:
            self.edit_status_label.setText("📝 편집 모드 ON - 텍스트 수정 후 '편집 내용 적용' 클릭")
            self.edit_status_label.setStyleSheet("color: #1976D2; font-size: 9pt; font-weight: bold;")
            # 편집 가능 시 스타일 변경
            edit_style = """
                QTextEdit {
                    background-color: #FFFEF0;
                    border: 2px solid #FFC107;
                }
            """
            self.documents_text.setStyleSheet(edit_style)
            self.cleaned_text.setStyleSheet(edit_style)
            self.summary_text.setStyleSheet(edit_style)
            self.thanks_text.setStyleSheet(edit_style)
            self.devstatus_text.setStyleSheet(edit_style)
        else:
            self.edit_status_label.setText("")
            self.edit_status_label.setStyleSheet("color: #666; font-size: 9pt;")
            # 기본 스타일로 복원
            self.documents_text.setStyleSheet("")
            self.cleaned_text.setStyleSheet("")
            self.summary_text.setStyleSheet("")
            self.thanks_text.setStyleSheet("")
            self.devstatus_text.setStyleSheet("")
        
        logger.info(f"편집 모드 변경: {is_editable}")
    
    @Slot()
    def _on_apply_edit(self):
        """편집 내용을 현재 데이터에 적용"""
        # 각 탭의 텍스트를 현재 데이터에 반영
        self.current_documents_text = self.documents_text.toPlainText()
        self.current_cleaned_text = self.cleaned_text.toPlainText()
        self.current_summary = self.summary_text.toPlainText()
        self.current_thanks = self.thanks_text.toPlainText()
        self.current_devstatus = self.devstatus_text.toPlainText()
        
        # 재분석 버튼 활성화 (데이터가 있는 경우)
        if self.current_documents_text:
            self.reanalyze_clean_btn.setEnabled(True)
        if self.current_cleaned_text:
            self.reanalyze_summary_btn.setEnabled(True)
            self.reanalyze_thanks_btn.setEnabled(True)
            self.reanalyze_devstatus_btn.setEnabled(True)
        if self.current_summary and self.current_thanks:
            self.save_btn.setEnabled(True)
        
        self.edit_status_label.setText("✅ 편집 내용이 적용되었습니다!")
        self.edit_status_label.setStyleSheet("color: #4CAF50; font-size: 9pt; font-weight: bold;")
        
        # 상태 메시지 표시
        self.status_label.setText("편집 내용 적용 완료 - 재분석 버튼으로 다음 단계 실행")
        
        logger.info("편집 내용 적용 완료")

    @Slot()
    def _on_stop_analysis(self):
        """분석 중지 핸들러"""
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.status_label.setText("⏹️ 분석 중지 요청됨... 현재 작업 완료 후 중단됩니다.")
            self.stop_btn.setEnabled(False)
            self.ai_thinking_text.append("\n\n⚠️ 사용자가 분석 중지를 요청했습니다.")
            logger.info("사용자가 분석 중지 요청")
        
        if hasattr(self, 'single_worker') and self.single_worker and self.single_worker.isRunning():
            self.single_worker.cancel()
            self.status_label.setText("⏹️ 재분석 중지 요청됨...")
            self.stop_btn.setEnabled(False)
            logger.info("사용자가 재분석 중지 요청")

    @Slot()
    def _on_gpu_kill(self):
        """GPU 프로세스 종료 핸들러"""
        import subprocess
        import sys
        
        # 시스템 모니터에서 종료 가능한 프로세스 목록 가져오기
        killable = []
        if hasattr(self, 'system_monitor') and self.system_monitor:
            killable = self.system_monitor.get_all_killable_processes()
        
        if not killable:
            QMessageBox.information(
                self, "GPU 정리",
                "종료할 GPU 프로세스가 없습니다.\n"
                "(Ollama와 시스템 프로세스는 보호됩니다)"
            )
            return
        
        # 확인 대화상자
        process_names = [f"• {p['name']}" for p in killable]
        msg = (
            f"다음 {len(killable)}개 프로세스를 종료하시겠습니까?\n\n"
            f"{chr(10).join(process_names[:10])}"
        )
        if len(killable) > 10:
            msg += f"\n... 외 {len(killable) - 10}개"
        
        msg += "\n\n⚠️ 저장하지 않은 작업이 있으면 먼저 저장하세요."
        
        reply = QMessageBox.question(
            self, "GPU 프로세스 종료",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # 프로세스 종료
        killed_count = 0
        failed_list = []
        
        # Windows에서 콘솔 창 숨김 설정
        startupinfo = None
        creationflags = 0
        if sys.platform == 'win32':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            creationflags = subprocess.CREATE_NO_WINDOW
        
        for proc in killable:
            try:
                result = subprocess.run(
                    ["taskkill", "/PID", str(proc["pid"]), "/F"],
                    capture_output=True, text=True, timeout=5,
                    startupinfo=startupinfo,
                    creationflags=creationflags
                )
                if result.returncode == 0:
                    killed_count += 1
                    logger.info(f"프로세스 종료: {proc['name']} (PID: {proc['pid']})")
                else:
                    failed_list.append(proc["name"])
            except Exception as e:
                failed_list.append(proc["name"])
                logger.warning(f"프로세스 종료 실패: {proc['name']} - {e}")
        
        # 결과 표시
        if killed_count > 0:
            result_msg = f"✅ {killed_count}개 프로세스를 종료했습니다."
            if failed_list:
                result_msg += f"\n\n❌ 종료 실패: {', '.join(failed_list)}"
            
            self.status_label.setText(f"GPU 정리 완료: {killed_count}개 종료")
            QMessageBox.information(self, "GPU 정리 완료", result_msg)
        else:
            QMessageBox.warning(
                self, "GPU 정리 실패",
                "프로세스를 종료하지 못했습니다.\n관리자 권한이 필요할 수 있습니다."
            )
        
        logger.info(f"GPU 정리 완료: {killed_count}개 종료, {len(failed_list)}개 실패")

    @Slot(str)
    def _on_error(self, error_msg: str):
        """오류 발생"""
        self._stop_timer()  # 타이머 중지
        self.stop_btn.setEnabled(False)  # 정지 버튼 비활성화
        QMessageBox.critical(self, "오류", error_msg)
        self.status_label.setText(f"오류: {error_msg}")

    @Slot()
    def _on_finished(self):
        """작업 완료"""
        self._stop_timer()  # 타이머 중지
        self._set_ui_enabled(True)
        self.stop_btn.setEnabled(False)  # 정지 버튼 비활성화
        
        # AI 생성 텍스트 영역에 완료 메시지 표시
        self.ai_thinking_text.setPlainText("✅ 분석 완료!")
        
        # 재분석 버튼 활성화 (데이터가 있는 경우)
        if self.current_documents_text:
            self.reanalyze_clean_btn.setEnabled(True)
        if self.current_cleaned_text:
            self.reanalyze_summary_btn.setEnabled(True)
            self.reanalyze_thanks_btn.setEnabled(True)
            self.reanalyze_devstatus_btn.setEnabled(True)
        
        if self.current_summary and self.current_thanks:
            self.save_btn.setEnabled(True)
        
        # DB에 분석 결과 저장
        self._save_analysis_to_db()
    
    def _update_elapsed_time(self):
        """경과 시간 업데이트 (1초마다 호출)"""
        elapsed_ms = self.elapsed_timer.elapsed()
        elapsed_sec = elapsed_ms // 1000
        minutes = elapsed_sec // 60
        seconds = elapsed_sec % 60
        self.time_label.setText(f"⏱️ {minutes:02d}:{seconds:02d}")
    
    def _stop_timer(self):
        """타이머 중지 및 최종 시간 표시"""
        self.display_timer.stop()
        
        # 최종 경과 시간 계산
        elapsed_ms = self.elapsed_timer.elapsed()
        elapsed_sec = elapsed_ms // 1000
        minutes = elapsed_sec // 60
        seconds = elapsed_sec % 60
        
        # 완료 스타일로 변경 (녹색)
        self.time_label.setText(f"✅ {minutes:02d}:{seconds:02d}")
        self.time_label.setStyleSheet(
            "font-size: 11pt; font-weight: bold; color: #4CAF50; "
            "padding: 5px 10px; background: #E8F5E9; border-radius: 4px;"
        )
    
    def _save_analysis_to_db(self):
        """분석 결과를 데이터베이스에 저장"""
        try:
            from datetime import date
            
            db = get_db_manager()
            
            # 파일명에서 날짜 추출 시도
            parser = TaskParser()
            analysis_date = None
            
            if hasattr(self, '_selected_files') and self._selected_files:
                for file_path in self._selected_files:
                    analysis_date = parser.extract_date_from_filename(file_path)
                    if analysis_date:
                        break
            
            # 날짜를 찾지 못하면 오늘 날짜 사용
            if not analysis_date:
                analysis_date = date.today()
            
            # 1. 분석 이력 저장
            file_count = len(self._selected_files) if hasattr(self, '_selected_files') else 0
            db.save_analysis_history(
                analysis_date=analysis_date,
                file_count=file_count,
                raw_text=self.current_documents_text,
                cleaned_text=self.current_cleaned_text,
                summary_text=self.current_summary,
                thanks_text=self.current_thanks,
                devstatus_text=self.current_devstatus
            )
            
            # 2. 정리된 텍스트에서 업무 데이터 파싱 후 저장
            if self.current_cleaned_text:
                tasks = parser.parse_cleaned_text(self.current_cleaned_text)
                
                for task in tasks:
                    db.add_daily_task(
                        member_name=task.member_name,
                        work_date=task.work_date,
                        task_content=task.task_content,
                        project_name=task.project_name,
                        progress_percent=task.progress_percent,
                        status=task.status
                    )
                
                logger.info(f"DB 저장 완료: 분석 이력 1건, 업무 {len(tasks)}건")
            else:
                logger.info("DB 저장 완료: 분석 이력 1건")
                
        except Exception as e:
            logger.error(f"DB 저장 오류: {e}")

    @Slot()
    def _on_reanalyze_clean(self):
        """정리된 텍스트 재분석"""
        if not self.current_documents_text:
            QMessageBox.warning(self, "경고", "원본 텍스트가 없습니다. 먼저 전체 분석을 실행해주세요.")
            return
        
        self._start_single_step_analysis("clean")
    
    @Slot()
    def _on_reanalyze_summary(self):
        """통합 회의록 재분석"""
        if not self.current_cleaned_text:
            QMessageBox.warning(self, "경고", "정리된 텍스트가 없습니다. 먼저 전체 분석을 실행해주세요.")
            return
        
        self._start_single_step_analysis("summary")
    
    @Slot()
    def _on_reanalyze_thanks(self):
        """감사인사 재분석"""
        if not self.current_cleaned_text:
            QMessageBox.warning(self, "경고", "정리된 텍스트가 없습니다. 먼저 전체 분석을 실행해주세요.")
            return
        
        self._start_single_step_analysis("thanks")
    
    @Slot()
    def _on_reanalyze_devstatus(self):
        """개발 현황 재분석"""
        if not self.current_cleaned_text:
            QMessageBox.warning(self, "경고", "정리된 텍스트가 없습니다. 먼저 전체 분석을 실행해주세요.")
            return
        
        self._start_single_step_analysis("devstatus")
    
    def _start_single_step_analysis(self, step_type: str):
        """개별 단계 재분석 시작"""
        # UI 비활성화
        self._set_ui_enabled(False)
        self.reanalyze_clean_btn.setEnabled(False)
        self.reanalyze_summary_btn.setEnabled(False)
        self.reanalyze_thanks_btn.setEnabled(False)
        self.reanalyze_devstatus_btn.setEnabled(False)
        
        # 정지 버튼 활성화
        self.stop_btn.setEnabled(True)
        
        # 타이머 시작
        self.elapsed_timer.start()
        self.display_timer.start(1000)
        self.time_label.setStyleSheet(
            "font-size: 11pt; font-weight: bold; color: #333; "
            "padding: 5px 10px; background: #FFF3E0; border-radius: 4px;"
        )
        
        # 개별 단계 워커 생성 및 실행
        from src.ui.single_step_worker import SingleStepWorker
        
        # 해당 단계의 설정 가져오기
        step_mapping = {"clean": "cleaning", "summary": "summary", "thanks": "thanks", "devstatus": "devstatus"}
        step_key = step_mapping.get(step_type, step_type)
        step_configs = self._build_step_configs()
        step_config = step_configs.get(step_key, {
            "provider": "ollama", "model": "llama3.2:latest",
            "base_url": "http://localhost:11434", "api_key": ""
        })
        
        self.single_worker = SingleStepWorker(
            step_type=step_type,
            source_text=self.current_documents_text if step_type == "clean" else self.current_cleaned_text,
            step_config=step_config
        )
        
        # 시그널 연결
        self.single_worker.finished.connect(self._on_single_step_finished)
        self.single_worker.error.connect(self._on_error)
        self.single_worker.progress.connect(self._on_progress)
        self.single_worker.ai_thinking.connect(self._on_ai_thinking)  # AI 실시간 생성 표시
        
        # AI 생성 텍스트 초기화
        self.ai_thinking_text.clear()
        self._ai_thinking_buffer = ""
        
        if step_type == "clean":
            self.single_worker.result_ready.connect(self._on_single_clean_result)
            self.status_label.setText("Step 2: 텍스트 정리 재분석 중...")
        elif step_type == "summary":
            self.single_worker.result_ready.connect(self._on_single_summary_result)
            self.status_label.setText("Step 3: 회의록 재생성 중...")
        elif step_type == "thanks":
            self.single_worker.result_ready.connect(self._on_single_thanks_result)
            self.status_label.setText("Step 4: 감사인사 재생성 중...")
        elif step_type == "devstatus":
            self.single_worker.result_ready.connect(self._on_single_devstatus_result)
            self.status_label.setText("Step 5: 개발 현황 재생성 중...")
        
        self.single_worker.start()
    
    @Slot(str)
    def _on_single_clean_result(self, result: str):
        """텍스트 정리 재분석 결과"""
        self.current_cleaned_text = result
        self.cleaned_text.setPlainText(result)
        self.tab_widget.setCurrentIndex(1)
    
    @Slot(str)
    def _on_single_summary_result(self, result: str):
        """회의록 재분석 결과"""
        self.current_summary = result
        self.summary_text.setPlainText(result)
        self.tab_widget.setCurrentIndex(2)
    
    @Slot(str)
    def _on_single_thanks_result(self, result: str):
        """감사인사 재분석 결과"""
        self.current_thanks = result
        self.thanks_text.setPlainText(result)
        self.tab_widget.setCurrentIndex(3)
    
    @Slot(str)
    def _on_single_devstatus_result(self, result: str):
        """개발 현황 재분석 결과"""
        self.current_devstatus = result
        self.devstatus_text.setPlainText(result)
        self.tab_widget.setCurrentIndex(4)
    
    @Slot()
    def _on_single_step_finished(self):
        """개별 단계 분석 완료"""
        self._stop_timer()
        self._set_ui_enabled(True)
        self.stop_btn.setEnabled(False)  # 정지 버튼 비활성화
        
        # 재분석 버튼 다시 활성화
        if self.current_documents_text:
            self.reanalyze_clean_btn.setEnabled(True)
        if self.current_cleaned_text:
            self.reanalyze_summary_btn.setEnabled(True)
            self.reanalyze_thanks_btn.setEnabled(True)
            self.reanalyze_devstatus_btn.setEnabled(True)
        
        if self.current_summary and self.current_thanks:
            self.save_btn.setEnabled(True)
        
        self.status_label.setText("재분석 완료!")

    @Slot()
    def _on_save(self):
        """결과 저장 핸들러"""
        if not self.current_summary or not self.current_thanks:
            return
        
        # 마지막 저장 경로에서 시작
        start_folder = self.settings.last_save_path or self.settings.last_folder_path or ""
        
        folder = QFileDialog.getExistingDirectory(
            self,
            "저장 위치 선택",
            start_folder
        )
        
        if not folder:
            return
        
        # 저장 경로 저장
        self.settings.last_save_path = folder
        
        # 파일명 생성
        summary_file = Path(folder) / \
            self.output_generator.generate_default_filename("회의록")
        thanks_file = Path(folder) / \
            self.output_generator.generate_default_filename("감사인사")
        
        # 저장
        success = True
        
        if not self.output_generator.save_summary(
            self.current_summary,
            str(summary_file)
        ):
            success = False
        
        if not self.output_generator.save_thanks(
            self.current_thanks,
            str(thanks_file)
        ):
            success = False
        
        if success:
            QMessageBox.information(
                self,
                "저장 완료",
                f"파일이 저장되었습니다:\n\n"
                f"• {summary_file.name}\n"
                f"• {thanks_file.name}"
            )
        else:
            QMessageBox.warning(
                self,
                "저장 오류",
                "파일 저장 중 오류가 발생했습니다"
            )

    def _set_ui_enabled(self, enabled: bool):
        """UI 활성화/비활성화"""
        self.folder_btn.setEnabled(enabled)
        self.manual_btn.setEnabled(enabled)
        self.auto_check.setEnabled(enabled)
        self.analyze_btn.setEnabled(enabled)

    def _load_available_models(self):
        """사용 가능한 모델 목록 로드 (각 단계별 제공자 기준)"""
        # 캐시 초기화
        self._provider_models_cache = {}
        
        self.model_info_label.setText("모델 목록 로딩 중...")
        
        steps = ["cleaning", "summary", "thanks", "devstatus"]
        connected_providers = set()
        failed_providers = set()
        
        for step in steps:
            # 저장된 설정 가져오기
            step_setting = self.settings.get_step_setting(step)
            saved_provider = step_setting.get("provider", "ollama")
            saved_model = step_setting.get("model", "")
            
            # 제공자 콤보박스 설정
            provider_combo = getattr(self, f"{step}_provider_combo", None)
            model_combo = getattr(self, f"{step}_model_combo", None)
            
            if not provider_combo or not model_combo:
                continue
            
            # 제공자 선택 (시그널 차단)
            provider_combo.blockSignals(True)
            for i in range(provider_combo.count()):
                if provider_combo.itemData(i) == saved_provider:
                    provider_combo.setCurrentIndex(i)
                    break
            provider_combo.blockSignals(False)
            
            # 해당 제공자의 모델 목록 가져오기
            models = self._get_models_for_provider(saved_provider)
            
            # 모델 콤보박스 설정 (시그널 차단)
            model_combo.blockSignals(True)
            model_combo.clear()
            
            if models:
                model_combo.addItems(models)
                connected_providers.add(saved_provider)
                # 저장된 모델 선택
                self._set_combo_model(model_combo, saved_model, models)
            else:
                failed_providers.add(saved_provider)
                model_combo.addItem("(연결 필요)")
            
            model_combo.blockSignals(False)
        
        # 상태 표시 업데이트
        if connected_providers:
            names = [AI_PROVIDERS[p]["name"] for p in connected_providers]
            self.model_info_label.setText(f"✅ 연결: {', '.join(names)}")
            self.model_info_label.setStyleSheet("color: green; font-size: 9pt;")
        elif failed_providers:
            names = [AI_PROVIDERS[p]["name"] for p in failed_providers]
            self.model_info_label.setText(f"⚠️ 연결 실패: {', '.join(names)}")
            self.model_info_label.setStyleSheet("color: orange; font-size: 9pt;")
    
    def _set_combo_model(self, combo: QComboBox, saved_model: str, models: list):
        """콤보박스에 저장된 모델 선택"""
        if saved_model in models:
            combo.setCurrentText(saved_model)
        elif "llama3.2:latest" in models:
            combo.setCurrentText("llama3.2:latest")
        elif models:
            combo.setCurrentIndex(0)
    
    def _restore_file_list(self):
        """저장된 파일 목록 복원"""
        saved_files = self.settings.last_file_list
        
        if not saved_files:
            return
        
        # 존재하는 파일만 필터링
        existing_files = [f for f in saved_files if Path(f).exists()]
        
        if existing_files:
            self._update_file_list(existing_files)
            logger.info(f"저장된 파일 목록 복원: {len(existing_files)}개")
        else:
            # 모든 파일이 삭제된 경우 설정 초기화
            self.settings.clear_file_list()

    @Slot(str)
    def _on_step_provider_changed(self, step: str):
        """단계별 AI 제공자 변경 - 해당 단계의 모델 목록 갱신"""
        provider_combo = getattr(self, f"{step}_provider_combo", None)
        model_combo = getattr(self, f"{step}_model_combo", None)
        if not provider_combo or not model_combo:
            return
        
        provider = provider_combo.currentData()
        if not provider:
            return
        
        # 해당 제공자의 모델 목록 로드
        models = self._get_models_for_provider(provider)
        
        # 모델 콤보박스 업데이트
        model_combo.blockSignals(True)
        model_combo.clear()
        if models:
            model_combo.addItems(models)
            # 저장된 모델이 있으면 선택
            saved = self.settings.get_step_setting(step)
            if saved.get("model") and saved.get("model") in models:
                model_combo.setCurrentText(saved["model"])
        else:
            model_combo.addItem("(연결 필요)")
        model_combo.blockSignals(False)
        
        # 설정 저장
        current_model = model_combo.currentText()
        if current_model and current_model != "(연결 필요)":
            self.settings.set_step_setting(step, provider, current_model)
        
        logger.debug(f"단계 제공자 변경: {step} → {provider}")
    
    def _on_step_model_changed(self, step: str, model_name: str):
        """단계별 모델 선택 변경"""
        if not model_name or model_name == "(연결 필요)":
            return
        
        provider_combo = getattr(self, f"{step}_provider_combo", None)
        if provider_combo:
            provider = provider_combo.currentData()
            self.settings.set_step_setting(step, provider, model_name)
            logger.debug(f"단계 모델 변경: {step} → {provider}/{model_name}")

    def _get_models_for_provider(self, provider: str) -> list:
        """제공자별 모델 목록 가져오기 (캐시 사용)"""
        # 캐시 확인
        if provider in self._provider_models_cache:
            return self._provider_models_cache[provider]
        
        # 제공자 정보 가져오기
        info = AI_PROVIDERS.get(provider, AI_PROVIDERS["ollama"])
        base_url = f"{info['url']}:{info['port']}"
        api_key = self.settings.get_api_key_for_provider(provider)
        
        # 모델 목록 가져오기
        models = OllamaClient.get_available_models(base_url, provider, api_key)
        
        # 캐시 저장
        if models:
            self._provider_models_cache[provider] = models
        
        return models
    
    def _build_step_configs(self) -> dict:
        """단계별 AI 설정 구성 (워커에 전달용)"""
        step_configs = {}
        steps = ["cleaning", "summary", "thanks", "devstatus"]
        
        for step in steps:
            provider_combo = getattr(self, f"{step}_provider_combo", None)
            model_combo = getattr(self, f"{step}_model_combo", None)
            
            if provider_combo and model_combo:
                provider = provider_combo.currentData() or "ollama"
                model = model_combo.currentText() or "llama3.2:latest"
                
                # 제공자 정보 가져오기
                info = AI_PROVIDERS.get(provider, AI_PROVIDERS["ollama"])
                base_url = f"{info['url']}:{info['port']}"
                api_key = self.settings.get_api_key_for_provider(provider)
                
                step_configs[step] = {
                    "provider": provider,
                    "model": model,
                    "base_url": base_url,
                    "api_key": api_key
                }
        
        return step_configs

    @Slot()
    def _on_edit_prompts(self):
        """프롬프트 편집 다이얼로그 열기"""
        dialog = PromptEditorDialog(self)
        dialog.exec()

    def _create_menu_bar(self):
        """메뉴바 생성"""
        menubar = self.menuBar()
        
        # 분석 메뉴
        analysis_menu = menubar.addMenu("분석(&A)")
        
        # 기간별 성과 분석
        period_analysis_action = QAction("📊 기간별 성과 분석", self)
        period_analysis_action.setShortcut("Ctrl+P")
        period_analysis_action.triggered.connect(self._on_show_period_analysis)
        analysis_menu.addAction(period_analysis_action)
        
        # 프로젝트 관리
        project_manager_action = QAction("📋 프로젝트 관리", self)
        project_manager_action.setShortcut("Ctrl+M")
        project_manager_action.triggered.connect(self._on_show_project_manager)
        analysis_menu.addAction(project_manager_action)
        
        analysis_menu.addSeparator()
        
        # DB 통계 보기
        db_stats_action = QAction("📁 데이터베이스 통계", self)
        db_stats_action.triggered.connect(self._on_show_db_stats)
        analysis_menu.addAction(db_stats_action)
        
        # 도움말 메뉴
        help_menu = menubar.addMenu("도움말(&H)")
        
        # 사용 설명서
        help_action = QAction("📖 사용 설명서", self)
        help_action.setShortcut("F1")
        help_action.triggered.connect(self._on_show_help)
        help_menu.addAction(help_action)
        
        help_menu.addSeparator()
        
        # Ollama 설치 가이드
        ollama_action = QAction("🤖 Ollama 설치 방법", self)
        ollama_action.triggered.connect(self._on_show_ollama_help)
        help_menu.addAction(ollama_action)
        
        # GPU 설정 가이드
        gpu_action = QAction("🎮 GPU 설정 방법", self)
        gpu_action.triggered.connect(self._on_show_gpu_help)
        help_menu.addAction(gpu_action)
        
        help_menu.addSeparator()
        
        # 프로그램 정보
        about_action = QAction("ℹ️ 프로그램 정보", self)
        about_action.triggered.connect(self._on_show_about)
        help_menu.addAction(about_action)

    @Slot()
    def _on_show_period_analysis(self):
        """기간별 성과 분석 다이얼로그 열기"""
        dialog = PeriodAnalysisDialog(self)
        dialog.exec()
    
    @Slot()
    def _on_show_project_manager(self):
        """프로젝트 관리 다이얼로그 열기"""
        dialog = ProjectManagerDialog(self)
        dialog.exec()
    
    @Slot()
    def _on_show_db_stats(self):
        """데이터베이스 통계 표시"""
        try:
            db = get_db_manager()
            stats = db.get_statistics()
            date_range = db.get_date_range()
            
            msg = (
                f"<h3>📁 데이터베이스 통계</h3>"
                f"<table>"
                f"<tr><td>팀원 수:</td><td><b>{stats['member_count']}명</b></td></tr>"
                f"<tr><td>프로젝트 수:</td><td><b>{stats['project_count']}개</b></td></tr>"
                f"<tr><td>업무 기록:</td><td><b>{stats['task_count']}건</b></td></tr>"
                f"<tr><td>분석 이력:</td><td><b>{stats['analysis_count']}건</b></td></tr>"
                f"</table>"
            )
            
            if date_range['min_date'] and date_range['max_date']:
                msg += f"<p>데이터 기간: {date_range['min_date']} ~ {date_range['max_date']}</p>"
            else:
                msg += "<p>저장된 업무 데이터가 없습니다.</p>"
            
            msg += f"<p style='color:#666; font-size:10px;'>DB 경로: {db.db_path}</p>"
            
            QMessageBox.information(self, "데이터베이스 통계", msg)
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"통계 조회 실패: {str(e)}")

    @Slot()
    def _on_show_help(self):
        """사용 설명서 다이얼로그 열기"""
        dialog = HelpDialog(self)
        dialog.exec()

    @Slot()
    def _on_show_ollama_help(self):
        """Ollama 설치 도움말 (탭 1번으로 열기)"""
        dialog = HelpDialog(self)
        dialog.tab_widget.setCurrentIndex(1)  # Ollama 탭
        dialog.exec()

    @Slot()
    def _on_show_gpu_help(self):
        """GPU 설정 도움말 (탭 2번으로 열기)"""
        dialog = HelpDialog(self)
        dialog.tab_widget.setCurrentIndex(2)  # GPU 탭
        dialog.exec()

    @Slot()
    def _on_show_about(self):
        """프로그램 정보 표시"""
        QMessageBox.about(
            self,
            "프로그램 정보",
            "<h3>업무일지 AI 분석 시스템</h3>"
            "<p>버전: 1.0.0</p>"
            "<p>팀원들의 일일 업무일지를 분석하여<br>"
            "통합 회의록과 감사 인사를 자동으로 생성합니다.</p>"
            "<p><b>기술 스택:</b><br>"
            "• PySide6 (GUI)<br>"
            "• Ollama (로컬 AI)<br>"
            "• PyMuPDF (PDF 파싱)</p>"
            "<p><a href='https://github.com/Han-sangcheol/workflow'>"
            "GitHub 저장소</a></p>"
        )

    def _check_and_start_ollama(self):
        """Ollama 서버 확인 및 자동 시작"""
        if self.ollama_manager.is_running():
            logger.info("✅ Ollama 서버가 이미 실행 중입니다")
            self.statusBar().showMessage("✅ Ollama 서버 연결됨", 3000)
        else:
            logger.info("⚙️ Ollama 서버를 시작합니다...")
            self.statusBar().showMessage("⚙️ Ollama 서버 시작 중...", 0)
            
            # 백그라운드에서 시작
            from PySide6.QtCore import QTimer
            QTimer.singleShot(100, self._start_ollama_async)

    def _start_ollama_async(self):
        """Ollama 비동기 시작"""
        if self.ollama_manager.start_server():
            logger.info("✅ Ollama 서버 시작 성공!")
            self.statusBar().showMessage("✅ Ollama 서버 시작됨", 3000)
            # 모델 목록 다시 로드
            self._load_available_models()
        else:
            logger.warning("⚠️ Ollama 서버 자동 시작 실패")
            self.statusBar().showMessage(
                "⚠️ Ollama를 수동으로 시작하세요 (ollama serve)",
                10000
            )
            QMessageBox.warning(
                self,
                "Ollama 시작 실패",
                "Ollama 서버를 자동으로 시작할 수 없습니다.\n\n"
                "다음 방법 중 하나를 시도하세요:\n"
                "1. 터미널에서 'ollama serve' 실행\n"
                "2. Ollama를 https://ollama.ai 에서 다운로드\n"
                "3. '모델 목록 새로고침' 버튼 클릭"
            )

    def closeEvent(self, event):
        """창 닫기 이벤트 - 메모리 클리어 및 리소스 정리"""
        import gc
        import subprocess
        
        logger.info("프로그램 종료 시작 - 리소스 정리 중...")
        
        # 1. 실행 중인 AI 작업 중단
        if hasattr(self, 'worker') and self.worker and self.worker.isRunning():
            logger.info("실행 중인 워커 종료 중...")
            self.worker.cancel()
            self.worker.wait(3000)  # 최대 3초 대기
        
        if hasattr(self, 'single_worker') and self.single_worker and self.single_worker.isRunning():
            logger.info("실행 중인 단일 워커 종료 중...")
            self.single_worker.cancel()
            self.single_worker.wait(3000)
        
        # 2. Ollama 모델 언로드 (GPU 메모리 해제)
        self._unload_ollama_model()
        
        # 3. GPU 프로세스 정리 (프로그램이 실행한 것만)
        self._cleanup_gpu_processes()
        
        # 4. 윈도우 크기/위치 저장
        self.settings.set_window_geometry(
            width=self.width(),
            height=self.height(),
            x=self.x(),
            y=self.y()
        )
        
        # 스플리터 상태 저장 (각 영역 크기)
        self.settings.set_splitter_sizes(
            main_sizes=self.main_splitter.sizes(),
            vertical_sizes=self.vertical_splitter.sizes()
        )
        
        # PDF 추출 모드 저장
        self.settings.pdf_extraction_mode = self.pdf_mode_combo.currentIndex()
        
        # 오늘 날짜 자동 검색 체크박스 저장
        self.settings.auto_search_today = self.auto_check.isChecked()
        
        # 분석 결과 저장 (다음 실행 시 복원)
        self.settings.save_analysis_results(
            documents_text=self.current_documents_text,
            cleaned_text=self.current_cleaned_text,
            summary_text=self.current_summary,
            thanks_text=self.current_thanks,
            devstatus_text=self.current_devstatus
        )
        
        logger.info("설정 저장 완료 (윈도우, 스플리터, PDF모드, 자동검색, 분석결과)")
        
        # 5. 시스템 모니터 중지
        if hasattr(self, 'system_monitor'):
            self.system_monitor.stop_monitoring()
        
        # 6. Python 가비지 컬렉션 강제 실행
        gc.collect()
        logger.info("가비지 컬렉션 완료")
        
        logger.info("프로그램 종료 완료 - 모든 리소스 정리됨")
        event.accept()
    
    def _unload_ollama_model(self):
        """Ollama 모델 언로드하여 GPU 메모리 해제"""
        import requests
        
        try:
            # 현재 로드된 모델 확인
            response = requests.get("http://localhost:11434/api/ps", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                
                for model in models:
                    model_name = model.get("name", "")
                    if model_name:
                        # 모델 언로드 (keep_alive=0으로 설정)
                        logger.info(f"Ollama 모델 언로드 중: {model_name}")
                        try:
                            requests.post(
                                "http://localhost:11434/api/generate",
                                json={
                                    "model": model_name,
                                    "keep_alive": 0  # 즉시 언로드
                                },
                                timeout=10
                            )
                            logger.info(f"모델 언로드 완료: {model_name}")
                        except Exception as e:
                            logger.warning(f"모델 언로드 실패: {model_name} - {e}")
        
        except requests.exceptions.ConnectionError:
            logger.debug("Ollama 서버가 실행 중이 아닙니다")
        except Exception as e:
            logger.warning(f"Ollama 모델 언로드 오류: {e}")
    
    def _cleanup_gpu_processes(self):
        """
        프로그램 종료 시 GPU 프로세스 정리
        
        주의: 이 기능은 기본적으로 비활성화되어 있습니다.
        다른 프로그램의 GPU 프로세스를 종료하면 데이터 손실 등의 
        문제가 발생할 수 있으므로, 이 기능은 사용하지 않는 것을 권장합니다.
        """
        # 설정에서 자동 정리 옵션 확인 (기본값: 비활성화)
        auto_cleanup = getattr(self.settings, 'auto_gpu_cleanup_on_exit', False)
        
        if not auto_cleanup:
            logger.debug("GPU 자동 정리 비활성화됨 (다른 프로그램 보호)")
            return
        
        # 이 기능은 다른 프로그램에 영향을 줄 수 있어 비활성화 상태 유지 권장
        logger.debug("GPU 자동 정리 기능은 안전을 위해 사용을 권장하지 않습니다")

    def _setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _apply_saved_settings(self):
        """저장된 설정 적용"""
        # 윈도우 크기/위치 적용
        geometry = self.settings.get_window_geometry()
        if geometry["width"] and geometry["height"]:
            self.resize(geometry["width"], geometry["height"])
        if geometry["x"] is not None and geometry["y"] is not None:
            self.move(geometry["x"], geometry["y"])
        
        # 스플리터 상태 복원 (각 영역 크기)
        splitter_sizes = self.settings.get_splitter_sizes()
        if splitter_sizes["main"]:
            self.main_splitter.setSizes(splitter_sizes["main"])
            logger.info(f"메인 스플리터 복원: {splitter_sizes['main']}")
        if splitter_sizes["vertical"]:
            self.vertical_splitter.setSizes(splitter_sizes["vertical"])
            logger.info(f"수직 스플리터 복원: {splitter_sizes['vertical']}")
        
        # PDF 추출 모드 적용
        pdf_mode_idx = self.settings.pdf_extraction_mode
        if 0 <= pdf_mode_idx < self.pdf_mode_combo.count():
            self.pdf_mode_combo.setCurrentIndex(pdf_mode_idx)
        
        # 오늘 날짜 자동 검색 체크박스 적용
        self.auto_check.setChecked(self.settings.auto_search_today)
        
        # 마지막 분석 결과 복원
        self._restore_analysis_results()
        
        logger.info("저장된 설정 적용 완료")
    
    def _restore_analysis_results(self):
        """저장된 분석 결과 복원"""
        results = self.settings.get_last_analysis_results()
        
        # 원본 텍스트 복원
        if results.get("documents_text"):
            self.current_documents_text = results["documents_text"]
            self.documents_text.setPlainText(results["documents_text"])
            self.reanalyze_clean_btn.setEnabled(True)
            logger.info("원본 텍스트 복원 완료")
        
        # 정리된 텍스트 복원
        if results.get("cleaned_text"):
            self.current_cleaned_text = results["cleaned_text"]
            self.cleaned_text.setPlainText(results["cleaned_text"])
            self.reanalyze_summary_btn.setEnabled(True)
            self.reanalyze_thanks_btn.setEnabled(True)
            self.reanalyze_devstatus_btn.setEnabled(True)
            logger.info("정리된 텍스트 복원 완료")
        
        # 회의록 복원
        if results.get("summary_text"):
            self.current_summary = results["summary_text"]
            self.summary_text.setPlainText(results["summary_text"])
            logger.info("회의록 복원 완료")
        
        # 감사인사 복원
        if results.get("thanks_text"):
            self.current_thanks = results["thanks_text"]
            self.thanks_text.setPlainText(results["thanks_text"])
            logger.info("감사인사 복원 완료")
        
        # 개발현황 복원
        if results.get("devstatus_text"):
            self.current_devstatus = results["devstatus_text"]
            self.devstatus_text.setPlainText(results["devstatus_text"])
            logger.info("개발현황 복원 완료")
        
        # 저장 버튼 활성화 (회의록과 감사인사가 있으면)
        if self.current_summary and self.current_thanks:
            self.save_btn.setEnabled(True)
        
        # 복원된 결과가 있으면 상태 표시
        has_results = any([
            results.get("documents_text"),
            results.get("cleaned_text"),
            results.get("summary_text"),
            results.get("thanks_text"),
            results.get("devstatus_text")
        ])
        
        if has_results:
            self.status_label.setText("✅ 이전 분석 결과가 복원되었습니다. 재분석 버튼으로 계속할 수 있습니다.")

