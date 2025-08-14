"""
애플리케이션 상태 관리 모듈 (리팩토링됨)
- 세션 상태 초기화 및 관리
- 사용자 세션 설정
- 디버그 모드 관리
"""

import streamlit as st
import time
import hashlib
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import os
import sys

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from src.utils.memory import (
    create_thread_config,
    create_memory_namespace
)
from src.utils.logging.logger import get_logger
from src.utils.logging.replay import get_replay_system


class AppStateManager:
    """애플리케이션 상태 관리 클래스"""
    
    def __init__(self):
        """상태 관리자 초기화"""
        self.logger = None
        self.replay_system = None
        self._initialize_session_state()
        self._initialize_user_session()
        self._initialize_logging()
    
    def _initialize_session_state(self):
        """세션 상태 초기화 (여러 번 호출되어도 안전)"""
        defaults = {
            # 실행기 관련
            "executor_ready": False,
            "direct_executor": None,
            
            # 메시지 관련
            "messages": [],
            "structured_messages": [],
            "terminal_messages": [],
            "event_history": [],
            
            # 모델 관련
            "current_model": None,
            "models_by_provider": {},
            "models_cache_timestamp": 0,
            
            # 워크플로우 관련
            "workflow_running": False,
            "initialization_in_progress": False,
            "initialization_error": None,
            
            # 에이전트 관련
            "active_agent": None,
            "completed_agents": [],
            "current_step": 0,
            "agent_status_placeholders": {},
            
            # UI 관련
            "terminal_placeholder": None,
            "terminal_history": [],
            "keep_initial_ui": True,
            "show_controls": False,
            
            # 세션 관련
            "session_start_time": time.time(),
            "debug_mode": os.getenv("DEBUG_MODE", "false").lower() == "true",
            
            # 재현 관련
            "replay_mode": False,
            "replay_session_id": None,
            "replay_completed": False,
            
            # 로깅 관련
            "logging_session_id": None,
        }
        
        for key, default_value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
    
    def _initialize_user_session(self):
        """사용자 세션 및 thread config 초기화"""
        # 사용자 ID 생성 (브라우저 기반)
        if "user_id" not in st.session_state:
            browser_info = f"{st.session_state.get('_session_id', '')}{datetime.now().strftime('%Y%m%d')}"
            user_hash = hashlib.md5(browser_info.encode()).hexdigest()[:8]
            st.session_state.user_id = f"user_{user_hash}"
        
        # Thread configuration 생성
        if "thread_config" not in st.session_state:
            st.session_state.thread_config = create_thread_config(
                user_id=st.session_state.user_id,
                conversation_id=None  # 기본 대화
            )
        
        # 메모리 네임스페이스 생성
        if "memory_namespace" not in st.session_state:
            st.session_state.memory_namespace = create_memory_namespace(
                user_id=st.session_state.user_id,
                namespace_type="memories"
            )
    
    def _initialize_logging(self):
        """로깅 시스템 초기화"""
        if "logger" not in st.session_state:
            st.session_state.logger = get_logger()
            st.session_state.replay_system = get_replay_system()
            self.logger = st.session_state.logger
            self.replay_system = st.session_state.replay_system
    
    def reset_session(self, keep_model: bool = True):
        """세션 초기화
        
        Args:
            keep_model: True면 현재 모델 설정 유지, False면 모델도 초기화
        """
        # 현재 로그 세션 종료
        if hasattr(st.session_state, 'logger') and st.session_state.logger and st.session_state.logger.current_session:
            st.session_state.logger.end_session()
        
        # 초기화할 키들
        reset_keys = [
            "executor_ready", "messages", "structured_messages", "terminal_messages",
            "workflow_running", "active_agent", "completed_agents", "current_step",
            "agent_status_placeholders", "terminal_placeholder", "event_history",
            "initialization_in_progress", "initialization_error", "terminal_history",
            "keep_initial_ui", "show_controls"
        ]
        
        # 모델 관련 키들 (옵션)
        if not keep_model:
            reset_keys.extend([
                "current_model", "models_by_provider", "models_cache_timestamp"
            ])
        
        # 재현 관련 키들
        replay_keys = ["replay_mode", "replay_session_id", "replay_completed"]
        reset_keys.extend(replay_keys)
        
        # 세션 시작 시간 리셋
        st.session_state.session_start_time = time.time()
        
        # 키별 초기화
        for key in reset_keys:
            if key in st.session_state:
                if key in ["agent_status_placeholders"]:
                    st.session_state[key] = {}
                elif key in ["messages", "structured_messages", "terminal_messages", 
                           "completed_agents", "event_history", "terminal_history"]:
                    st.session_state[key] = []
                elif key in ["current_step"]:
                    st.session_state[key] = 0
                elif key in ["keep_initial_ui"]:
                    st.session_state[key] = True
                else:
                    st.session_state[key] = False if key not in ["current_model", "terminal_placeholder", "direct_executor"] else None
        
        # DirectExecutor 재생성
        if "direct_executor" in st.session_state:
            st.session_state.direct_executor = None
    
    def create_new_conversation(self):
        """새로운 대화 세션 생성"""
        # 새로운 conversation_id로 thread config 생성
        new_conversation_id = str(uuid.uuid4())
        st.session_state.thread_config = create_thread_config(
            user_id=st.session_state.user_id,
            conversation_id=new_conversation_id
        )
        
        # 세션 초기화 (모델은 유지)
        self.reset_session(keep_model=True)
        
        return new_conversation_id
    
    def get_env_config(self) -> Dict[str, Any]:
        """환경 설정 로드"""
        return {
            "debug_mode": os.getenv("DEBUG_MODE", "false").lower() == "true",
            "theme": os.getenv("THEME", "dark"),
            "docker_container": os.getenv("DOCKER_CONTAINER", "decepticon-kali"),
            "chat_height": int(os.getenv("CHAT_HEIGHT", "700"))
        }
    
    def set_debug_mode(self, mode: bool):
        """디버그 모드 설정"""
        st.session_state.debug_mode = mode
    
    def get_session_stats(self) -> Dict[str, Any]:
        """세션 통계 정보 반환"""
        # 세션 상태 변수들을 안전하게 접근
        session_start_time = getattr(st.session_state, 'session_start_time', time.time())
        elapsed_time = int(time.time() - session_start_time)
        
        # 기본값으로 안전하게 접근
        structured_messages = getattr(st.session_state, 'structured_messages', [])
        event_history = getattr(st.session_state, 'event_history', [])
        current_step = getattr(st.session_state, 'current_step', 0)
        active_agent = getattr(st.session_state, 'active_agent', None)
        completed_agents = getattr(st.session_state, 'completed_agents', [])
        
        return {
            "messages_count": len(structured_messages),
            "events_count": len(event_history),
            "steps_count": current_step,
            "elapsed_time": elapsed_time,
            "active_agent": active_agent,
            "completed_agents_count": len(completed_agents)
        }
    
    def get_debug_info(self) -> Dict[str, Any]:
        """디버그 정보 반환"""
        debug_info = {
            "user_id": st.session_state.get("user_id", "Not set"),
            "thread_id": st.session_state.get("thread_config", {}).get("configurable", {}).get("thread_id", "Not set"),
            "executor_ready": getattr(st.session_state, 'executor_ready', False),
            "workflow_running": getattr(st.session_state, 'workflow_running', False),
        }
        
        # 로깅 정보 추가
        if hasattr(st.session_state, 'logger') and st.session_state.logger and st.session_state.logger.current_session:
            current_session = st.session_state.logger.current_session
            debug_info["logging"] = {
                "session_id": current_session.session_id,
                "events_count": len(current_session.events),
            }
        
        return debug_info
    
    def is_ready(self) -> bool:
        """애플리케이션이 사용 준비가 되었는지 확인"""
        return (
            st.session_state.executor_ready and 
            st.session_state.current_model is not None and
            not st.session_state.initialization_in_progress
        )


# 전역 상태 관리자 인스턴스
_app_state_manager = None

def get_app_state_manager() -> AppStateManager:
    """앱 상태 관리자 싱글톤 인스턴스 반환"""
    global _app_state_manager
    if _app_state_manager is None:
        _app_state_manager = AppStateManager()
    return _app_state_manager
