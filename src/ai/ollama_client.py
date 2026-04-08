"""
AI 클라이언트 (다중 제공자 지원)
Ollama, LM Studio, Jan 등 다양한 로컬 AI 서버를 지원합니다.
- Ollama: /api/generate (네이티브 Ollama API, 스트리밍)
- LM Studio: /v1/chat/completions (OpenAI 호환 API, SSE 스트리밍, 기본포트 1234)
- Jan: /v1/chat/completions (OpenAI 호환 API, SSE 스트리밍, 기본포트 1337)
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

# 제공자별 API 정보
PROVIDER_CONFIG = {
    "ollama": {
        "api_type": "ollama",
        "models_endpoint": "/api/tags",
        "generate_endpoint": "/api/generate",
    },
    "lm_studio": {
        "api_type": "openai",
        "models_endpoint": "/v1/models",
        "generate_endpoint": "/v1/chat/completions",
    },
    "jan": {
        "api_type": "openai",
        "models_endpoint": "/v1/models",
        "generate_endpoint": "/v1/chat/completions",
    },
}


class OllamaClient:
    """다중 AI 제공자 클라이언트 (Ollama, LM Studio, Jan 지원)"""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.2",
        timeout: int = 120,
        provider: str = "ollama",
        api_key: str = ""
    ):
        """
        초기화
        
        Args:
            base_url: AI 서버 기본 URL (포트 포함)
            model: 사용할 모델 이름
            timeout: 요청 타임아웃 (초)
            provider: AI 제공자 ("ollama", "lm_studio", "jan")
            api_key: API 키 (Jan 등 필요한 경우)
        """
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.provider = provider
        self.api_key = api_key
        self.config = PROVIDER_CONFIG.get(provider, PROVIDER_CONFIG["ollama"])
        
        # 취소 관련 속성
        self._is_cancelled = False
        self._current_response = None  # 현재 진행 중인 HTTP 응답 (취소 시 종료용)
    
    def cancel(self):
        """
        진행 중인 AI 생성을 즉시 취소합니다.
        HTTP 스트리밍 연결을 강제로 종료합니다.
        """
        self._is_cancelled = True
        logger.info(f"AI 생성 취소 요청됨 (제공자: {self.provider})")
        
        # 진행 중인 HTTP 연결 강제 종료
        if self._current_response is not None:
            try:
                self._current_response.close()
                logger.info("HTTP 스트리밍 연결 강제 종료됨")
            except Exception as e:
                logger.warning(f"HTTP 연결 종료 중 오류: {e}")
            finally:
                self._current_response = None
    
    def reset(self):
        """취소 플래그 리셋 (새 작업 시작 전 호출)"""
        self._is_cancelled = False
        self._current_response = None

    @staticmethod
    def get_available_models(
        base_url: str = "http://localhost:11434",
        provider: str = "ollama",
        api_key: str = ""
    ) -> list:
        """
        설치된 모델 목록 가져오기
        
        Args:
            base_url: AI 서버 기본 URL
            provider: AI 제공자 ("ollama", "lm_studio", "jan")
            api_key: API 키 (LM Studio, Jan 등 필요한 경우)
            
        Returns:
            모델 이름 리스트
        """
        if requests is None:
            logger.error("requests 라이브러리가 설치되지 않았습니다")
            return []

        config = PROVIDER_CONFIG.get(provider, PROVIDER_CONFIG["ollama"])
        endpoint = config["models_endpoint"]
        
        headers = {}
        if api_key and config["api_type"] == "openai":
            headers["Authorization"] = f"Bearer {api_key}"
        
        # LM Studio JIT 모델 로딩 시 시간이 더 필요할 수 있음
        timeout = 10 if config["api_type"] == "openai" else 5
        url = f"{base_url}{endpoint}"
        
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            
            if response.status_code == 200:
                data = response.json()
                
                if config["api_type"] == "ollama":
                    models = [
                        model.get("name", "")
                        for model in data.get("models", [])
                    ]
                else:
                    # OpenAI 호환 (LM Studio, Jan): {"data": [{"id": "..."}]}
                    models = [
                        model.get("id", "")
                        for model in data.get("data", [])
                    ]
                
                logger.info(f"모델 목록 조회 성공 ({provider}): {len(models)}개")
                return sorted([m for m in models if m])
            else:
                body = ""
                try:
                    body = response.text[:200]
                except Exception:
                    pass
                logger.warning(
                    f"모델 목록 조회 실패 ({provider}): "
                    f"HTTP {response.status_code} - {body}"
                )
                return []
                
        except requests.ConnectionError:
            logger.warning(
                f"{provider} 서버에 연결할 수 없습니다 ({url}). "
                f"서버가 실행 중인지 확인하세요."
            )
            return []
        except requests.Timeout:
            logger.warning(
                f"{provider} 서버 응답 시간 초과 ({url}). "
                f"모델 로딩 중일 수 있습니다."
            )
            return []
        except Exception as e:
            logger.warning(f"모델 목록 조회 실패 ({provider}): {str(e)}")
            return []

    def is_available(self) -> bool:
        """AI 서버 연결 가능 여부 확인"""
        if requests is None:
            logger.error("requests 라이브러리가 설치되지 않았습니다")
            return False

        endpoint = self.config["models_endpoint"]
        
        headers = {}
        if self.api_key and self.config["api_type"] == "openai":
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        timeout = 10 if self.config["api_type"] == "openai" else 5
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            if response.status_code == 200:
                return True
            logger.warning(
                f"{self.provider} 서버 응답 오류: HTTP {response.status_code}"
            )
            return False
        except requests.ConnectionError:
            logger.warning(
                f"{self.provider} 서버에 연결할 수 없습니다 ({url}). "
                f"서버가 실행 중인지 확인하세요."
            )
            return False
        except requests.Timeout:
            logger.warning(
                f"{self.provider} 서버 응답 시간 초과 ({url})"
            )
            return False
        except Exception as e:
            logger.warning(f"AI 서버 연결 실패 ({self.provider}): {str(e)}")
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
        AI API로 텍스트 생성 (제공자에 따라 다른 API 형식 사용)
        
        Args:
            prompt: 프롬프트
            progress_callback: 진행 상황 콜백
            
        Returns:
            생성된 텍스트 (실패 시 None)
        """
        if not self.is_available():
            logger.error(f"AI 서버에 연결할 수 없습니다 ({self.provider})")
            return None

        try:
            logger.info(f"AI 생성 시작 (제공자: {self.provider}, 모델: {self.model})")
            
            if self.config["api_type"] == "ollama":
                return self._generate_ollama(prompt, progress_callback)
            else:
                return self._generate_openai(prompt, progress_callback)

        except requests.Timeout:
            logger.error("요청 타임아웃: AI 응답 시간 초과")
            return None
        except Exception as e:
            logger.error(f"AI 생성 오류: {str(e)}")
            return None
    
    def _generate_ollama(
        self,
        prompt: str,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Optional[str]:
        """Ollama API로 텍스트 생성"""
        # 시작 전 취소 플래그 리셋
        self._is_cancelled = False
        
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "system": SYSTEM_PROMPT,
                "stream": True,
                "options": {
                    "temperature": 0.3
                }
            },
            stream=True,
            timeout=self.timeout
        )
        
        response.raise_for_status()
        
        # 현재 응답 저장 (취소 시 강제 종료용)
        self._current_response = response
        
        full_text = ""
        try:
            for line in response.iter_lines():
                # 취소 체크 - 즉시 중단
                if self._is_cancelled:
                    logger.info("AI 생성 취소됨 (Ollama)")
                    break
                
                if line:
                    data = json.loads(line)
                    chunk = data.get("response", "")
                    full_text += chunk
                    
                    if progress_callback:
                        progress_callback(chunk)
                    
                    if data.get("done", False):
                        break
        except Exception as e:
            if self._is_cancelled:
                logger.info(f"취소로 인한 연결 종료: {e}")
            else:
                raise
        finally:
            self._current_response = None
        
        # 취소된 경우 부분 결과 반환하지 않음
        if self._is_cancelled:
            return None
        
        logger.info(f"AI 생성 완료: {len(full_text)} 문자")
        return full_text if full_text.strip() else None
    
    def _generate_openai(
        self,
        prompt: str,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Optional[str]:
        """OpenAI 호환 API로 텍스트 생성 (LM Studio, Jan)
        Qwen 등 reasoning 모델의 reasoning_content 도 처리합니다.
        """
        self._is_cancelled = False
        
        endpoint = self.config["generate_endpoint"]
        url = f"{self.base_url}{endpoint}"
        
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        request_body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": -1,
            "stream": True
        }
        
        logger.info(
            f"OpenAI 호환 API 요청: {url}, 모델={self.model}, "
            f"제공자={self.provider}"
        )
        
        response = requests.post(
            url,
            headers=headers,
            json=request_body,
            stream=True,
            timeout=self.timeout
        )
        
        if response.status_code != 200:
            error_body = ""
            try:
                error_body = response.text[:500]
            except Exception:
                pass
            logger.error(
                f"{self.provider} API 오류: HTTP {response.status_code} - "
                f"{error_body}"
            )
            response.raise_for_status()
        
        self._current_response = response
        
        full_text = ""
        reasoning_text = ""
        in_reasoning = False
        reasoning_notified = False
        
        try:
            for line in response.iter_lines():
                if self._is_cancelled:
                    logger.info(f"AI 생성 취소됨 ({self.provider})")
                    break
                
                if not line:
                    continue
                
                line_str = line.decode('utf-8') if isinstance(line, bytes) else line
                line_str = line_str.strip()
                
                if not line_str.startswith("data:"):
                    continue
                
                data_str = line_str[5:].strip()
                
                if data_str == "[DONE]":
                    break
                
                if not data_str:
                    continue
                
                try:
                    data = json.loads(data_str)
                    choices = data.get("choices", [])
                    if not choices:
                        continue
                    
                    delta = choices[0].get("delta", {})
                    finish = choices[0].get("finish_reason")
                    
                    # Qwen 등 reasoning 모델: reasoning_content 처리
                    reasoning_chunk = delta.get("reasoning_content", "")
                    if reasoning_chunk:
                        if not in_reasoning:
                            in_reasoning = True
                            if progress_callback and not reasoning_notified:
                                progress_callback("\n⏳ AI 사고 중...\n")
                                reasoning_notified = True
                        reasoning_text += reasoning_chunk
                        if progress_callback:
                            progress_callback(reasoning_chunk)
                    
                    # 실제 응답 content 처리
                    content_chunk = delta.get("content", "")
                    if content_chunk:
                        if in_reasoning:
                            in_reasoning = False
                            if progress_callback:
                                progress_callback("\n\n📝 응답 생성 중...\n")
                        full_text += content_chunk
                        if progress_callback:
                            progress_callback(content_chunk)
                    
                    if finish in ("stop", "length"):
                        if finish == "length":
                            logger.warning(
                                f"토큰 제한 도달 (reasoning={len(reasoning_text)}자, "
                                f"content={len(full_text)}자)"
                            )
                        break
                        
                except json.JSONDecodeError as je:
                    logger.debug(f"JSON 파싱 스킵: {data_str[:100]} - {je}")
                    continue
        except Exception as e:
            if self._is_cancelled:
                logger.info(f"취소로 인한 연결 종료 ({self.provider}): {e}")
            else:
                raise
        finally:
            self._current_response = None
        
        if self._is_cancelled:
            return None
        
        # reasoning만 있고 content가 없는 경우 reasoning을 결과로 사용
        result = full_text if full_text.strip() else reasoning_text
        
        logger.info(
            f"AI 생성 완료 ({self.provider}): "
            f"content={len(full_text)}자, reasoning={len(reasoning_text)}자"
        )
        return result if result.strip() else None

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
            # 취소 체크 - 다음 팀원 처리 전 확인
            if self._is_cancelled:
                logger.info(f"팀원별 정리 중 취소됨 ({idx}/{len(member_sections)})")
                return None
            
            if progress_callback:
                progress_callback(f"\n\n--- {member_name} 정리 중 ({idx+1}/{len(member_sections)}) ---\n\n")
            
            # 단일 팀원용 프롬프트 생성
            prompt = self._create_single_member_cleaning_prompt(member_name, member_text)
            
            # AI 호출
            result = self._generate(prompt, progress_callback)
            
            # 취소로 인한 실패 체크
            if self._is_cancelled:
                logger.info("AI 호출 중 취소됨")
                return None
            
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
        # - FW팀 홍길동 일일업무일지 (공백 구분)
        # - FW팀_홍길동_일일업무일지 (언더스코어 구분)
        # - FW팀 홍길동 일일업무 일지 (일일업무 일지 중간 공백)
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

