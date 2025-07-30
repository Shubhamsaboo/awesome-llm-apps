"""
Executor 관리 모듈 (리팩토링됨)
- Executor 초기화 및 설정
- 모델 정보 기반 스웜 초기화
- 실행기 상태 관리
"""

import streamlit as st
import asyncio
from typing import Optional, Dict, Any
import os
import sys

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from frontend.web.core.executor import Executor
from src.utils.logging.logger import get_logger


class ExecutorManager:
    """Executor 관리 클래스"""
    
    def __init__(self):
        """실행기 관리자 초기화"""
        self.executor = None
        self._ensure_executor()
    
    def _ensure_executor(self):
        """Executor 인스턴스 확보"""
        if "direct_executor" not in st.session_state or st.session_state.direct_executor is None:
            st.session_state.direct_executor = Executor()
        
        self.executor = st.session_state.direct_executor
    
    def is_ready(self) -> bool:
        """실행기가 준비되었는지 확인"""
        self._ensure_executor()
        return self.executor.is_ready() if self.executor else False
    
    async def initialize_with_model(self, model_info: Dict[str, Any]) -> bool:
        """모델 정보로 실행기 초기화
        
        Args:
            model_info: 모델 정보 딕셔너리
            
        Returns:
            bool: 초기화 성공 여부
        """
        try:
            # 로거 초기화 확인
            if "logger" not in st.session_state or st.session_state.logger is None:
                st.session_state.logger = get_logger()
            
            # 로깅 세션 시작
            model_display_name = model_info.get('display_name', 'Unknown Model')
            session_id = st.session_state.logger.start_session(model_display_name)
            st.session_state.logging_session_id = session_id
            
            # 실행기 초기화
            self._ensure_executor()
            await self.executor.initialize_swarm(model_info)
            
            # 상태 업데이트
            st.session_state.current_model = model_info
            st.session_state.executor_ready = True
            st.session_state.initialization_in_progress = False
            st.session_state.initialization_error = None
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to initialize AI agents: {str(e)}"
            
            st.session_state.executor_ready = False
            st.session_state.initialization_in_progress = False
            st.session_state.initialization_error = error_msg
            
            return False
    
    async def initialize_default(self) -> bool:
        """기본 설정으로 실행기 초기화
        
        Returns:
            bool: 초기화 성공 여부
        """
        try:
            # 로거 초기화 확인
            if "logger" not in st.session_state or st.session_state.logger is None:
                st.session_state.logger = get_logger()
            
            # 실행기 초기화
            self._ensure_executor()
            await self.executor.initialize_swarm()
            
            # 상태 업데이트
            st.session_state.executor_ready = True
            st.session_state.initialization_in_progress = False
            st.session_state.initialization_error = None
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to initialize AI agents: {str(e)}"
            
            st.session_state.executor_ready = False
            st.session_state.initialization_in_progress = False
            st.session_state.initialization_error = error_msg
            
            return False
    
    def reset(self):
        """실행기 리셋"""
        st.session_state.direct_executor = Executor()
        self.executor = st.session_state.direct_executor
        st.session_state.executor_ready = False
    
    def get_executor(self) -> Optional[Executor]:
        """현재 실행기 인스턴스 반환"""
        self._ensure_executor()
        return self.executor
    
    async def execute_workflow(self, user_input: str, config: Dict[str, Any]):
        """워크플로우 실행
        
        Args:
            user_input: 사용자 입력
            config: 스레드 설정
            
        Yields:
            이벤트 스트림
        """
        if not self.is_ready():
            raise RuntimeError("Executor not ready")
        
        # 로거에 사용자 입력 기록
        if "logger" in st.session_state and st.session_state.logger:
            st.session_state.logger.log_user_input(user_input)
        
        # 워크플로우 실행
        async for event in self.executor.execute_workflow(user_input, config=config):
            yield event


# 전역 실행기 관리자 인스턴스
_executor_manager = None

def get_executor_manager() -> ExecutorManager:
    """실행기 관리자 싱글톤 인스턴스 반환"""
    global _executor_manager
    if _executor_manager is None:
        _executor_manager = ExecutorManager()
    return _executor_manager