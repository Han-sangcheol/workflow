"""
설정 관리 모듈
애플리케이션 설정을 JSON 파일로 저장/로드합니다.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# 기본 설정값
DEFAULT_SETTINGS = {
    "cleaning_model": "llama3.2:latest",
    "writing_model": "llama3.2:latest",
    "pdf_extraction_mode": 0,  # 0: smart, 1: layout, 2: simple
    "auto_search_today": True,
    "last_folder_path": "",
    "last_save_path": "",
    "window_width": 1100,
    "window_height": 750,
    "window_x": None,
    "window_y": None,
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
        """설정 파일 경로 반환 (프로젝트 폴더 내)"""
        # 프로젝트 루트 폴더에 설정 파일 저장
        project_root = Path(__file__).parent.parent.parent
        settings_file = project_root / self.SETTINGS_FILE
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
        """작성용 AI 모델"""
        return self.get("writing_model", DEFAULT_SETTINGS["writing_model"])
    
    @writing_model.setter
    def writing_model(self, value: str) -> None:
        self.set("writing_model", value)
    
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


# 전역 설정 인스턴스
_settings_instance: Optional[SettingsManager] = None


def get_settings() -> SettingsManager:
    """전역 설정 인스턴스 반환"""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = SettingsManager()
    return _settings_instance

