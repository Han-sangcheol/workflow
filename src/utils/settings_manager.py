"""
설정 관리 모듈
애플리케이션 설정을 JSON 파일로 저장/로드합니다.
"""

import sys
import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def get_app_data_dir() -> Path:
    """애플리케이션 데이터 디렉토리 반환 (설정, 로그, DB 파일 저장용)"""
    if sys.platform == 'win32':
        # Windows: %LOCALAPPDATA%\WorkflowAnalyzer
        base_dir = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local'))
    else:
        # Linux/Mac: ~/.local/share/WorkflowAnalyzer
        base_dir = Path.home() / '.local' / 'share'
    
    app_dir = base_dir / 'WorkflowAnalyzer'
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir

# 기본 설정값
DEFAULT_SETTINGS = {
    # AI 모델 설정 (각 단계별 별도 선택 가능)
    "cleaning_model": "llama3.2:latest",    # 텍스트 정리용
    "summary_model": "llama3.2:latest",     # 회의록 생성용
    "thanks_model": "llama3.2:latest",      # 감사인사 생성용
    "devstatus_model": "llama3.2:latest",   # 개발현황 생성용
    # 레거시 호환성 (기존 writing_model은 summary_model로 마이그레이션)
    "writing_model": "llama3.2:latest",
    "pdf_extraction_mode": 0,  # 0: smart, 1: layout, 2: simple
    "auto_search_today": True,
    "last_folder_path": "",
    "last_save_path": "",
    # 윈도우 크기/위치
    "window_width": 1100,
    "window_height": 750,
    "window_x": None,
    "window_y": None,
    # 스플리터 상태 (각 영역 크기 저장)
    "main_splitter_sizes": None,      # 좌/우 분할 [왼쪽너비, 오른쪽너비]
    "vertical_splitter_sizes": None,  # 상/하 분할 [상단높이, 하단높이]
    # 사용자 프롬프트 (빈 문자열이면 코드 기본값 사용)
    "cleaning_prompt": "",
    "summary_prompt": "",
    "thanks_prompt": "",
    "devstatus_prompt": "",
    # 마지막 분석 결과 (프로그램 재시작 시 복원)
    "last_analysis_results": {
        "documents_text": "",    # 1단계: 원본 텍스트
        "cleaned_text": "",      # 2단계: 정리된 텍스트
        "summary_text": "",      # 3단계: 회의록
        "thanks_text": "",       # 4단계: 감사인사
        "devstatus_text": "",    # 5단계: 개발현황
    },
    # 분석 이력 (예상 시간 계산용) - 최근 10개 기록 유지
    # 형식: {"step_N": [{"text_len": int, "seconds": float}, ...]}
    "analysis_history": {
        "step_1": [],  # 문서 파싱
        "step_2": [],  # 텍스트 정리
        "step_3": [],  # 회의록 생성
        "step_4": [],  # 감사인사 생성
        "step_5": [],  # 개발현황 생성
    },
}


class SettingsManager:
    """애플리케이션 설정 관리 클래스"""
    
    # 설정 파일명
    SETTINGS_FILE = "settings.json"
    
    def __init__(self, app_name: str = "WorkflowAI"):
        """
        초기화
        
        Args:
            app_name: 애플리케이션 이름 (설정 폴더명)
        """
        self.app_name = app_name
        self._settings: Dict[str, Any] = DEFAULT_SETTINGS.copy()
        self._settings_path = self._get_settings_path()
        self._load_settings()
    
    def _get_settings_path(self) -> Path:
        """설정 파일 경로 반환 (사용자 데이터 폴더)"""
        # 사용자 데이터 폴더에 설정 파일 저장 (Program Files 권한 문제 방지)
        app_data_dir = get_app_data_dir()
        settings_file = app_data_dir / self.SETTINGS_FILE
        return settings_file
    
    def _load_settings(self) -> None:
        """설정 파일 로드"""
        try:
            if self._settings_path.exists():
                with open(self._settings_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # 기본값과 병합 (새 설정 항목 자동 추가)
                    for key, value in DEFAULT_SETTINGS.items():
                        if key not in loaded:
                            loaded[key] = value
                    self._settings = loaded
                    logger.info(f"설정 파일 로드 완료: {self._settings_path}")
            else:
                logger.info("설정 파일 없음, 기본값 사용")
        except Exception as e:
            logger.error(f"설정 로드 오류: {e}")
            self._settings = DEFAULT_SETTINGS.copy()
    
    def save_settings(self) -> bool:
        """설정 파일 저장"""
        try:
            with open(self._settings_path, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, ensure_ascii=False, indent=2)
            logger.info(f"설정 파일 저장 완료: {self._settings_path}")
            return True
        except Exception as e:
            logger.error(f"설정 저장 오류: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """설정값 조회"""
        return self._settings.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """설정값 변경 (자동 저장)"""
        self._settings[key] = value
        self.save_settings()
    
    def set_multiple(self, settings: Dict[str, Any]) -> None:
        """여러 설정값 한번에 변경 (자동 저장)"""
        self._settings.update(settings)
        self.save_settings()
    
    # === 편의 메서드 ===
    
    @property
    def cleaning_model(self) -> str:
        """정리용 AI 모델"""
        return self.get("cleaning_model", DEFAULT_SETTINGS["cleaning_model"])
    
    @cleaning_model.setter
    def cleaning_model(self, value: str) -> None:
        self.set("cleaning_model", value)
    
    @property
    def writing_model(self) -> str:
        """작성용 AI 모델 (레거시 호환)"""
        return self.get("writing_model", DEFAULT_SETTINGS["writing_model"])
    
    @writing_model.setter
    def writing_model(self, value: str) -> None:
        self.set("writing_model", value)
    
    @property
    def summary_model(self) -> str:
        """회의록 생성용 AI 모델"""
        return self.get("summary_model", DEFAULT_SETTINGS["summary_model"])
    
    @summary_model.setter
    def summary_model(self, value: str) -> None:
        self.set("summary_model", value)
    
    @property
    def thanks_model(self) -> str:
        """감사인사 생성용 AI 모델"""
        return self.get("thanks_model", DEFAULT_SETTINGS["thanks_model"])
    
    @thanks_model.setter
    def thanks_model(self, value: str) -> None:
        self.set("thanks_model", value)
    
    @property
    def devstatus_model(self) -> str:
        """개발현황 생성용 AI 모델"""
        return self.get("devstatus_model", DEFAULT_SETTINGS["devstatus_model"])
    
    @devstatus_model.setter
    def devstatus_model(self, value: str) -> None:
        self.set("devstatus_model", value)
    
    @property
    def pdf_extraction_mode(self) -> int:
        """PDF 추출 모드 인덱스"""
        return self.get("pdf_extraction_mode", DEFAULT_SETTINGS["pdf_extraction_mode"])
    
    @pdf_extraction_mode.setter
    def pdf_extraction_mode(self, value: int) -> None:
        self.set("pdf_extraction_mode", value)
    
    @property
    def auto_search_today(self) -> bool:
        """오늘 날짜 자동 검색 여부"""
        return self.get("auto_search_today", DEFAULT_SETTINGS["auto_search_today"])
    
    @auto_search_today.setter
    def auto_search_today(self, value: bool) -> None:
        self.set("auto_search_today", value)
    
    @property
    def last_folder_path(self) -> str:
        """마지막 사용 폴더 경로"""
        return self.get("last_folder_path", DEFAULT_SETTINGS["last_folder_path"])
    
    @last_folder_path.setter
    def last_folder_path(self, value: str) -> None:
        self.set("last_folder_path", value)
    
    @property
    def last_save_path(self) -> str:
        """마지막 저장 경로"""
        return self.get("last_save_path", DEFAULT_SETTINGS["last_save_path"])
    
    @last_save_path.setter
    def last_save_path(self, value: str) -> None:
        self.set("last_save_path", value)
    
    def get_window_geometry(self) -> Dict[str, Optional[int]]:
        """윈도우 크기/위치 반환"""
        return {
            "width": self.get("window_width"),
            "height": self.get("window_height"),
            "x": self.get("window_x"),
            "y": self.get("window_y"),
        }
    
    def set_window_geometry(
        self,
        width: int,
        height: int,
        x: Optional[int] = None,
        y: Optional[int] = None
    ) -> None:
        """윈도우 크기/위치 저장"""
        self.set_multiple({
            "window_width": width,
            "window_height": height,
            "window_x": x,
            "window_y": y,
        })
    
    # === 스플리터 상태 저장/복원 ===
    
    def get_splitter_sizes(self) -> Dict[str, Optional[list]]:
        """스플리터 크기 반환"""
        return {
            "main": self.get("main_splitter_sizes"),
            "vertical": self.get("vertical_splitter_sizes"),
        }
    
    def set_splitter_sizes(
        self,
        main_sizes: Optional[list] = None,
        vertical_sizes: Optional[list] = None
    ) -> None:
        """스플리터 크기 저장"""
        settings_to_save = {}
        if main_sizes is not None:
            settings_to_save["main_splitter_sizes"] = main_sizes
        if vertical_sizes is not None:
            settings_to_save["vertical_splitter_sizes"] = vertical_sizes
        
        if settings_to_save:
            self.set_multiple(settings_to_save)
            logger.info(f"스플리터 상태 저장: main={main_sizes}, vertical={vertical_sizes}")
    
    # === 프롬프트 설정 ===
    
    @property
    def cleaning_prompt(self) -> str:
        """텍스트 정리용 프롬프트 (빈 문자열이면 기본값 사용)"""
        return self.get("cleaning_prompt", "")
    
    @cleaning_prompt.setter
    def cleaning_prompt(self, value: str) -> None:
        self.set("cleaning_prompt", value)
    
    @property
    def summary_prompt(self) -> str:
        """통합 회의록용 프롬프트 (빈 문자열이면 기본값 사용)"""
        return self.get("summary_prompt", "")
    
    @summary_prompt.setter
    def summary_prompt(self, value: str) -> None:
        self.set("summary_prompt", value)
    
    @property
    def thanks_prompt(self) -> str:
        """감사 인사용 프롬프트 (빈 문자열이면 기본값 사용)"""
        return self.get("thanks_prompt", "")
    
    @thanks_prompt.setter
    def thanks_prompt(self, value: str) -> None:
        self.set("thanks_prompt", value)
    
    @property
    def devstatus_prompt(self) -> str:
        """개발 현황용 프롬프트 (빈 문자열이면 기본값 사용)"""
        return self.get("devstatus_prompt", "")
    
    @devstatus_prompt.setter
    def devstatus_prompt(self, value: str) -> None:
        self.set("devstatus_prompt", value)
    
    # === 분석 결과 저장/복원 ===
    
    def get_last_analysis_results(self) -> Dict[str, str]:
        """마지막 분석 결과 반환"""
        default_results = DEFAULT_SETTINGS.get("last_analysis_results", {})
        return self.get("last_analysis_results", default_results)
    
    def save_analysis_results(
        self,
        documents_text: str = "",
        cleaned_text: str = "",
        summary_text: str = "",
        thanks_text: str = "",
        devstatus_text: str = ""
    ) -> None:
        """분석 결과 저장 (프로그램 재시작 시 복원용)"""
        results = {
            "documents_text": documents_text,
            "cleaned_text": cleaned_text,
            "summary_text": summary_text,
            "thanks_text": thanks_text,
            "devstatus_text": devstatus_text,
        }
        self.set("last_analysis_results", results)
        logger.info("분석 결과 저장 완료")
    
    def clear_analysis_results(self) -> None:
        """저장된 분석 결과 초기화"""
        self.set("last_analysis_results", DEFAULT_SETTINGS.get("last_analysis_results", {}))
    
    def get_all_prompts(self) -> Dict[str, str]:
        """모든 사용자 프롬프트 반환"""
        return {
            "cleaning": self.cleaning_prompt,
            "summary": self.summary_prompt,
            "thanks": self.thanks_prompt,
            "devstatus": self.devstatus_prompt,
        }
    
    def set_all_prompts(
        self,
        cleaning: str = "",
        summary: str = "",
        thanks: str = "",
        devstatus: str = ""
    ) -> None:
        """모든 프롬프트 한번에 저장 (자동 저장)"""
        self.set_multiple({
            "cleaning_prompt": cleaning,
            "summary_prompt": summary,
            "thanks_prompt": thanks,
            "devstatus_prompt": devstatus,
        })
    
    # === 분석 이력 관리 (예상 시간 계산용) ===
    
    MAX_HISTORY_COUNT = 10  # 스텝당 최대 이력 수
    
    def add_analysis_record(self, step: int, text_length: int, elapsed_seconds: float) -> None:
        """
        분석 이력 추가
        
        Args:
            step: 스텝 번호 (1~5)
            text_length: 처리한 텍스트 길이 (문자 수)
            elapsed_seconds: 소요 시간 (초)
        """
        history = self.get("analysis_history", DEFAULT_SETTINGS["analysis_history"])
        step_key = f"step_{step}"
        
        if step_key not in history:
            history[step_key] = []
        
        # 새 기록 추가
        history[step_key].append({
            "text_len": text_length,
            "seconds": elapsed_seconds
        })
        
        # 최대 개수 유지 (오래된 것부터 삭제)
        if len(history[step_key]) > self.MAX_HISTORY_COUNT:
            history[step_key] = history[step_key][-self.MAX_HISTORY_COUNT:]
        
        self.set("analysis_history", history)
        logger.debug(f"분석 이력 추가: step={step}, len={text_length}, time={elapsed_seconds:.1f}s")
    
    def get_analysis_history(self, step: int) -> list:
        """특정 스텝의 분석 이력 조회"""
        history = self.get("analysis_history", DEFAULT_SETTINGS["analysis_history"])
        step_key = f"step_{step}"
        return history.get(step_key, [])
    
    def estimate_step_time(self, step: int, text_length: int) -> Optional[float]:
        """
        스텝별 예상 소요 시간 계산
        
        Args:
            step: 스텝 번호 (1~5)
            text_length: 처리할 텍스트 길이 (문자 수)
            
        Returns:
            예상 소요 시간 (초), 이력이 없으면 None
        """
        records = self.get_analysis_history(step)
        
        if not records:
            return None
        
        # 평균 처리 속도 계산 (초당 문자 수)
        total_chars = sum(r["text_len"] for r in records)
        total_seconds = sum(r["seconds"] for r in records)
        
        if total_seconds <= 0 or total_chars <= 0:
            return None
        
        chars_per_second = total_chars / total_seconds
        
        # 예상 시간 계산
        estimated = text_length / chars_per_second
        
        return estimated
    
    def estimate_total_time(self, text_length: int) -> Dict[str, Optional[float]]:
        """
        전체 분석 예상 시간 계산
        
        Args:
            text_length: 입력 텍스트 길이
            
        Returns:
            {"step_1": float, ..., "step_5": float, "total": float}
        """
        result = {}
        total = 0.0
        has_estimate = False
        
        for step in range(1, 6):
            est = self.estimate_step_time(step, text_length)
            result[f"step_{step}"] = est
            if est is not None:
                total += est
                has_estimate = True
        
        result["total"] = total if has_estimate else None
        return result


# 전역 설정 인스턴스
_settings_instance: Optional[SettingsManager] = None


def get_settings() -> SettingsManager:
    """전역 설정 인스턴스 반환"""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = SettingsManager()
    return _settings_instance

