"""
데이터베이스 관리 모듈
SQLite를 사용하여 업무일지 분석 결과를 저장하고 조회합니다.
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DatabaseManager:
    """SQLite 데이터베이스 관리 클래스"""
    
    DB_FILE = "workflow_analysis.db"
    
    def __init__(self, db_path: Optional[str] = None):
        """
        초기화
        
        Args:
            db_path: 데이터베이스 파일 경로 (None이면 프로젝트 루트에 생성)
        """
        if db_path:
            self.db_path = Path(db_path)
        else:
            # 프로젝트 루트에 DB 파일 생성
            project_root = Path(__file__).parent.parent.parent
            self.db_path = project_root / self.DB_FILE
        
        self._init_database()
    
    @contextmanager
    def _get_connection(self):
        """데이터베이스 연결 컨텍스트 매니저"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_database(self):
        """데이터베이스 스키마 초기화"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 팀원 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    team TEXT DEFAULT 'FW팀',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 프로젝트 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    category TEXT,
                    description TEXT,
                    target_progress INTEGER DEFAULT 100,
                    current_progress INTEGER DEFAULT 0,
                    target_date DATE,
                    priority TEXT DEFAULT '보통',
                    status TEXT DEFAULT '진행중',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 일일 업무 기록 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    member_id INTEGER NOT NULL,
                    project_id INTEGER,
                    work_date DATE NOT NULL,
                    task_content TEXT,
                    progress_percent INTEGER DEFAULT 0,
                    status TEXT DEFAULT '진행중',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (member_id) REFERENCES members(id),
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                )
            """)
            
            # 분석 이력 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analysis_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_date DATE NOT NULL,
                    file_count INTEGER DEFAULT 0,
                    raw_text TEXT,
                    cleaned_text TEXT,
                    summary_text TEXT,
                    thanks_text TEXT,
                    devstatus_text TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 인덱스 생성
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_daily_tasks_date 
                ON daily_tasks(work_date)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_daily_tasks_member 
                ON daily_tasks(member_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_daily_tasks_project 
                ON daily_tasks(project_id)
            """)
            
            logger.info(f"데이터베이스 초기화 완료: {self.db_path}")
    
    # === 팀원 관리 ===
    
    def add_member(self, name: str, team: str = "FW팀") -> int:
        """
        팀원 추가 (이미 존재하면 ID 반환)
        
        Returns:
            팀원 ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 기존 팀원 확인
            cursor.execute("SELECT id FROM members WHERE name = ?", (name,))
            row = cursor.fetchone()
            
            if row:
                return row["id"]
            
            # 새 팀원 추가
            cursor.execute(
                "INSERT INTO members (name, team) VALUES (?, ?)",
                (name, team)
            )
            return cursor.lastrowid
    
    def get_all_members(self) -> List[Dict[str, Any]]:
        """모든 팀원 조회"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM members ORDER BY name")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_member_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """이름으로 팀원 조회"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM members WHERE name = ?", (name,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    # === 프로젝트 관리 ===
    
    def add_project(
        self,
        name: str,
        category: Optional[str] = None,
        description: Optional[str] = None
    ) -> int:
        """
        프로젝트 추가 (이미 존재하면 ID 반환)
        
        Returns:
            프로젝트 ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 기존 프로젝트 확인
            cursor.execute("SELECT id FROM projects WHERE name = ?", (name,))
            row = cursor.fetchone()
            
            if row:
                return row["id"]
            
            # 새 프로젝트 추가
            cursor.execute(
                "INSERT INTO projects (name, category, description) VALUES (?, ?, ?)",
                (name, category, description)
            )
            return cursor.lastrowid
    
    def get_all_projects(self) -> List[Dict[str, Any]]:
        """모든 프로젝트 조회"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects ORDER BY category, name")
            return [dict(row) for row in cursor.fetchall()]
    
    def update_project(
        self,
        project_id: int,
        target_progress: Optional[int] = None,
        current_progress: Optional[int] = None,
        target_date: Optional[date] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
        description: Optional[str] = None
    ) -> bool:
        """프로젝트 정보 업데이트"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if target_progress is not None:
                updates.append("target_progress = ?")
                params.append(target_progress)
            if current_progress is not None:
                updates.append("current_progress = ?")
                params.append(current_progress)
            if target_date is not None:
                updates.append("target_date = ?")
                params.append(target_date)
            if priority is not None:
                updates.append("priority = ?")
                params.append(priority)
            if status is not None:
                updates.append("status = ?")
                params.append(status)
            if description is not None:
                updates.append("description = ?")
                params.append(description)
            
            if not updates:
                return False
            
            params.append(project_id)
            query = f"UPDATE projects SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            
            return cursor.rowcount > 0
    
    def get_projects_with_stats(self) -> List[Dict[str, Any]]:
        """프로젝트 목록과 통계 조회"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    p.*,
                    COUNT(dt.id) as task_count,
                    COUNT(DISTINCT dt.member_id) as member_count,
                    MAX(dt.work_date) as last_activity
                FROM projects p
                LEFT JOIN daily_tasks dt ON p.id = dt.project_id
                GROUP BY p.id
                ORDER BY p.priority DESC, p.name
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def calculate_project_progress(self, project_id: int) -> int:
        """프로젝트 진행률 자동 계산 (최근 업무 기준)"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT AVG(progress_percent) as avg_progress
                FROM daily_tasks
                WHERE project_id = ?
                AND work_date >= date('now', '-30 days')
            """, (project_id,))
            row = cursor.fetchone()
            
            if row and row['avg_progress']:
                return int(row['avg_progress'])
            return 0
    
    def get_project_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """이름으로 프로젝트 조회"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects WHERE name = ?", (name,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    # === 일일 업무 관리 ===
    
    def add_daily_task(
        self,
        member_name: str,
        work_date: date,
        task_content: str,
        project_name: Optional[str] = None,
        progress_percent: int = 0,
        status: str = "진행중"
    ) -> int:
        """
        일일 업무 추가
        
        Returns:
            업무 ID
        """
        # 팀원 ID 조회/생성
        member_id = self.add_member(member_name)
        
        # 프로젝트 ID 조회/생성 (있는 경우)
        project_id = None
        if project_name:
            project_id = self.add_project(project_name)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO daily_tasks 
                (member_id, project_id, work_date, task_content, progress_percent, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (member_id, project_id, work_date, task_content, progress_percent, status))
            
            return cursor.lastrowid
    
    def get_tasks_by_date_range(
        self,
        start_date: date,
        end_date: date,
        member_name: Optional[str] = None,
        project_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        기간별 업무 조회
        
        Args:
            start_date: 시작일
            end_date: 종료일
            member_name: 팀원 필터 (선택)
            project_name: 프로젝트 필터 (선택)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    dt.id,
                    dt.work_date,
                    dt.task_content,
                    dt.progress_percent,
                    dt.status,
                    m.name as member_name,
                    m.team,
                    p.name as project_name,
                    p.category as project_category
                FROM daily_tasks dt
                JOIN members m ON dt.member_id = m.id
                LEFT JOIN projects p ON dt.project_id = p.id
                WHERE dt.work_date BETWEEN ? AND ?
            """
            params = [start_date, end_date]
            
            if member_name:
                query += " AND m.name = ?"
                params.append(member_name)
            
            if project_name:
                query += " AND p.name = ?"
                params.append(project_name)
            
            query += " ORDER BY dt.work_date DESC, m.name, p.name"
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_member_tasks_summary(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """팀원별 업무 요약 조회"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    m.name as member_name,
                    COUNT(dt.id) as task_count,
                    COUNT(DISTINCT dt.work_date) as work_days,
                    AVG(dt.progress_percent) as avg_progress,
                    COUNT(CASE WHEN dt.status = '완료' THEN 1 END) as completed_count
                FROM daily_tasks dt
                JOIN members m ON dt.member_id = m.id
                WHERE dt.work_date BETWEEN ? AND ?
                GROUP BY m.id, m.name
                ORDER BY task_count DESC
            """, (start_date, end_date))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_project_tasks_summary(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """프로젝트별 업무 요약 조회"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    p.name as project_name,
                    p.category as project_category,
                    COUNT(dt.id) as task_count,
                    COUNT(DISTINCT m.id) as member_count,
                    AVG(dt.progress_percent) as avg_progress,
                    GROUP_CONCAT(DISTINCT m.name) as members
                FROM daily_tasks dt
                JOIN members m ON dt.member_id = m.id
                LEFT JOIN projects p ON dt.project_id = p.id
                WHERE dt.work_date BETWEEN ? AND ?
                GROUP BY p.id, p.name, p.category
                ORDER BY task_count DESC
            """, (start_date, end_date))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # === 분석 이력 관리 ===
    
    def save_analysis_history(
        self,
        analysis_date: date,
        file_count: int,
        raw_text: str = "",
        cleaned_text: str = "",
        summary_text: str = "",
        thanks_text: str = "",
        devstatus_text: str = ""
    ) -> int:
        """
        분석 이력 저장
        
        Returns:
            이력 ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 같은 날짜의 기존 이력이 있으면 업데이트
            cursor.execute(
                "SELECT id FROM analysis_history WHERE analysis_date = ?",
                (analysis_date,)
            )
            row = cursor.fetchone()
            
            if row:
                cursor.execute("""
                    UPDATE analysis_history SET
                        file_count = ?,
                        raw_text = ?,
                        cleaned_text = ?,
                        summary_text = ?,
                        thanks_text = ?,
                        devstatus_text = ?,
                        created_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (file_count, raw_text, cleaned_text, summary_text, 
                      thanks_text, devstatus_text, row["id"]))
                return row["id"]
            
            # 새 이력 추가
            cursor.execute("""
                INSERT INTO analysis_history 
                (analysis_date, file_count, raw_text, cleaned_text, 
                 summary_text, thanks_text, devstatus_text)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (analysis_date, file_count, raw_text, cleaned_text,
                  summary_text, thanks_text, devstatus_text))
            
            return cursor.lastrowid
    
    def get_analysis_history(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """분석 이력 조회"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM analysis_history"
            params = []
            
            if start_date and end_date:
                query += " WHERE analysis_date BETWEEN ? AND ?"
                params = [start_date, end_date]
            elif start_date:
                query += " WHERE analysis_date >= ?"
                params = [start_date]
            elif end_date:
                query += " WHERE analysis_date <= ?"
                params = [end_date]
            
            query += " ORDER BY analysis_date DESC"
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    # === 통계 ===
    
    def get_date_range(self) -> Dict[str, Optional[date]]:
        """저장된 데이터의 날짜 범위 조회"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    MIN(work_date) as min_date,
                    MAX(work_date) as max_date
                FROM daily_tasks
            """)
            row = cursor.fetchone()
            
            return {
                "min_date": row["min_date"],
                "max_date": row["max_date"]
            }
    
    def get_statistics(self) -> Dict[str, int]:
        """전체 통계 조회"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            cursor.execute("SELECT COUNT(*) as cnt FROM members")
            stats["member_count"] = cursor.fetchone()["cnt"]
            
            cursor.execute("SELECT COUNT(*) as cnt FROM projects")
            stats["project_count"] = cursor.fetchone()["cnt"]
            
            cursor.execute("SELECT COUNT(*) as cnt FROM daily_tasks")
            stats["task_count"] = cursor.fetchone()["cnt"]
            
            cursor.execute("SELECT COUNT(*) as cnt FROM analysis_history")
            stats["analysis_count"] = cursor.fetchone()["cnt"]
            
            return stats


# 전역 인스턴스
_db_instance: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """전역 데이터베이스 매니저 인스턴스 반환"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
    return _db_instance

