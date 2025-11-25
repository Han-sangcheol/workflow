"""
파일 선택 유틸리티
수동 선택과 날짜 기반 자동 선택을 지원합니다.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional

logger = logging.getLogger(__name__)


class FileSelector:
    """파일 선택 로직 클래스"""

    SUPPORTED_EXTENSIONS = [".pdf", ".docx", ".doc"]

    @staticmethod
    def get_today_date_string() -> str:
        """오늘 날짜를 YYMMDD 형식으로 반환"""
        return datetime.now().strftime("%y%m%d")

    def find_files_by_date(
        self,
        directory: str,
        date_string: Optional[str] = None
    ) -> List[str]:
        """
        특정 날짜가 포함된 파일 검색
        
        Args:
            directory: 검색할 디렉토리 경로
            date_string: 검색할 날짜 (YYMMDD, None이면 오늘)
            
        Returns:
            찾은 파일 경로 리스트
        """
        if date_string is None:
            date_string = self.get_today_date_string()

        try:
            dir_path = Path(directory)
            if not dir_path.exists() or not dir_path.is_dir():
                logger.error(f"유효하지 않은 디렉토리: {directory}")
                return []

            found_files = []
            
            for file_path in dir_path.rglob("*"):
                if not file_path.is_file():
                    continue
                
                # 확장자 확인
                if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
                    continue
                
                # 파일명에 날짜 포함 여부 확인
                if date_string in file_path.name:
                    found_files.append(str(file_path))
                    logger.info(f"날짜로 파일 발견: {file_path.name}")

            logger.info(
                f"날짜 '{date_string}'로 {len(found_files)}개 파일 발견"
            )
            return sorted(found_files)

        except Exception as e:
            logger.error(f"파일 검색 오류: {str(e)}")
            return []

    def validate_files(self, file_paths: List[str]) -> List[str]:
        """
        파일 목록 유효성 검사
        
        Args:
            file_paths: 검사할 파일 경로 리스트
            
        Returns:
            유효한 파일 경로 리스트
        """
        valid_files = []
        
        for file_path in file_paths:
            path = Path(file_path)
            
            if not path.exists():
                logger.warning(f"파일이 존재하지 않음: {file_path}")
                continue
            
            if not path.is_file():
                logger.warning(f"파일이 아님: {file_path}")
                continue
            
            if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
                logger.warning(
                    f"지원하지 않는 형식: {path.suffix}"
                )
                continue
            
            valid_files.append(file_path)
        
        return valid_files

    def is_supported_file(self, file_path: str) -> bool:
        """파일 형식 지원 여부 확인"""
        path = Path(file_path)
        return path.suffix.lower() in self.SUPPORTED_EXTENSIONS

