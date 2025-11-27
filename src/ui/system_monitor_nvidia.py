"""
NVIDIA GPU 모니터링 (pynvml 사용)
GPUtil 대신 더 안정적인 pynvml 사용
에러 발생 시 반복 로그 방지 및 자동 비활성화
"""

import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

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

