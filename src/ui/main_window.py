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
from .styles import APP_STYLE
from ..utils.file_selector import FileSelector
from ..utils.output_generator import OutputGenerator
from ..utils.ollama_manager import OllamaManager
from ..utils.settings_manager import get_settings
from ..ai.ollama_client import OllamaClient

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
        
        # 타이머 관련 변수
        self.elapsed_timer = QElapsedTimer()  # 경과 시간 측정
        self.display_timer = QTimer()  # UI 업데이트용 타이머
        self.display_timer.timeout.connect(self._update_elapsed_time)
        
        # 스텝별 시간 저장
        self.step_times = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}
        
        self._init_ui()
        self._setup_logging()
        self._apply_saved_settings()  # 저장된 설정 적용
        self._check_and_start_ollama()
        self._load_available_models()

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
        
        # 메인 수평 스플리터 (좌/우 분할)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
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
        
        # 상/하 스플리터 (상단 고정 영역 / 결과 영역)
        vertical_splitter = QSplitter(Qt.Orientation.Vertical)
        vertical_splitter.addWidget(top_widget)
        vertical_splitter.addWidget(bottom_widget)
        
        # 초기 비율 설정 (상단: 30%, 하단: 70%)
        vertical_splitter.setStretchFactor(0, 3)
        vertical_splitter.setStretchFactor(1, 7)
        
        left_layout.addWidget(vertical_splitter)
        
        # === 오른쪽: 시스템 모니터 ===
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 5, 5, 5)
        
        self.system_monitor = SystemMonitor()
        right_layout.addWidget(self.system_monitor)
        
        # 메인 스플리터에 추가
        main_splitter.addWidget(left_widget)
        main_splitter.addWidget(right_widget)
        
        # 초기 비율 설정 (왼쪽: 75%, 오른쪽: 25%)
        main_splitter.setStretchFactor(0, 75)
        main_splitter.setStretchFactor(1, 25)
        
        # 스플리터 스타일링
        main_splitter.setHandleWidth(4)
        vertical_splitter.setHandleWidth(4)
        
        main_layout.addWidget(main_splitter)

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
        
        # 파일 목록
        self.file_list = QListWidget()
        self.file_list.setMinimumHeight(60)
        layout.addWidget(self.file_list)
        
        return group

    def _create_model_selection_area(self) -> QWidget:
        """AI 모델 선택 영역 생성"""
        group = QGroupBox("🤖 AI 모델 설정")
        layout = QVBoxLayout(group)
        
        # 첫 번째 행: 정리용 모델
        cleaning_layout = QHBoxLayout()
        cleaning_label = QLabel("📝 정리용 모델:")
        cleaning_label.setMinimumWidth(100)
        cleaning_layout.addWidget(cleaning_label)
        
        self.cleaning_model_combo = QComboBox()
        self.cleaning_model_combo.setMinimumWidth(200)
        self.cleaning_model_combo.currentTextChanged.connect(
            self._on_cleaning_model_changed
        )
        cleaning_layout.addWidget(self.cleaning_model_combo)
        
        cleaning_info = QLabel("(텍스트 정리 및 구조화)")
        cleaning_info.setStyleSheet("color: gray; font-size: 9pt;")
        cleaning_layout.addWidget(cleaning_info)
        cleaning_layout.addStretch()
        
        layout.addLayout(cleaning_layout)
        
        # 두 번째 행: 작성용 모델
        writing_layout = QHBoxLayout()
        writing_label = QLabel("✍️ 작성용 모델:")
        writing_label.setMinimumWidth(100)
        writing_layout.addWidget(writing_label)
        
        self.writing_model_combo = QComboBox()
        self.writing_model_combo.setMinimumWidth(200)
        self.writing_model_combo.currentTextChanged.connect(
            self._on_writing_model_changed
        )
        writing_layout.addWidget(self.writing_model_combo)
        
        writing_info = QLabel("(회의록 및 감사 인사 생성)")
        writing_info.setStyleSheet("color: gray; font-size: 9pt;")
        writing_layout.addWidget(writing_info)
        writing_layout.addStretch()
        
        layout.addLayout(writing_layout)
        
        # 세 번째 행: 새로고침 버튼, 프롬프트 편집, 정보
        control_layout = QHBoxLayout()
        
        self.refresh_models_btn = QPushButton("🔄 모델 목록 새로고침")
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
        
        # 분석 시작 버튼
        self.analyze_btn = QPushButton("🚀 분석 시작")
        self.analyze_btn.setStyleSheet(
            "font-size: 12pt; padding: 10px;"
        )
        self.analyze_btn.clicked.connect(self._on_analyze)
        self.analyze_btn.setEnabled(False)
        layout.addWidget(self.analyze_btn)
        
        # 진행률 및 시간 표시 행
        progress_time_layout = QHBoxLayout()
        
        # 진행률 표시
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 4)
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
        
        # 스텝별 시간 표시
        self.step_times_label = QLabel("Step 1: --:-- | Step 2: --:-- | Step 3: --:-- | Step 4: --:--")
        self.step_times_label.setStyleSheet(
            "font-size: 9pt; color: #666; background: #F5F5F5; "
            "padding: 4px 8px; border-radius: 3px;"
        )
        self.step_times_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.step_times_label)
        
        # 진행 상황 텍스트
        self.status_label = QLabel("파일을 선택하세요")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        return group

    def _create_result_area(self) -> QWidget:
        """결과 표시 영역 생성"""
        self.tab_widget = QTabWidget()
        
        # 탭1: 원본 텍스트
        self.documents_text = QTextEdit()
        self.documents_text.setReadOnly(True)
        self.documents_text.setPlaceholderText(
            "Step 1: 파일에서 추출된 원본 텍스트"
        )
        self.tab_widget.addTab(self.documents_text, "1️⃣ 원본 텍스트")
        
        # 탭2: 정리된 텍스트
        self.cleaned_text = QTextEdit()
        self.cleaned_text.setReadOnly(True)
        self.cleaned_text.setPlaceholderText(
            "Step 2: AI가 정리한 구조화된 텍스트"
        )
        self.tab_widget.addTab(self.cleaned_text, "2️⃣ 정리된 텍스트")
        
        # 탭3: 통합 회의록
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setPlaceholderText(
            "Step 3: AI가 생성한 통합 회의록"
        )
        self.tab_widget.addTab(self.summary_text, "3️⃣ 통합 회의록")
        
        # 탭4: 감사 인사
        self.thanks_text = QTextEdit()
        self.thanks_text.setReadOnly(True)
        self.thanks_text.setPlaceholderText(
            "Step 4: AI가 생성한 감사 인사"
        )
        self.tab_widget.addTab(self.thanks_text, "4️⃣ 감사 인사")
        
        return self.tab_widget

    def _create_save_button(self) -> QWidget:
        """저장 버튼 생성"""
        self.save_btn = QPushButton("💾 결과 저장")
        self.save_btn.setStyleSheet("font-size: 11pt; padding: 8px;")
        self.save_btn.clicked.connect(self._on_save)
        self.save_btn.setEnabled(False)
        return self.save_btn

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
        
        self._update_file_list(files)

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
            from pathlib import Path
            self.settings.last_folder_path = str(Path(files[0]).parent)
            self._update_file_list(files)

    def _find_all_supported_files(self, folder: str) -> List[str]:
        """폴더에서 지원되는 모든 파일 찾기"""
        files = []
        folder_path = Path(folder)
        
        for ext in FileSelector.SUPPORTED_EXTENSIONS:
            files.extend(
                str(p) for p in folder_path.rglob(f"*{ext}")
            )
        
        return sorted(files)

    def _update_file_list(self, files: List[str]):
        """파일 목록 업데이트"""
        self.file_list.clear()
        
        valid_files = self.file_selector.validate_files(files)
        
        if not valid_files:
            self.status_label.setText("유효한 파일이 없습니다")
            self.analyze_btn.setEnabled(False)
            return
        
        for file_path in valid_files:
            self.file_list.addItem(Path(file_path).name)
        
        self.status_label.setText(
            f"{len(valid_files)}개 파일 선택됨"
        )
        self.analyze_btn.setEnabled(True)
        
        # 내부 저장
        self._selected_files = valid_files

    @Slot()
    def _on_analyze(self):
        """분석 시작 핸들러"""
        if not hasattr(self, '_selected_files'):
            return
        
        # UI 비활성화
        self._set_ui_enabled(False)
        
        # 타이머 시작
        self.elapsed_timer.start()
        self.display_timer.start(1000)  # 1초마다 업데이트
        self.time_label.setText("⏱️ 00:00")
        self.time_label.setStyleSheet(
            "font-size: 11pt; font-weight: bold; color: #FF9800; "
            "padding: 5px 10px; background: #FFF3E0; border-radius: 4px;"
        )
        
        # 스텝별 시간 초기화
        self.step_times = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}
        self.step_times_label.setText("Step 1: --:-- | Step 2: --:-- | Step 3: --:-- | Step 4: --:--")
        
        # 이전 결과 초기화
        self.documents_text.clear()
        self.cleaned_text.clear()
        self.summary_text.clear()
        self.thanks_text.clear()
        self.progress_bar.setValue(0)
        
        # PDF 추출 모드 파싱 (콤보박스 텍스트에서 모드명만 추출)
        pdf_mode_text = self.pdf_mode_combo.currentText()
        pdf_extraction_mode = pdf_mode_text.split(' ')[0]  # "smart", "layout", "simple"
        
        # 워커 스레드 시작 (선택된 모델들과 PDF 추출 모드 전달)
        self.worker = AnalysisWorker(
            self._selected_files,
            pdf_extraction_mode=pdf_extraction_mode,
            cleaning_model=self.selected_cleaning_model,
            writing_model=self.selected_writing_model
        )
        self.worker.progress_updated.connect(self._on_progress)
        self.worker.step_completed.connect(self._on_step_completed)
        self.worker.step_time_recorded.connect(self._on_step_time_recorded)
        self.worker.documents_parsed.connect(self._on_documents_parsed)
        self.worker.text_cleaned.connect(self._on_text_cleaned)
        self.worker.summary_ready.connect(self._on_summary_ready)
        self.worker.thanks_ready.connect(self._on_thanks_ready)
        self.worker.error_occurred.connect(self._on_error)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    @Slot(str)
    def _on_progress(self, message: str):
        """진행 상황 업데이트"""
        self.status_label.setText(message)

    @Slot(int)
    def _on_step_completed(self, step: int):
        """단계 완료"""
        self.progress_bar.setValue(step)

    @Slot(int, float)
    def _on_step_time_recorded(self, step: int, elapsed_seconds: float):
        """스텝별 소요 시간 기록"""
        self.step_times[step] = elapsed_seconds
        self._update_step_times_display()
    
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
            for i in range(1, 5)
        ])
        self.step_times_label.setText(times_text)

    @Slot(str)
    def _on_documents_parsed(self, documents_text: str):
        """원본 텍스트 파싱 완료"""
        self.current_documents_text = documents_text
        self.documents_text.setPlainText(documents_text)
        # 원본 텍스트 탭으로 자동 전환
        self.tab_widget.setCurrentIndex(0)

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
    def _on_error(self, error_msg: str):
        """오류 발생"""
        self._stop_timer()  # 타이머 중지
        QMessageBox.critical(self, "오류", error_msg)
        self.status_label.setText(f"오류: {error_msg}")

    @Slot()
    def _on_finished(self):
        """작업 완료"""
        self._stop_timer()  # 타이머 중지
        self._set_ui_enabled(True)
        
        if self.current_summary and self.current_thanks:
            self.save_btn.setEnabled(True)
    
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
        """사용 가능한 모델 목록 로드"""
        self.cleaning_model_combo.clear()
        self.writing_model_combo.clear()
        self.model_info_label.setText("모델 목록 로딩 중...")
        
        # Ollama에서 모델 목록 가져오기
        models = OllamaClient.get_available_models()
        
        if models:
            self.cleaning_model_combo.addItems(models)
            self.writing_model_combo.addItems(models)
            
            # 저장된 모델 또는 기본 모델 선택
            saved_cleaning = self.settings.cleaning_model
            saved_writing = self.settings.writing_model
            
            # 정리용 모델 선택
            if saved_cleaning in models:
                self.cleaning_model_combo.setCurrentText(saved_cleaning)
            elif "llama3.2:latest" in models:
                self.cleaning_model_combo.setCurrentText("llama3.2:latest")
            elif models:
                self.cleaning_model_combo.setCurrentIndex(0)
            
            # 작성용 모델 선택
            if saved_writing in models:
                self.writing_model_combo.setCurrentText(saved_writing)
            elif "llama3.2:latest" in models:
                self.writing_model_combo.setCurrentText("llama3.2:latest")
            elif models:
                self.writing_model_combo.setCurrentIndex(0)
            
            self.model_info_label.setText(
                f"✅ {len(models)}개 모델 사용 가능"
            )
            self.model_info_label.setStyleSheet("color: green; font-size: 9pt;")
        else:
            # 모델이 없으면 기본값 추가
            default_models = [
                "llama3.2:latest",
                "llama3.2:1b",
                "llama3:latest",
                "mistral:latest",
                "gemma:latest"
            ]
            self.cleaning_model_combo.addItems(default_models)
            self.writing_model_combo.addItems(default_models)
            
            # 저장된 모델 선택 시도
            saved_cleaning = self.settings.cleaning_model
            saved_writing = self.settings.writing_model
            if saved_cleaning in default_models:
                self.cleaning_model_combo.setCurrentText(saved_cleaning)
            if saved_writing in default_models:
                self.writing_model_combo.setCurrentText(saved_writing)
            
            self.model_info_label.setText(
                "⚠️ Ollama 연결 실패 또는 모델 없음"
            )
            self.model_info_label.setStyleSheet(
                "color: orange; font-size: 9pt;"
            )

    @Slot(str)
    def _on_cleaning_model_changed(self, model_name: str):
        """정리용 모델 선택 변경"""
        self.selected_cleaning_model = model_name
        self.settings.cleaning_model = model_name  # 설정 저장
        logger.info(f"선택된 정리용 AI 모델: {model_name}")

    @Slot(str)
    def _on_writing_model_changed(self, model_name: str):
        """작성용 모델 선택 변경"""
        self.selected_writing_model = model_name
        self.settings.writing_model = model_name  # 설정 저장
        logger.info(f"선택된 작성용 AI 모델: {model_name}")

    @Slot()
    def _on_edit_prompts(self):
        """프롬프트 편집 다이얼로그 열기"""
        dialog = PromptEditorDialog(self)
        dialog.exec()

    def _create_menu_bar(self):
        """메뉴바 생성"""
        menubar = self.menuBar()
        
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
        """창 닫기 이벤트"""
        # 윈도우 크기/위치 저장
        self.settings.set_window_geometry(
            width=self.width(),
            height=self.height(),
            x=self.x(),
            y=self.y()
        )
        
        # PDF 추출 모드 저장
        self.settings.pdf_extraction_mode = self.pdf_mode_combo.currentIndex()
        
        # 오늘 날짜 자동 검색 체크박스 저장
        self.settings.auto_search_today = self.auto_check.isChecked()
        
        logger.info("설정 저장 완료")
        
        # 시스템 모니터 중지
        if hasattr(self, 'system_monitor'):
            self.system_monitor.stop_monitoring()
        
        # Ollama 서버는 계속 실행 (다른 용도로 사용 가능)
        # 필요시 주석 해제:
        # self.ollama_manager.stop_server()
        
        event.accept()

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
        
        # PDF 추출 모드 적용
        pdf_mode_idx = self.settings.pdf_extraction_mode
        if 0 <= pdf_mode_idx < self.pdf_mode_combo.count():
            self.pdf_mode_combo.setCurrentIndex(pdf_mode_idx)
        
        # 오늘 날짜 자동 검색 체크박스 적용
        self.auto_check.setChecked(self.settings.auto_search_today)
        
        logger.info("저장된 설정 적용 완료")

