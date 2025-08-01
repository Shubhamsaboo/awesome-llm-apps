"""
테마 UI 컴포넌트 (리팩토링됨 - 순수 UI 로직)
테마 토글 버튼, 테마 CSS 적용 등 테마 관련 UI 렌더링
"""

import streamlit as st
from pathlib import Path
from typing import Dict, Any, Optional, Callable


class ThemeUIComponent:
    """테마 UI 컴포넌트"""
    
    def __init__(self):
        """컴포넌트 초기화"""
        # 프로젝트 루트 경로 찾기
        self.base_path = Path(__file__).parent
        while not (self.base_path / "pyproject.toml").exists() and self.base_path.parent != self.base_path:
            self.base_path = self.base_path.parent
        
        self.css_dir = self.base_path / "frontend" / "static" / "css"
    
    def load_theme_css(self, theme: str = "dark") -> str:
        """테마 CSS 로드
        
        Args:
            theme: 테마 이름 ("dark" 또는 "light")
            
        Returns:
            str: CSS 내용
        """
        css_file = self.css_dir / f"{theme}_theme.css"
        
        try:
            with open(css_file, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"테마 CSS 파일 로드 오류: {str(e)}")
            return ""
    
    def apply_theme_css(self, theme: str = "dark"):
        """테마 CSS 적용
        
        Args:
            theme: 적용할 테마 ("dark" 또는 "light")
        """
        css = self.load_theme_css(theme)
        
        if css:
            # 테마별 색상 변수 계산
            colors = self._get_theme_colors(theme)
            
            # 기본 테마 CSS 적용
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
            
            # 추가 오버라이드 CSS 적용
            override_css = self._generate_theme_overrides(colors, theme)
            st.markdown(override_css, unsafe_allow_html=True)
            
            # 다른 CSS 파일들도 로드
            self._load_additional_css_files()
    
    def _get_theme_colors(self, theme: str) -> Dict[str, str]:
        """테마별 색상 정의
        
        Args:
            theme: 테마 이름
            
        Returns:
            Dict: 색상 정의
        """
        if theme == "dark":
            return {
                "sidebar_bg": "#0B0B12",
                "sidebar_text": "#FAFAFA",
                "toggle_bg": "#1E1E1E",
                "toggle_text": "#FFFFFF",
                "toggle_border": "rgba(255, 255, 255, 0.2)",
                "button_bg": "#262730",
                "button_text": "#FAFAFA",
                "button_border": "#404040",
                "button_hover_bg": "#404040",
                "button_hover_text": "#FFFFFF",
                "button_active_bg": "#FF4B4B",
                "button_active_text": "#FFFFFF",
                "agent_bg": "linear-gradient(to right, #222222, #2d2d2d, #222222)",
                "agent_border": "transparent",
                "agent_text": "#FAFAFA",
                "agent_hover_bg": "linear-gradient(to right, #262626, #323232, #262626)",
                "active_bg": "linear-gradient(to right, #3a1515, #4a1f1f, #3a1515)",
                "active_border": "#ff4b4b",
                "active_shadow": "rgba(255, 75, 75, 0.9)",
                "active_text_shadow": "rgba(255, 75, 75, 0.8)",
                "completed_bg": "linear-gradient(to right, #152315, #1e3a1e, #152315)",
                "completed_border": "#4CAF50",
                "header_text": "#F0F0F0",
                "header_border": "rgba(255, 255, 255, 0.1)",
                "message_bg": "rgba(45, 45, 45, 0.5)",
                "terminal_bg": "#1E1E1E",
                "terminal_text": "#FFFFFF",
                "terminal_header_bg": "#333333",
                "terminal_header_text": "#FFFFFF",
                "terminal_prompt": "#4EC9B0",
                "terminal_command": "#DCDCAA",
                "terminal_output": "#CCCCCC",
                "terminal_cursor": "#FFFFFF",
                "terminal_shadow": "rgba(0, 0, 0, 0.5)",
                "chat_container_bg": "#262730",
                "chat_input_bg": "#1E1E1E",
                "chat_input_text": "#FAFAFA",
                "chat_border": "#404040"
            }
        else:  # light theme
            return {
                "sidebar_bg": "#F0F2F6",
                "sidebar_text": "#31333F",
                "toggle_bg": "#F0F2F6",
                "toggle_text": "#31333F",
                "toggle_border": "rgba(49, 51, 63, 0.2)",
                "button_bg": "#FFFFFF",
                "button_text": "#31333F",
                "button_border": "#DFE2E6",
                "button_hover_bg": "#E8EAF0",
                "button_hover_text": "#31333F",
                "button_active_bg": "#FF4B4B",
                "button_active_text": "#FFFFFF",
                "agent_bg": "linear-gradient(to right, #F0F2F6, #FFFFFF, #F0F2F6)",
                "agent_border": "#DFE2E6",
                "agent_text": "#31333F",
                "agent_hover_bg": "linear-gradient(to right, #E8EAF0, #F5F7F9, #E8EAF0)",
                "active_bg": "linear-gradient(to right, #FFF0F0, #FFF5F5, #FFF0F0)",
                "active_border": "#FF4B4B",
                "active_shadow": "rgba(255, 75, 75, 0.6)",
                "active_text_shadow": "rgba(255, 75, 75, 0.4)",
                "completed_bg": "linear-gradient(to right, #F0FFF0, #F5FFF5, #F0FFF0)",
                "completed_border": "#4CAF50",
                "header_text": "#31333F",
                "header_border": "rgba(0, 0, 0, 0.1)",
                "message_bg": "rgba(240, 242, 246, 0.5)",
                "terminal_bg": "#F5F5F5",
                "terminal_text": "#333333",
                "terminal_header_bg": "#E0E0E0",
                "terminal_header_text": "#333333",
                "terminal_prompt": "#0B7285",
                "terminal_command": "#AD8400",
                "terminal_output": "#555555",
                "terminal_cursor": "#333333",
                "terminal_shadow": "rgba(0, 0, 0, 0.1)",
                "chat_container_bg": "#FFFFFF",
                "chat_input_bg": "#F0F2F6",
                "chat_input_text": "#31333F",
                "chat_border": "#DFE2E6"
            }
    
    def _generate_theme_overrides(self, colors: Dict[str, str], theme: str) -> str:
        """테마 오버라이드 CSS 생성
        
        Args:
            colors: 색상 정의
            theme: 테마 이름
            
        Returns:
            str: CSS 문자열
        """
        animation_name = "pulse-button-dark" if theme == "dark" else "pulse-button-light"
        
        return f'''
        <style id="custom-theme-overrides">
        /* Streamlit 테마 오버라이드 - 강력한 선택자 사용 */
        
        /* 사이드바 메인 배경 */
        section[data-testid="stSidebar"] > div,
        section[data-testid="stSidebar"] > div > div,
        section[data-testid="stSidebar"] > div > div > div,
        section[data-testid="stSidebar"] div.st-emotion-cache-*,
        .st-emotion-cache-*[data-testid="stSidebar"] {{
            background-color: {colors["sidebar_bg"]} !important;
            color: {colors["sidebar_text"]} !important;
        }}
        
        /* 사이드바 내부 요소 */
        section[data-testid="stSidebar"] h1, 
        section[data-testid="stSidebar"] h2, 
        section[data-testid="stSidebar"] h3, 
        section[data-testid="stSidebar"] h4, 
        section[data-testid="stSidebar"] h5, 
        section[data-testid="stSidebar"] h6,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] div,
        section[data-testid="stSidebar"] label {{
            color: {colors["sidebar_text"]} !important;
        }}
        
        /* 사이드바 버튼 스타일 */
        section[data-testid="stSidebar"] button,
        section[data-testid="stSidebar"] .stButton > button {{
            background-color: {colors["button_bg"]} !important;
            color: {colors["button_text"]} !important;
            border: 1px solid {colors["button_border"]} !important;
            border-radius: 6px !important;
            padding: 8px 16px !important;
            font-weight: 500 !important;
            transition: all 0.2s ease !important;
            width: 100% !important;
            box-sizing: border-box !important;
            min-height: 40px !important;
        }}
        
        /* 사이드바 버튼 호버 효과 */
        section[data-testid="stSidebar"] button:hover,
        section[data-testid="stSidebar"] .stButton > button:hover {{
            background-color: {colors["button_hover_bg"]} !important;
            color: {colors["button_hover_text"]} !important;
            border-color: {colors["button_border"]} !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
        }}
        
        /* 에이전트 상태 컨테이너 스타일 */
        .agent-status {{
            display: flex;
            align-items: center;
            margin-bottom: 10px;
            padding: 8px 12px;
            border-radius: 5px;
            background: {colors["agent_bg"]} !important;
            transition: all 0.3s ease;
            border: 1px solid {colors["agent_border"]} !important;
            font-size: 18px;
            color: {colors["agent_text"]} !important;
            box-shadow: none !important;
        }}
        
        .agent-status div {{
            color: {colors["agent_text"]} !important;
            font-size: 18px !important;
        }}
        
        .agent-status:hover {{
            background: {colors["agent_hover_bg"]} !important;
        }}
        
        .agent-status.status-active {{
            background: {colors["active_bg"]} !important;
            border: 2px solid {colors["active_border"]} !important;
            box-shadow: 0 0 15px {colors["active_shadow"]} !important;
            animation: {animation_name} 1.5s infinite alternate;
            font-weight: bold;
            text-shadow: 0 0 10px {colors["active_text_shadow"]};
        }}
        
        .agent-status.status-completed {{
            background: {colors["completed_bg"]} !important;
            border: 2px solid {colors["completed_border"]} !important;
        }}
        
        /* 채팅 메시지 헤더 스타일 */
        .agent-header {{
            font-size: 24px !important;
            font-weight: 600;
            color: {colors["header_text"]} !important;
            margin-bottom: 10px;
            padding-bottom: 8px;
            border-bottom: 1px solid {colors["header_border"]} !important;
            position: relative;
        }}
        
        /* 애니메이션 정의 */
        @keyframes pulse-button-dark {{
            0% {{
                background-color: rgba(255, 75, 75, 0.2);
                box-shadow: 0 0 0 0 rgba(255, 75, 75, 0.7);
            }}
            50% {{
                background-color: rgba(255, 75, 75, 0.4);
                box-shadow: 0 0 20px 5px rgba(255, 75, 75, 0.9);
            }}
            100% {{
                background-color: rgba(255, 75, 75, 0.2);
                box-shadow: 0 0 0 0 rgba(255, 75, 75, 0);
            }}
        }}
        
        @keyframes pulse-button-light {{
            0% {{
                background-color: rgba(255, 75, 75, 0.15);
                box-shadow: 0 0 0 0 rgba(255, 75, 75, 0.5);
                border-color: rgba(255, 75, 75, 0.7);
            }}
            50% {{
                background-color: rgba(255, 75, 75, 0.3);
                box-shadow: 0 0 20px 5px rgba(255, 75, 75, 0.8);
                border-color: rgba(255, 75, 75, 1);
            }}
            100% {{
                background-color: rgba(255, 75, 75, 0.15);
                box-shadow: 0 0 0 0 rgba(255, 75, 75, 0);
                border-color: rgba(255, 75, 75, 0.7);
            }}
        }}
        </style>
        '''
    
    def _load_additional_css_files(self):
        """추가 CSS 파일들 로드"""
        css_files = [
            "layout.css",
            "model_info.css", 
            "input_fix.css"
        ]
        
        for css_file in css_files:
            css_path = self.css_dir / css_file
            if css_path.exists():
                try:
                    with open(css_path, "r", encoding="utf-8") as f:
                        css = f.read()
                    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
                except Exception as e:
                    print(f"CSS 파일 로드 오류 ({css_file}): {e}")
    
    def create_theme_toggle(
        self,
        container=None,
        current_theme: str = "dark",
        callback: Optional[Callable] = None
    ) -> bool:
        """테마 토글 버튼 생성
        
        Args:
            container: 표시할 컨테이너 (기본값: st)
            current_theme: 현재 테마
            callback: 테마 변경 콜백 함수
            
        Returns:
            bool: 테마가 변경되었는지 여부
        """
        if container is None:
            container = st
        
        theme_label = "🌙 Dark" if current_theme == "dark" else "☀️ Light"
        is_dark = current_theme == "dark"
        
        # 토글 버튼
        toggle_value = container.toggle(
            theme_label,
            value=is_dark,
            key="theme_toggle"
        )
        
        # 값이 변경되었는지 확인
        if toggle_value != is_dark:
            new_theme = "dark" if toggle_value else "light"
            
            if callback:
                callback(new_theme)
            
            return True
        
        return False
    
    def show_theme_preview(self, theme: str = "dark"):
        """테마 미리보기 표시
        
        Args:
            theme: 미리보기할 테마
        """
        colors = self._get_theme_colors(theme)
        
        st.markdown(f"""
        ### 🎨 {theme.title()} Theme Preview
        
        <div style="
            background: {colors['agent_bg']};
            border: 1px solid {colors['agent_border']};
            border-radius: 8px;
            padding: 16px;
            margin: 16px 0;
        ">
            <div style="color: {colors['agent_text']}; font-weight: bold;">
                Sample Agent Status
            </div>
            <div style="color: {colors['header_text']}; font-size: 14px; margin-top: 8px;">
                This is how the interface will look in {theme} mode.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def apply_page_theme(self, theme: str = "dark"):
        """페이지 전체 테마 적용
        
        Args:
            theme: 적용할 테마
        """
        # 기본 페이지 설정
        st.set_page_config(
            page_title="Decepticon",
            page_icon="assets/logo.png",
            layout="wide"
        )
        
        # 테마 CSS 적용
        self.apply_theme_css(theme)
