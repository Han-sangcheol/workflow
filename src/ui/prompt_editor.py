"""
프롬프트 편집 다이얼로그
사용자가 AI 프롬프트를 직접 편집/저장/불러오기 할 수 있는 UI입니다.
"""

import logging
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QTextEdit, QLabel, QFileDialog,
    QMessageBox, QWidget
)
from PySide6.QtCore import Qt

from ..ai.prompt_config import get_default_prompt, get_prompt
from ..utils.settings_manager import get_settings

logger = logging.getLogger(__name__)


class PromptEditorDialog(QDialog):
    """프롬프트 편집 다이얼로그"""
    
    # 프롬프트 타입별 정보
    PROMPT_TYPES = {
        "cleaning": {
            "title": "텍스트 정리 프롬프트",
            "description": "원본 텍스트를 구조화된 형식으로 정리하는 프롬프트",
            "tab_name": "1️⃣ 텍스트 정리",
        },
        "summary": {
            "title": "통합 회의록 프롬프트",
            "description": "정리된 텍스트를 바탕으로 회의록을 생성하는 프롬프트",
            "tab_name": "2️⃣ 통합 회의록",
        },
        "thanks": {
            "title": "감사 인사 프롬프트",
            "description": "팀원별 감사 인사를 생성하는 프롬프트",
            "tab_name": "3️⃣ 감사 인사",
        },
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = get_settings()
        self.prompt_editors = {}  # 타입별 QTextEdit
        
        self._init_ui()
        self._load_prompts()
    
    def _init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("프롬프트 편집")
        self.setMinimumSize(800, 600)
        self.resize(900, 700)
        
        layout = QVBoxLayout(self)
        
        # 설명 라벨
        info_label = QLabel(
            "💡 프롬프트를 수정하여 AI의 동작을 커스터마이징할 수 있습니다.\n"
            "   비어있으면 기본 프롬프트가 사용됩니다."
        )
        info_label.setStyleSheet("color: #666; font-size: 10pt; padding: 5px;")
        layout.addWidget(info_label)
        
        # 탭 위젯
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget, stretch=1)
        
        # 각 프롬프트 타입별 탭 생성
        for prompt_type, info in self.PROMPT_TYPES.items():
            tab = self._create_prompt_tab(prompt_type, info)
            self.tab_widget.addTab(tab, info["tab_name"])
        
        # 하단 버튼
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("💾 저장")
        self.save_btn.setStyleSheet("font-size: 11pt; padding: 8px 20px;")
        self.save_btn.clicked.connect(self._on_save)
        
        self.cancel_btn = QPushButton("취소")
        self.cancel_btn.setStyleSheet("font-size: 11pt; padding: 8px 20px;")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _create_prompt_tab(self, prompt_type: str, info: dict) -> QWidget:
        """프롬프트 편집 탭 생성"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 상단: 설명 및 버튼
        header_layout = QHBoxLayout()
        
        # 설명
        desc_label = QLabel(f"📝 {info['description']}")
        desc_label.setStyleSheet("font-size: 10pt; color: #555;")
        header_layout.addWidget(desc_label)
        
        header_layout.addStretch()
        
        # 버튼들
        reset_btn = QPushButton("🔄 초기화")
        reset_btn.setToolTip("기본 프롬프트로 복원")
        reset_btn.clicked.connect(
            lambda: self._reset_prompt(prompt_type)
        )
        header_layout.addWidget(reset_btn)
        
        load_btn = QPushButton("📂 불러오기")
        load_btn.setToolTip("파일에서 프롬프트 불러오기")
        load_btn.clicked.connect(
            lambda: self._load_from_file(prompt_type)
        )
        header_layout.addWidget(load_btn)
        
        export_btn = QPushButton("📤 내보내기")
        export_btn.setToolTip("프롬프트를 파일로 저장")
        export_btn.clicked.connect(
            lambda: self._export_to_file(prompt_type)
        )
        header_layout.addWidget(export_btn)
        
        layout.addLayout(header_layout)
        
        # 텍스트 편집 영역
        editor = QTextEdit()
        editor.setPlaceholderText(
            "프롬프트를 입력하세요...\n"
            "비어있으면 기본 프롬프트가 사용됩니다."
        )
        editor.setStyleSheet(
            "font-family: 'Consolas', 'Courier New', monospace; "
            "font-size: 10pt;"
        )
        layout.addWidget(editor)
        
        # 에디터 저장
        self.prompt_editors[prompt_type] = editor
        
        return tab
    
    def _load_prompts(self):
        """저장된 프롬프트 로드"""
        for prompt_type, editor in self.prompt_editors.items():
            # 사용자 저장 프롬프트 조회
            user_prompts = self.settings.get_all_prompts()
            user_prompt = user_prompts.get(prompt_type, "")
            
            if user_prompt:
                editor.setPlainText(user_prompt)
            else:
                # 비어있으면 기본 프롬프트 표시 (회색)
                editor.setPlaceholderText(
                    f"(기본 프롬프트 사용 중)\n\n{get_default_prompt(prompt_type)[:500]}..."
                )
    
    def _reset_prompt(self, prompt_type: str):
        """프롬프트 초기화 (기본값으로 복원)"""
        reply = QMessageBox.question(
            self,
            "초기화 확인",
            f"'{self.PROMPT_TYPES[prompt_type]['title']}'을(를) 기본값으로 초기화하시겠습니까?\n\n"
            "현재 입력된 내용은 삭제됩니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 에디터 비우기 (비어있으면 기본 프롬프트 사용)
            self.prompt_editors[prompt_type].clear()
            logger.info(f"프롬프트 초기화: {prompt_type}")
    
    def _load_from_file(self, prompt_type: str):
        """파일에서 프롬프트 불러오기"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "프롬프트 파일 불러오기",
            "",
            "텍스트 파일 (*.txt);;모든 파일 (*.*)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.prompt_editors[prompt_type].setPlainText(content)
            logger.info(f"프롬프트 불러오기: {file_path}")
            
            QMessageBox.information(
                self,
                "불러오기 완료",
                f"프롬프트를 불러왔습니다:\n{Path(file_path).name}"
            )
        except Exception as e:
            logger.error(f"프롬프트 불러오기 실패: {e}")
            QMessageBox.critical(
                self,
                "오류",
                f"파일을 불러올 수 없습니다:\n{str(e)}"
            )
    
    def _export_to_file(self, prompt_type: str):
        """프롬프트를 파일로 내보내기"""
        editor = self.prompt_editors[prompt_type]
        content = editor.toPlainText()
        
        # 비어있으면 기본 프롬프트 내보내기
        if not content.strip():
            content = get_default_prompt(prompt_type)
        
        # 기본 파일명 생성
        default_name = f"prompt_{prompt_type}.txt"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "프롬프트 내보내기",
            default_name,
            "텍스트 파일 (*.txt);;모든 파일 (*.*)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"프롬프트 내보내기: {file_path}")
            
            QMessageBox.information(
                self,
                "내보내기 완료",
                f"프롬프트를 저장했습니다:\n{Path(file_path).name}"
            )
        except Exception as e:
            logger.error(f"프롬프트 내보내기 실패: {e}")
            QMessageBox.critical(
                self,
                "오류",
                f"파일을 저장할 수 없습니다:\n{str(e)}"
            )
    
    def _on_save(self):
        """저장 버튼 클릭"""
        # 모든 프롬프트 저장
        prompts = {}
        for prompt_type, editor in self.prompt_editors.items():
            prompts[prompt_type] = editor.toPlainText().strip()
        
        self.settings.set_all_prompts(
            cleaning=prompts.get("cleaning", ""),
            summary=prompts.get("summary", ""),
            thanks=prompts.get("thanks", "")
        )
        
        logger.info("프롬프트 저장 완료")
        
        QMessageBox.information(
            self,
            "저장 완료",
            "프롬프트가 저장되었습니다.\n\n"
            "다음 분석부터 적용됩니다."
        )
        
        self.accept()

