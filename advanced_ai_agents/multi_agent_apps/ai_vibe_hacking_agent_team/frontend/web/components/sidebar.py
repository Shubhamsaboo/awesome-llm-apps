"""
사이드바 UI 컴포넌트 (리팩토링됨 - 순수 UI 로직)
에이전트 상태, 네비게이션, 설정 등 사이드바 UI 렌더링
"""

import streamlit as st
from typing import Dict, Any, List, Optional, Callable
from frontend.web.utils.constants import (
    AGENTS_INFO,
    CSS_CLASS_AGENT_STATUS,
    CSS_CLASS_STATUS_ACTIVE,
    CSS_CLASS_STATUS_COMPLETED,
    COMPANY_LINK
)
from src.utils.agents import AgentManager


class SidebarComponent:
    """사이드바 UI 컴포넌트"""
    
    def __init__(self):
        """컴포넌트 초기화"""
        pass
    
    def render_agent_status(
        self, 
        container, 
        active_agent: Optional[str] = None,
        completed_agents: Optional[List[str]] = None
    ):
        """에이전트 상태 표시
        
        Args:
            container: 표시할 컨테이너
            active_agent: 현재 활성 에이전트
            completed_agents: 완료된 에이전트 목록
        """
        if completed_agents is None:
            completed_agents = []
        
        # 플레이스홀더 관리
        if "agent_status_placeholders" not in st.session_state:
            st.session_state.agent_status_placeholders = {}
        
        # 초기 UI 상태 유지 체크
        is_initial_ui = st.session_state.get("keep_initial_ui", True)
        
        # 각 에이전트의 상태 표시
        for agent in AGENTS_INFO:
            agent_id = agent["id"]
            agent_name = agent["name"]
            agent_icon = agent["icon"]
            
            # 플레이스홀더 생성
            if agent_id not in st.session_state.agent_status_placeholders:
                st.session_state.agent_status_placeholders[agent_id] = container.empty()
            
            # 상태 클래스 결정
            status_class = ""
            
            if not is_initial_ui:
                # 활성 에이전트 (현재 실행중)
                if agent_id == active_agent:
                    status_class = CSS_CLASS_STATUS_ACTIVE
                # 완료된 에이전트
                elif agent_id in completed_agents:
                    status_class = CSS_CLASS_STATUS_COMPLETED
            
            # 상태 업데이트
            st.session_state.agent_status_placeholders[agent_id].html(
                f"<div class='{CSS_CLASS_AGENT_STATUS} {status_class}'>" +
                f"<div>{agent_icon} {agent_name}</div>" +
                f"</div>"
            )
    
    def render_model_info(self, model_info: Optional[Dict[str, Any]] = None):
        """현재 모델 정보 표시
        
        Args:
            model_info: 모델 정보 딕셔너리
        """
        if model_info:
            model_name = model_info.get('display_name', 'Unknown Model')
            provider = model_info.get('provider', 'Unknown')
            
            # 테마에 따른 색상 설정
            is_dark = st.session_state.get('dark_mode', True)
            
            if is_dark:
                bg_color = "#1a1a1a"
                border_color = "#333333"
                text_color = "#ffffff"
                subtitle_color = "#888888"
                icon_color = "#4a9eff"
            else:
                bg_color = "#f8f9fa"
                border_color = "#e9ecef"
                text_color = "#212529"
                subtitle_color = "#6c757d"
                icon_color = "#0d6efd"
            
            st.markdown(f"""
            <div style="
                background: {bg_color};
                border: 1px solid {border_color};
                border-radius: 8px;
                padding: 12px 16px;
                margin: 8px 0;
                display: flex;
                align-items: center;
                gap: 12px;
                transition: all 0.2s ease;
            ">
                <div style="
                    color: {icon_color};
                    font-size: 18px;
                    line-height: 1;
                ">🤖</div>
                <div style="flex: 1; min-width: 0;">
                    <div style="
                        color: {text_color};
                        font-weight: 600;
                        font-size: 14px;
                        margin: 0;
                        white-space: nowrap;
                        overflow: hidden;
                        text-overflow: ellipsis;
                    ">{model_name}</div>
                    <div style="
                        color: {subtitle_color};
                        font-size: 12px;
                        margin: 2px 0 0 0;
                        opacity: 0.8;
                    ">{provider}</div>
                </div>
                <div style="
                    width: 8px;
                    height: 8px;
                    background: #10b981;
                    border-radius: 50%;
                    flex-shrink: 0;
                "></div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # 모델이 선택되지 않은 경우
            is_dark = st.session_state.get('dark_mode', True)
            
            if is_dark:
                bg_color = "#1a1a1a"
                border_color = "#444444"
                text_color = "#888888"
                icon_color = "#666666"
            else:
                bg_color = "#f8f9fa"
                border_color = "#dee2e6"
                text_color = "#6c757d"
                icon_color = "#adb5bd"
            
            st.markdown(f"""
            <div style="
                background: {bg_color};
                border: 1px dashed {border_color};
                border-radius: 8px;
                padding: 12px 16px;
                margin: 8px 0;
                display: flex;
                align-items: center;
                gap: 12px;
                opacity: 0.7;
            ">
                <div style="
                    color: {icon_color};
                    font-size: 18px;
                    line-height: 1;
                ">🤖</div>
                <div style="flex: 1;">
                    <div style="
                        color: {text_color};
                        font-weight: 500;
                        font-size: 14px;
                        margin: 0;
                    ">No Model Selected</div>
                    <div style="
                        color: {text_color};
                        font-size: 12px;
                        margin: 2px 0 0 0;
                        opacity: 0.6;
                    ">Choose a model to start</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    def render_navigation_buttons(self, callbacks: Dict[str, Callable] = None):
        """네비게이션 버튼들 렌더링
        
        Args:
            callbacks: 버튼 클릭 콜백 함수들
        """
        if callbacks is None:
            callbacks = {}
        
        # 모델 변경 버튼
        if st.button("🔁 Change Model", use_container_width=True):
            if "on_change_model" in callbacks:
                callbacks["on_change_model"]()
            else:
                st.switch_page("streamlit_app.py")
        
        # 채팅 히스토리 버튼
        if st.button("📋 Chat History", use_container_width=True):
            if "on_chat_history" in callbacks:
                callbacks["on_chat_history"]()
            else:
                st.switch_page("pages/02_📋_Chat_History.py")
        
        # 새 채팅 버튼
        if st.button("✨ New Chat", use_container_width=True):
            if "on_new_chat" in callbacks:
                callbacks["on_new_chat"]()
    
    def render_settings_section(self, callbacks: Dict[str, Callable] = None):
        """설정 섹션 렌더링
        
        Args:
            callbacks: 설정 변경 콜백 함수들
        """
        if callbacks is None:
            callbacks = {}
        
        st.markdown("### ⚙️ Settings")
        
        # 테마 토글
        if "on_theme_toggle" in callbacks:
            theme_manager = st.session_state.get('theme_manager')
            if theme_manager:
                theme_manager.create_theme_toggle(st)
        
        # Debug 모드
        current_debug = st.session_state.get('debug_mode', False)
        debug_mode = st.checkbox("🐞 Debug Mode", value=current_debug)
        
        if debug_mode != current_debug:
            if "on_debug_mode_change" in callbacks:
                callbacks["on_debug_mode_change"](debug_mode)
    
    def render_session_stats(self, stats: Dict[str, Any]):
        """세션 통계 표시
        
        Args:
            stats: 세션 통계 데이터
        """
        with st.expander("📊 Session Stats", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Messages", stats.get("messages_count", 0))
                st.metric("Events", stats.get("events_count", 0))
            with col2:
                st.metric("Steps", stats.get("steps_count", 0))
                st.metric("Time", f"{stats.get('elapsed_time', 0)}s")
    
    def render_debug_info(self, debug_info: Dict[str, Any]):
        """디버그 정보 표시
        
        Args:
            debug_info: 디버그 정보 데이터
        """
        if not st.session_state.get('debug_mode'):
            return
        
        with st.expander("🔍 Debug Info", expanded=False):
            st.markdown("**Session Info:**")
            session_info = {
                "user_id": debug_info.get("user_id", "Not set"),
                "thread_id": debug_info.get("thread_id", "Not set")[:8] + "..." if len(debug_info.get("thread_id", "")) > 8 else debug_info.get("thread_id", "Not set"),
            }
            st.json(session_info)
            
            if "logging" in debug_info:
                st.markdown("**Logging Info:**")
                st.json(debug_info["logging"])
    
    def render_complete_sidebar(
        self,
        model_info: Optional[Dict[str, Any]] = None,
        active_agent: Optional[str] = None,
        completed_agents: Optional[List[str]] = None,
        session_stats: Optional[Dict[str, Any]] = None,
        debug_info: Optional[Dict[str, Any]] = None,
        callbacks: Optional[Dict[str, Callable]] = None
    ):
        """완전한 사이드바 렌더링
        
        Args:
            model_info: 모델 정보
            active_agent: 활성 에이전트
            completed_agents: 완료된 에이전트 목록
            session_stats: 세션 통계
            debug_info: 디버그 정보
            callbacks: 콜백 함수들
        """
        with st.sidebar:
            # 에이전트 상태
            agents_container = st.container()
            self.render_agent_status(agents_container, active_agent, completed_agents)
            
            st.divider()
            
            # 현재 모델 정보
            self.render_model_info(model_info)
            st.divider()
            
            # 네비게이션 버튼들
            self.render_navigation_buttons(callbacks)
            
            st.divider()
            
            # 설정 섹션
            self.render_settings_section(callbacks)
            
            # 세션 통계 (있는 경우)
            if session_stats:
                self.render_session_stats(session_stats)
            
            # 디버그 정보 (있는 경우)
            if debug_info:
                self.render_debug_info(debug_info)
    
    def hide_sidebar(self):
        """사이드바 숨기기 (CSS 사용)"""
        st.markdown("""
        <style>
            [data-testid="stSidebarNav"] {
                display: none;
            }
            
            section[data-testid="stSidebar"] {
                display: none !important;
            }
            
            /* 메인 컨텐트를 전체 화면에 확장 */
            .main .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
                max-width: none;
            }
        </style>
        """, unsafe_allow_html=True)
    
    def show_back_button(self, callback: Callable = None, text: str = "← Back"):
        """뒤로가기 버튼 표시
        
        Args:
            callback: 클릭 콜백 함수
            text: 버튼 텍스트
            
        Returns:
            bool: 버튼이 클릭되었는지 여부
        """
        if st.button(text, use_container_width=True):
            if callback:
                callback()
                return True
            return True
        return False
