"""
업무 데이터 파싱 유틸리티
정리된 텍스트에서 팀원별, 프로젝트별 업무 데이터를 추출합니다.
"""

import re
import logging
from datetime import datetime, date
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TaskData:
    """업무 데이터 클래스"""
    member_name: str
    work_date: date
    project_name: Optional[str]
    task_content: str
    progress_percent: int = 0
    status: str = "진행중"


class TaskParser:
    """정리된 텍스트에서 업무 데이터를 파싱하는 클래스"""
    
    # 팀원 섹션 패턴: "########## 김종민 (2025.11.25) ##########"
    MEMBER_SECTION_PATTERN = re.compile(
        r"#{5,}\s*(.+?)\s*\((\d{4}\.\d{2}\.\d{2})\)\s*#{5,}"
    )
    
    # 프로젝트 대분류 패턴: "[프로젝트 대분류: bright Simple]"
    PROJECT_PATTERN = re.compile(
        r"\[프로젝트 대분류:\s*(.+?)\]"
    )
    
    # 진행률 패턴: "진행률: 계획 90% / 달성 85%"
    PROGRESS_PATTERN = re.compile(
        r"진행률:.*?달성\s*(\d+)%"
    )
    
    # 상태 패턴: "(완료)", "(진행중)" 등
    STATUS_PATTERN = re.compile(
        r"\((완료|진행중|대기|예정)\)"
    )
    
    # 팀원 목록 패턴
    MEMBER_LIST_PATTERN = re.compile(
        r"#{5,}\s*팀원\s*목록\s*#{5,}\s*\n(.+?)(?:\n\n|#{5,})",
        re.DOTALL
    )
    
    def __init__(self):
        """초기화"""
        pass
    
    def parse_cleaned_text(self, cleaned_text: str) -> List[TaskData]:
        """
        정리된 텍스트에서 업무 데이터 추출
        
        Args:
            cleaned_text: AI가 정리한 텍스트
            
        Returns:
            TaskData 리스트
        """
        tasks = []
        
        if not cleaned_text:
            return tasks
        
        try:
            # 팀원 목록 추출
            member_names = self._extract_member_list(cleaned_text)
            logger.debug(f"추출된 팀원: {member_names}")
            
            # 팀원별 섹션 분리
            member_sections = self._split_by_member(cleaned_text)
            
            for member_name, work_date, section_text in member_sections:
                # 섹션 내 프로젝트별 업무 파싱
                project_tasks = self._parse_member_section(
                    member_name, work_date, section_text
                )
                tasks.extend(project_tasks)
            
            logger.info(f"총 {len(tasks)}개 업무 추출 완료")
            
        except Exception as e:
            logger.error(f"텍스트 파싱 오류: {e}")
        
        return tasks
    
    def _extract_member_list(self, text: str) -> List[str]:
        """팀원 목록 추출"""
        match = self.MEMBER_LIST_PATTERN.search(text)
        if match:
            names_text = match.group(1).strip()
            # 쉼표나 줄바꿈으로 구분된 이름들
            names = re.split(r'[,\n]', names_text)
            return [name.strip() for name in names if name.strip()]
        
        # 팀원 목록이 없으면 섹션 헤더에서 추출
        matches = self.MEMBER_SECTION_PATTERN.findall(text)
        return list(set(m[0].strip() for m in matches))
    
    def _split_by_member(self, text: str) -> List[tuple]:
        """
        텍스트를 팀원별 섹션으로 분리
        
        Returns:
            [(팀원명, 작업일, 섹션텍스트), ...]
        """
        sections = []
        
        # 팀원 섹션 시작 위치 찾기
        matches = list(self.MEMBER_SECTION_PATTERN.finditer(text))
        
        for i, match in enumerate(matches):
            member_name = match.group(1).strip()
            date_str = match.group(2)
            
            try:
                work_date = datetime.strptime(date_str, "%Y.%m.%d").date()
            except ValueError:
                work_date = date.today()
            
            # 섹션 텍스트 추출 (현재 매치부터 다음 매치 전까지)
            start_pos = match.end()
            if i < len(matches) - 1:
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(text)
            
            section_text = text[start_pos:end_pos].strip()
            sections.append((member_name, work_date, section_text))
        
        return sections
    
    def _parse_member_section(
        self,
        member_name: str,
        work_date: date,
        section_text: str
    ) -> List[TaskData]:
        """팀원 섹션에서 프로젝트별 업무 파싱"""
        tasks = []
        
        # 프로젝트별로 분리
        project_blocks = self._split_by_project(section_text)
        
        for project_name, block_text in project_blocks:
            # 업무 내용 추출
            task_content = self._extract_task_content(block_text)
            
            # 진행률 추출
            progress = self._extract_progress(block_text)
            
            # 상태 추출
            status = self._extract_status(block_text)
            
            if task_content:
                tasks.append(TaskData(
                    member_name=member_name,
                    work_date=work_date,
                    project_name=project_name,
                    task_content=task_content,
                    progress_percent=progress,
                    status=status
                ))
        
        # 프로젝트 구분이 없는 경우 전체를 하나의 업무로
        if not tasks and section_text.strip():
            tasks.append(TaskData(
                member_name=member_name,
                work_date=work_date,
                project_name=None,
                task_content=section_text.strip()[:500],  # 최대 500자
                progress_percent=0,
                status="진행중"
            ))
        
        return tasks
    
    def _split_by_project(self, section_text: str) -> List[tuple]:
        """
        섹션을 프로젝트별로 분리
        
        Returns:
            [(프로젝트명, 블록텍스트), ...]
        """
        blocks = []
        
        # 프로젝트 패턴 매치 찾기
        matches = list(self.PROJECT_PATTERN.finditer(section_text))
        
        if not matches:
            # 프로젝트 구분이 없으면 전체를 하나로
            return [(None, section_text)]
        
        for i, match in enumerate(matches):
            project_name = match.group(1).strip()
            
            start_pos = match.end()
            if i < len(matches) - 1:
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(section_text)
            
            block_text = section_text[start_pos:end_pos].strip()
            blocks.append((project_name, block_text))
        
        return blocks
    
    def _extract_task_content(self, block_text: str) -> str:
        """업무 내용 추출"""
        # 불필요한 패턴 제거
        content = block_text
        
        # 진행률 라인 제거
        content = re.sub(r"•?\s*진행률:.*?\n?", "", content)
        
        # 빈 줄 정리
        content = re.sub(r"\n{3,}", "\n\n", content)
        
        return content.strip()[:1000]  # 최대 1000자
    
    def _extract_progress(self, block_text: str) -> int:
        """진행률 추출"""
        match = self.PROGRESS_PATTERN.search(block_text)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
        return 0
    
    def _extract_status(self, block_text: str) -> str:
        """상태 추출"""
        match = self.STATUS_PATTERN.search(block_text)
        if match:
            return match.group(1)
        
        # 텍스트 내용으로 상태 추정
        if "완료" in block_text:
            return "완료"
        elif "예정" in block_text or "대기" in block_text:
            return "대기"
        
        return "진행중"
    
    def extract_date_from_text(self, text: str) -> Optional[date]:
        """
        텍스트에서 날짜 추출
        
        지원 형식:
        - 2025.11.25
        - 2025-11-25
        - 25.11.25
        - 251125
        """
        patterns = [
            (r"(\d{4})\.(\d{2})\.(\d{2})", "%Y.%m.%d"),
            (r"(\d{4})-(\d{2})-(\d{2})", "%Y-%m-%d"),
            (r"(\d{2})\.(\d{2})\.(\d{2})", "%y.%m.%d"),
            (r"(\d{2})(\d{2})(\d{2})", "%y%m%d"),
        ]
        
        for pattern, date_format in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    date_str = match.group(0)
                    # %y 형식인 경우 직접 파싱
                    if date_format in ["%y.%m.%d", "%y%m%d"]:
                        groups = match.groups()
                        year = 2000 + int(groups[0])
                        month = int(groups[1])
                        day = int(groups[2])
                        return date(year, month, day)
                    else:
                        return datetime.strptime(date_str, date_format).date()
                except ValueError:
                    continue
        
        return None
    
    def extract_date_from_filename(self, filename: str) -> Optional[date]:
        """파일명에서 날짜 추출"""
        return self.extract_date_from_text(filename)


def parse_tasks_from_cleaned_text(cleaned_text: str) -> List[TaskData]:
    """
    정리된 텍스트에서 업무 데이터 추출 (편의 함수)
    
    Args:
        cleaned_text: AI가 정리한 텍스트
        
    Returns:
        TaskData 리스트
    """
    parser = TaskParser()
    return parser.parse_cleaned_text(cleaned_text)



