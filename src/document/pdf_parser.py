"""
PDF 파일 파싱 모듈
PyMuPDF를 사용하여 PDF 파일의 텍스트를 추출합니다.
세 가지 추출 모드 지원: simple, smart, layout
"""

import re
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

    # 지원하는 추출 모드
    EXTRACTION_MODES = ["simple", "smart", "layout"]

    @staticmethod
    def is_available() -> bool:
        """PyMuPDF 설치 여부 확인"""
        return fitz is not None

    def parse_file(
        self, 
        file_path: str, 
        extraction_mode: str = "smart"
    ) -> Optional[str]:
        """
        PDF 파일에서 텍스트 추출
        
        Args:
            file_path: PDF 파일 경로
            extraction_mode: 추출 모드 (simple, smart, layout)
                - simple: 기본 텍스트 추출
                - smart: 블록 기반 정렬 (표 형식에 최적)
                - layout: 레이아웃 보존 (복잡한 문서용)
            
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

            logger.info(
                f"PDF 파일 파싱 시작: {path.name} "
                f"(모드: {extraction_mode})"
            )
            
            doc = fitz.open(file_path)
            text_parts = []
            page_count = len(doc)
            
            for page_num in range(page_count):
                page = doc[page_num]
                
                # 모드별 텍스트 추출
                if extraction_mode == "smart":
                    text = self._extract_smart(page)
                elif extraction_mode == "layout":
                    text = self._extract_layout(page)
                else:  # simple
                    text = self._extract_simple(page)
                
                # 텍스트 정리
                cleaned_text = self._clean_text(text)
                
                if cleaned_text.strip():
                    text_parts.append(
                        f"--- 페이지 {page_num + 1} ---\n{cleaned_text}"
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

    def _extract_simple(self, page) -> str:
        """기본 텍스트 추출"""
        return page.get_text("text", sort=True)

    def _extract_smart(self, page) -> str:
        """
        스마트 추출 (블록 기반 정렬)
        표 형식 문서에 최적화
        """
        blocks = page.get_text("blocks", sort=True)
        text_lines = []
        
        for block in blocks:
            # block[4]가 텍스트 내용
            block_text = block[4].strip()
            if block_text:
                text_lines.append(block_text)
        
        return "\n".join(text_lines)

    def _extract_layout(self, page) -> str:
        """
        레이아웃 보존 추출
        복잡한 레이아웃의 문서용
        """
        text_dict = page.get_text("dict", sort=True)
        text_lines = []
        
        for block in text_dict.get("blocks", []):
            if block.get("type") == 0:  # 텍스트 블록
                for line in block.get("lines", []):
                    line_text = ""
                    for span in line.get("spans", []):
                        line_text += span.get("text", "")
                    if line_text.strip():
                        text_lines.append(line_text.strip())
        
        return "\n".join(text_lines)

    def _clean_text(self, text: str) -> str:
        """텍스트 정리 (불필요한 공백, 줄바꿈 제거)"""
        # 여러 공백을 하나로
        text = re.sub(r' +', ' ', text)
        # 3개 이상 연속 줄바꿈을 2개로
        text = re.sub(r'\n{3,}', '\n\n', text)
        # 각 줄 앞뒤 공백 제거
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        return text

