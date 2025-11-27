"""
개별 분석 단계를 실행하는 워커 클래스
- clean: 원본 텍스트 → 정리된 텍스트
- summary: 정리된 텍스트 → 통합 회의록
- thanks: 정리된 텍스트 → 감사 인사
- devstatus: 정리된 텍스트 → 개발 현황
AI 실시간 생성 표시 지원
"""
import logging
from PySide6.QtCore import QThread, Signal, Slot

from src.ai.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class SingleStepWorker(QThread):
    """개별 분석 단계 실행 워커"""
    
    # 시그널 정의
    progress = Signal(str)          # 진행 상황 메시지
    result_ready = Signal(str)      # 분석 결과
    error = Signal(str)             # 오류 메시지
    finished = Signal()             # 완료 시그널
    ai_thinking = Signal(str)       # AI 실시간 생성 텍스트
    
    def __init__(
        self,
        step_type: str,
        source_text: str,
        cleaning_model: str = "gemma3:4b",
        summary_model: str = "gemma3:4b",
        thanks_model: str = "gemma3:4b",
        devstatus_model: str = "gemma3:4b"
    ):
        """
        Args:
            step_type: 실행할 단계 ("clean", "summary", "thanks", "devstatus")
            source_text: 입력 텍스트
            cleaning_model: 텍스트 정리용 AI 모델
            summary_model: 회의록 생성용 AI 모델
            thanks_model: 감사인사 생성용 AI 모델
            devstatus_model: 개발현황 생성용 AI 모델
        """
        super().__init__()
        self.step_type = step_type
        self.source_text = source_text
        self.cleaning_model = cleaning_model
        self.summary_model = summary_model
        self.thanks_model = thanks_model
        self.devstatus_model = devstatus_model
        self._is_cancelled = False
    
    def cancel(self):
        """작업 취소 요청"""
        self._is_cancelled = True
        logger.info(f"SingleStepWorker 취소 요청: {self.step_type}")
    
    def run(self):
        """워커 실행"""
        try:
            if self.step_type == "clean":
                self._run_clean()
            elif self.step_type == "summary":
                self._run_summary()
            elif self.step_type == "thanks":
                self._run_thanks()
            elif self.step_type == "devstatus":
                self._run_devstatus()
            else:
                self.error.emit(f"알 수 없는 단계: {self.step_type}")
                return
        except Exception as e:
            logger.error(f"단일 단계 분석 오류: {e}")
            self.error.emit(f"분석 중 오류 발생: {str(e)}")
        finally:
            self.finished.emit()
    
    def _ai_progress_callback(self, chunk: str):
        """AI 생성 진행 중 콜백 - 실시간 텍스트 전달"""
        if chunk:
            self.ai_thinking.emit(chunk)
    
    def _run_clean(self):
        """텍스트 정리 실행"""
        self.progress.emit("Step 2: 텍스트 정리 중...")
        
        client = OllamaClient(model=self.cleaning_model)
        if not client.is_available():
            self.error.emit("Ollama 서버에 연결할 수 없습니다.")
            return
        
        result = client.clean_and_organize(
            self.source_text,
            progress_callback=self._ai_progress_callback
        )
        if result:
            self.result_ready.emit(result)
            self.progress.emit("텍스트 정리 완료!")
        else:
            self.error.emit("텍스트 정리에 실패했습니다.")
    
    def _run_summary(self):
        """회의록 생성 실행"""
        self.progress.emit("Step 3: 회의록 생성 중...")
        
        client = OllamaClient(model=self.summary_model)
        if not client.is_available():
            self.error.emit("Ollama 서버에 연결할 수 없습니다.")
            return
        
        result = client.generate_summary(
            self.source_text,
            progress_callback=self._ai_progress_callback
        )
        if result:
            self.result_ready.emit(result)
            self.progress.emit("회의록 생성 완료!")
        else:
            self.error.emit("회의록 생성에 실패했습니다.")
    
    def _run_thanks(self):
        """감사인사 생성 실행"""
        self.progress.emit("Step 4: 감사인사 생성 중...")
        
        client = OllamaClient(model=self.thanks_model)
        if not client.is_available():
            self.error.emit("Ollama 서버에 연결할 수 없습니다.")
            return
        
        result = client.generate_thanks(
            self.source_text,
            progress_callback=self._ai_progress_callback
        )
        if result:
            self.result_ready.emit(result)
            self.progress.emit("감사인사 생성 완료!")
        else:
            self.error.emit("감사인사 생성에 실패했습니다.")
    
    def _run_devstatus(self):
        """개발 현황 생성 실행"""
        self.progress.emit("Step 5: 개발 현황 생성 중...")
        
        client = OllamaClient(model=self.devstatus_model)
        if not client.is_available():
            self.error.emit("Ollama 서버에 연결할 수 없습니다.")
            return
        
        result = client.generate_devstatus(
            self.source_text,
            progress_callback=self._ai_progress_callback
        )
        if result:
            self.result_ready.emit(result)
            self.progress.emit("개발 현황 생성 완료!")
        else:
            self.error.emit("개발 현황 생성에 실패했습니다.")

