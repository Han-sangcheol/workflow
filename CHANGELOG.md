# 변경 이력

## [1.0.0] - 2025-11-25

### 추가
- 🎉 프로젝트 초기 릴리스
- 📄 PDF 문서 파싱 기능 (PyMuPDF)
- 📝 DOCX 문서 파싱 기능 (python-docx)
- 🤖 Ollama AI 연동 (로컬 LLM)
- 📋 통합 회의록 자동 생성
- 💌 개인별 감사 인사 자동 생성
- 🖥️ PySide6 기반 GUI
- 📁 파일 수동/자동 선택 기능
- 💾 DOCX 결과 저장 기능
- 🔄 백그라운드 스레드 처리 (UI 프리징 방지)
- 📊 진행 상황 표시 (Progress Bar)
- 🧪 단위 테스트 (pytest)
- 📚 상세한 문서화 (README, USAGE, PROJECT_SUMMARY)
- 🚀 설치/실행 스크립트 (Windows/Linux/Mac)
- 📝 로그 파일 자동 생성

### 기술 스택
- PySide6 6.6.0+
- PyMuPDF 1.23.0+
- python-docx 1.1.0+
- requests 2.31.0+
- pytest 7.4.0+

### 문서
- README.md: 설치 및 실행 가이드
- USAGE.md: 상세 사용 가이드
- PROJECT_SUMMARY.md: 프로젝트 개요
- CHANGELOG.md: 변경 이력

### 스크립트
- setup.bat/sh: 가상환경 설치 스크립트
- run.bat/sh: 프로그램 실행 스크립트

---

## 버전 규칙

- **Major (X.0.0)**: 호환성이 깨지는 대규모 변경
- **Minor (x.X.0)**: 새로운 기능 추가
- **Patch (x.x.X)**: 버그 수정 및 개선

