"""
문서 파서 테스트
"""

import pytest
from src.document.document_parser import DocumentParser
from src.document.pdf_parser import PDFParser
from src.document.docx_parser import DOCXParser


def test_parser_initialization():
    """파서 초기화 테스트"""
    parser = DocumentParser()
    assert parser.pdf_parser is not None
    assert parser.docx_parser is not None


def test_is_supported_file():
    """지원 파일 형식 확인 테스트"""
    parser = DocumentParser()
    
    # 지원 형식
    assert parser.is_supported_file("document.pdf")
    assert parser.is_supported_file("document.docx")
    assert parser.is_supported_file("document.doc")
    
    # 미지원 형식
    assert not parser.is_supported_file("document.txt")
    assert not parser.is_supported_file("document.xlsx")


def test_pdf_parser_availability():
    """PDF 파서 사용 가능 여부 테스트"""
    parser = PDFParser()
    # PyMuPDF 설치 여부에 따라 결과가 달라짐
    is_available = parser.is_available()
    assert isinstance(is_available, bool)


def test_docx_parser_availability():
    """DOCX 파서 사용 가능 여부 테스트"""
    parser = DOCXParser()
    # python-docx 설치 여부에 따라 결과가 달라짐
    is_available = parser.is_available()
    assert isinstance(is_available, bool)

