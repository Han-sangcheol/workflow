# 프로젝트 요약

## 업무일지 AI 분석 시스템

### 개요
팀원들의 일일 업무일지(PDF/DOCX)를 로컬 AI(Ollama)로 분석하여 통합 회의록과 개인별 감사 인사를 자동 생성하는 PySide6 기반 데스크톱 애플리케이션입니다.

### 핵심 기능

#### 1. 문서 파싱 (Step 1)
- **PDF 파싱**: PyMuPDF를 사용한 텍스트 추출
- **DOCX 파싱**: python-docx를 사용한 텍스트 추출
- **자동 형식 감지**: 파일 확장자 기반 파서 자동 선택
- **다중 파일 처리**: 여러 파일을 한 번에 처리

#### 2. AI 분석 (Step 2 & 3)
- **로컬 AI**: Ollama 사용 (인터넷 연결 불필요)
- **통합 회의록 생성**: 팀 전체 업무를 하나의 회의록으로 통합
- **감사 인사 생성**: 각 팀원의 업무 내용 기반 개인별 감사 인사
- **스트리밍 응답**: 실시간 텍스트 생성 지원

#### 3. 파일 선택
- **수동 선택**: 사용자가 직접 파일 선택
- **자동 검색**: 오늘 날짜(YYMMDD)로 파일 자동 검색
- **폴더 검색**: 지정 폴더의 모든 문서 검색

#### 4. 결과 저장
- **DOCX 출력**: 분석 결과를 Word 문서로 저장
- **자동 파일명**: 날짜 기반 자동 파일명 생성
- **분리 저장**: 회의록과 감사 인사를 각각 저장

### 기술 스택

| 카테고리 | 기술 |
|---------|------|
| GUI | PySide6 (Qt for Python) |
| AI | Ollama (로컬 LLM) |
| 문서 파싱 | PyMuPDF, python-docx |
| HTTP | requests |
| 테스트 | pytest, pytest-qt |
| 언어 | Python 3.8+ |

### 프로젝트 구조

```
workflow/
├── main.py                    # 진입점
├── requirements.txt           # 의존성
├── README.md                  # 설치/실행 가이드
├── USAGE.md                   # 상세 사용 가이드
├── PROJECT_SUMMARY.md         # 본 문서
├── .cursorrules              # 프로젝트 규칙
├── .gitignore                # Git 무시 파일
├── pytest.ini                # pytest 설정
├── setup.bat/sh              # 설치 스크립트
├── run.bat/sh                # 실행 스크립트
│
├── src/
│   ├── document/             # 문서 파싱
│   │   ├── pdf_parser.py
│   │   ├── docx_parser.py
│   │   └── document_parser.py
│   │
│   ├── ai/                   # AI 연동
│   │   └── ollama_client.py
│   │
│   ├── utils/                # 유틸리티
│   │   ├── file_selector.py
│   │   └── output_generator.py
│   │
│   └── ui/                   # GUI
│       ├── main_window.py
│       └── worker.py
│
└── tests/                    # 테스트
    ├── test_document_parser.py
    ├── test_file_selector.py
    ├── test_ollama_client.py
    └── test_output_generator.py
```

### 아키텍처 설계

#### 레이어 구조
```
┌─────────────────────────┐
│   Presentation Layer    │
│   (UI - PySide6)        │
└───────────┬─────────────┘
            │
┌───────────▼─────────────┐
│   Business Logic Layer  │
│   (Worker Thread)       │
└─┬─────────┬─────────┬───┘
  │         │         │
  ▼         ▼         ▼
┌─────┐ ┌─────┐ ┌─────┐
│ Doc │ │ AI  │ │Utils│
│Parse│ │ API │ │     │
└─────┘ └─────┘ └─────┘
```

#### 스레드 모델
- **메인 스레드**: UI 렌더링 및 이벤트 처리
- **워커 스레드**: 문서 파싱 및 AI 분석
- **Signal-Slot**: 스레드 간 안전한 통신

### 코드 품질 규칙

#### 복잡도 제한
- 파일당 최대 300줄
- 함수당 최대 50줄
- 들여쓰기 최대 3단계
- 함수 인자 최대 4개

#### 네이밍 컨벤션
- 함수/변수: `snake_case`
- 클래스: `PascalCase`
- 상수: `UPPER_SNAKE_CASE`

#### 문서화
- 모든 함수에 docstring 작성
- 주석은 한국어 사용
- 로그는 INFO 레벨 기본

### 테스트 전략

#### 단위 테스트
- 각 모듈별 독립 테스트
- Mock 객체 활용 (AI, 파일 I/O)
- 커버리지 목표: 80% 이상

#### 실행 방법
```bash
# 가상환경 활성화 후
pytest tests/ -v
```

### 환경 요구사항

#### 필수
- Python 3.8 이상
- Windows 10/11, Linux, macOS
- RAM 8GB 이상 (AI 실행용)
- 디스크 여유 공간 5GB 이상

#### 선택
- GPU (AI 속도 향상)
- SSD (파일 읽기 속도 향상)

### 보안 및 프라이버시

- **로컬 처리**: 모든 데이터는 로컬에서만 처리
- **인터넷 불필요**: Ollama 로컬 실행 시 인터넷 연결 불필요
- **데이터 보관 없음**: 원본 파일 및 생성 결과만 저장
- **로그 파일**: `workflow.log`에 민감 정보 저장 안 함

### 향후 개선 사항

#### 단기 (v1.1)
- [ ] GPU 가속 지원 자동 감지
- [ ] 다양한 AI 모델 선택 UI
- [ ] 진행 상황 더 상세히 표시
- [ ] 결과 미리보기 기능

#### 중기 (v1.5)
- [ ] 이미지 PDF OCR 지원
- [ ] 템플릿 기반 출력 커스터마이징
- [ ] 히스토리 관리 기능
- [ ] 배치 처리 자동화

#### 장기 (v2.0)
- [ ] 클라우드 동기화 옵션
- [ ] 다국어 지원
- [ ] 플러그인 시스템
- [ ] 웹 버전 제공

### 기여자

- **개발**: AI Assistant
- **요구사항 정의**: Dentium 팀
- **프레임워크**: PySide6, Ollama

### 라이선스

Dentium 내부용 - 무단 배포 금지

### 연락처

프로젝트 관련 문의: Dentium 개발팀

---

**마지막 업데이트**: 2025-11-25
**버전**: 1.0.0

