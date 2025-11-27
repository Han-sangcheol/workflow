"""
PDF 파일 파싱 모듈
PyMuPDF를 사용하여 PDF 파일의 텍스트를 추출합니다.
세 가지 추출 모드 지원: simple, smart, layout
업무일지 표 형식 데이터 1차 정리 기능 포함
"""

import re
import logging
from pathlib import Path
from typing import Optional, List, Tuple

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

logger = logging.getLogger(__name__)


# 업무일지에서 제거할 노이즈 패턴들
NOISE_PATTERNS = [
    r'^결\s*$',           # 결재란 "결"
    r'^재\s*$',           # 결재란 "재"
    r'^작\s*성\s*$',      # 작성
    r'^검\s*토\s*$',      # 검토
    r'^승\s*인\s*$',      # 승인
    r'^작성\s*$',
    r'^검토\s*$', 
    r'^승인\s*$',
    r'^\d+\s*$',          # 단독 숫자 (페이지 번호 등)
    r'^[\d\s]+%?\s*$',    # 숫자만 있는 줄 (진행률 단독)
    r'^Unit\s*$',         # 단독 Unit
    r'^Chair\s*$',        # 단독 Chair
]

# 업무일지 키워드 패턴
WORK_LOG_KEYWORDS = [
    '일 일 업 무 일 지',
    '일일업무일지',
    '금일업무',
    '익일업무',
    '목 적',
    'Action',
    '계획',
    '달성',
]


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

    def preprocess_work_log_text(self, text: str) -> str:
        """
        업무일지 텍스트 1차 정리 (AI 전달 전 전처리)
        
        PDF에서 추출된 표 형식의 텍스트를 정리하여 AI가 이해하기 쉬운 형태로 변환합니다.
        
        Args:
            text: PDF에서 추출된 원본 텍스트
            
        Returns:
            정리된 텍스트
        """
        if not text:
            return text
        
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # 빈 줄 건너뛰기
            if not line:
                continue
            
            # 한 글자 줄 삭제 (의미 없는 단일 문자)
            # 단, 숫자나 특수 기호는 유지할 수 있으므로 한글/영문 한 글자만 삭제
            if len(line) == 1 and re.match(r'^[가-힣a-zA-Z]$', line):
                continue
            
            # 두 글자 이하의 무의미한 줄도 삭제 (결재란 조각 등)
            # 예: "금", "일", "업", "무" 등 깨진 텍스트
            if len(line) <= 2 and re.match(r'^[가-힣]{1,2}$', line):
                # 의미 있는 두 글자 단어는 유지 (목적, 완료 등)
                meaningful_words = ['목적', '완료', '진행', '예정', '시작', '종료', '계획', '달성']
                if line not in meaningful_words:
                    continue
            
            # 노이즈 패턴 제거
            is_noise = False
            for pattern in NOISE_PATTERNS:
                if re.match(pattern, line):
                    is_noise = True
                    break
            
            if is_noise:
                continue
            
            # 결재란 헤더 제거 (작성 검토 승인 결 일일업무일지 이름 이름 이름 재)
            if self._is_approval_header(line):
                continue
            
            # 유의미한 줄 추가
            cleaned_lines.append(line)
        
        # 텍스트 재구성
        result = '\n'.join(cleaned_lines)
        
        # 추가 정리: 연속된 숫자 열 정리
        result = self._clean_numeric_sequences(result)
        
        # 업무일지 구조 정리
        result = self._restructure_work_log(result)
        
        return result
    
    def _is_approval_header(self, line: str) -> bool:
        """결재란 헤더인지 확인"""
        # 결재란 패턴들
        approval_patterns = [
            r'작\s*성\s+검\s*토\s+승\s*인',
            r'작성\s+검토\s+승인',
        ]
        for pattern in approval_patterns:
            if re.search(pattern, line):
                return True
        return False
    
    def _clean_numeric_sequences(self, text: str) -> str:
        """연속된 숫자/진행률 시퀀스 정리"""
        # 단독으로 있는 진행률 숫자들을 해당 줄과 합치기
        # 예: "10 10 50 50" → 계획(H): 10, 달성(H): 10, 계획(%): 50, 달성(%): 50
        
        lines = text.split('\n')
        result_lines = []
        skip_next = False
        
        for i, line in enumerate(lines):
            if skip_next:
                skip_next = False
                continue
            
            # 숫자 4개 패턴 (계획H 달성H 계획% 달성%)
            numeric_match = re.match(
                r'^(\d+)\s+(\d+)\s+(\d+%?)\s+(\d+%?)$', 
                line.strip()
            )
            
            if numeric_match and i > 0:
                # 이전 줄에 진행률 추가
                plan_h, done_h, plan_p, done_p = numeric_match.groups()
                if result_lines:
                    prev_line = result_lines[-1]
                    # 진행률 정보를 이전 줄에 추가
                    progress_info = f" [계획: {plan_h}H, 달성: {done_h}H, 진행률: {done_p}%]"
                    result_lines[-1] = prev_line + progress_info
                continue
            
            result_lines.append(line)
        
        return '\n'.join(result_lines)
    
    def _restructure_work_log(self, text: str) -> str:
        """업무일지 구조 정리 - 팀원별 섹션 구분"""
        # FW팀 [이름] 패턴으로 팀원 섹션 찾기
        team_pattern = r'FW\s*팀\s+(\w+)\s+일자\s*[:：]?\s*(\d{4}[\.\-/]\d{1,2}[\.\-/]\d{1,2})'
        
        lines = text.split('\n')
        result_lines = []
        current_member = None
        current_date = None
        
        for line in lines:
            # 팀원 헤더 찾기
            match = re.search(team_pattern, line)
            if match:
                current_member = match.group(1)
                current_date = match.group(2)
                result_lines.append("")
                result_lines.append(f"========== {current_member} ({current_date}) ==========")
                continue
            
            # "일 일 업 무 일 지" 패턴 정리
            if '일 일 업 무 일 지' in line or '일일업무일지' in line:
                continue  # 중복 제목 제거
            
            # "분류 구분 상세내용..." 헤더 제거
            if re.match(r'^분류\s+구\s*분\s+상\s*세', line):
                continue
            
            # 금일업무/익일업무 표시
            if '금일업무' in line or '금' in line and '일' in line and '업' in line:
                if '금일' not in line:
                    line = line.replace('금', '금일').replace('일업무', '업무')
                result_lines.append("")
                result_lines.append("【금일업무】")
                continue
            
            if '익일업무' in line or '익' in line and '일' in line and '업' in line:
                result_lines.append("")
                result_lines.append("【익일업무】")
                continue
            
            # 프로젝트/업무 내용 정리
            # "1 bright Simple..." 같은 프로젝트 시작
            project_match = re.match(r'^(\d+)\s+(.+?(?:목표|개발|개선|준비|지원))', line)
            if project_match:
                result_lines.append(f"\n● 프로젝트: {line}")
                continue
            
            # "1.1 목 적", "1.2 Action" 패턴
            if re.match(r'^\d+\.\d+\s+(목\s*적|Action|목적)', line):
                line = line.replace('목 적', '목적')
                result_lines.append(f"  {line}")
                continue
            
            # 일반 내용
            result_lines.append(line)
        
        return '\n'.join(result_lines)

