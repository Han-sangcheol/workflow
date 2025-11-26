"""
사용 설명서 다이얼로그
Ollama 설치, GPU 설정, 프로그램 사용법을 안내합니다.
"""

import logging

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QTextBrowser, QLabel, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl

logger = logging.getLogger(__name__)


class HelpDialog(QDialog):
    """사용 설명서 다이얼로그"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("📖 사용 설명서")
        self.setMinimumSize(700, 550)
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # 탭 위젯
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget, stretch=1)
        
        # 탭 추가
        self.tab_widget.addTab(self._create_overview_tab(), "🏠 개요")
        self.tab_widget.addTab(self._create_ollama_tab(), "🤖 Ollama 설치")
        self.tab_widget.addTab(self._create_gpu_tab(), "🎮 GPU 설정")
        self.tab_widget.addTab(self._create_usage_tab(), "📝 사용 방법")
        self.tab_widget.addTab(self._create_troubleshoot_tab(), "🔧 문제 해결")
        
        # 닫기 버튼
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("닫기")
        close_btn.setStyleSheet("font-size: 11pt; padding: 8px 20px;")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _create_text_browser(self, html_content: str) -> QTextBrowser:
        """텍스트 브라우저 생성"""
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml(html_content)
        browser.setStyleSheet(
            "font-size: 10pt; padding: 10px; "
            "background-color: #FAFAFA;"
        )
        return browser
    
    def _create_overview_tab(self) -> QWidget:
        """개요 탭"""
        html = """
        <h2>🏠 업무일지 AI 분석 시스템</h2>
        
        <p>이 프로그램은 팀원들의 일일 업무일지(PDF, DOCX)를 분석하여 
        <b>통합 회의록</b>과 <b>감사 인사</b>를 자동으로 생성합니다.</p>
        
        <h3>📋 주요 기능</h3>
        <ul>
            <li><b>문서 파싱</b>: PDF, DOCX 파일에서 텍스트 추출</li>
            <li><b>텍스트 정리</b>: AI가 업무 내용을 구조화</li>
            <li><b>회의록 생성</b>: 프로젝트별 통합 회의록 작성</li>
            <li><b>감사 인사</b>: 팀원별 개인화된 감사 메시지 생성</li>
        </ul>
        
        <h3>⚙️ 필수 요구사항</h3>
        <ul>
            <li><b>Ollama</b>: 로컬 AI 엔진 (필수)</li>
            <li><b>AI 모델</b>: llama3.2 또는 다른 모델</li>
            <li><b>NVIDIA GPU</b>: 빠른 처리를 위해 권장</li>
        </ul>
        
        <h3>🚀 빠른 시작</h3>
        <ol>
            <li>Ollama 설치 (다음 탭 참조)</li>
            <li>AI 모델 다운로드: <code>ollama pull llama3.2</code></li>
            <li>프로그램 실행</li>
            <li>업무일지 파일 선택</li>
            <li>"분석 시작" 버튼 클릭</li>
        </ol>
        """
        return self._create_text_browser(html)
    
    def _create_ollama_tab(self) -> QWidget:
        """Ollama 설치 탭"""
        html = """
        <h2>🤖 Ollama 설치 방법</h2>
        
        <p>Ollama는 로컬에서 AI 모델을 실행하는 엔진입니다. 
        이 프로그램을 사용하려면 <b>반드시 Ollama가 설치</b>되어 있어야 합니다.</p>
        
        <h3>📥 다운로드</h3>
        <p>공식 사이트에서 다운로드: 
        <a href="https://ollama.ai">https://ollama.ai</a></p>
        
        <h3>🖥️ Windows 설치</h3>
        <ol>
            <li>위 사이트에서 <b>"Download for Windows"</b> 클릭</li>
            <li>다운로드된 <code>OllamaSetup.exe</code> 실행</li>
            <li>설치 마법사 따라 진행</li>
            <li>설치 완료 후 자동으로 시스템 트레이에 실행됨</li>
        </ol>
        
        <h3>🔧 AI 모델 다운로드</h3>
        <p>Ollama 설치 후, 터미널(PowerShell)에서 모델을 다운로드합니다:</p>
        
        <pre style="background: #2D2D2D; color: #FFF; padding: 10px; border-radius: 5px;">
# 권장 모델 (약 2GB)
ollama pull llama3.2

# 경량 모델 (약 1.3GB) - 메모리가 부족한 경우
ollama pull llama3.2:1b

# 고성능 모델 (약 4GB) - GPU가 좋은 경우
ollama pull llama3:8b
        </pre>
        
        <h3>✅ 설치 확인</h3>
        <p>터미널에서 다음 명령어로 설치된 모델을 확인합니다:</p>
        <pre style="background: #2D2D2D; color: #FFF; padding: 10px; border-radius: 5px;">
ollama list
        </pre>
        
        <h3>▶️ 서버 실행</h3>
        <p>프로그램이 자동으로 Ollama 서버를 시작하지만, 수동으로 실행하려면:</p>
        <pre style="background: #2D2D2D; color: #FFF; padding: 10px; border-radius: 5px;">
ollama serve
        </pre>
        
        <h3>⚠️ 주의사항</h3>
        <ul>
            <li>첫 번째 모델 다운로드는 인터넷 속도에 따라 시간이 걸릴 수 있습니다</li>
            <li>모델은 <code>C:\\Users\\[사용자]\\.ollama\\models</code>에 저장됩니다</li>
            <li>디스크 공간이 충분한지 확인하세요 (최소 5GB 권장)</li>
        </ul>
        """
        return self._create_text_browser(html)
    
    def _create_gpu_tab(self) -> QWidget:
        """GPU 설정 탭"""
        html = """
        <h2>🎮 GPU 설정 및 드라이버 설치</h2>
        
        <p>NVIDIA GPU를 사용하면 AI 처리 속도가 <b>5~10배</b> 빨라집니다.
        GPU를 활용하려면 올바른 드라이버가 설치되어 있어야 합니다.</p>
        
        <h3>🔍 GPU 확인</h3>
        <p>내 PC의 GPU를 확인하는 방법:</p>
        <ol>
            <li>Windows 키 + R → <code>dxdiag</code> 입력</li>
            <li>"디스플레이" 탭에서 GPU 모델 확인</li>
            <li>또는 작업 관리자 → 성능 → GPU 확인</li>
        </ol>
        
        <h3>📥 NVIDIA 드라이버 설치</h3>
        <p><b>권장 드라이버 버전: 550.x 이상</b></p>
        
        <ol>
            <li>NVIDIA 드라이버 다운로드 페이지 방문:
            <a href="https://www.nvidia.com/download/index.aspx">https://www.nvidia.com/download/index.aspx</a></li>
            <li>GPU 모델 선택 (예: GeForce RTX 4060, RTX A4000 등)</li>
            <li>운영체제: Windows 10/11 64-bit 선택</li>
            <li>다운로드 타입: <b>Game Ready Driver</b> 또는 <b>Studio Driver</b></li>
            <li>다운로드 후 설치 (재부팅 필요)</li>
        </ol>
        
        <h3>✅ 드라이버 버전 확인</h3>
        <p>터미널에서 다음 명령어 실행:</p>
        <pre style="background: #2D2D2D; color: #FFF; padding: 10px; border-radius: 5px;">
nvidia-smi
        </pre>
        <p>우측 상단에 "Driver Version: 5XX.XX" 표시 확인</p>
        
        <h3>⚡ GPU 사용 확인 (Ollama)</h3>
        <p>Ollama가 GPU를 사용하는지 확인:</p>
        <pre style="background: #2D2D2D; color: #FFF; padding: 10px; border-radius: 5px;">
ollama ps
        </pre>
        <p>출력에서 <b>"100% GPU"</b> 또는 유사한 표시 확인</p>
        
        <h3>🔧 GPU 관련 환경 변수 (선택)</h3>
        <p>Ollama GPU 사용을 강제하려면:</p>
        <pre style="background: #2D2D2D; color: #FFF; padding: 10px; border-radius: 5px;">
# PowerShell에서
$env:CUDA_VISIBLE_DEVICES = "0"
ollama serve
        </pre>
        
        <h3>⚠️ GPU 미인식 시 체크리스트</h3>
        <ul>
            <li>드라이버 버전이 550.x 이상인지 확인</li>
            <li>CUDA가 설치되어 있는지 확인 (드라이버에 포함됨)</li>
            <li>Ollama를 완전히 종료 후 재시작</li>
            <li>PC 재부팅</li>
            <li>최신 Ollama 버전으로 업데이트</li>
        </ul>
        
        <h3>💡 CPU만 사용하는 경우</h3>
        <p>GPU가 없거나 설정이 어려운 경우에도 CPU로 동작합니다.
        다만 처리 시간이 더 오래 걸립니다.</p>
        """
        return self._create_text_browser(html)
    
    def _create_usage_tab(self) -> QWidget:
        """사용 방법 탭"""
        html = """
        <h2>📝 프로그램 사용 방법</h2>
        
        <h3>1️⃣ 파일 선택</h3>
        <ul>
            <li><b>폴더 선택</b>: 폴더 내 모든 업무일지 자동 검색</li>
            <li><b>파일 직접 선택</b>: 특정 파일만 선택</li>
            <li><b>오늘 날짜 자동 검색</b>: 파일명에 오늘 날짜가 포함된 파일만 선택</li>
        </ul>
        
        <h3>2️⃣ PDF 추출 모드</h3>
        <ul>
            <li><b>smart (권장)</b>: 표 형식 문서에 최적화</li>
            <li><b>layout</b>: 복잡한 레이아웃 보존</li>
            <li><b>simple</b>: 빠른 기본 추출</li>
        </ul>
        
        <h3>3️⃣ AI 모델 선택</h3>
        <ul>
            <li><b>정리용 모델</b>: 원본 텍스트를 구조화하는 모델</li>
            <li><b>작성용 모델</b>: 회의록과 감사 인사를 생성하는 모델</li>
            <li>동일한 모델을 사용해도 되고, 다른 모델을 선택해도 됩니다</li>
        </ul>
        
        <h3>4️⃣ 분석 시작</h3>
        <p>"🚀 분석 시작" 버튼을 클릭하면 4단계로 처리됩니다:</p>
        <ol>
            <li><b>Step 1</b>: 문서 파일에서 텍스트 추출</li>
            <li><b>Step 2</b>: AI로 텍스트 정리 및 구조화</li>
            <li><b>Step 3</b>: 통합 회의록 생성</li>
            <li><b>Step 4</b>: 감사 인사 생성</li>
        </ol>
        
        <h3>5️⃣ 결과 확인</h3>
        <p>하단 탭에서 각 단계의 결과를 확인할 수 있습니다:</p>
        <ul>
            <li><b>원본 텍스트</b>: 파일에서 추출된 텍스트</li>
            <li><b>정리된 텍스트</b>: AI가 구조화한 텍스트</li>
            <li><b>통합 회의록</b>: 생성된 회의록</li>
            <li><b>감사 인사</b>: 팀원별 감사 메시지</li>
        </ul>
        
        <h3>6️⃣ 결과 저장</h3>
        <p>"💾 결과 저장" 버튼으로 DOCX 파일로 저장합니다.</p>
        
        <h3>📝 프롬프트 편집</h3>
        <p>"📝 프롬프트 편집" 버튼으로 AI 프롬프트를 직접 수정할 수 있습니다.
        회의록 양식이나 출력 형식을 변경하고 싶을 때 사용하세요.</p>
        """
        return self._create_text_browser(html)
    
    def _create_troubleshoot_tab(self) -> QWidget:
        """문제 해결 탭"""
        html = """
        <h2>🔧 문제 해결</h2>
        
        <h3>❌ "Ollama 서버 연결 실패" 오류</h3>
        <p><b>원인</b>: Ollama가 실행되지 않음</p>
        <p><b>해결</b>:</p>
        <ol>
            <li>시스템 트레이에서 Ollama 아이콘 확인</li>
            <li>터미널에서 <code>ollama serve</code> 실행</li>
            <li>"모델 목록 새로고침" 버튼 클릭</li>
        </ol>
        
        <h3>❌ 모델 목록이 비어있음</h3>
        <p><b>원인</b>: 모델이 설치되지 않음</p>
        <p><b>해결</b>:</p>
        <pre style="background: #2D2D2D; color: #FFF; padding: 10px; border-radius: 5px;">
ollama pull llama3.2
        </pre>
        
        <h3>❌ 처리 속도가 너무 느림</h3>
        <p><b>원인</b>: GPU를 사용하지 않고 CPU로만 처리 중</p>
        <p><b>해결</b>:</p>
        <ul>
            <li>NVIDIA 드라이버 업데이트 (550.x 이상)</li>
            <li>Ollama 재시작</li>
            <li>경량 모델 사용: <code>ollama pull llama3.2:1b</code></li>
        </ul>
        
        <h3>❌ PDF 텍스트 추출이 이상함</h3>
        <p><b>원인</b>: PDF 형식이 복잡하거나 스캔 이미지</p>
        <p><b>해결</b>:</p>
        <ul>
            <li>PDF 추출 모드를 "layout"으로 변경</li>
            <li>원본 DOCX 파일이 있다면 DOCX 사용</li>
        </ul>
        
        <h3>❌ 회의록 형식이 원하는 대로 안 나옴</h3>
        <p><b>해결</b>:</p>
        <ul>
            <li>"📝 프롬프트 편집"에서 프롬프트 수정</li>
            <li>원하는 양식을 프롬프트에 직접 명시</li>
        </ul>
        
        <h3>❌ 메모리 부족 오류</h3>
        <p><b>원인</b>: RAM 또는 GPU 메모리 부족</p>
        <p><b>해결</b>:</p>
        <ul>
            <li>다른 프로그램 종료</li>
            <li>경량 모델 사용: <code>llama3.2:1b</code></li>
        </ul>
        
        <h3>❌ 한글이 깨져서 출력됨</h3>
        <p><b>해결</b>:</p>
        <ul>
            <li>파일 인코딩을 UTF-8로 확인</li>
            <li>최신 AI 모델 사용 (llama3.2 권장)</li>
        </ul>
        
        <h3>📞 추가 지원</h3>
        <ul>
            <li>Ollama 공식 문서: <a href="https://ollama.ai">https://ollama.ai</a></li>
            <li>GitHub 이슈: <a href="https://github.com/Han-sangcheol/workflow">https://github.com/Han-sangcheol/workflow</a></li>
        </ul>
        """
        return self._create_text_browser(html)

