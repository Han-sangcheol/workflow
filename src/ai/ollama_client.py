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
                    "stream": True
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
        """텍스트 정리 프롬프트"""
        return f"""다음은 PDF/DOCX 파일에서 추출한 원본 텍스트입니다.
이 텍스트를 읽기 쉽게 정리하고 구조화해주세요.

요구사항:
1. 불필요한 공백, 줄바꿈, 특수문자 제거
2. 날짜, 작성자, 주요 내용을 명확히 구분
3. 각 팀원별로 내용 분리
4. 업무 항목을 구조화 (진행 업무, 완료 업무, 이슈 등)
5. 원본 내용은 유지하되 가독성 향상
6. 한국어로 작성

원본 텍스트:
{documents_text}

정리된 텍스트:"""

    def _create_summary_prompt(self, documents_text: str) -> str:
        """통합 회의록 생성 프롬프트"""
        return f"""다음은 정리된 팀원들의 일일 업무일지입니다. 
이 내용을 바탕으로 팀 전체의 통합 회의록을 작성해주세요.

요구사항:
1. 각 팀원의 주요 업무 내용을 간결하게 정리
2. 팀 전체의 진행 상황과 성과를 요약
3. 주요 이슈나 특이사항이 있다면 언급
4. 전문적이고 간결한 톤 유지
5. 한국어로 작성

업무일지:
{documents_text}

통합 회의록:"""

    def _create_thanks_prompt(self, documents_text: str) -> str:
        """감사 인사 생성 프롬프트"""
        return f"""다음은 팀원들의 일일 업무일지입니다.
각 팀원의 업무 내용을 바탕으로 개인별 감사 인사를 작성해주세요.

요구사항:
1. 각 팀원의 구체적인 업무 내용을 언급
2. 진심 어린 감사의 마음을 전달
3. 각 팀원당 2-3문장 정도
4. 따뜻하고 격려하는 톤 유지
5. 한국어로 작성

업무일지:
{documents_text}

감사 인사:"""

