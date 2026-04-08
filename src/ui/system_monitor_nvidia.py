"""
NVIDIA GPU 모니터링 (pynvml 사용)
GPUtil 대신 더 안정적인 pynvml 사용
에러 발생 시 반복 로그 방지 및 자동 비활성화
GPU 사용 프로세스 목록 조회 기능 포함
"""

import logging
import subprocess
import sys
from typing import List, Tuple, Optional, Dict

logger = logging.getLogger(__name__)


def _get_subprocess_startupinfo():
    """Windows에서 콘솔 창 숨김을 위한 startupinfo 반환"""
    if sys.platform == 'win32':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        return startupinfo
    return None


def _get_subprocess_creationflags():
    """Windows에서 콘솔 창 생성 방지를 위한 creationflags 반환"""
    if sys.platform == 'win32':
        return subprocess.CREATE_NO_WINDOW
    return 0

try:
    import pynvml
    PYNVML_AVAILABLE = True
except ImportError:
    pynvml = None
    PYNVML_AVAILABLE = False


class NvidiaGPUMonitor:
    """NVIDIA GPU 모니터링 클래스"""

    # 에러 발생 시 비활성화까지의 허용 횟수
    MAX_ERROR_COUNT = 3

    def __init__(self):
        self.initialized = False
        self.device_count = 0
        self._error_count = 0  # 연속 에러 횟수
        self._disabled = False  # 에러로 인한 비활성화 상태
        self._error_logged = False  # 에러 로그 출력 여부 (1회만)
        
        if PYNVML_AVAILABLE:
            try:
                pynvml.nvmlInit()
                self.device_count = pynvml.nvmlDeviceGetCount()
                self.initialized = True
                logger.info(f"NVIDIA GPU {self.device_count}개 초기화 완료")
            except Exception as e:
                logger.warning(f"NVIDIA GPU 초기화 실패: {e}")

    def is_available(self) -> bool:
        """NVIDIA GPU 사용 가능 여부"""
        return self.initialized and self.device_count > 0 and not self._disabled

    def get_gpu_info(self) -> List[Tuple[str, int, int, int]]:
        """
        GPU 정보 가져오기
        
        Returns:
            List of (name, memory_used_mb, memory_total_mb, utilization_percent)
        """
        # 비활성화된 경우 빈 리스트 반환 (로그 없음)
        if self._disabled:
            return []
        
        if not self.initialized or self.device_count == 0:
            return []

        gpu_info = []
        try:
            for i in range(self.device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                
                # GPU 이름
                name = pynvml.nvmlDeviceGetName(handle)
                if isinstance(name, bytes):
                    name = name.decode('utf-8')
                
                # 메모리 정보
                memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                memory_used = memory_info.used // (1024 ** 2)  # MB
                memory_total = memory_info.total // (1024 ** 2)  # MB
                
                # 사용률
                try:
                    utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    gpu_util = utilization.gpu
                except Exception:
                    gpu_util = 0
                
                gpu_info.append((name, memory_used, memory_total, gpu_util))
            
            # 성공하면 에러 카운트 리셋
            self._error_count = 0
        
        except Exception as e:
            self._error_count += 1
            
            # 에러 로그는 1회만 출력
            if not self._error_logged:
                logger.warning(f"GPU 정보 읽기 실패: {e}")
                self._error_logged = True
            
            # 연속 에러 횟수 초과 시 GPU 모니터링 비활성화
            if self._error_count >= self.MAX_ERROR_COUNT:
                self._disabled = True
                logger.info(
                    f"GPU 정보 읽기 {self.MAX_ERROR_COUNT}회 연속 실패 - "
                    "GPU 모니터링을 비활성화합니다."
                )
        
        return gpu_info

    def shutdown(self):
        """pynvml 종료"""
        if self.initialized:
            try:
                pynvml.nvmlShutdown()
                logger.info("NVIDIA GPU 모니터링 종료")
            except Exception as e:
                # 종료 시 에러는 무시 (이미 종료된 상태일 수 있음)
                pass
    
    def get_gpu_processes(self) -> List[Dict]:
        """
        GPU를 사용하는 프로세스 목록 가져오기
        
        Returns:
            List of {"pid": int, "name": str, "type": str}
            - pid: 프로세스 ID
            - name: 프로세스 이름 (짧은 이름)
            - type: 프로세스 타입 (C: Compute, G: Graphics, C+G: 둘 다)
        """
        processes = []
        
        try:
            # Windows에서 콘솔 창 숨김 설정
            startupinfo = _get_subprocess_startupinfo()
            creationflags = _get_subprocess_creationflags()
            
            # nvidia-smi로 프로세스 목록 가져오기
            result = subprocess.run(
                ["nvidia-smi", "--query-compute-apps=pid,process_name", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5,
                startupinfo=startupinfo,
                creationflags=creationflags
            )
            
            if result.returncode == 0 and result.stdout.strip():
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = line.split(', ')
                        if len(parts) >= 2:
                            try:
                                pid = int(parts[0].strip())
                                full_path = parts[1].strip()
                                # 파일 이름만 추출
                                name = full_path.split('\\')[-1] if '\\' in full_path else full_path.split('/')[-1]
                                processes.append({
                                    "pid": pid,
                                    "name": name,
                                    "type": "C"  # Compute
                                })
                            except (ValueError, IndexError):
                                continue
            
            # Graphics 프로세스도 가져오기 (별도 쿼리)
            result_gpu = subprocess.run(
                ["nvidia-smi", "--query-graphics-apps=pid,process_name", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5,
                startupinfo=startupinfo,
                creationflags=creationflags
            )
            
            if result_gpu.returncode == 0 and result_gpu.stdout.strip():
                existing_pids = {p["pid"] for p in processes}
                for line in result_gpu.stdout.strip().split('\n'):
                    if line.strip():
                        parts = line.split(', ')
                        if len(parts) >= 2:
                            try:
                                pid = int(parts[0].strip())
                                full_path = parts[1].strip()
                                name = full_path.split('\\')[-1] if '\\' in full_path else full_path.split('/')[-1]
                                
                                if pid in existing_pids:
                                    # 이미 있으면 타입 업데이트
                                    for p in processes:
                                        if p["pid"] == pid:
                                            p["type"] = "C+G"
                                            break
                                else:
                                    processes.append({
                                        "pid": pid,
                                        "name": name,
                                        "type": "G"  # Graphics
                                    })
                            except (ValueError, IndexError):
                                continue
        
        except FileNotFoundError:
            logger.debug("nvidia-smi를 찾을 수 없습니다")
        except subprocess.TimeoutExpired:
            logger.warning("nvidia-smi 타임아웃")
        except Exception as e:
            logger.debug(f"GPU 프로세스 목록 조회 실패: {e}")
        
        return processes
    
    def get_killable_processes(self) -> List[Dict]:
        """
        종료 가능한 GPU 프로세스 목록 (시스템 프로세스 제외)
        
        Returns:
            종료해도 안전한 프로세스 목록
        """
        # 종료하면 안 되는 시스템 프로세스들
        SYSTEM_PROCESSES = {
            'explorer.exe', 'dwm.exe', 'csrss.exe', 'winlogon.exe',
            'services.exe', 'svchost.exe', 'lsass.exe', 'System',
            'ShellExperienceHost.exe', 'SearchHost.exe', 'StartMenuExperienceHost.exe',
            'TextInputHost.exe', 'ApplicationFrameHost.exe', 'ShellHost.exe',
            'SystemSettings.exe', 'CrossDeviceResume.exe', 'PhoneExperienceHost.exe',
            'msedgewebview2.exe'  # WebView는 다른 앱이 사용할 수 있음
        }
        
        # Ollama는 제외 (사용자가 실행 중인 AI)
        PROTECTED_PROCESSES = {'ollama.exe', 'ollama_llama_server.exe'}
        
        # 기존 인스턴스의 get_gpu_processes 사용 (새 인스턴스 생성 방지)
        all_processes = self.get_gpu_processes()
        
        killable = []
        for proc in all_processes:
            name_lower = proc["name"].lower()
            if name_lower not in {p.lower() for p in SYSTEM_PROCESSES}:
                if name_lower not in {p.lower() for p in PROTECTED_PROCESSES}:
                    killable.append(proc)
        
        return killable

