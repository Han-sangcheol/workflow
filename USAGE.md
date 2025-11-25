# 사용 가이드

## 빠른 시작

### 1. 설치

**Windows:**
```bash
setup.bat
```

**Linux/Mac:**
```bash
chmod +x setup.sh run.sh
./setup.sh
```

### 2. 실행

**Windows:**
```bash
run.bat
```

**Linux/Mac:**
```bash
./run.sh
```

## 상세 사용법

### 업무일지 파일 준비

업무일지 파일은 다음 형식을 지원합니다:
- PDF (.pdf)
- Word 문서 (.docx, .doc)

**권장 파일명 형식:**
```
팀원이름_251125.pdf
업무일지_251125.docx
```

날짜는 YYMMDD 형식 (예: 251125 = 2025년 11월 25일)

### 파일 선택 방법

#### 방법 1: 폴더 선택 + 자동 검색
1. "폴더 선택" 버튼 클릭
2. 업무일지가 있는 폴더 선택
3. "오늘 날짜로 자동 검색" 체크박스 활성화
4. 오늘 날짜(YYMMDD)가 파일명에 포함된 파일만 자동 선택됨

#### 방법 2: 폴더 선택 + 수동 확인
1. "폴더 선택" 버튼 클릭
2. "오늘 날짜로 자동 검색" 체크박스 해제
3. 폴더 내 모든 PDF/DOCX 파일이 표시됨

#### 방법 3: 파일 직접 선택
1. "파일 직접 선택" 버튼 클릭
2. 원하는 파일들을 선택 (다중 선택 가능)

### 분석 실행

1. 파일 선택 후 "🚀 분석 시작" 버튼 클릭
2. 진행 상황 확인:
   - **Step 1**: 문서 텍스트 추출
   - **Step 2**: AI로 통합 회의록 생성
   - **Step 3**: AI로 감사 인사 생성
3. 분석 완료 후 결과 탭에서 확인

### 결과 저장

1. "💾 결과 저장" 버튼 클릭
2. 저장할 폴더 선택
3. 자동으로 생성되는 파일:
   - `회의록_YYMMDD.docx`
   - `감사인사_YYMMDD.docx`

## Ollama 설정

### 설치 확인
```bash
ollama --version
```

### 모델 다운로드
```bash
ollama pull llama3.2
```

### 서버 실행
```bash
ollama serve
```

### 다른 모델 사용 (선택사항)

코드 수정이 필요합니다:

`src/ai/ollama_client.py` 파일에서:
```python
def __init__(
    self,
    base_url: str = "http://localhost:11434",
    model: str = "llama3.2",  # 여기를 변경
    timeout: int = 120
):
```

사용 가능한 모델 예시:
- `llama3.2` (추천, 빠르고 정확)
- `llama3`
- `mistral`
- `gemma`

## 문제 해결

### "Ollama 서버에 연결할 수 없습니다"
- Ollama가 실행 중인지 확인: `ollama serve`
- 방화벽 설정 확인
- 포트 11434가 사용 가능한지 확인

### "회의록 생성 실패"
- Ollama 모델이 다운로드되었는지 확인: `ollama list`
- 모델이 없다면: `ollama pull llama3.2`
- 시스템 메모리가 충분한지 확인 (최소 8GB RAM 권장)

### "문서를 읽을 수 없습니다"
- PDF/DOCX 파일이 손상되지 않았는지 확인
- 파일에 실제 텍스트가 있는지 확인 (이미지만 있는 PDF는 미지원)
- 파일 권한 확인

### 가상환경 관련 오류
```bash
# Windows
venv\Scripts\activate.bat

# Linux/Mac
source venv/bin/activate
```

## 성능 팁

### AI 생성 속도 개선
- GPU가 있는 경우 Ollama GPU 버전 사용
- 더 작은 모델 사용 (속도 우선)
- 더 큰 모델 사용 (품질 우선)

### 메모리 사용량 감소
- 한 번에 처리하는 파일 수 줄이기
- 더 작은 AI 모델 사용

## 테스트 실행

```bash
# 가상환경 활성화 후
pytest tests/ -v
```

## 로그 확인

프로그램 실행 시 `workflow.log` 파일에 상세 로그가 기록됩니다.

```bash
# Windows
type workflow.log

# Linux/Mac
cat workflow.log
```

