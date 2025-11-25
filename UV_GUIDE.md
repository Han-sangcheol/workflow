# uv 사용 가이드

## uv란?

**uv**는 Rust로 작성된 매우 빠른 Python 패키지 설치 및 관리 도구입니다.
- pip보다 10-100배 빠름
- 가상환경 생성 및 관리
- 의존성 해결 최적화

## 설치

### Windows
```bash
python -m pip install uv
```

### Linux/Mac
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 설치 확인
```bash
python -m uv --version
# 또는 (PATH에 등록된 경우)
uv --version
```

## 기본 사용법

### 가상환경 생성
```bash
python -m uv venv
# 또는 특정 이름으로
python -m uv venv myenv
```

### 패키지 설치
```bash
# requirements.txt에서 설치
python -m uv pip install -r requirements.txt

# 개별 패키지 설치
python -m uv pip install PySide6

# 특정 버전 설치
python -m uv pip install PySide6==6.6.0
```

### 패키지 업그레이드
```bash
# 모든 패키지 업그레이드
python -m uv pip install -r requirements.txt --upgrade

# 특정 패키지 업그레이드
python -m uv pip install --upgrade PySide6
```

### 패키지 제거
```bash
python -m uv pip uninstall package-name
```

### 설치된 패키지 목록
```bash
python -m uv pip list
```

### requirements.txt 생성
```bash
python -m uv pip freeze > requirements.txt
```

## Windows Store Python 사용 시 주의사항

Windows Store 버전 Python을 사용하는 경우:
- ✅ `python -m uv` 형식으로 실행 (권장)
- ❌ `uv` 직접 실행은 PATH 문제로 작동하지 않을 수 있음

## 본 프로젝트에서의 사용

### 초기 설정
```bash
# 자동 설정 (권장)
.\setup.bat          # Windows
./setup.sh           # Linux/Mac

# 수동 설정
python -m uv venv
python -m uv pip install -r requirements.txt
```

### 가상환경 활성화
```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### 의존성 추가
```bash
# 1. 패키지 설치
python -m uv pip install new-package

# 2. requirements.txt 업데이트
python -m uv pip freeze > requirements.txt

# 3. 다른 환경에서 동기화
python -m uv pip install -r requirements.txt
```

### 개발 의존성
```bash
# 개발용 패키지 설치
python -m uv pip install pytest black flake8 mypy

# 별도 파일로 관리
python -m uv pip freeze | grep -E "pytest|black|flake8|mypy" > requirements-dev.txt
```

## 성능 비교

| 작업 | pip | uv | 개선 |
|------|-----|-----|------|
| 가상환경 생성 | 10초 | 0.1초 | 100배 |
| 의존성 설치 | 45초 | 5초 | 9배 |
| 캐시 재사용 | 20초 | 0.5초 | 40배 |

## 문제 해결

### 'uv' is not recognized 오류 (Windows)
**해결책:** `python -m uv` 형식으로 실행
```bash
# 잘못된 방법
uv venv

# 올바른 방법
python -m uv venv
```

### 가상환경 활성화 실패
```bash
# 가상환경 삭제 후 재생성
rmdir /s /q .venv
python -m uv venv
```

### 패키지 설치 오류
```bash
# 캐시 삭제
python -m uv cache clean

# pip로 폴백
.venv\Scripts\activate     # Windows
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

## uv vs pip

### uv 장점
- ✅ 매우 빠른 속도
- ✅ 더 나은 의존성 해결
- ✅ 병렬 다운로드
- ✅ 효율적인 캐싱

### uv 단점
- ❌ 일부 edge case에서 호환성 문제 가능
- ❌ 상대적으로 새로운 도구

### 언제 pip를 사용할까?
- uv 설치가 불가능한 환경
- 특정 패키지 설치 문제 발생 시
- 레거시 시스템

## 추가 자료

- 공식 문서: https://github.com/astral-sh/uv
- 벤치마크: https://github.com/astral-sh/uv#benchmarks
- 이슈 트래커: https://github.com/astral-sh/uv/issues

## 본 프로젝트 명령어 요약

```bash
# 설치
.\setup.bat              # Windows 자동 설치
./setup.sh               # Linux/Mac 자동 설치

# 실행
.\run.bat                # Windows
./run.sh                 # Linux/Mac

# 패키지 추가
python -m uv pip install package-name
python -m uv pip freeze > requirements.txt

# 업데이트
python -m uv pip install -r requirements.txt --upgrade

# 테스트
.venv\Scripts\activate   # Windows
source .venv/bin/activate # Linux/Mac
pytest tests/
```

## 추가 팁

### uv 업데이트
```bash
python -m pip install --upgrade uv
```

### 가상환경 정보 확인
```bash
.venv\Scripts\activate
python -c "import sys; print(sys.prefix)"
```

### 캐시 관리
```bash
# 캐시 크기 확인
python -m uv cache dir

# 캐시 정리
python -m uv cache clean
```
