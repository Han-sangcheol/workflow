"""
업무일지 AI 분석 시스템 - 메인 진입점

팀원들의 업무일지를 AI로 분석하여 통합 회의록과 감사 인사를 생성합니다.
"""

import sys
import os
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication

from src.ui.main_window import MainWindow


def get_app_data_dir() -> Path:
    """애플리케이션 데이터 디렉토리 반환 (로그, 설정 파일 저장용)"""
    if sys.platform == 'win32':
        # Windows: %LOCALAPPDATA%\WorkflowAnalyzer
        base_dir = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local'))
    else:
        # Linux/Mac: ~/.local/share/WorkflowAnalyzer
        base_dir = Path.home() / '.local' / 'share'
    
    app_dir = base_dir / 'WorkflowAnalyzer'
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def setup_logging():
    """로깅 설정"""
    # 로그 파일을 사용자 데이터 폴더에 저장 (Program Files 권한 문제 방지)
    log_dir = get_app_data_dir()
    log_file = log_dir / 'workflow.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(str(log_file), encoding='utf-8')
        ]
    )


def main():
    """메인 함수"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 50)
    logger.info("업무일지 AI 분석 시스템 시작")
    logger.info("=" * 50)
    
    app = QApplication(sys.argv)
    app.setApplicationName("업무일지 AI 분석 시스템")
    app.setOrganizationName("Dentium")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

