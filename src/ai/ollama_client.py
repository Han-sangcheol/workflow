"""
Ollama AI 클라이언트
로컬 Ollama API를 통해 텍스트 분석 및 생성을 수행합니다.
"""

import re
import json
import logging
from typing import Optional, Callable, List, Tuple

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
        추출된 텍스트를 정리 및 구조화 (팀원별 개별 처리)
        
        Args:
            documents_text: 원본 텍스트
            progress_callback: 진행 상황 콜백 함수
            
        Returns:
            정리된 텍스트 (실패 시 None)
        """
        # 파일 구분자로 팀원별 텍스트 분리
        member_sections = self._parse_by_file_separator(documents_text)
        
        if not member_sections:
            # 파일 구분자가 없으면 전체를 한 번에 처리 (기존 방식)
            logger.info("파일 구분자 없음, 전체 텍스트를 한 번에 처리")
            prompt = self._create_cleaning_prompt(documents_text)
            return self._generate(prompt, progress_callback)
        
        logger.info(f"팀원별 개별 처리: {len(member_sections)}명 발견")
        
        # 팀원 목록 추출
        member_names = [name for name, _ in member_sections]
        
        # 결과 저장
        all_results = []
        all_results.append(f"########## 팀원 목록 ##########")
        all_results.append(", ".join(member_names))
        all_results.append("")
        
        # 각 팀원별로 개별 AI 호출
        for idx, (member_name, member_text) in enumerate(member_sections):
            if progress_callback:
                progress_callback(f"\n\n--- {member_name} 정리 중 ({idx+1}/{len(member_sections)}) ---\n\n")
            
            # 단일 팀원용 프롬프트 생성
            prompt = self._create_single_member_cleaning_prompt(member_name, member_text)
            
            # AI 호출
            result = self._generate(prompt, progress_callback)
            
            if result:
                all_results.append(result.strip())
                all_results.append("")
            else:
                logger.warning(f"{member_name} 정리 실패")
                all_results.append(f"########## {member_name} ##########")
                all_results.append("(정리 실패)")
                all_results.append("")
        
        return "\n".join(all_results) if all_results else None
    
    def _parse_by_file_separator(self, text: str) -> List[Tuple[str, str]]:
        """
        파일 구분자로 텍스트를 팀원별로 분리
        
        Args:
            text: 전체 원본 텍스트
            
        Returns:
            [(팀원명, 해당 팀원의 텍스트), ...] 리스트
        """
        # 파일 구분자 패턴 (다양한 형식 지원):
        # - FW팀 김상일 일일업무일지 (공백 구분)
        # - FW팀_전상민_일일업무일지 (언더스코어 구분)
        # - FW팀 김종민 일일업무 일지 (일일업무 일지 중간 공백)
        pattern = r'===\s*파일:\s*.*?FW팀[\s_]+([^\s_]+)[\s_]+일일업무[\s_]*일지.*?==='
        
        # 모든 구분자 위치와 이름 찾기
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        
        if not matches:
            logger.warning("파일 구분자를 찾을 수 없습니다. 대체 패턴 시도...")
            # 대체 패턴: === 파일: ... === 구분자만 찾기
            alt_pattern = r'(===\s*파일:\s*[^=]+===)'
            alt_matches = list(re.finditer(alt_pattern, text))
            
            if alt_matches:
                results = []
                for i, match in enumerate(alt_matches):
                    # 파일명에서 이름 추출 시도
                    file_header = match.group(1)
                    name_match = re.search(r'FW팀[\s_]*([가-힣]+)', file_header)
                    
                    if name_match:
                        member_name = name_match.group(1)
                    else:
                        member_name = f"팀원{i+1}"
                    
                    start_pos = match.end()
                    if i + 1 < len(alt_matches):
                        end_pos = alt_matches[i + 1].start()
                    else:
                        end_pos = len(text)
                    
                    member_text = text[start_pos:end_pos].strip()
                    results.append((member_name, member_text))
                
                logger.info(f"대체 패턴으로 {len(results)}명 발견")
                return results
            
            return []
        
        logger.info(f"파일 구분자로 {len(matches)}명 발견")
        
        results = []
        for i, match in enumerate(matches):
            member_name = match.group(1)
            start_pos = match.end()
            
            # 다음 구분자까지 또는 끝까지
            if i + 1 < len(matches):
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(text)
            
            member_text = text[start_pos:end_pos].strip()
            results.append((member_name, member_text))
            logger.debug(f"팀원 발견: {member_name} ({len(member_text)}자)")
        
        return results
    
    def _create_single_member_cleaning_prompt(self, member_name: str, member_text: str) -> str:
        """단일 팀원용 텍스트 정리 프롬프트"""
        return f"""다음은 {member_name}의 일일 업무일지 원본 텍스트입니다.
PDF에서 추출되어 구조가 깨져있으므로 읽기 쉽게 정리해주세요.

[핵심 규칙]
1. 원본 내용 100% 유지 (삭제/요약 금지)
2. 줄맞춤, 띄어쓰기, 문단 구분만 정돈
3. 금일업무와 익일업무를 구분하여 표시

[출력 형식]
########## {member_name} (날짜) ##########

【금일업무】
• 프로젝트: [프로젝트명]
  - 목적: [내용]
  - Action: [내용]
  - 진행률: [계획]% / [달성]%

【익일업무】
• 프로젝트: [프로젝트명]
  - [내용]

[원본 텍스트]
{member_text}
"""

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

