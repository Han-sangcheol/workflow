"""
통합 문서 파서
PDF와 DOCX 파일을 자동으로 구분하여 파싱합니다.
"""

import logging
from pathlib import Path
from typing import Optional

from .pdf_parser import PDFParser
from .docx_parser import DOCXParser

logger = logging.getLogger(__name__)


class DocumentParser:
    """통합 문서 파서 클래스"""

    def __init__(self):
        self.pdf_parser = PDFParser()
        self.docx_parser = DOCXParser()

    def parse_file(self, file_path: str) -> Optional[str]:
        """
        파일 확장자에 따라 적절한 파서로 텍스트 추출
        
        Args:
            file_path: 문서 파일 경로
            
        Returns:
            추출된 텍스트 (실패 시 None)
        """
        path = Path(file_path)
        extension = path.suffix.lower()

        if extension == ".pdf":
            return self.pdf_parser.parse_file(file_path)
        elif extension in [".docx", ".doc"]:
            return self.docx_parser.parse_file(file_path)
        else:
            logger.warning(
                f"지원하지 않는 파일 형식입니다: {extension}"
            )
            return None

    def is_supported_file(self, file_path: str) -> bool:
        """파일 형식 지원 여부 확인"""
        path = Path(file_path)
        return path.suffix.lower() in [".pdf", ".docx", ".doc"]

