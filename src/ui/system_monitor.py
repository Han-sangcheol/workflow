"""
시스템 모니터링 위젯
CPU/GPU 사용량을 실시간으로 표시합니다.
"""

import logging
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
)
from PySide6.QtCore import QTimer, Slot

try:
    import psutil
except ImportError:
    psutil = None

try:
    import GPUtil
    GPU_AVAILABLE = True
except ImportError:
    GPUtil = None
    GPU_AVAILABLE = False

# pynvml을 우선 사용 (더 안정적)
try:
    from .system_monitor_nvidia import NvidiaGPUMonitor
    NVIDIA_AVAILABLE = True
except ImportError:
    NvidiaGPUMonitor = None
    NVIDIA_AVAILABLE = False

logger = logging.getLogger(__name__)


class SystemMonitor(QWidget):
    """시스템 리소스 모니터링 위젯"""

    def __init__(self, update_interval: int = 1000):
        """
        초기화
        
        Args:
            update_interval: 업데이트 간격 (밀리초)
        """
        super().__init__()
        self.update_interval = update_interval
        self.nvidia_monitor = None
        
        # NVIDIA GPU 모니터 초기화 (우선순위 1)
        if NVIDIA_AVAILABLE:
            try:
                self.nvidia_monitor = NvidiaGPUMonitor()
                if self.nvidia_monitor.is_available():
                    logger.info("NVIDIA GPU 모니터링 활성화 (pynvml)")
            except Exception as e:
                logger.warning(f"NVIDIA 모니터 초기화 실패: {e}")
        
        self._init_ui()
        self._start_monitoring()

    def _init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 제목
        title = QLabel("📊 시스템 리소스")
        title.setStyleSheet("font-weight: bold; font-size: 11pt;")
        layout.addWidget(title)
        
        # CPU 전체 사용률
        cpu_layout = QHBoxLayout()
        self.cpu_label = QLabel("CPU 전체:")
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setMaximum(100)
        self.cpu_bar.setTextVisible(True)
        self.cpu_bar.setFormat("%v%")
        cpu_layout.addWidget(self.cpu_label)
        cpu_layout.addWidget(self.cpu_bar)
        layout.addLayout(cpu_layout)
        
        # CPU 코어별 사용률
        if psutil:
            cpu_count = psutil.cpu_count()
            if cpu_count and cpu_count > 1:
                # 코어가 여러 개면 개별 표시
                self.cpu_core_bars = []
                for i in range(min(cpu_count, 8)):  # 최대 8개 코어만 표시
                    core_layout = QHBoxLayout()
                    core_label = QLabel(f"  Core {i}:")
                    core_label.setStyleSheet("font-size: 8pt;")
                    core_bar = QProgressBar()
                    core_bar.setMaximum(100)
                    core_bar.setTextVisible(True)
                    core_bar.setFormat("%v%")
                    core_bar.setMaximumHeight(15)
                    core_layout.addWidget(core_label)
                    core_layout.addWidget(core_bar)
                    layout.addLayout(core_layout)
                    self.cpu_core_bars.append((core_label, core_bar))
            else:
                self.cpu_core_bars = []
        else:
            self.cpu_core_bars = []
        
        # 메모리 모니터링
        mem_layout = QHBoxLayout()
        self.mem_label = QLabel("메모리:")
        self.mem_bar = QProgressBar()
        self.mem_bar.setMaximum(100)
        self.mem_bar.setTextVisible(True)
        self.mem_bar.setFormat("%v%")
        mem_layout.addWidget(self.mem_label)
        mem_layout.addWidget(self.mem_bar)
        layout.addLayout(mem_layout)
        
        # GPU 모니터링 (NVIDIA 우선)
        self.gpu_bars = []
        gpu_detected = False
        
        # 1. NVIDIA GPU (pynvml)
        if self.nvidia_monitor and self.nvidia_monitor.is_available():
            gpu_count = self.nvidia_monitor.device_count
            logger.info(f"NVIDIA GPU {gpu_count}개 감지")
            
            for i in range(gpu_count):
                gpu_layout = QHBoxLayout()
                gpu_label = QLabel(f"GPU {i}:")
                gpu_bar = QProgressBar()
                gpu_bar.setMaximum(100)
                gpu_bar.setTextVisible(True)
                gpu_bar.setFormat("%v%")
                gpu_layout.addWidget(gpu_label)
                gpu_layout.addWidget(gpu_bar)
                layout.addLayout(gpu_layout)
                self.gpu_bars.append((gpu_label, gpu_bar, "nvidia"))
            gpu_detected = True
        
        # 2. GPUtil 폴백 (다른 GPU)
        elif self._is_gpu_available():
            try:
                gpus = GPUtil.getGPUs()
                for i, gpu in enumerate(gpus):
                    gpu_layout = QHBoxLayout()
                    gpu_label = QLabel(f"GPU {i}:")
                    gpu_bar = QProgressBar()
                    gpu_bar.setMaximum(100)
                    gpu_bar.setTextVisible(True)
                    gpu_bar.setFormat("%v%")
                    gpu_layout.addWidget(gpu_label)
                    gpu_layout.addWidget(gpu_bar)
                    layout.addLayout(gpu_layout)
                    self.gpu_bars.append((gpu_label, gpu_bar, gpu.name))
                gpu_detected = True
            except Exception as e:
                logger.debug(f"GPUtil GPU 초기화 실패: {e}")
        
        # 3. GPU 없음
        if not gpu_detected:
            gpu_info = QLabel("ℹ️ GPU 없음 또는 모니터링 미지원")
            gpu_info.setStyleSheet("color: gray; font-size: 8pt;")
            layout.addWidget(gpu_info)
        
        layout.addStretch()

    def _is_gpu_available(self) -> bool:
        """GPU 모니터링 가능 여부 확인"""
        if not GPU_AVAILABLE or GPUtil is None:
            logger.debug("GPUtil 라이브러리를 사용할 수 없습니다")
            return False
        
        try:
            gpus = GPUtil.getGPUs()
            has_gpu = len(gpus) > 0
            if has_gpu:
                logger.info(f"GPU {len(gpus)}개 감지됨")
            else:
                logger.info("시스템에 GPU가 없습니다")
            return has_gpu
        except Exception as e:
            logger.warning(f"GPU 감지 실패: {e}")
            return False

    def _start_monitoring(self):
        """모니터링 시작"""
        if psutil is None:
            logger.warning("psutil이 설치되지 않아 모니터링을 시작할 수 없습니다")
            self.cpu_label.setText("CPU: psutil 필요")
            self.mem_label.setText("메모리: psutil 필요")
            return
        
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_stats)
        self.timer.start(self.update_interval)

    @Slot()
    def _update_stats(self):
        """시스템 통계 업데이트"""
        if psutil is None:
            return
        
        try:
            # CPU 전체 사용률
            cpu_percent = psutil.cpu_percent(interval=0)
            self.cpu_bar.setValue(int(cpu_percent))
            self._update_bar_color(self.cpu_bar, cpu_percent)
            
            # CPU 코어별 사용률
            if self.cpu_core_bars:
                try:
                    per_cpu = psutil.cpu_percent(interval=0, percpu=True)
                    for i, (label, bar) in enumerate(self.cpu_core_bars):
                        if i < len(per_cpu):
                            core_percent = per_cpu[i]
                            bar.setValue(int(core_percent))
                            self._update_bar_color(bar, core_percent)
                except Exception as e:
                    logger.debug(f"코어별 CPU 읽기 실패: {e}")
            
            # 메모리 사용률
            mem = psutil.virtual_memory()
            mem_percent = mem.percent
            self.mem_bar.setValue(int(mem_percent))
            self.mem_label.setText(
                f"메모리: {mem.used // (1024**3)}GB / "
                f"{mem.total // (1024**3)}GB"
            )
            self._update_bar_color(self.mem_bar, mem_percent)
            
            # GPU 사용률 (NVIDIA 우선)
            if self.gpu_bars:
                # NVIDIA GPU (pynvml)
                if self.nvidia_monitor and self.nvidia_monitor.is_available():
                    try:
                        gpu_info_list = self.nvidia_monitor.get_gpu_info()
                        for i, (label, bar, gpu_type) in enumerate(self.gpu_bars):
                            if i < len(gpu_info_list) and gpu_type == "nvidia":
                                name, mem_used, mem_total, util = gpu_info_list[i]
                                bar.setValue(int(util))
                                label.setText(
                                    f"GPU {i} ({name[:12]}): "
                                    f"{mem_used}MB / {mem_total}MB"
                                )
                                self._update_bar_color(bar, util)
                    except Exception as e:
                        logger.debug(f"NVIDIA GPU 정보 읽기 실패: {e}")
                
                # GPUtil 폴백
                elif GPU_AVAILABLE and GPUtil:
                    try:
                        gpus = GPUtil.getGPUs()
                        for i, (label, bar, name) in enumerate(self.gpu_bars):
                            if i < len(gpus):
                                gpu = gpus[i]
                                gpu_percent = gpu.load * 100
                                bar.setValue(int(gpu_percent))
                                label.setText(
                                    f"GPU {i} ({name[:10]}): "
                                    f"{int(gpu.memoryUsed)}MB / {int(gpu.memoryTotal)}MB"
                                )
                                self._update_bar_color(bar, gpu_percent)
                    except Exception as e:
                        logger.debug(f"GPUtil GPU 정보 읽기 실패: {e}")
        
        except Exception as e:
            logger.error(f"시스템 통계 업데이트 오류: {e}")

    def _update_bar_color(self, bar: QProgressBar, value: float):
        """사용률에 따라 프로그레스바 색상 변경"""
        if value < 50:
            color = "#4CAF50"  # 녹색
        elif value < 80:
            color = "#FF9800"  # 주황색
        else:
            color = "#F44336"  # 빨간색
        
        bar.setStyleSheet(f"""
            QProgressBar::chunk {{
                background-color: {color};
            }}
        """)

    def stop_monitoring(self):
        """모니터링 중지"""
        if hasattr(self, 'timer'):
            self.timer.stop()
        
        # NVIDIA 모니터 종료
        if self.nvidia_monitor:
            self.nvidia_monitor.shutdown()

