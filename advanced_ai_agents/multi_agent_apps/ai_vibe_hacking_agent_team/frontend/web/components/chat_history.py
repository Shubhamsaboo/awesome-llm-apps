"""
채팅 히스토리 UI 컴포넌트 (리팩토링됨 - 순수 UI 로직)
세션 목록 표시, 재현 버튼, 익스포트 등 히스토리 UI 렌더링
"""

import streamlit as st
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from frontend.web.utils.constants import ICON, ICON_TEXT, COMPANY_LINK
import time

class ChatHistoryComponent:
    """채팅 히스토리 UI 컴포넌트"""
    
    def __init__(self):
        """컴포넌트 초기화"""
        pass
    
    def render_page_header(self):
        """페이지 헤더 렌더링"""
        # 로고 표시
        st.logo(ICON_TEXT, icon_image=ICON, size="large", link=COMPANY_LINK)
        st.title("📊 :red[Session Logs]")
    
    def render_back_button(self, callback: Callable = None) -> bool:
        """뒤로가기 버튼 렌더링
        
        Args:
            callback: 클릭 콜백 함수
            
        Returns:
            bool: 버튼이 클릭되었는지 여부
        """
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("← Back", use_container_width=True):
                if callback:
                    callback()
                return True
        return False
    
    def render_empty_state(self):
        """세션이 없을 때의 상태 렌더링
        
        Returns:
            bool: 새 채팅 버튼이 클릭되었는지 여부
        """
        st.info("📭 No chat sessions found")
        st.markdown("""
        Start a new conversation to see your chat history here.
        """)
        
        # 새 채팅 시작 버튼
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Start New Chat", use_container_width=True, type="primary"):
                return True
        return False
    
    def render_sessions_header(self, session_count: int, total_count: int = None):
        """세션 목록 헤더 렌더링
        
        Args:
            session_count: 표시할 세션 수
            total_count: 전체 세션 수 (선택적)
        """
        st.subheader("📋 Recent Sessions")
        if total_count and total_count > session_count:
            st.caption(f"Showing {session_count} of {total_count} sessions")
        else:
            st.caption(f"Showing {session_count} recent sessions")
    
    def render_filter_options(self) -> Dict[str, str]:
        """필터 옵션 렌더링
        
        Returns:
            Dict: 선택된 필터 옵션들
        """
        with st.expander("🔍 Filter Options", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                date_filter = st.selectbox(
                    "Filter by Date",
                    options=["All", "Today", "Last 7 days", "Last 30 days"],
                    index=0
                )
            
            with col2:
                sort_option = st.selectbox(
                    "Sort by",
                    options=["Newest First", "Oldest First", "Most Events"],
                    index=0
                )
        
        return {
            "date_filter": date_filter,
            "sort_option": sort_option
        }
    
    def format_session_time(self, session_time: str) -> str:
        """세션 시간 포맷팅
        
        Args:
            session_time: 원본 시간 문자열
            
        Returns:
            str: 포맷된 시간 문자열
        """
        try:
            dt = datetime.fromisoformat(session_time.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return session_time[:19] if len(session_time) > 19 else session_time
    
    def render_session_card(
        self, 
        session: Dict[str, Any], 
        index: int,
        callbacks: Optional[Dict[str, Callable]] = None
    ) -> Optional[str]:
        """세션 카드 렌더링
        
        Args:
            session: 세션 데이터
            index: 세션 인덱스
            callbacks: 콜백 함수들
            
        Returns:
            Optional[str]: 발생한 액션 ("replay", "details", "export")
        """
        if callbacks is None:
            callbacks = {}
        
        session_id = session.get('session_id', 'Unknown')
        
        with st.container():
            # 세션 헤더
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                # 시간 표시
                time_str = self.format_session_time(session.get('start_time', ''))
                st.markdown(f"**🕒 {time_str}**")
                st.caption(f"Session: {session_id[:16]}...")
                
                # 내용 미리보기
                preview_text = session.get('preview', "No user input found")
                if len(preview_text) > 100:
                    preview_text = preview_text[:100] + "..."
                st.caption(f"💬 {preview_text}")
                
                # 모델 정보 표시
                model_info = session.get('model')
                if model_info:
                    st.caption(f"🤖 Model: {model_info}")
            
            with col2:
                st.metric("Events", session.get('event_count', 0))
            
            with col3:
                # 세션 상세 정보 버튼
                if st.button("📄 Details", key=f"details_{index}", use_container_width=True):
                    return "details"
            
            with col4:
                # Replay 버튼 (핵심 기능)
                if st.button("🎬 Replay", key=f"replay_{index}", use_container_width=True, type="primary"):
                    if "on_replay" in callbacks:
                        callbacks["on_replay"](session_id)
                    return "replay"
            
            # Export 기능 (별도 행)
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col4:
                export_filename = f"session_{session_id[:8]}_{datetime.now().strftime('%Y%m%d')}.json"
                
                if "get_export_data" in callbacks:
                    export_data = callbacks["get_export_data"](session_id)
                    if export_data:
                        st.download_button(
                            label="💾 Export",
                            data=export_data,
                            file_name=export_filename,
                            mime="application/json",
                            key=f"export_{index}",
                            use_container_width=True
                        )
                    else:
                        st.button("❌ Export", disabled=True, key=f"export_disabled_{index}", use_container_width=True)
            
            st.divider()
        
        return None
    
    def render_session_details(self, session: Dict[str, Any]):
        """세션 상세 정보 렌더링
        
        Args:
            session: 세션 데이터
        """
        session_id = session.get('session_id', 'Unknown')
        
        with st.expander(f"Session Details - {session_id[:16]}...", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Session Info:**")
                session_info = {
                    "Session ID": session_id,
                    "Start Time": session.get('start_time', 'Unknown'),
                    "Event Count": session.get('event_count', 0),
                    "Model": session.get('model', 'Unknown')
                }
                st.json(session_info)
            
            with col2:
                st.markdown("**Preview:**")
                preview = session.get('preview', 'No preview available')
                st.text_area("Content", value=preview, height=100, disabled=True)
    
    def render_sessions_list(
        self, 
        sessions: List[Dict[str, Any]], 
        callbacks: Optional[Dict[str, Callable]] = None
    ):
        """세션 목록 렌더링
        
        Args:
            sessions: 세션 목록
            callbacks: 콜백 함수들
        """
        # 필터 옵션
        filter_options = self.render_filter_options()
        
        # 실제 필터링은 비즈니스 로직에서 처리하고, 여기서는 UI만 표시
        filtered_sessions = sessions  # 필터링된 세션들
        
        st.divider()
        
        # 세션 카드들
        for i, session in enumerate(filtered_sessions):
            action = self.render_session_card(session, i, callbacks)
            
            # 세션 상세 정보 표시
            if action == "details":
                self.render_session_details(session)
    
    def render_complete_history_page(
        self,
        sessions: List[Dict[str, Any]] = None,
        callbacks: Optional[Dict[str, Callable]] = None
    ):
        """완전한 히스토리 페이지 렌더링
        
        Args:
            sessions: 세션 목록
            callbacks: 콜백 함수들
        """
        # 사이드바 숨김
        self.hide_sidebar()
        
        # 페이지 헤더
        self.render_page_header()
        
        # 뒤로가기 버튼
        if self.render_back_button():
            if callbacks and "on_back" in callbacks:
                callbacks["on_back"]()
        
        # 세션 목록 처리
        if not sessions:
            if self.render_empty_state():
                if callbacks and "on_new_chat" in callbacks:
                    callbacks["on_new_chat"]()
        else:
            # 세션 목록 헤더
            self.render_sessions_header(len(sessions))
            
            # 세션 목록 표시
            self.render_sessions_list(sessions, callbacks)
    
    def hide_sidebar(self):
        """사이드바 숨기기"""
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
    
    def show_loading_state(self, message: str = "Loading sessions..."):
        """로딩 상태 표시
        
        Args:
            message: 로딩 메시지
        """
        with st.spinner(message):
            time.sleep(0.1)
    
    def show_error_state(self, error_msg: str):
        """에러 상태 표시
        
        Args:
            error_msg: 에러 메시지
            
        Returns:
            bool: 재시도 버튼이 클릭되었는지 여부
        """
        st.error(f"Error loading sessions: {error_msg}")
        
        if st.button("🔄 Retry", use_container_width=True):
            return True
        return False
    
    def show_replay_start_message(self, session_id: str):
        """재현 시작 메시지 표시 (제거됨 - 바로 재현)
        
        Args:
            session_id: 세션 ID
        """
        # 메시지 출력 제거 - 바로 이전 대화 내역 재현
        pass
