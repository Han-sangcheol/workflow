"""
프롬프트 편집 다이얼로그
사용자가 AI 프롬프트를 직접 편집/저장/불러오기 할 수 있는 UI입니다.
- 각 항목별 프롬프트와 예제를 별도 탭에서 관리
- 예제는 프롬프트에서 {examples} 플레이스홀더로 참조 가능
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
            "example_hint": "예: 올바른 출력 형식, 프로젝트 분류 예시 등",
        },
        "summary": {
            "title": "통합 회의록 프롬프트",
            "description": "정리된 텍스트를 바탕으로 회의록을 생성하는 프롬프트",
            "tab_name": "2️⃣ 통합 회의록",
            "example_hint": "예: 회의록 작성 예시, 번호 체계 예시 등",
        },
        "thanks": {
            "title": "감사 인사 프롬프트",
            "description": "팀원별 감사 인사를 생성하는 프롬프트",
            "tab_name": "3️⃣ 감사 인사",
            "example_hint": "예: 감사 인사 문구 예시, 톤앤매너 참조 등",
        },
        "devstatus": {
            "title": "개발 현황 프롬프트",
            "description": "오전/오후 개발 현황 메시지를 생성하는 프롬프트",
            "tab_name": "4️⃣ 개발 현황",
            "example_hint": "예: 오전/오후 메시지 예시, 항목 작성 형식 등",
        },
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = get_settings()
        self.prompt_editors = {}  # 타입별 프롬프트 QTextEdit
        self.example_editors = {}  # 타입별 예제 QTextEdit
        
        self._init_ui()
        self._load_prompts()
        self._load_examples()
    
    def _init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("프롬프트 편집")
        self.setMinimumSize(900, 700)
        self.resize(1000, 800)
        
        layout = QVBoxLayout(self)
        
        # 설명 라벨
        info_label = QLabel(
            "💡 프롬프트와 예제를 수정하여 AI의 동작을 커스터마이징할 수 있습니다.\n"
            "   예제는 프롬프트에서 {examples} 플레이스홀더로 참조됩니다. 비어있으면 기본값이 사용됩니다."
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
        """프롬프트 편집 탭 생성 (프롬프트/예제 서브탭 포함)"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 서브 탭 위젯 (프롬프트 / 예제)
        sub_tab_widget = QTabWidget()
        sub_tab_widget.setStyleSheet("QTabBar::tab { padding: 6px 15px; }")
        
        # 프롬프트 서브탭
        prompt_sub_tab = self._create_prompt_sub_tab(prompt_type, info)
        sub_tab_widget.addTab(prompt_sub_tab, "📝 프롬프트")
        
        # 예제 서브탭
        example_sub_tab = self._create_example_sub_tab(prompt_type, info)
        sub_tab_widget.addTab(example_sub_tab, "📋 예제")
        
        layout.addWidget(sub_tab_widget)
        
        return tab
    
    def _create_prompt_sub_tab(self, prompt_type: str, info: dict) -> QWidget:
        """프롬프트 편집 서브탭 생성"""
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
            lambda: self._load_from_file(prompt_type, is_example=False)
        )
        header_layout.addWidget(load_btn)
        
        export_btn = QPushButton("📤 내보내기")
        export_btn.setToolTip("프롬프트를 파일로 저장")
        export_btn.clicked.connect(
            lambda: self._export_to_file(prompt_type, is_example=False)
        )
        header_layout.addWidget(export_btn)
        
        layout.addLayout(header_layout)
        
        # 텍스트 편집 영역
        editor = QTextEdit()
        editor.setPlaceholderText(
            "프롬프트를 입력하세요...\n"
            "비어있으면 기본 프롬프트가 사용됩니다.\n\n"
            "💡 팁: {examples} 플레이스홀더를 추가하면 예제 탭의 내용이 삽입됩니다."
        )
        editor.setStyleSheet(
            "font-family: 'Consolas', 'Courier New', monospace; "
            "font-size: 10pt;"
        )
        layout.addWidget(editor)
        
        # 에디터 저장
        self.prompt_editors[prompt_type] = editor
        
        return tab
    
    def _create_example_sub_tab(self, prompt_type: str, info: dict) -> QWidget:
        """예제 편집 서브탭 생성"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 상단: 설명 및 버튼
        header_layout = QHBoxLayout()
        
        # 설명
        hint = info.get("example_hint", "예제를 입력하세요")
        desc_label = QLabel(f"📋 예제 등록 - {hint}")
        desc_label.setStyleSheet("font-size: 10pt; color: #555;")
        header_layout.addWidget(desc_label)
        
        header_layout.addStretch()
        
        # 버튼들
        clear_btn = QPushButton("🗑️ 비우기")
        clear_btn.setToolTip("예제 내용 비우기")
        clear_btn.clicked.connect(
            lambda: self._clear_example(prompt_type)
        )
        header_layout.addWidget(clear_btn)
        
        load_btn = QPushButton("📂 불러오기")
        load_btn.setToolTip("파일에서 예제 불러오기")
        load_btn.clicked.connect(
            lambda: self._load_from_file(prompt_type, is_example=True)
        )
        header_layout.addWidget(load_btn)
        
        export_btn = QPushButton("📤 내보내기")
        export_btn.setToolTip("예제를 파일로 저장")
        export_btn.clicked.connect(
            lambda: self._export_to_file(prompt_type, is_example=True)
        )
        header_layout.addWidget(export_btn)
        
        layout.addLayout(header_layout)
        
        # 안내 라벨
        guide_label = QLabel(
            "💡 여기에 등록한 예제는 프롬프트의 {examples} 위치에 자동 삽입됩니다.\n"
            "   예제를 자주 변경하면서 프롬프트는 그대로 유지할 수 있습니다."
        )
        guide_label.setStyleSheet(
            "color: #0066cc; font-size: 9pt; padding: 5px; "
            "background-color: #e8f4fc; border-radius: 4px;"
        )
        layout.addWidget(guide_label)
        
        # 텍스트 편집 영역
        editor = QTextEdit()
        editor.setPlaceholderText(
            f"예제를 입력하세요...\n\n"
            f"{hint}\n\n"
            "이 내용은 프롬프트의 {examples} 플레이스홀더 위치에 삽입됩니다."
        )
        editor.setStyleSheet(
            "font-family: 'Consolas', 'Courier New', monospace; "
            "font-size: 10pt;"
        )
        layout.addWidget(editor)
        
        # 예제 에디터 저장
        self.example_editors[prompt_type] = editor
        
        return tab
    
    def _load_prompts(self):
        """저장된 프롬프트 로드"""
        for prompt_type, editor in self.prompt_editors.items():
            # 사용자 저장 프롬프트 조회
            user_prompts = self.settings.get_all_prompts()
            user_prompt = user_prompts.get(prompt_type, "")
            
            if user_prompt:
                # 사용자 저장 프롬프트가 있으면 표시
                editor.setPlainText(user_prompt)
            else:
                # 없으면 기본 프롬프트를 직접 표시
                default_prompt = get_default_prompt(prompt_type)
                editor.setPlainText(default_prompt)
    
    def _load_examples(self):
        """저장된 예제 로드"""
        user_examples = self.settings.get_all_examples()
        for prompt_type, editor in self.example_editors.items():
            example = user_examples.get(prompt_type, "")
            if example:
                editor.setPlainText(example)
    
    def _reset_prompt(self, prompt_type: str):
        """프롬프트 초기화 (기본값으로 복원)"""
        reply = QMessageBox.question(
            self,
            "초기화 확인",
            f"'{self.PROMPT_TYPES[prompt_type]['title']}'을(를) 기본값으로 초기화하시겠습니까?\n\n"
            "현재 입력된 내용이 기본 프롬프트로 대체됩니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 기본 프롬프트로 복원
            default_prompt = get_default_prompt(prompt_type)
            self.prompt_editors[prompt_type].setPlainText(default_prompt)
            logger.info(f"프롬프트 초기화: {prompt_type}")
    
    def _clear_example(self, prompt_type: str):
        """예제 비우기"""
        reply = QMessageBox.question(
            self,
            "예제 비우기",
            f"'{self.PROMPT_TYPES[prompt_type]['title']}' 예제를 비우시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.example_editors[prompt_type].clear()
            logger.info(f"예제 비우기: {prompt_type}")
    
    def _load_from_file(self, prompt_type: str, is_example: bool = False):
        """파일에서 프롬프트/예제 불러오기"""
        target_name = "예제" if is_example else "프롬프트"
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"{target_name} 파일 불러오기",
            "",
            "텍스트 파일 (*.txt);;모든 파일 (*.*)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if is_example:
                self.example_editors[prompt_type].setPlainText(content)
            else:
                self.prompt_editors[prompt_type].setPlainText(content)
            
            logger.info(f"{target_name} 불러오기: {file_path}")
            
            QMessageBox.information(
                self,
                "불러오기 완료",
                f"{target_name}를 불러왔습니다:\n{Path(file_path).name}"
            )
        except Exception as e:
            logger.error(f"{target_name} 불러오기 실패: {e}")
            QMessageBox.critical(
                self,
                "오류",
                f"파일을 불러올 수 없습니다:\n{str(e)}"
            )
    
    def _export_to_file(self, prompt_type: str, is_example: bool = False):
        """프롬프트/예제를 파일로 내보내기"""
        target_name = "예제" if is_example else "프롬프트"
        
        if is_example:
            editor = self.example_editors[prompt_type]
            content = editor.toPlainText()
            default_name = f"example_{prompt_type}.txt"
        else:
            editor = self.prompt_editors[prompt_type]
            content = editor.toPlainText()
            default_name = f"prompt_{prompt_type}.txt"
            # 비어있으면 기본 프롬프트 내보내기
            if not content.strip():
                content = get_default_prompt(prompt_type)
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"{target_name} 내보내기",
            default_name,
            "텍스트 파일 (*.txt);;모든 파일 (*.*)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"{target_name} 내보내기: {file_path}")
            
            QMessageBox.information(
                self,
                "내보내기 완료",
                f"{target_name}를 저장했습니다:\n{Path(file_path).name}"
            )
        except Exception as e:
            logger.error(f"{target_name} 내보내기 실패: {e}")
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
            current_text = editor.toPlainText().strip()
            default_text = get_default_prompt(prompt_type).strip()
            
            # 기본 프롬프트와 동일하면 빈 문자열로 저장 (기본값 사용)
            if current_text == default_text:
                prompts[prompt_type] = ""
            else:
                prompts[prompt_type] = current_text
        
        self.settings.set_all_prompts(
            cleaning=prompts.get("cleaning", ""),
            summary=prompts.get("summary", ""),
            thanks=prompts.get("thanks", ""),
            devstatus=prompts.get("devstatus", "")
        )
        
        # 모든 예제 저장
        examples = {}
        for prompt_type, editor in self.example_editors.items():
            examples[prompt_type] = editor.toPlainText().strip()
        
        self.settings.set_all_examples(
            cleaning=examples.get("cleaning", ""),
            summary=examples.get("summary", ""),
            thanks=examples.get("thanks", ""),
            devstatus=examples.get("devstatus", "")
        )
        
        logger.info("프롬프트 및 예제 저장 완료")
        
        # 저장 결과 메시지 생성
        saved_prompt_count = sum(1 for v in prompts.values() if v)
        saved_example_count = sum(1 for v in examples.values() if v)
        
        msg_parts = []
        if saved_prompt_count > 0:
            msg_parts.append(f"커스텀 프롬프트 {saved_prompt_count}개")
        if saved_example_count > 0:
            msg_parts.append(f"예제 {saved_example_count}개")
        
        if msg_parts:
            msg = f"{', '.join(msg_parts)}가 저장되었습니다.\n\n"
        else:
            msg = "모든 프롬프트가 기본값으로 설정되었습니다.\n\n"
        msg += "다음 분석부터 적용됩니다."
        
        QMessageBox.information(
            self,
            "저장 완료",
            msg
        )
        
        self.accept()

