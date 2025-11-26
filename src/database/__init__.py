"""
데이터베이스 모듈
업무일지 분석 결과를 저장하고 조회합니다.
"""

from .db_manager import DatabaseManager, get_db_manager

__all__ = ["DatabaseManager", "get_db_manager"]

