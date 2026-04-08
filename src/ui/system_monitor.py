"""
시스템 모니터링 위젯
CPU/GPU 사용량을 실시간 그래프로 표시합니다.
"""

import logging
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QProgressBar, QGroupBox, QListWidget, QListWidgetItem
)
from PySide6.QtCore import QTimer, Slot, Qt

from .resource_graph import ResourceGraph, MultiResourceGraph

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
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 제목
        title = QLabel("📊 시스템 리소스")
        title.setStyleSheet("font-weight: bold; font-size: 11pt;")
        layout.addWidget(title)
        
        # === CPU/메모리 그래프 ===
        self.cpu_mem_graph = MultiResourceGraph(
            title="CPU & Memory",
            max_points=60  # 60초 기록
        )
        self.cpu_mem_graph.add_series("CPU", "#00BCD4")   # 시안
        self.cpu_mem_graph.add_series("MEM", "#FF9800")   # 주황
        layout.addWidget(self.cpu_mem_graph)
        
        # CPU 전체 사용률 (프로그레스바)
        cpu_layout = QHBoxLayout()
        self.cpu_label = QLabel("CPU:")
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setMaximum(100)
        self.cpu_bar.setTextVisible(True)
        self.cpu_bar.setFormat("%v%")
        self.cpu_bar.setMaximumHeight(18)
        cpu_layout.addWidget(self.cpu_label)
        cpu_layout.addWidget(self.cpu_bar)
        layout.addLayout(cpu_layout)
        
        # 메모리 모니터링
        mem_layout = QHBoxLayout()
        self.mem_label = QLabel("MEM:")
        self.mem_bar = QProgressBar()
        self.mem_bar.setMaximum(100)
        self.mem_bar.setTextVisible(True)
        self.mem_bar.setFormat("%v%")
        self.mem_bar.setMaximumHeight(18)
        mem_layout.addWidget(self.mem_label)
        mem_layout.addWidget(self.mem_bar)
        layout.addLayout(mem_layout)
        
        # CPU 코어별 사용률 (접힘 가능)
        self.cpu_core_bars = []
        if psutil:
            cpu_count = psutil.cpu_count()
            if cpu_count and cpu_count > 1:
                cores_group = QGroupBox(f"CPU 코어 ({cpu_count}개)")
                cores_group.setStyleSheet("font-size: 8pt;")
                cores_layout = QVBoxLayout(cores_group)
                cores_layout.setSpacing(2)
                
                for i in range(min(cpu_count, 8)):
                    core_layout = QHBoxLayout()
                    core_label = QLabel(f"C{i}:")
                    core_label.setFixedWidth(25)
                    core_bar = QProgressBar()
                    core_bar.setMaximum(100)
                    core_bar.setTextVisible(True)
                    core_bar.setFormat("%v%")
                    core_bar.setMaximumHeight(12)
                    core_layout.addWidget(core_label)
                    core_layout.addWidget(core_bar)
                    cores_layout.addLayout(core_layout)
                    self.cpu_core_bars.append((core_label, core_bar))
                
                layout.addWidget(cores_group)
        
        # === GPU 그래프 ===
        self.gpu_bars = []
        self.gpu_graphs = []
        gpu_detected = False
        
        # 1. NVIDIA GPU (pynvml)
        if self.nvidia_monitor and self.nvidia_monitor.is_available():
            gpu_count = self.nvidia_monitor.device_count
            logger.info(f"NVIDIA GPU {gpu_count}개 감지")
            
            for i in range(gpu_count):
                # GPU 그래프
                gpu_graph = ResourceGraph(
                    title=f"GPU {i}",
                    color="#4CAF50",  # 녹색
                    max_points=60
                )
                layout.addWidget(gpu_graph)
                self.gpu_graphs.append(gpu_graph)
                
                # GPU 프로그레스바
                gpu_layout = QHBoxLayout()
                gpu_label = QLabel(f"GPU {i}:")
                gpu_bar = QProgressBar()
                gpu_bar.setMaximum(100)
                gpu_bar.setTextVisible(True)
                gpu_bar.setFormat("%v%")
                gpu_bar.setMaximumHeight(18)
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
                    # GPU 그래프
                    gpu_graph = ResourceGraph(
                        title=f"GPU {i} ({gpu.name[:10]})",
                        color="#4CAF50",
                        max_points=60
                    )
                    layout.addWidget(gpu_graph)
                    self.gpu_graphs.append(gpu_graph)
                    
                    # GPU 프로그레스바
                    gpu_layout = QHBoxLayout()
                    gpu_label = QLabel(f"GPU {i}:")
                    gpu_bar = QProgressBar()
                    gpu_bar.setMaximum(100)
                    gpu_bar.setTextVisible(True)
                    gpu_bar.setFormat("%v%")
                    gpu_bar.setMaximumHeight(18)
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
        
        # === GPU 프로세스 리스트 ===
        if gpu_detected:
            gpu_proc_group = QGroupBox("🔧 GPU 사용 프로세스")
            gpu_proc_group.setStyleSheet("font-size: 8pt;")
            gpu_proc_layout = QVBoxLayout(gpu_proc_group)
            gpu_proc_layout.setSpacing(2)
            gpu_proc_layout.setContentsMargins(5, 5, 5, 5)
            
            self.gpu_process_list = QListWidget()
            self.gpu_process_list.setMaximumHeight(120)
            self.gpu_process_list.setStyleSheet("""
                QListWidget {
                    font-size: 8pt;
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                    border: 1px solid #3c3c3c;
                }
                QListWidget::item {
                    padding: 2px;
                }
                QListWidget::item:selected {
                    background-color: #264f78;
                }
            """)
            self.gpu_process_list.setToolTip("GPU를 사용 중인 프로세스 목록\n(Ollama, 시스템 프로세스 제외)")
            gpu_proc_layout.addWidget(self.gpu_process_list)
            
            # 프로세스 수 라벨
            self.gpu_proc_count_label = QLabel("프로세스: 0개")
            self.gpu_proc_count_label.setStyleSheet("color: #888; font-size: 7pt;")
            gpu_proc_layout.addWidget(self.gpu_proc_count_label)
            
            layout.addWidget(gpu_proc_group)
        else:
            self.gpu_process_list = None
            self.gpu_proc_count_label = None
        
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
            
            # CPU/메모리 그래프 업데이트
            self.cpu_mem_graph.add_value(0, cpu_percent)
            
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
                f"MEM: {mem.used // (1024**3)}GB / "
                f"{mem.total // (1024**3)}GB"
            )
            self._update_bar_color(self.mem_bar, mem_percent)
            
            # 메모리 그래프 업데이트
            self.cpu_mem_graph.add_value(1, mem_percent)
            
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
                                
                                # GPU 그래프 업데이트
                                if i < len(self.gpu_graphs):
                                    self.gpu_graphs[i].add_value(util)
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
                                
                                # GPU 그래프 업데이트
                                if i < len(self.gpu_graphs):
                                    self.gpu_graphs[i].add_value(gpu_percent)
                    except Exception as e:
                        logger.debug(f"GPUtil GPU 정보 읽기 실패: {e}")
            
            # GPU 프로세스 리스트 업데이트 (5초마다)
            if self.gpu_process_list is not None:
                self._update_gpu_process_list()
        
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

    def _update_gpu_process_list(self):
        """GPU 프로세스 리스트 업데이트 (5초마다)"""
        # 업데이트 주기 조절 (매초 호출되지만 5초마다만 실행)
        if not hasattr(self, '_gpu_proc_update_counter'):
            self._gpu_proc_update_counter = 0
        
        self._gpu_proc_update_counter += 1
        if self._gpu_proc_update_counter < 5:  # 5초마다 업데이트
            return
        self._gpu_proc_update_counter = 0
        
        if self.gpu_process_list is None or self.nvidia_monitor is None:
            return
        
        try:
            # 종료 가능한 프로세스만 가져오기 (기존 인스턴스 사용)
            processes = self.nvidia_monitor.get_killable_processes()
            
            # 리스트 업데이트
            self.gpu_process_list.clear()
            
            for proc in processes:
                # 타입에 따른 아이콘
                type_icon = "🖥️" if proc["type"] == "G" else "⚙️" if proc["type"] == "C" else "🔷"
                item_text = f"{type_icon} {proc['name']} (PID: {proc['pid']})"
                
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, proc)  # 프로세스 정보 저장
                self.gpu_process_list.addItem(item)
            
            # 프로세스 수 업데이트
            if self.gpu_proc_count_label:
                count = len(processes)
                color = "#4CAF50" if count <= 3 else "#FF9800" if count <= 6 else "#F44336"
                self.gpu_proc_count_label.setText(f"종료 가능: {count}개")
                self.gpu_proc_count_label.setStyleSheet(f"color: {color}; font-size: 7pt;")
        
        except Exception as e:
            logger.debug(f"GPU 프로세스 리스트 업데이트 실패: {e}")
    
    def get_selected_process(self) -> Optional[dict]:
        """현재 선택된 GPU 프로세스 정보 반환"""
        if self.gpu_process_list is None:
            return None
        
        current_item = self.gpu_process_list.currentItem()
        if current_item:
            return current_item.data(Qt.ItemDataRole.UserRole)
        return None
    
    def get_all_killable_processes(self) -> list:
        """모든 종료 가능한 GPU 프로세스 목록 반환"""
        if self.nvidia_monitor is None:
            return []
        
        return self.nvidia_monitor.get_killable_processes()

    def stop_monitoring(self):
        """모니터링 중지"""
        if hasattr(self, 'timer'):
            self.timer.stop()
        
        # NVIDIA 모니터 종료
        if self.nvidia_monitor:
            self.nvidia_monitor.shutdown()

