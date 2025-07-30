"""
워크플로우 실행 처리 모듈 (리팩토링됨 - 순수 비즈니스 로직)
- 사용자 입력 처리
- 워크플로우 이벤트 스트림 관리
- 메시지 처리 로직
- UI는 콜백으로 분리됨
"""

import streamlit as st
import asyncio
from typing import Dict, Any, List, Optional, Callable
import os
import sys

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from frontend.web.core.message_processor import MessageProcessor
from frontend.web.core.executor_manager import get_executor_manager


class WorkflowHandler:
    """워크플로우 실행 핸들러 - 순수 비즈니스 로직"""
    
    def __init__(self):
        """워크플로우 핸들러 초기화"""
        self.message_processor = MessageProcessor()
        self.executor_manager = get_executor_manager()
    
    def validate_execution_state(self) -> Dict[str, Any]:
        """실행 가능한 상태인지 검증
        
        Returns:
            Dict: {"can_execute": bool, "error_message": str}
        """
        if not self.executor_manager.is_ready():
            return {
                "can_execute": False,
                "error_message": "AI agents not ready. Please initialize first."
            }
        
        if st.session_state.workflow_running:
            return {
                "can_execute": False,
                "error_message": "Another workflow is already running. Please wait."
            }
        
        return {"can_execute": True, "error_message": ""}
    
    def prepare_user_input(self, user_input: str) -> Dict[str, Any]:
        """사용자 입력을 워크플로우용으로 준비
        
        Args:
            user_input: 사용자 입력 텍스트
            
        Returns:
            Dict: 처리된 사용자 메시지
        """
        user_message = self.message_processor._create_user_message(user_input)
        st.session_state.structured_messages.append(user_message)
        return user_message
    
    async def execute_workflow_logic(
        self, 
        user_input: str,
        ui_callbacks: Dict[str, Callable] = None,
        terminal_ui = None
    ) -> Dict[str, Any]:
        """워크플로우 실행 핵심 로직
        
        Args:
            user_input: 사용자 입력 텍스트
            ui_callbacks: UI 콜백 함수들
            
        Returns:
            Dict: 실행 결과
        """
        # UI 콜백 기본값 설정
        if ui_callbacks is None:
            ui_callbacks = {}
        
        # 워크플로우 실행 상태 설정
        st.session_state.workflow_running = True
        
        execution_result = {
            "success": False,
            "event_count": 0,
            "agent_activity": {},
            "error_message": "",
            "terminal_ui": terminal_ui  # 터미널 UI 인스턴스 저장
        }
        
        try:
            event_count = 0
            agent_activity = {}
            
            async for event in self.executor_manager.execute_workflow(
                user_input,
                config=st.session_state.thread_config
            ):
                event_count += 1
                st.session_state.event_history.append(event)
                
                try:
                    # 이벤트 처리
                    success = await self._process_event_logic(
                        event, 
                        agent_activity,
                        ui_callbacks,
                        terminal_ui
                    )
                    
                    if not success:
                        break
                    
                    # 에이전트 상태 업데이트 (순수 로직)
                    self._update_agent_status_logic()
                    
                except Exception as e:
                    if st.session_state.debug_mode:
                        execution_result["error_message"] = f"Event processing error: {str(e)}"
            
            # 실행 결과 설정
            execution_result.update({
                "success": True,
                "event_count": event_count,
                "agent_activity": agent_activity
            })
        
        except Exception as e:
            execution_result["error_message"] = f"Workflow execution error: {str(e)}"
        
        finally:
            st.session_state.workflow_running = False
            # 세션 자동 저장
            if "logger" in st.session_state and st.session_state.logger:
                st.session_state.logger.save_session()
        
        return execution_result
    
    async def _process_event_logic(
        self,
        event: Dict[str, Any],
        agent_activity: Dict[str, int],
        ui_callbacks: Dict[str, Callable],
        terminal_ui = None
    ) -> bool:
        """이벤트 처리 순수 로직
        
        Args:
            event: 처리할 이벤트
            agent_activity: 에이전트 활동 추적
            ui_callbacks: UI 콜백 함수들
            
        Returns:
            bool: 처리 성공 여부
        """
        event_type = event.get("type", "")
        
        if event_type == "message":
            return await self._process_message_event_logic(
                event, agent_activity, ui_callbacks, terminal_ui
            )
        elif event_type == "workflow_complete":
            if "on_workflow_complete" in ui_callbacks:
                ui_callbacks["on_workflow_complete"]()
            return True
        elif event_type == "error":
            error_msg = event.get("error", "Unknown error")
            if "on_error" in ui_callbacks:
                ui_callbacks["on_error"](error_msg)
            return False
        
        return True
    
    async def _process_message_event_logic(
        self,
        event: Dict[str, Any],
        agent_activity: Dict[str, int],
        ui_callbacks: Dict[str, Callable],
        terminal_ui = None
    ) -> bool:
        """메시지 이벤트 처리 순수 로직"""
        # 메시지 변환
        frontend_message = self.message_processor.process_cli_event(event)
        
        # 중복 메시지 체크
        if self.message_processor.is_duplicate_message(
            frontend_message, st.session_state.structured_messages
        ):
            return True
        
        # 메시지 저장
        st.session_state.structured_messages.append(frontend_message)
        
        # 로깅 처리
        self._log_message_event(event, frontend_message)
        
        # 에이전트 활동 추적
        agent_name = event.get("agent_name", "Unknown")
        if agent_name not in agent_activity:
            agent_activity[agent_name] = 0
        agent_activity[agent_name] += 1
        
        # UI 콜백 호출 (메시지 표시)
        if "on_message_ready" in ui_callbacks:
            ui_callbacks["on_message_ready"](frontend_message)
        
        # 터미널 메시지 처리 - 이전 버전의 직접 호출 방식
        if frontend_message.get("type") == "tool" and terminal_ui:
            try:
                tool_name = frontend_message.get("tool_display_name", "Tool")
                content = frontend_message.get("content", "")
                
                if tool_name and content:
                    # 명령어와 출력 직접 추가 (이전 버전 방식)
                    terminal_ui.add_command(tool_name)
                    terminal_ui.add_output(content)
                    
                    # 디버깅 로그
                    if st.session_state.get("debug_mode", False):
                        print(f"Terminal direct update: {tool_name} -> {content[:100]}...")
                        
            except Exception as e:
                if st.session_state.get("debug_mode", False):
                    print(f"Terminal direct update error: {e}")
        
                # 기존 콜백 방식도 유지 (호환성)
        elif frontend_message.get("type") == "tool":
            self._process_terminal_message_logic(frontend_message, ui_callbacks)
        
        return True
    
    def _process_terminal_message_logic(
        self, 
        frontend_message: Dict[str, Any], 
        ui_callbacks: Dict[str, Callable]
    ):
        """터미널 메시지 처리 순수 로직 (간소화된 버전)"""
        # terminal_messages 초기화 확인
        if "terminal_messages" not in st.session_state:
            st.session_state.terminal_messages = []
        
        # 터미널 메시지 저장
        st.session_state.terminal_messages.append(frontend_message)
        
        # 터미널 UI 콜백 호출 (더 이상 강제 업데이트 안함)
        if "on_terminal_message" in ui_callbacks:
            tool_name = frontend_message.get("tool_display_name", "Tool")
            content = frontend_message.get("content", "")
            
            if tool_name and content:
                ui_callbacks["on_terminal_message"](tool_name, content)
    
    def _log_message_event(self, event: Dict[str, Any], frontend_message: Dict[str, Any]):
        """메시지 이벤트 로깅 로직"""
        if "logger" not in st.session_state or not st.session_state.logger:
            return
        
        logger = st.session_state.logger
        agent_name = event.get("agent_name", "Unknown")
        message_type = event.get("message_type", "unknown")
        content = event.get("content", "")
        
        if message_type == "ai":
            logger.log_agent_response(
                agent_name=agent_name,
                content=content,
                tool_calls=frontend_message.get("tool_calls")
            )
        elif message_type == "tool":
            tool_name = event.get("tool_name", "Unknown Tool")
            if "command" in event:  # 도구 명령
                logger.log_tool_command(
                    tool_name=tool_name,
                    command=event.get("command", content)
                )
            else:  # 도구 출력
                logger.log_tool_output(
                    tool_name=tool_name,
                    output=content
                )
    
    def _update_agent_status_logic(self):
        """에이전트 상태 업데이트 순수 로직"""
        # 최근 이벤트에서 활성 에이전트 찾기
        active_agent = None
        for event in reversed(st.session_state.event_history):
            if event.get("type") == "message" and event.get("message_type") == "ai":
                agent_name = event.get("agent_name")
                if agent_name and agent_name != "Unknown":
                    active_agent = agent_name.lower()
                    break
        
        # 활성 에이전트 업데이트
        if active_agent and active_agent != st.session_state.active_agent:
            if st.session_state.active_agent and st.session_state.active_agent not in st.session_state.completed_agents:
                st.session_state.completed_agents.append(st.session_state.active_agent)
            
            st.session_state.active_agent = active_agent
        
        # 초기 UI 상태 업데이트
        if st.session_state.get("keep_initial_ui", True) and (
            st.session_state.active_agent or st.session_state.completed_agents
        ):
            st.session_state.keep_initial_ui = False
    
    def get_agent_status(self) -> Dict[str, Any]:
        """현재 에이전트 상태 반환"""
        return {
            "active_agent": st.session_state.active_agent,
            "completed_agents": st.session_state.completed_agents,
            "keep_initial_ui": st.session_state.get("keep_initial_ui", True)
        }


# 전역 워크플로우 핸들러 인스턴스
_workflow_handler = None

def get_workflow_handler() -> WorkflowHandler:
    """워크플로우 핸들러 싱글톤 인스턴스 반환"""
    global _workflow_handler
    if _workflow_handler is None:
        _workflow_handler = WorkflowHandler()
    return _workflow_handler