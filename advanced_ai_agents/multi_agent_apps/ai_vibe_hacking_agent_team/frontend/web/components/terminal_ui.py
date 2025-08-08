"""
터미널 UI 컴포넌트 (리팩토링됨 - 순수 UI 로직)
터미널 화면 렌더링, 플로팅 기능 등 순수 UI만 담당
"""

import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
from typing import Dict, Any, List, Optional
from frontend.web.utils.constants import (
    CSS_PATH_TERMINAL,
    CSS_CLASS_TERMINAL_CONTAINER,
    CSS_CLASS_MAC_TERMINAL_HEADER
)


class TerminalUIComponent:
    """터미널 UI 렌더링 컴포넌트"""
    
    def __init__(self):
        """컴포넌트 초기화"""
        self.placeholder = None
    
    def apply_terminal_css(self):
        """터미널 CSS 스타일 적용"""
        try:
            with open(CSS_PATH_TERMINAL, "r", encoding="utf-8") as f:
                css = f.read()
                st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
        except Exception as e:
            print(f"Error loading terminal CSS: {e}")
    
    def create_terminal_header(self) -> str:
        """맥 스타일 터미널 헤더 HTML 생성
        
        Returns:
            str: 터미널 헤더 HTML
        """
        return '''
        <div class="mac-terminal-header">
            <div class="mac-buttons">
                <div class="terminal-header-button red"></div>
                <div class="terminal-header-button yellow"></div>
                <div class="terminal-header-button green"></div>
            </div>
        </div>
        '''
    
    def create_terminal(self, container):
        """터미널 컨테이너 생성
        
        Args:
            container: Streamlit 컨테이너
            
        Returns:
            Streamlit placeholder
        """
        # 맥 스타일 헤더 표시
        container.markdown(self.create_terminal_header(), unsafe_allow_html=True)
        
        # 터미널 컨테이너 생성
        self.placeholder = container.empty()
        
        return self.placeholder
    
    def render_terminal_display(self, terminal_history: List[Dict[str, Any]]):
        """터미널 디스플레이 렌더링
        
        Args:
            terminal_history: 터미널 히스토리 목록
        """
        if not self.placeholder:
            return
        
        terminal_content = ""
        for entry in terminal_history:
            entry_type = entry.get("type", "output")
            content = entry.get("content", "")
            
            if entry_type == "command":
                # 명령어 표시 형식
                terminal_content += (
                    f'<div class="terminal-prompt">'
                    f'<span class="terminal-user">root@kali</span>'
                    f'<span class="terminal-prompt-text">:~$ </span>'
                    f'<span class="terminal-command-text">{content}</span>'
                    f'</div>'
                )
            elif entry_type == "output":
                terminal_content += f'<div class="terminal-output">{content}</div>'
        
        # 커서 추가
        terminal_content += (
            '<div class="terminal-prompt">'
            '<span class="terminal-user">root@kali</span>'
            '<span class="terminal-prompt-text">:~$ </span>'
            '<span class="terminal-cursor"></span>'
            '</div>'
        )
        
        # 터미널 컨테이너 HTML 생성
        terminal_html = f'''
        <div class="{CSS_CLASS_TERMINAL_CONTAINER}" id="terminal-container">
            {terminal_content}
        </div>
        <script type="text/javascript">
        (function() {{
            const terminal = document.getElementById('terminal-container');
            if (terminal) {{
                terminal.scrollTop = terminal.scrollHeight;
            }}
        }})();
        </script>
        '''
        
        # HTML을 플레이스홀더에 적용
        self.placeholder.markdown(terminal_html, unsafe_allow_html=True)
    
    def display_command_entry(self, command: str, timestamp: str = None):
        """단일 명령어 엔트리 표시
        
        Args:
            command: 명령어 텍스트
            timestamp: 타임스탬프 (선택적)
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%H:%M:%S")
        
        st.markdown(
            f'<div class="terminal-prompt">'
            f'<span class="terminal-user">root@kali</span>'
            f'<span class="terminal-prompt-text">:~$ </span>'
            f'<span class="terminal-command-text">{command}</span>'
            f'</div>',
            unsafe_allow_html=True
        )
    
    def display_output_entry(self, output: str):
        """단일 출력 엔트리 표시
        
        Args:
            output: 출력 텍스트
        """
        st.markdown(
            f'<div class="terminal-output">{output}</div>',
            unsafe_allow_html=True
        )
    
    def create_floating_terminal(self, terminal_history: List[Dict[str, Any]]) -> st.container:
        """플로팅 터미널 생성
        
        Args:
            terminal_history: 터미널 히스토리
            
        Returns:
            st.container: 터미널 컨테이너
        """
        from frontend.web.utils.float import float_css_helper
        
        terminal_container = st.container()
        
        with terminal_container:
            # 터미널 CSS 재적용
            self.apply_terminal_css()
            
            # wrapper 클래스를 사용하여 Streamlit 기본 스타일 숨기기
            st.markdown('<div class="terminal-wrapper">', unsafe_allow_html=True)
            
            # 터미널 생성
            self.create_terminal(st.container())
            
            # 터미널 히스토리 렌더링
            self.render_terminal_display(terminal_history)
            
            # wrapper 닫기
            st.markdown('</div>', unsafe_allow_html=True)
            
            # 디버깅 정보 (디버그 모드에서만)
            if st.session_state.get("debug_mode", False):
                st.write(f"Debug - terminal_history: {len(terminal_history)}")
        
        # Floating CSS 적용
        terminal_css = float_css_helper(
            width="350px",
            height="500px",
            right="40px",
            top="50%",
            transform="translateY(-50%)",
            z_index="1000",
            border_radius="12px",
            box_shadow="0 25px 50px -12px rgba(0, 0, 0, 0.25)",
            backdrop_filter="blur(16px)",
            background="linear-gradient(145deg, #1f2937 0%, #111827 100%)",
            border="1px solid #374151",
            max_height="500px",
            overflow_y="auto"
        )
        
        terminal_container.float(terminal_css)
        
        return terminal_container
    
    def create_floating_toggle_button(self, is_visible: bool) -> st.container:
        """플로팅 토글 버튼 생성
        
        Args:
            is_visible: 터미널 표시 여부
            
        Returns:
            st.container: 토글 버튼 컨테이너
        """
        from frontend.web.utils.float import float_css_helper
        
        toggle_container = st.container()
        
        with toggle_container:
            # 터미널 상태에 따른 버튼
            if is_visible:
                button_text = "💻 Hide Terminal"
                button_type = "secondary"
            else:
                button_text = "💻 Show Terminal"
                button_type = "primary"
            
            # 토글 버튼
            if st.button(button_text, type=button_type, use_container_width=True):
                return True  # 토글 이벤트 발생
        
        # Floating CSS 적용
        toggle_css = float_css_helper(
            width="140px",
            right="40px",
            bottom="20px",
            z_index="1001",
            border_radius="12px",
            box_shadow="0 8px 32px rgba(0,0,0,0.12)",
            backdrop_filter="blur(16px)",
            background="rgba(255, 255, 255, 0.9)"
        )
        
        toggle_container.float(toggle_css)
        
        return False  # 토글 이벤트 미발생
    
    def clear_terminal(self):
        """터미널 디스플레이 초기화"""
        if self.placeholder:
            self.placeholder.empty()

    
    def display_terminal_in_container(self, container, terminal_history: List[Dict[str, Any]]):
        """컨테이너 내부에 터미널 표시
        
        Args:
            container: 표시할 컨테이너
            terminal_history: 터미널 히스토리
        """
        with container:
            self.apply_terminal_css()
            # wrapper 클래스 사용
            st.markdown('<div class="terminal-wrapper">', unsafe_allow_html=True)
            placeholder = self.create_terminal(st.container())
            self.render_terminal_display(terminal_history)
            st.markdown('</div>', unsafe_allow_html=True)
    
    def show_terminal_loading(self, message: str = "Loading terminal..."):
        """터미널 로딩 상태 표시
        
        Args:
            message: 로딩 메시지
        """
        if self.placeholder:
            with self.placeholder:
                st.spinner(message)
    
    def show_terminal_error(self, error_msg: str):
        """터미널 에러 상태 표시
        
        Args:
            error_msg: 에러 메시지
        """
        if self.placeholder:
            with self.placeholder:
                st.error(f"Terminal Error: {error_msg}")
    
    def process_structured_messages(self, messages: List[Dict[str, Any]]):
        """구조화된 메시지들을 터미널 형식으로 처리 (replay 기능용)
        
        Args:
            messages: 처리할 메시지 목록
        """
        # terminal_processor를 사용하여 메시지 처리
        try:
            from frontend.web.core.terminal_processor import get_terminal_processor
            terminal_processor = get_terminal_processor()
            
            # 터미널 히스토리 초기화
            terminal_processor.initialize_terminal_state()
            
            # 메시지 처리
            terminal_entries = terminal_processor.process_structured_messages(messages)
            
            # 터미널 히스토리 업데이트
            if terminal_entries:
                terminal_processor.update_terminal_history(terminal_entries)
            
            # 터미널 히스토리를 인스턴스 변수로 저장 (replay에서 사용)
            if not hasattr(self, 'terminal_history'):
                self.terminal_history = []
            self.terminal_history = terminal_processor.get_terminal_history()
            
        except Exception as e:
            # 에러 발생 시 빈 리스트로 초기화
            if not hasattr(self, 'terminal_history'):
                self.terminal_history = []
            print(f"Error processing structured messages: {e}")


# Helper 함수들
def load_terminal_css():
    """터미널 CSS 로드 (전역 함수)"""
    try:
        with open(CSS_PATH_TERMINAL, "r", encoding="utf-8") as f:
            css_content = f.read()
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    except Exception as e:
        print(f"Warning: Could not load terminal.css: {e}")


def create_floating_terminal(terminal_ui_component, terminal_history: List[Dict[str, Any]]):
    """플로팅 터미널 생성 (전역 함수)
    
    Args:
        terminal_ui_component: TerminalUIComponent 인스턴스
        terminal_history: 터미널 히스토리
        
    Returns:
        st.container: 터미널 컨테이너
    """
    return terminal_ui_component.create_floating_terminal(terminal_history)


def create_floating_toggle_button(terminal_ui_component, is_visible: bool):
    """플로팅 토글 버튼 생성 (전역 함수)
    
    Args:
        terminal_ui_component: TerminalUIComponent 인스턴스
        is_visible: 터미널 표시 여부
        
    Returns:
        bool: 토글 이벤트 발생 여부
    """
    return terminal_ui_component.create_floating_toggle_button(is_visible)