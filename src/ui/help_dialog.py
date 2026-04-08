"""
사용 설명서 다이얼로그
AI 서버(Ollama/LM Studio/Jan) 설치, GPU 설정, 프로그램 사용법을 안내합니다.
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
        self.tab_widget.addTab(self._create_recommend_tab(), "⭐ 추천 설정")
        self.tab_widget.addTab(self._create_overview_tab(), "🏠 개요")
        self.tab_widget.addTab(self._create_ai_server_tab(), "🤖 AI 서버 설치")
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
    
    def _create_recommend_tab(self) -> QWidget:
        """추천 설정 탭"""
        html = """
        <h2>⭐ 추천 AI 제공자 및 설정</h2>
        
        <p style="background: #E8F5E9; padding: 15px; border-radius: 8px; border-left: 4px solid #4CAF50;">
        <b>🥇 1순위 추천 조합</b><br>
        • <b>텍스트 정리</b>: Jan + Dark-Desires-12B (긴 텍스트 구조화에 강함)<br>
        • <b>나머지 단계</b>: Ollama + gemma3:12b (요약/생성에 탁월)
        </p>
        
        <hr>
        
        <h3>🏆 추천 설정</h3>
        
        <table border="1" cellpadding="8" style="border-collapse: collapse; width: 100%; margin: 10px 0;">
            <tr style="background: #1976D2; color: white;">
                <th>단계</th>
                <th>AI 제공자</th>
                <th>추천 모델</th>
                <th>설명</th>
            </tr>
            <tr style="background: #FFF3E0;">
                <td><b>1️⃣ 텍스트 정리</b></td>
                <td><b>Jan</b></td>
                <td><code>Dark-Desires-12B</code></td>
                <td>구조화 능력 우수, 긴 텍스트 처리</td>
            </tr>
            <tr style="background: #E3F2FD;">
                <td><b>2️⃣ 회의록 생성</b></td>
                <td>Ollama</td>
                <td><code>gemma3:12b</code></td>
                <td>요약 및 정리 능력 탁월</td>
            </tr>
            <tr style="background: #E3F2FD;">
                <td><b>3️⃣ 감사 인사</b></td>
                <td>Ollama</td>
                <td><code>gemma3:12b</code></td>
                <td>자연스러운 문장 생성</td>
            </tr>
            <tr style="background: #E3F2FD;">
                <td><b>4️⃣ 개발 현황</b></td>
                <td>Ollama</td>
                <td><code>gemma3:12b</code></td>
                <td>간결한 요약</td>
            </tr>
        </table>
        
        <p style="background: #FFF3E0; padding: 10px; border-radius: 5px; border-left: 4px solid #FF9800;">
        <b>💡 참고</b>: 텍스트 정리 단계는 Jan + Dark-Desires 모델이 긴 원본 텍스트 처리에 효과적입니다.<br>
        Jan 사용 시 <b>API 키 설정이 필수</b>입니다. (기본값: <code>jan-local-key</code>)
        </p>
        
        <h3>📥 추천 모델 설치</h3>
        
        <p><b>Ollama 모델</b> (터미널에서 실행):</p>
        <pre style="background: #2D2D2D; color: #FFF; padding: 15px; border-radius: 5px;">ollama pull gemma3:12b      # 고성능 (약 7GB) - 추천
ollama pull llama3.2        # 범용 (약 2GB) - 대안</pre>
        
        <p><b>Jan 모델</b> (프로그램 내에서 설치):</p>
        <ol>
            <li>Jan 프로그램 실행</li>
            <li>좌측 <b>Model Hub</b> 클릭</li>
            <li><b>Dark-Desires-12B</b> 검색 후 다운로드</li>
        </ol>
        
        <hr>
        
        <h3>🔌 AI 제공자별 연결 정보</h3>
        
        <table border="1" cellpadding="8" style="border-collapse: collapse; width: 100%; margin: 10px 0;">
            <tr style="background: #333; color: white;">
                <th>제공자</th>
                <th>URL</th>
                <th>포트</th>
                <th>API 키</th>
            </tr>
            <tr style="background: #E8F5E9;">
                <td><b>🥇 Ollama</b></td>
                <td>http://localhost</td>
                <td><b>11434</b></td>
                <td>불필요 ✅</td>
            </tr>
            <tr>
                <td>🥈 LM Studio</td>
                <td>http://localhost</td>
                <td><b>1234</b></td>
                <td>불필요 ✅</td>
            </tr>
            <tr>
                <td>🥉 Jan</td>
                <td>http://localhost</td>
                <td><b>1337</b></td>
                <td><span style="color: red;"><b>필수!</b></span> (jan-local-key)</td>
            </tr>
        </table>
        
        <hr>
        
        <h3>💡 빠른 시작 가이드</h3>
        
        <ol style="line-height: 2;">
            <li><b>Ollama 설치</b>: <a href="https://ollama.ai">https://ollama.ai</a> → 모델: <code>ollama pull gemma3:12b</code></li>
            <li><b>Jan 설치</b>: <a href="https://jan.ai">https://jan.ai</a> → Model Hub에서 Dark-Desires-12B 다운로드</li>
            <li><b>Jan API 키 설정</b>: Settings → Local API Server → API Key에 <code>jan-local-key</code> 입력</li>
            <li><b>프로그램 실행</b></li>
            <li><b>단계별 설정</b>:
                <ul>
                    <li>1️⃣ 텍스트 정리: <b>Jan</b> / Dark-Desires</li>
                    <li>2️⃣~4️⃣ 나머지: <b>Ollama</b> / gemma3:12b</li>
                </ul>
            </li>
            <li><b>분석 시작!</b></li>
        </ol>
        
        <hr>
        
        <h3>⚠️ 주의사항</h3>
        <ul>
            <li><b>GPU 권장</b>: NVIDIA GPU가 있으면 처리 속도가 5~10배 빨라집니다</li>
            <li><b>디스크 공간</b>: 모델당 2~7GB 필요 (최소 10GB 여유 권장)</li>
            <li><b>메모리</b>: RAM 16GB 이상, GPU VRAM 8GB 이상 권장</li>
        </ul>
        
        <p style="background: #FFF3E0; padding: 15px; border-radius: 8px; border-left: 4px solid #FF9800;">
        <b>💡 팁</b>: 메모리가 부족하면 <code>llama3.2:1b</code> 경량 모델을 사용하세요.
        품질은 약간 떨어지지만 안정적으로 동작합니다.
        </p>
        """
        return self._create_text_browser(html)
    
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
            <li><b>개발 현황</b>: 오전/오후 개발현황 메시지 생성</li>
        </ul>
        
        <h3>⚙️ 필수 요구사항</h3>
        <ul>
            <li><b>AI 서버</b>: 다음 중 하나 이상 필요
                <ul>
                    <li><b>Ollama</b> (권장) - 가벼움, 자동 시작</li>
                    <li><b>LM Studio</b> - GUI 친화적</li>
                    <li><b>Jan</b> - 채팅 UI 포함 (API 키 필수)</li>
                </ul>
            </li>
            <li><b>NVIDIA GPU</b>: 빠른 처리를 위해 권장 (선택)</li>
        </ul>
        
        <h3>🔌 단계별 AI 제공자 선택</h3>
        <p>각 분석 단계마다 <b>다른 AI 제공자와 모델</b>을 선택할 수 있습니다:</p>
        <ul>
            <li>1️⃣ 텍스트 정리: Ollama / gemma3:12b</li>
            <li>2️⃣ 회의록 생성: Jan / Dark-Desires</li>
            <li>3️⃣ 감사 인사: Ollama / llama3.2</li>
            <li>4️⃣ 개발 현황: LM Studio / mistral</li>
        </ul>
        
        <h3>🚀 빠른 시작</h3>
        <ol>
            <li>AI 서버 설치 (다음 탭 참조)</li>
            <li>AI 모델 다운로드</li>
            <li>프로그램 실행</li>
            <li>각 단계별 AI 제공자/모델 선택</li>
            <li>업무일지 파일 선택</li>
            <li>"분석 시작" 버튼 클릭</li>
        </ol>
        """
        return self._create_text_browser(html)
    
    def _create_ai_server_tab(self) -> QWidget:
        """AI 서버 설치 탭"""
        html = """
        <h2>🤖 AI 서버 설치 방법</h2>
        
        <p>다음 AI 서버 중 <b>하나 이상</b>을 설치하세요. 
        각 단계별로 다른 AI 제공자를 사용할 수 있습니다.</p>
        
        <hr>
        
        <h3>🦙 옵션 A: Ollama (권장)</h3>
        <p><b>특징</b>: 가벼움, CLI 친화적, 자동 시작 지원</p>
        
        <p><b>📥 다운로드</b>: <a href="https://ollama.ai">https://ollama.ai</a></p>
        
        <p><b>설치 방법</b>:</p>
        <ol>
            <li>"Download for Windows" 클릭</li>
            <li><code>OllamaSetup.exe</code> 실행</li>
            <li>설치 완료 후 시스템 트레이에 자동 실행</li>
        </ol>
        
        <p><b>모델 다운로드</b> (터미널에서):</p>
        <pre style="background: #2D2D2D; color: #FFF; padding: 10px; border-radius: 5px;">ollama pull llama3.2      # 권장 (약 2GB)
ollama pull gemma3:12b    # 고성능 (약 7GB)</pre>
        
        <p><b>기본 포트</b>: 11434 | <b>API 키</b>: 불필요</p>
        <p>💡 프로그램이 자동으로 Ollama 서버를 감지하고 시작합니다</p>
        
        <hr>
        
        <h3>💻 옵션 B: LM Studio</h3>
        <p><b>특징</b>: GUI 친화적, 모델 관리 편리</p>
        
        <p><b>📥 다운로드</b>: <a href="https://lmstudio.ai">https://lmstudio.ai</a></p>
        
        <p><b>설치 방법</b>:</p>
        <ol>
            <li>OS에 맞는 버전 다운로드 후 설치</li>
            <li>프로그램 내에서 원하는 모델 다운로드</li>
        </ol>
        
        <p><b>🔌 서버 시작 방법</b>:</p>
        <ol>
            <li>LM Studio 프로그램 실행</li>
            <li>좌측 메뉴에서 <b>💻 Local Server</b> 탭 클릭</li>
            <li>상단 드롭다운에서 사용할 모델 선택</li>
            <li><b>Start Server</b> 버튼 클릭</li>
            <li>"Running on port 1234" 표시 확인</li>
        </ol>
        
        <p><b>기본 포트</b>: 1234 | <b>API 키</b>: 불필요</p>
        
        <hr>
        
        <h3>🤖 옵션 C: Jan (⚠️ API 키 필수)</h3>
        <p><b>특징</b>: 채팅 UI 포함, 초보자 친화적</p>
        
        <p><b>📥 다운로드</b>: <a href="https://jan.ai">https://jan.ai</a></p>
        
        <p><b>설치 방법</b>:</p>
        <ol>
            <li>OS에 맞는 버전 다운로드 후 설치</li>
            <li>프로그램 내 Model Hub에서 모델 다운로드</li>
        </ol>
        
        <p><b>🔌 서버 시작 방법</b> (⚠️ API 키 설정 필수!):</p>
        <ol>
            <li>Jan 프로그램 실행</li>
            <li>좌측 하단 <b>⚙️ Settings</b> 클릭</li>
            <li><b>Advanced Settings</b> → <b>Local API Server</b> 섹션</li>
            <li>API Server 토글 <b>ON</b></li>
            <li style="color: #FF6B6B;"><b>⚠️ API Key 항목에 키 입력 (예: jan-local-key)</b></li>
            <li>Server 주소: 127.0.0.1, 포트: 1337</li>
            <li><b>Start Server</b> 클릭</li>
        </ol>
        
        <p><b>기본 포트</b>: 1337 | <b>⚠️ API 키</b>: 필수 (기본값: <code>jan-local-key</code>)</p>
        
        <hr>
        
        <h3>📊 AI 서버 비교</h3>
        <table border="1" cellpadding="5" style="border-collapse: collapse; width: 100%;">
            <tr style="background: #333; color: #FFF;">
                <th>도구</th><th>특징</th><th>포트</th><th>API 키</th><th>난이도</th>
            </tr>
            <tr><td>Ollama</td><td>CLI, 자동 시작</td><td>11434</td><td>불필요</td><td>⭐ 쉬움</td></tr>
            <tr><td>LM Studio</td><td>GUI, 모델 관리</td><td>1234</td><td>불필요</td><td>⭐⭐ 보통</td></tr>
            <tr><td>Jan</td><td>채팅 UI</td><td>1337</td><td>필수</td><td>⭐⭐⭐ 복잡</td></tr>
        </table>
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
        
        <h3>❌ Ollama 연결 실패</h3>
        <p><b>원인</b>: Ollama가 실행되지 않음</p>
        <p><b>해결</b>:</p>
        <ol>
            <li>시스템 트레이에서 Ollama 아이콘 확인</li>
            <li>터미널에서 <code>ollama serve</code> 실행</li>
            <li>"🔄 모델 새로고침" 버튼 클릭</li>
        </ol>
        
        <h3>❌ LM Studio 연결 실패</h3>
        <p><b>원인</b>: 서버가 시작되지 않음</p>
        <p><b>해결</b>:</p>
        <ol>
            <li>LM Studio 프로그램이 실행 중인지 확인</li>
            <li><b>Local Server</b> 탭에서 "Running" 상태 확인</li>
            <li>상단 드롭다운에서 모델이 선택되어 있는지 확인</li>
            <li>포트가 1234인지 확인</li>
        </ol>
        
        <h3 style="color: #FF6B6B;">❌ Jan 연결 실패 (가장 흔한 문제)</h3>
        <p><b>원인</b>: <span style="color: #FF6B6B;"><b>API 키가 설정되지 않음!</b></span></p>
        <p><b>해결</b>:</p>
        <ol>
            <li>Jan → Settings → Advanced Settings → Local API Server</li>
            <li>API Server 토글 <b>ON</b> 확인</li>
            <li style="color: #FF6B6B;"><b>⚠️ API Key에 "jan-local-key" 입력 (필수!)</b></li>
            <li>Start Server 클릭</li>
            <li>프로그램에서 "🔄 모델 새로고침" 클릭</li>
        </ol>
        <p style="background: #FFF3CD; padding: 10px; border-radius: 5px;">
        💡 <b>Jan API 키 기본값</b>: <code>jan-local-key</code><br>
        프로그램에서 이 키를 자동으로 사용합니다.
        </p>
        
        <h3>❌ 모델 목록이 비어있음</h3>
        <p><b>원인</b>: 모델이 설치되지 않음</p>
        <p><b>해결</b> (Ollama의 경우):</p>
        <pre style="background: #2D2D2D; color: #FFF; padding: 10px; border-radius: 5px;">ollama pull llama3.2</pre>
        
        <h3>❌ 처리 속도가 너무 느림</h3>
        <p><b>원인</b>: GPU를 사용하지 않고 CPU로만 처리 중</p>
        <p><b>해결</b>:</p>
        <ul>
            <li>NVIDIA 드라이버 업데이트 (550.x 이상)</li>
            <li>AI 서버 재시작</li>
            <li>경량 모델 사용: <code>llama3.2:1b</code></li>
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
        
        <h3>📞 추가 지원</h3>
        <ul>
            <li>Ollama: <a href="https://ollama.ai">https://ollama.ai</a></li>
            <li>LM Studio: <a href="https://lmstudio.ai">https://lmstudio.ai</a></li>
            <li>Jan: <a href="https://jan.ai">https://jan.ai</a></li>
        </ul>
        """
        return self._create_text_browser(html)

