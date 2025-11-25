"""
NVIDIA GPU 모니터링 (pynvml 사용)
GPUtil 대신 더 안정적인 pynvml 사용
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

    def __init__(self):
        self.initialized = False
        self.device_count = 0
        
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
        return self.initialized and self.device_count > 0

    def get_gpu_info(self) -> List[Tuple[str, int, int, int]]:
        """
        GPU 정보 가져오기
        
        Returns:
            List of (name, memory_used_mb, memory_total_mb, utilization_percent)
        """
        if not self.is_available():
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
        
        except Exception as e:
            logger.error(f"GPU 정보 읽기 실패: {e}")
        
        return gpu_info

    def shutdown(self):
        """pynvml 종료"""
        if self.initialized:
            try:
                pynvml.nvmlShutdown()
                logger.info("NVIDIA GPU 모니터링 종료")
            except Exception as e:
                logger.error(f"pynvml 종료 실패: {e}")

