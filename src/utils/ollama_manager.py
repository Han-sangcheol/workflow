"""
Ollama 서버 관리
자동 시작 및 상태 확인
"""

import logging
import subprocess
import platform
import time
from typing import Optional

try:
    import requests
except ImportError:
    requests = None

logger = logging.getLogger(__name__)


class OllamaManager:
    """Ollama 서버 관리 클래스"""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.process: Optional[subprocess.Popen] = None

    def is_running(self) -> bool:
        """Ollama 서버 실행 여부 확인"""
        if requests is None:
            return False

        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=2
            )
            return response.status_code == 200
        except Exception:
            return False

    def start_server(self, wait_time: int = 5) -> bool:
        """
        Ollama 서버 시작
        
        Args:
            wait_time: 서버 시작 대기 시간 (초)
            
        Returns:
            시작 성공 여부
        """
        if self.is_running():
            logger.info("Ollama 서버가 이미 실행 중입니다")
            return True

        logger.info("Ollama 서버 자동 시작 시도...")

        try:
            # Ollama 명령어 확인
            if not self._is_ollama_installed():
                logger.warning("Ollama가 설치되지 않았습니다")
                return False

            # OS별 백그라운드 실행
            if platform.system() == "Windows":
                # Windows: 백그라운드로 실행
                self.process = subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                # Linux/Mac: 백그라운드로 실행
                self.process = subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )

            logger.info(f"Ollama 서버 시작됨 (PID: {self.process.pid})")

            # 서버가 준비될 때까지 대기
            for i in range(wait_time * 2):
                time.sleep(0.5)
                if self.is_running():
                    logger.info("Ollama 서버 시작 완료!")
                    return True

            logger.warning("Ollama 서버가 시간 내에 시작되지 않았습니다")
            return False

        except FileNotFoundError:
            logger.error("ollama 명령을 찾을 수 없습니다")
            return False
        except Exception as e:
            logger.error(f"Ollama 서버 시작 실패: {str(e)}")
            return False

    def _is_ollama_installed(self) -> bool:
        """Ollama 설치 여부 확인"""
        try:
            result = subprocess.run(
                ["ollama", "--version"],
                capture_output=True,
                timeout=3
            )
            return result.returncode == 0
        except Exception:
            return False

    def stop_server(self):
        """Ollama 서버 중지"""
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
                logger.info("Ollama 서버 중지됨")
            except Exception as e:
                logger.error(f"Ollama 서버 중지 실패: {e}")
                try:
                    self.process.kill()
                except Exception:
                    pass

    def ensure_running(self) -> bool:
        """
        Ollama 서버가 실행 중인지 확인하고 필요시 시작
        
        Returns:
            서버 실행 여부
        """
        if self.is_running():
            return True

        logger.info("Ollama 서버를 자동으로 시작합니다...")
        return self.start_server()

