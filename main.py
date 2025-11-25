"""
업무일지 AI 분석 시스템 - 메인 진입점

팀원들의 업무일지를 AI로 분석하여 통합 회의록과 감사 인사를 생성합니다.
"""

import sys
import logging
from PySide6.QtWidgets import QApplication

from src.ui.main_window import MainWindow


def setup_logging():
    """로깅 설정"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('workflow.log', encoding='utf-8')
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

