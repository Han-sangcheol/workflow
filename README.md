# 업무일지 AI 분석 시스템

팀원들의 일일 업무일지를 AI로 분석하여 통합 회의록과 개인별 감사 인사를 자동으로 생성하는 프로그램입니다.

## 주요 기능

- 📄 **문서 파싱**: PDF, DOCX, DOC 파일의 텍스트 자동 추출
- 🤖 **AI 분석**: 로컬 Ollama AI를 통한 지능형 텍스트 분석
- 📋 **통합 회의록**: 팀원들의 업무를 하나의 회의록으로 통합
- 💌 **감사 인사**: 각 팀원의 업무 내용을 바탕으로 개인별 감사 인사 작성
- 💾 **결과 저장**: 분석 결과를 DOCX 파일로 저장

## 사전 준비

### 1. Python 설치
- Python 3.8 이상 필요
- [Python 공식 웹사이트](https://www.python.org/)에서 다운로드

### 2. Ollama 설치 및 실행
본 프로그램은 로컬 AI 분석을 위해 **Ollama**를 사용합니다.

1. [Ollama 공식 웹사이트](https://ollama.ai)에서 다운로드
2. 설치 후 터미널에서 모델 다운로드:
   ```bash
   ollama pull llama3.2
   ```
3. Ollama 서버 실행 확인:
   ```bash
   ollama serve
   ```

## 설치 방법

**⚠️ 중요: 본 프로젝트는 가상환경에서 실행됩니다.**

본 프로젝트는 빠른 의존성 관리를 위해 **uv**를 사용합니다.

### 자동 설치 (권장)

**Windows:**
```bash
.\setup.bat
```

**Linux/Mac:**
```bash
chmod +x setup.sh run.sh
./setup.sh
```

setup.bat/sh 스크립트가 자동으로:
1. uv 설치 (없는 경우)
2. 가상환경 생성 (.venv)
3. 의존성 설치

### 수동 설치

#### 1. uv 설치

**Windows:**
```bash
pip install uv
```

**Linux/Mac:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### 2. 가상환경 생성 및 의존성 설치

```bash
# 가상환경 생성
uv venv

# 의존성 설치
uv pip install -r requirements.txt
```

## 실행 방법

**Windows:**
```bash
.\run.bat
```

**Linux/Mac:**
```bash
./run.sh
```

또는 수동 실행:
```bash
# Windows
.venv\Scripts\activate
python main.py

# Linux/Mac
source .venv/bin/activate
python main.py
```

**💡 Ollama 자동 시작**: 프로그램이 Ollama 서버를 자동으로 감지하고 시작합니다.
별도로 `ollama serve`를 실행할 필요가 없습니다!

## 사용 방법

### 1. 파일 선택
- **폴더 선택**: 업무일지가 있는 폴더 선택
  - "오늘 날짜로 자동 검색" 체크: 오늘 날짜(YYMMDD)가 포함된 파일만 자동 선택
  - 체크 해제: 폴더 내 모든 PDF/DOCX 파일 표시
- **파일 직접 선택**: 특정 파일들을 직접 선택

### 2. 분석 실행
- "🚀 분석 시작" 버튼 클릭
- 진행 상황:
  - Step 1: 문서 파일 텍스트 추출
  - Step 2: AI로 통합 회의록 생성
  - Step 3: AI로 감사 인사 생성

### 3. 결과 확인
- **통합 회의록 탭**: 팀 전체 업무 요약
- **감사 인사 탭**: 각 팀원에게 전달할 감사 메시지

### 4. 결과 저장
- "💾 결과 저장" 버튼 클릭
- 저장 위치 선택
- 생성 파일:
  - `회의록_YYMMDD.docx`
  - `감사인사_YYMMDD.docx`

## 파일 구조

```
workflow/
├── main.py                     # 프로그램 진입점
├── requirements.txt            # Python 의존성
├── README.md                   # 본 문서
├── .cursorrules               # 프로젝트 규칙
├── src/
│   ├── document/              # 문서 파싱
│   │   ├── pdf_parser.py
│   │   ├── docx_parser.py
│   │   └── document_parser.py
│   ├── ai/                    # AI 연동
│   │   └── ollama_client.py
│   ├── utils/                 # 유틸리티
│   │   ├── file_selector.py
│   │   └── output_generator.py
│   └── ui/                    # GUI
│       ├── main_window.py
│       └── worker.py
└── tests/                     # 테스트
```

## 문제 해결

### Ollama 연결 오류
- Ollama가 실행 중인지 확인: `ollama serve`
- 모델이 다운로드되었는지 확인: `ollama list`

### 문서 파싱 오류
- PDF/DOCX 파일이 손상되지 않았는지 확인
- 파일에 텍스트가 포함되어 있는지 확인 (이미지만 있는 PDF는 미지원)

### 가상환경 관련
- 가상환경이 활성화되어 있는지 확인
- 터미널 프롬프트에 `(venv)` 표시 확인

## 기술 스택

- **GUI**: PySide6 (Qt for Python)
- **문서 파싱**: PyMuPDF (PDF), python-docx (DOCX)
- **AI**: Ollama (로컬 LLM)
- **언어**: Python 3.8+

## 라이선스

Dentium 내부용

## 개발자

Dentium 개발팀

