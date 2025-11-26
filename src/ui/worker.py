"""
작업 스레드
문서 파싱과 AI 분석을 백그라운드에서 수행합니다.
"""

import logging
import time
from typing import List

from PySide6.QtCore import QThread, Signal

from ..document.document_parser import DocumentParser
from ..ai.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class AnalysisWorker(QThread):
    """분석 작업 워커 스레드"""

    # 신호 정의
    progress_updated = Signal(str)  # 진행 상황 메시지
    step_completed = Signal(int)  # 단계 완료 (1,2,3,4,5)
    step_time_recorded = Signal(int, float)  # 스텝별 소요 시간 (스텝 번호, 초)
    step_analysis_recorded = Signal(int, int, float)  # 분석 이력 기록 (스텝 번호, 텍스트 길이, 소요 시간)
    documents_parsed = Signal(str)  # 문서 파싱 완료 (원본 텍스트)
    text_cleaned = Signal(str)  # 텍스트 정리 완료
    summary_ready = Signal(str)  # 회의록 준비 완료
    thanks_ready = Signal(str)  # 감사 인사 준비 완료
    devstatus_ready = Signal(str)  # 개발 현황 준비 완료
    error_occurred = Signal(str)  # 오류 발생
    finished = Signal()  # 작업 완료

    def __init__(
        self,
        file_paths: List[str],
        pdf_extraction_mode: str = "smart",
        cleaning_model: str = "llama3.2",
        writing_model: str = "llama3.2"
    ):
        """
        초기화
        
        Args:
            file_paths: 분석할 파일 경로 리스트
            pdf_extraction_mode: PDF 추출 모드 (simple, smart, layout)
            cleaning_model: 텍스트 정리용 AI 모델
            writing_model: 회의록/감사인사 작성용 AI 모델
        """
        super().__init__()
        self.file_paths = file_paths
        self.pdf_extraction_mode = pdf_extraction_mode
        self.doc_parser = DocumentParser()
        self.cleaning_client = OllamaClient(model=cleaning_model)
        self.writing_client = OllamaClient(model=writing_model)
        self._is_cancelled = False
        
        logger.info(
            f"워커 초기화: PDF모드={pdf_extraction_mode}, "
            f"정리={cleaning_model}, 작성={writing_model}, "
            f"파일={len(file_paths)}개"
        )

    def run(self):
        """작업 실행"""
        try:
            # Step 1: 문서 파싱
            self.progress_updated.emit(
                "Step 1: 문서 파일 읽기 중..."
            )
            
            step1_start = time.time()
            documents_text = self._parse_documents()
            step1_time = time.time() - step1_start
            
            if not documents_text:
                self.error_occurred.emit(
                    "문서를 읽을 수 없습니다"
                )
                return
            
            # 원본 텍스트 전달
            documents_len = len(documents_text)
            self.documents_parsed.emit(documents_text)
            self.step_completed.emit(1)
            self.step_time_recorded.emit(1, step1_time)
            self.step_analysis_recorded.emit(1, documents_len, step1_time)
            
            if self._is_cancelled:
                return
            
            # Step 2: 텍스트 정리 및 구조화
            self.progress_updated.emit(
                "Step 2: AI로 텍스트 정리 중..."
            )
            
            step2_start = time.time()
            cleaned_text = self.cleaning_client.clean_and_organize(
                documents_text,
                progress_callback=self._ai_progress_callback
            )
            step2_time = time.time() - step2_start
            
            if not cleaned_text:
                self.error_occurred.emit(
                    "텍스트 정리 실패. Ollama가 실행 중인지 확인하세요"
                )
                return
            
            cleaned_len = len(cleaned_text)
            self.text_cleaned.emit(cleaned_text)
            self.step_completed.emit(2)
            self.step_time_recorded.emit(2, step2_time)
            self.step_analysis_recorded.emit(2, documents_len, step2_time)
            
            if self._is_cancelled:
                return
            
            # Step 3: 통합 회의록 생성
            self.progress_updated.emit(
                "Step 3: AI로 회의록 생성 중..."
            )
            
            step3_start = time.time()
            summary = self.writing_client.generate_summary(
                cleaned_text,  # 정리된 텍스트 사용
                progress_callback=self._ai_progress_callback
            )
            step3_time = time.time() - step3_start
            
            if not summary:
                self.error_occurred.emit(
                    "회의록 생성 실패"
                )
                return
            
            self.summary_ready.emit(summary)
            self.step_completed.emit(3)
            self.step_time_recorded.emit(3, step3_time)
            self.step_analysis_recorded.emit(3, cleaned_len, step3_time)
            
            if self._is_cancelled:
                return
            
            # Step 4: 감사 인사 생성
            self.progress_updated.emit(
                "Step 4: AI로 감사 인사 생성 중..."
            )
            
            step4_start = time.time()
            thanks = self.writing_client.generate_thanks(
                cleaned_text,  # 정리된 텍스트 사용
                progress_callback=self._ai_progress_callback
            )
            step4_time = time.time() - step4_start
            
            if not thanks:
                self.error_occurred.emit("감사 인사 생성 실패")
                return
            
            self.thanks_ready.emit(thanks)
            self.step_completed.emit(4)
            self.step_time_recorded.emit(4, step4_time)
            self.step_analysis_recorded.emit(4, cleaned_len, step4_time)
            
            if self._is_cancelled:
                return
            
            # Step 5: 개발 현황 생성
            self.progress_updated.emit(
                "Step 5: AI로 개발 현황 생성 중..."
            )
            
            step5_start = time.time()
            devstatus = self.writing_client.generate_devstatus(
                cleaned_text,  # 정리된 텍스트 사용
                progress_callback=self._ai_progress_callback
            )
            step5_time = time.time() - step5_start
            
            if not devstatus:
                self.error_occurred.emit("개발 현황 생성 실패")
                return
            
            self.devstatus_ready.emit(devstatus)
            self.step_completed.emit(5)
            self.step_time_recorded.emit(5, step5_time)
            self.step_analysis_recorded.emit(5, cleaned_len, step5_time)
            
            self.progress_updated.emit("모든 작업 완료!")
            
        except Exception as e:
            logger.error(f"작업 중 오류: {str(e)}")
            self.error_occurred.emit(f"오류 발생: {str(e)}")
        
        finally:
            self.finished.emit()

    def _parse_documents(self) -> str:
        """문서 파싱"""
        all_text = []
        
        for i, file_path in enumerate(self.file_paths, 1):
            if self._is_cancelled:
                break
            
            self.progress_updated.emit(
                f"파일 {i}/{len(self.file_paths)} 읽기 중..."
            )
            
            text = self.doc_parser.parse_file(
                file_path,
                pdf_extraction_mode=self.pdf_extraction_mode
            )
            if text:
                all_text.append(f"=== 파일: {file_path} ===\n{text}")
        
        return "\n\n".join(all_text)

    def _ai_progress_callback(self, chunk: str):
        """AI 생성 진행 중 콜백"""
        # 실시간 업데이트는 UI에 부담이 될 수 있어 생략
        pass

    def cancel(self):
        """작업 취소"""
        self._is_cancelled = True
        logger.info("작업 취소 요청됨")

