"""
버전 정보 중앙 관리 파일

이 파일은 애플리케이션의 버전 정보를 중앙에서 관리합니다.
PyInstaller, Inno Setup, 메인 윈도우 등에서 이 파일을 참조합니다.
"""

# 애플리케이션 정보
APP_NAME = "업무일지 AI 분석 시스템"
APP_NAME_EN = "WorkflowAnalyzer"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "팀원들의 업무일지를 AI로 분석하여 통합 회의록과 감사 인사를 생성합니다."

# 저작권 정보
APP_AUTHOR = "Dentium"
APP_COPYRIGHT = "Copyright (C) 2025 Dentium. All rights reserved."

# 버전 정보 (Windows 버전 리소스용)
VERSION_TUPLE = (1, 0, 0, 0)  # (major, minor, patch, build)

# 파일 정보
EXECUTABLE_NAME = "WorkflowAnalyzer.exe"
INSTALLER_NAME = f"WorkflowAnalyzer_Setup_{APP_VERSION}.exe"








