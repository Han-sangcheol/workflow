"""
GPU 진단 도구
GPU 종류를 파악하고 모니터링 가능 여부를 확인합니다.
"""

import sys
import platform

print("=" * 60)
print("GPU 진단 도구")
print("=" * 60)
print()

# 1. 시스템 정보
print("[1] 시스템 정보")
print(f"  OS: {platform.system()} {platform.release()}")
print(f"  Python: {sys.version}")
print()

# 2. GPUtil 테스트
print("[2] GPUtil 테스트")
try:
    import GPUtil
    print("  ✅ GPUtil 설치됨:", GPUtil.__version__ if hasattr(GPUtil, '__version__') else "버전 확인 불가")
    
    try:
        gpus = GPUtil.getGPUs()
        print(f"  감지된 GPU: {len(gpus)}개")
        
        if gpus:
            for i, gpu in enumerate(gpus):
                print(f"\n  GPU {i}:")
                print(f"    이름: {gpu.name}")
                print(f"    ID: {gpu.id}")
                print(f"    메모리: {gpu.memoryTotal}MB")
                print(f"    드라이버: {gpu.driver}")
                print(f"    사용률: {gpu.load * 100:.1f}%")
        else:
            print("  ⚠️ GPU가 감지되지 않음")
    except Exception as e:
        print(f"  ❌ GPU 정보 읽기 실패: {e}")
        
except ImportError:
    print("  ❌ GPUtil이 설치되지 않음")
print()

# 3. nvidia-smi 확인 (NVIDIA GPU)
print("[3] NVIDIA GPU 확인 (nvidia-smi)")
try:
    import subprocess
    result = subprocess.run(
        ["nvidia-smi"],
        capture_output=True,
        text=True,
        timeout=5
    )
    
    if result.returncode == 0:
        print("  ✅ NVIDIA GPU 감지됨")
        lines = result.stdout.split('\n')
        for line in lines:
            if 'NVIDIA' in line or 'GeForce' or 'RTX' in line or 'GTX' in line:
                print(f"    {line.strip()}")
    else:
        print("  ⚠️ nvidia-smi 실행 실패")
        print(f"    {result.stderr[:200]}")
except FileNotFoundError:
    print("  ℹ️ nvidia-smi를 찾을 수 없음 (NVIDIA GPU 없음 또는 드라이버 미설치)")
except Exception as e:
    print(f"  ❌ 오류: {e}")
print()

# 4. wmi를 통한 GPU 확인 (Windows)
if platform.system() == "Windows":
    print("[4] Windows GPU 정보 (WMI)")
    try:
        import subprocess
        result = subprocess.run(
            ["wmic", "path", "win32_VideoController", "get", "name"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            print("  감지된 GPU:")
            for line in lines[1:]:  # 첫 줄은 헤더
                if line.strip():
                    print(f"    - {line.strip()}")
        else:
            print("  ⚠️ WMI 쿼리 실패")
    except Exception as e:
        print(f"  ❌ 오류: {e}")
    print()

# 5. py3nvml 테스트 (NVIDIA 전용)
print("[5] py3nvml 테스트 (NVIDIA 전용 라이브러리)")
try:
    import pynvml
    
    print("  ✅ pynvml 설치됨")
    try:
        pynvml.nvmlInit()
        device_count = pynvml.nvmlDeviceGetCount()
        print(f"  감지된 NVIDIA GPU: {device_count}개")
        
        for i in range(device_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            name = pynvml.nvmlDeviceGetName(handle)
            memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
            
            print(f"\n  GPU {i}:")
            print(f"    이름: {name}")
            print(f"    메모리: {memory_info.total // (1024**2)}MB")
            print(f"    사용 중: {memory_info.used // (1024**2)}MB")
            print(f"    GPU 사용률: {utilization.gpu}%")
        
        pynvml.nvmlShutdown()
    except Exception as e:
        print(f"  ❌ pynvml 초기화 실패: {e}")
        
except ImportError:
    print("  ℹ️ pynvml 미설치 (설치: pip install pynvml)")
print()

# 6. DirectX 정보 (Windows)
if platform.system() == "Windows":
    print("[6] DirectX 진단 (dxdiag)")
    print("  수동으로 확인하려면 'dxdiag' 명령 실행")
    print()

# 7. 권장 사항
print("=" * 60)
print("권장 사항")
print("=" * 60)

print("""
1. NVIDIA GPU가 있는 경우:
   - nvidia-smi가 작동하면: pip install pynvml
   - pynvml로 모니터링 가능
   
2. AMD GPU가 있는 경우:
   - GPUtil은 AMD를 지원하지 않음
   - 대안: wmi (Windows) 또는 rocm-smi (Linux)
   
3. Intel 내장 그래픽만 있는 경우:
   - GPUtil 지원 제한적
   - CPU 모니터링으로 충분
   
4. GPUtil이 작동하지 않으면:
   - NVIDIA의 경우: pynvml 사용 권장
   - 기타: GPU 모니터링 비활성화 (정상)
""")

print("진단 완료!")

