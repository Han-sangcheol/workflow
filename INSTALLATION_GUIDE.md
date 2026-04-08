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

### 2. AI 서버 설치 (택 1)

본 프로그램은 다음 AI 서버 중 **하나 이상**을 선택하여 사용합니다.
각 단계별로 다른 AI 제공자를 사용할 수 있습니다.

---

#### 옵션 A: Ollama (기본 - 권장)

**설치**

| 플랫폼 | 설치 방법 |
|--------|----------|
| Windows | https://ollama.ai → 인스톨러 다운로드 → 실행 |
| Linux | `curl -fsSL https://ollama.ai/install.sh \| sh` |
| macOS | `brew install ollama` 또는 공식 사이트에서 다운로드 |

**설치 확인**
```bash
ollama --version
```

**모델 다운로드**
```bash
ollama pull llama3.2        # 기본 모델
ollama pull gemma3:12b      # 대안 모델
ollama list                 # 설치 확인
```

**서버 시작** (자동 시작되지 않는 경우)
```bash
ollama serve
```

- **기본 포트**: 11434
- **API 키**: 불필요
- 💡 프로그램이 Ollama 서버를 자동 감지하고 시작합니다

---

#### 옵션 B: LM Studio

**설치**
1. https://lmstudio.ai/ 방문
2. OS에 맞는 버전 다운로드
3. 설치 실행
4. 프로그램 내에서 원하는 모델 다운로드 (예: Llama 3, Mistral, Gemma 등)

**서버 시작 방법**
```
1. LM Studio 프로그램 실행
2. 좌측 메뉴에서 💻 Local Server 탭 클릭
3. 상단 드롭다운에서 사용할 모델 선택
4. Start Server 버튼 클릭
5. 상태가 "Running on port 1234"로 표시되면 성공
```

- **기본 포트**: 1234
- **API 키**: 불필요

---

#### 옵션 C: Jan (⚠️ API 키 필수)

**설치**
1. https://jan.ai/ 방문
2. OS에 맞는 버전 다운로드
3. 설치 실행
4. 프로그램 내 Model Hub에서 원하는 모델 다운로드

**서버 시작 방법** ⚠️ API 키 설정 필수
```
1. Jan 프로그램 실행
2. 좌측 하단 ⚙️ Settings 클릭
3. Advanced Settings → Local API Server 섹션 찾기
4. API Server 토글 ON
5. ⚠️ API Key 항목에 키 입력 (예: jan-local-key)
   - 반드시 입력해야 연결됩니다!
   - 프로그램 기본값: jan-local-key
6. Server 주소: 127.0.0.1 또는 localhost
7. 포트: 1337 (기본값)
8. Start Server 클릭
```

- **기본 포트**: 1337
- **⚠️ API 키**: 필수 (프로그램 기본값: `jan-local-key`)

---

> 💡 **참고**: 세 가지 도구 비교
> | 도구 | 특징 | 난이도 |
> |------|------|--------|
> | Ollama | CLI 친화적, 가벼움, 자동 시작 | ⭐ 쉬움 |
> | LM Studio | GUI 친화적, 모델 관리 편리 | ⭐⭐ 보통 |
> | Jan | 채팅 UI 포함, API 키 설정 필요 | ⭐⭐⭐ 약간 복잡 |

### 3. AI 모델 다운로드 (Ollama 사용 시)

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

### LM Studio 연결 오류
1. **프로그램 실행 확인**: LM Studio가 실행 중인지 확인
2. **서버 시작 확인**: Local Server 탭에서 "Running" 상태인지 확인
3. **모델 선택 확인**: 상단 드롭다운에서 모델이 선택되어 있는지 확인
4. **포트 확인**: 기본 포트 1234 사용 중인지 확인

### Jan 연결 오류 ⚠️ 가장 흔한 문제: API 키 미설정
```
체크리스트:
1. Settings → Local API Server → API Server 토글 ON 확인
2. ⚠️ API Key 입력 확인 (빈 값이면 연결 거부!)
   - 기본값: jan-local-key
3. Start Server 버튼 클릭 확인
4. 프로그램에서 🔄 모델 새로고침 클릭
```

**Jan API 키 설정 방법**:
1. Jan → Settings → Advanced Settings → Local API Server
2. API Key 항목에 `jan-local-key` 입력
3. Start Server 클릭
4. 프로그램에서 Jan 제공자 선택 시 자동 연결

### 방화벽 오류
- Windows Defender 방화벽에서 각 AI 서버 허용
- 포트 허용: Ollama(11434), LM Studio(1234), Jan(1337)

## 삭제 방법

### 프로그램 삭제
```bash
# 가상환경 폴더 삭제
rm -rf venv  # Linux/Mac
rmdir /s venv  # Windows

# 프로젝트 폴더 전체 삭제
```

### AI 서버 삭제

#### Ollama 삭제
| 플랫폼 | 삭제 방법 |
|--------|----------|
| Windows | 제어판 → 프로그램 추가/제거 → Ollama 제거 |
| Linux | `sudo systemctl stop ollama && sudo rm /usr/local/bin/ollama` |
| macOS | `brew uninstall ollama` |

#### LM Studio 삭제
| 플랫폼 | 삭제 방법 |
|--------|----------|
| Windows | 제어판 → 프로그램 추가/제거 → LM Studio 제거 |
| macOS | 응용 프로그램 폴더에서 LM Studio 휴지통으로 이동 |

#### Jan 삭제
| 플랫폼 | 삭제 방법 |
|--------|----------|
| Windows | 제어판 → 프로그램 추가/제거 → Jan 제거 |
| macOS | 응용 프로그램 폴더에서 Jan 휴지통으로 이동 |

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

