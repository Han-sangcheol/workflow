"""
출력 생성기 테스트
"""

import pytest
from datetime import datetime
from src.utils.output_generator import OutputGenerator


def test_generator_initialization():
    """생성기 초기화 테스트"""
    generator = OutputGenerator()
    assert generator is not None


def test_is_available():
    """python-docx 사용 가능 여부 테스트"""
    generator = OutputGenerator()
    is_available = generator.is_available()
    assert isinstance(is_available, bool)


def test_generate_default_filename():
    """기본 파일명 생성 테스트"""
    filename = OutputGenerator.generate_default_filename("회의록")
    
    # 파일명 형식 확인
    assert filename.startswith("회의록_")
    assert filename.endswith(".docx")
    
    # 날짜 부분 확인 (YYMMDD)
    date_part = filename.split("_")[1].replace(".docx", "")
    assert len(date_part) == 6
    assert date_part.isdigit()
    
    # 오늘 날짜와 일치 확인
    today = datetime.now().strftime("%y%m%d")
    assert date_part == today


def test_generate_default_filename_different_prefix():
    """다른 접두사로 파일명 생성 테스트"""
    filename = OutputGenerator.generate_default_filename("감사인사")
    
    assert filename.startswith("감사인사_")
    assert filename.endswith(".docx")

