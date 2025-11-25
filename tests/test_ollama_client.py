"""
Ollama 클라이언트 테스트
"""

import pytest
from src.ai.ollama_client import OllamaClient


def test_client_initialization():
    """클라이언트 초기화 테스트"""
    client = OllamaClient()
    assert client.base_url == "http://localhost:11434"
    assert client.model == "llama3.2"
    assert client.timeout == 120


def test_client_custom_initialization():
    """커스텀 설정으로 초기화 테스트"""
    client = OllamaClient(
        base_url="http://custom:8080",
        model="custom-model",
        timeout=60
    )
    assert client.base_url == "http://custom:8080"
    assert client.model == "custom-model"
    assert client.timeout == 60


def test_is_available():
    """서버 연결 가능 여부 테스트"""
    client = OllamaClient()
    # 실제 Ollama 서버 실행 여부에 따라 결과가 달라짐
    is_available = client.is_available()
    assert isinstance(is_available, bool)


def test_prompt_creation():
    """프롬프트 생성 테스트"""
    client = OllamaClient()
    
    # 테스트용 문서 텍스트
    test_text = "팀원 A: 프로젝트 완료\n팀원 B: 리뷰 진행"
    
    # 프라이빗 메서드 테스트
    summary_prompt = client._create_summary_prompt(test_text)
    assert "통합 회의록" in summary_prompt
    assert test_text in summary_prompt
    
    thanks_prompt = client._create_thanks_prompt(test_text)
    assert "감사" in thanks_prompt
    assert test_text in thanks_prompt

