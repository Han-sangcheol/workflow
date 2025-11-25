"""
PDF 파일 파싱 모듈
PyMuPDF를 사용하여 PDF 파일의 텍스트를 추출합니다.
"""

import logging
from pathlib import Path
from typing import Optional

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

logger = logging.getLogger(__name__)


class PDFParser:
    """PDF 문서 텍스트 추출 클래스"""

    @staticmethod
    def is_available() -> bool:
        """PyMuPDF 설치 여부 확인"""
        return fitz is not None

    def parse_file(self, file_path: str) -> Optional[str]:
        """
        PDF 파일에서 텍스트 추출
        
        Args:
            file_path: PDF 파일 경로
            
        Returns:
            추출된 텍스트 (실패 시 None)
        """
        if not self.is_available():
            logger.error("PyMuPDF가 설치되지 않았습니다")
            return None

        try:
            path = Path(file_path)
            if not path.exists():
                logger.error(f"파일을 찾을 수 없습니다: {file_path}")
                return None

            logger.info(f"PDF 파일 파싱 시작: {path.name}")
            
            doc = fitz.open(file_path)
            text_parts = []
            page_count = len(doc)
            
            for page_num in range(page_count):
                page = doc[page_num]
                text = page.get_text()
                
                if text.strip():
                    text_parts.append(
                        f"--- 페이지 {page_num + 1} ---\n{text}"
                    )
            
            doc.close()
            
            result = "\n\n".join(text_parts)
            logger.info(
                f"PDF 파싱 완료: {page_count} 페이지, "
                f"{len(result)} 문자"
            )
            
            return result if result.strip() else None

        except Exception as e:
            logger.error(f"PDF 파싱 오류: {str(e)}")
            return None

