"""
Chat History Page (리팩토링됨)
불필요한 래퍼 함수 제거, 새로운 컴포넌트 및 비즈니스 로직 구조 적용
"""

import streamlit as st
import os
import sys

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# 새로운 컴포넌트들
from frontend.web.components.chat_history import ChatHistoryComponent
from frontend.web.components.theme_ui import ThemeUIComponent

# 리팩토링된 비즈니스 로직
from frontend.web.core.history_manager import get_history_manager
from frontend.web.core.app_state import get_app_state_manager

# 전역 매니저들 초기화
history_manager = get_history_manager()
app_state = get_app_state_manager()

# UI 컴포넌트들 초기화
theme_ui = ThemeUIComponent()
chat_history = ChatHistoryComponent()


def main():
    """Chat History 페이지 메인"""
    
    # 테마 초기화
    current_theme = "dark" if st.session_state.get('dark_mode', True) else "light"
    theme_ui.apply_theme_css(current_theme)
    
    # 콜백 함수들 정의
    callbacks = {
        "on_back": _handle_back_button,
        "on_new_chat": _handle_new_chat,
        "on_replay": _handle_replay,
        "get_export_data": _get_export_data
    }
    
    # 세션 로딩 및 UI 표시
    _display_history_interface(callbacks)


def _display_history_interface(callbacks):
    """히스토리 인터페이스 표시"""
    
    # 로딩 상태 표시
    chat_history.show_loading_state("Loading sessions...")
    
    # 세션 데이터 로드
    sessions_result = history_manager.load_sessions(limit=20)
    
    if not sessions_result["success"]:
        # 에러 상태 처리
        retry_clicked = chat_history.show_error_state(sessions_result["error"])
        if retry_clicked:
            st.rerun()
        return
    
    sessions = sessions_result["sessions"]
    
    # 완전한 히스토리 페이지 렌더링
    chat_history.render_complete_history_page(sessions, callbacks)


def _handle_back_button():
    """뒤로가기 버튼 처리"""
    st.switch_page("pages/01_Chat.py")


def _handle_new_chat():
    """새 채팅 버튼 처리"""
    st.switch_page("pages/01_Chat.py")


def _handle_replay(session_id: str):
    """재현 버튼 처리 (개선됨 - 바로 대화 내역 로드)
    
    Args:
        session_id: 재현할 세션 ID
    """
    # 세션 ID 검증
    if not history_manager.validate_session_id(session_id):
        st.error("Invalid session ID")
        return
    
    # 재현 시작
    replay_result = history_manager.start_replay(session_id)
    
    if replay_result["success"]:
        # 재현 모드 설정
        st.session_state.replay_session_id = session_id
        st.session_state.replay_mode = True
        st.session_state.replay_completed = False
        
        # 바로 메인 채팅 페이지로 이동 (메시지 제거)
        st.switch_page("pages/01_Chat.py")
    else:
        st.error(f"Failed to start replay: {replay_result['error']}")


def _get_export_data(session_id: str) -> str:
    """익스포트 데이터 가져오기
    
    Args:
        session_id: 세션 ID
        
    Returns:
        str: JSON 형태의 익스포트 데이터
    """
    try:
        export_data = history_manager.prepare_export_data(session_id)
        return export_data
        
    except Exception as e:
        st.error(f"Export failed: {str(e)}")
        return None


if __name__ == "__main__":
    main()
