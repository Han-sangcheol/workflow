"""
Ollama AI 클라이언트
로컬 Ollama API를 통해 텍스트 분석 및 생성을 수행합니다.
"""

import json
import logging
from typing import Optional, Callable

try:
    import requests
except ImportError:
    requests = None

from .prompt_config import SYSTEM_PROMPT, get_prompt

logger = logging.getLogger(__name__)


class OllamaClient:
    """Ollama API 클라이언트"""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.2",
        timeout: int = 120
    ):
        """
        초기화
        
        Args:
            base_url: Ollama API 기본 URL
            model: 사용할 모델 이름
            timeout: 요청 타임아웃 (초)
        """
        self.base_url = base_url
        self.model = model
        self.timeout = timeout

    @staticmethod
    def get_available_models(
        base_url: str = "http://localhost:11434"
    ) -> list:
        """
        설치된 모델 목록 가져오기
        
        Args:
            base_url: Ollama API 기본 URL
            
        Returns:
            모델 이름 리스트
        """
        if requests is None:
            logger.error("requests 라이브러리가 설치되지 않았습니다")
            return []

        try:
            response = requests.get(
                f"{base_url}/api/tags",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                models = [
                    model.get("name", "")
                    for model in data.get("models", [])
                ]
                return sorted(models)
            else:
                logger.warning("모델 목록을 가져올 수 없습니다")
                return []
                
        except Exception as e:
            logger.warning(f"모델 목록 조회 실패: {str(e)}")
            return []

    def is_available(self) -> bool:
        """Ollama 서버 연결 가능 여부 확인"""
        if requests is None:
            logger.error("requests 라이브러리가 설치되지 않았습니다")
            return False

        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama 서버 연결 실패: {str(e)}")
            return False

    def generate_summary(
        self,
        documents_text: str,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Optional[str]:
        """
        업무일지를 통합 회의록으로 요약
        
        Args:
            documents_text: 팀원들의 업무일지 텍스트
            progress_callback: 진행 상황 콜백 함수
            
        Returns:
            생성된 회의록 (실패 시 None)
        """
        prompt = self._create_summary_prompt(documents_text)
        return self._generate(prompt, progress_callback)

    def generate_thanks(
        self,
        documents_text: str,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Optional[str]:
        """
        팀원들에게 감사 인사 생성
        
        Args:
            documents_text: 팀원들의 업무일지 텍스트
            progress_callback: 진행 상황 콜백 함수
            
        Returns:
            생성된 감사 인사 (실패 시 None)
        """
        prompt = self._create_thanks_prompt(documents_text)
        return self._generate(prompt, progress_callback)

    def generate_devstatus(
        self,
        documents_text: str,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Optional[str]:
        """
        오전/오후 개발 현황 생성
        
        Args:
            documents_text: 팀원들의 업무일지 텍스트
            progress_callback: 진행 상황 콜백 함수
            
        Returns:
            생성된 개발 현황 (실패 시 None)
        """
        prompt = self._create_devstatus_prompt(documents_text)
        return self._generate(prompt, progress_callback)

    def generate_period_analysis(
        self,
        tasks_text: str,
        period_info: str,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Optional[str]:
        """
        기간별 성과 분석 생성
        
        Args:
            tasks_text: 기간 내 업무 목록 텍스트
            period_info: 기간 정보 (예: "2025.11.01 ~ 2025.11.25")
            progress_callback: 진행 상황 콜백 함수
            
        Returns:
            생성된 성과 분석 보고서 (실패 시 None)
        """
        prompt = self._create_period_analysis_prompt(tasks_text, period_info)
        return self._generate(prompt, progress_callback)

    def _generate(
        self,
        prompt: str,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Optional[str]:
        """
        Ollama API로 텍스트 생성
        
        Args:
            prompt: 프롬프트
            progress_callback: 진행 상황 콜백
            
        Returns:
            생성된 텍스트 (실패 시 None)
        """
        if not self.is_available():
            logger.error("Ollama 서버에 연결할 수 없습니다")
            return None

        try:
            logger.info(f"AI 생성 시작 (모델: {self.model})")
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "system": SYSTEM_PROMPT,
                    "stream": True,
                    "options": {
                        "temperature": 0.3  # 일관된 출력을 위해 낮은 온도 설정
                    }
                },
                stream=True,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            full_text = ""
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    chunk = data.get("response", "")
                    full_text += chunk
                    
                    if progress_callback:
                        progress_callback(chunk)
                    
                    if data.get("done", False):
                        break
            
            logger.info(f"AI 생성 완료: {len(full_text)} 문자")
            return full_text if full_text.strip() else None

        except requests.Timeout:
            logger.error("요청 타임아웃: AI 응답 시간 초과")
            return None
        except Exception as e:
            logger.error(f"AI 생성 오류: {str(e)}")
            return None

    def clean_and_organize(
        self,
        documents_text: str,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Optional[str]:
        """
        추출된 텍스트를 정리 및 구조화
        
        Args:
            documents_text: 원본 텍스트
            progress_callback: 진행 상황 콜백 함수
            
        Returns:
            정리된 텍스트 (실패 시 None)
        """
        prompt = self._create_cleaning_prompt(documents_text)
        return self._generate(prompt, progress_callback)

    def _create_cleaning_prompt(self, documents_text: str) -> str:
        """텍스트 정리 프롬프트 (사용자 설정 또는 기본값)"""
        prompt_template = get_prompt("cleaning")
        return prompt_template.format(documents_text=documents_text)

    def _create_summary_prompt(self, documents_text: str) -> str:
        """통합 회의록 생성 프롬프트 (사용자 설정 또는 기본값)"""
        prompt_template = get_prompt("summary")
        return prompt_template.format(cleaned_text=documents_text)

    def _create_thanks_prompt(self, documents_text: str) -> str:
        """감사 인사 생성 프롬프트 (사용자 설정 또는 기본값)"""
        prompt_template = get_prompt("thanks")
        return prompt_template.format(cleaned_text=documents_text)

    def _create_devstatus_prompt(self, documents_text: str) -> str:
        """개발 현황 생성 프롬프트 (사용자 설정 또는 기본값)"""
        prompt_template = get_prompt("devstatus")
        return prompt_template.format(cleaned_text=documents_text)

    def _create_period_analysis_prompt(self, tasks_text: str, period_info: str) -> str:
        """기간별 성과 분석 프롬프트 (사용자 설정 또는 기본값)"""
        prompt_template = get_prompt("period_analysis")
        return prompt_template.format(tasks_text=tasks_text, period_info=period_info)

    def generate_project_recommendation(
        self,
        project_data: str,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Optional[str]:
        """
        프로젝트 분석 및 할 일 추천
        
        Args:
            project_data: 프로젝트 현황 텍스트
            progress_callback: 진행 상황 콜백 함수
            
        Returns:
            생성된 추천 보고서 (실패 시 None)
        """
        prompt = self._create_project_recommend_prompt(project_data)
        return self._generate(prompt, progress_callback)

    def _create_project_recommend_prompt(self, project_data: str) -> str:
        """프로젝트 추천 프롬프트 (사용자 설정 또는 기본값)"""
        prompt_template = get_prompt("project_recommend")
        return prompt_template.format(project_data=project_data)

