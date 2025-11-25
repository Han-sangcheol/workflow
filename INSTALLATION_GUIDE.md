# 설치 가이드

## 사전 요구사항

### 1. Python 설치
- **버전**: Python 3.8 이상 필요
- **다운로드**: https://www.python.org/downloads/
- **설치 확인**:
  ```bash
  python --version
  # 또는
  python3 --version
  ```

### 2. Ollama 설치

#### Windows
1. https://ollama.ai 방문
2. Windows용 인스톨러 다운로드
3. 설치 실행
4. 설치 확인:
   ```bash
   ollama --version
   ```

#### Linux
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

#### macOS
```bash
# Homebrew 사용
brew install ollama

# 또는 공식 인스톤러 사용
# https://ollama.ai에서 다운로드
```

### 3. AI 모델 다운로드

```bash
# 기본 모델 (권장)
ollama pull llama3.2

# 설치 확인
ollama list
```

## 프로젝트 설치

### 방법 1: 자동 설치 스크립트 (권장)

#### Windows
```bash
# 프로젝트 디렉토리에서
setup.bat
```

#### Linux/Mac
```bash
# 실행 권한 부여
chmod +x setup.sh run.sh

# 설치 실행
./setup.sh
```

### 방법 2: 수동 설치

#### 1단계: 가상환경 생성
```bash
# Windows
python -m venv venv

# Linux/Mac
python3 -m venv venv
```

#### 2단계: 가상환경 활성화
```bash
# Windows (Command Prompt)
venv\Scripts\activate.bat

# Windows (PowerShell)
venv\Scripts\Activate.ps1

# Linux/Mac
source venv/bin/activate
```

#### 3단계: 의존성 설치
```bash
pip install -r requirements.txt
```

## 설치 확인

### 1. Python 패키지 확인
```bash
# 가상환경 활성화 후
pip list
```

다음 패키지들이 보여야 합니다:
- PySide6
- PyMuPDF
- python-docx
- requests
- pytest

### 2. Ollama 서버 시작
```bash
# 새 터미널에서
ollama serve
```

### 3. 프로그램 실행 테스트
```bash
# Windows
run.bat

# Linux/Mac
./run.sh
```

## 문제 해결

### Python 버전 오류
```bash
# Python 버전 확인
python --version

# 3.8 미만이면 최신 버전 설치
```

### 가상환경 활성화 오류 (Windows PowerShell)
```powershell
# PowerShell 실행 정책 변경
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### pip 설치 오류
```bash
# pip 업그레이드
python -m pip install --upgrade pip

# 의존성 재설치
pip install -r requirements.txt --upgrade
```

### Ollama 연결 오류
```bash
# 1. Ollama 서비스 시작
ollama serve

# 2. 모델 확인
ollama list

# 3. 모델 없으면 다운로드
ollama pull llama3.2

# 4. 테스트
ollama run llama3.2 "안녕하세요"
```

### 방화벽 오류
- Windows Defender 방화벽에서 Ollama 허용
- 포트 11434 열기

## 삭제 방법

### 프로그램 삭제
```bash
# 가상환경 폴더 삭제
rm -rf venv  # Linux/Mac
rmdir /s venv  # Windows

# 프로젝트 폴더 전체 삭제
```

### Ollama 삭제

#### Windows
- 제어판 > 프로그램 추가/제거 > Ollama 제거

#### Linux
```bash
sudo systemctl stop ollama
sudo rm /usr/local/bin/ollama
sudo rm -rf /usr/share/ollama
```

#### macOS
```bash
brew uninstall ollama
```

## 업데이트

### 프로그램 업데이트
```bash
# 가상환경 활성화 후
pip install -r requirements.txt --upgrade
```

### Ollama 업데이트
```bash
# 모델 재다운로드
ollama pull llama3.2

# 버전 확인
ollama --version
```

## 개발자용 설치

### 추가 개발 도구
```bash
pip install black flake8 mypy
```

### 테스트 실행
```bash
pytest tests/ -v --cov=src
```

---

**도움말**: 설치 중 문제가 발생하면 `USAGE.md`의 문제 해결 섹션을 참고하세요.

