"""
파일 선택기 테스트
"""

import pytest
from datetime import datetime
from src.utils.file_selector import FileSelector


def test_get_today_date_string():
    """오늘 날짜 문자열 생성 테스트"""
    selector = FileSelector()
    date_str = selector.get_today_date_string()
    
    # YYMMDD 형식인지 확인
    assert len(date_str) == 6
    assert date_str.isdigit()
    
    # 실제 오늘 날짜와 일치하는지 확인
    expected = datetime.now().strftime("%y%m%d")
    assert date_str == expected


def test_is_supported_file():
    """지원 파일 형식 확인 테스트"""
    selector = FileSelector()
    
    # 지원 형식
    assert selector.is_supported_file("test.pdf")
    assert selector.is_supported_file("test.docx")
    assert selector.is_supported_file("test.doc")
    assert selector.is_supported_file("TEST.PDF")  # 대소문자 무관
    
    # 미지원 형식
    assert not selector.is_supported_file("test.txt")
    assert not selector.is_supported_file("test.xlsx")


def test_validate_files_empty():
    """빈 파일 목록 검증 테스트"""
    selector = FileSelector()
    result = selector.validate_files([])
    assert result == []

