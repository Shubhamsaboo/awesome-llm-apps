"""
채팅 화면에서 세션 자동 재생 기능 (단순화됨)
플레이스홀더 기반 터미널 UI에 맞게 최적화
"""

import streamlit as st
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any

from src.utils.logging.replay import get_replay_system
from frontend.web.core.message_processor import MessageProcessor

class ReplayManager:
    """자동 재생 관리자 - 단순화된 터미널 UI 적용"""
    
    def __init__(self):
        self.replay_system = get_replay_system()
        self.message_processor = MessageProcessor()
    
    def is_replay_mode(self) -> bool:
        """재생 모드인지 확인"""
        return st.session_state.get("replay_mode", False)
    
    def handle_replay_in_main_app(self, chat_area, agents_container, chat_ui, terminal_ui) -> bool:
        """메인 앱에서 재현 처리 - 중복 호출 제거"""
        if not self.is_replay_mode():
            return False
        
        replay_session_id = st.session_state.get("replay_session_id")
        if not replay_session_id:
            return False
        
        try:
            # ReplaySystem.start_replay()를 직접 호출 (내부에서 load_session 처리)
            if self.replay_system.start_replay(replay_session_id):
                # 단순화된 재현 실행
                asyncio.run(self._execute_replay_simplified(chat_area, agents_container, chat_ui, terminal_ui))
                
                # 재현 완료 후 정리
                self.replay_system.stop_replay()
                
                return True
            else:
                st.error(f"세션 {replay_session_id}를 찾을 수 없습니다.")
                return False
            
        except Exception as e:
            st.error(f"Replay error: {e}")
            # 에러 발생 시 재현 모드 해제
            self.replay_system.stop_replay()
        
        return False
    
    async def _execute_replay_simplified(self, chat_area, agents_container, chat_ui, terminal_ui):
        """단순화된 재현 실행 - 세션 상태에서 데이터 가져오기"""
        # 세션 데이터는 ReplaySystem.start_replay()에서 이미 세션 상태에 저장됨
        session = st.session_state.get("replay_session")
        if not session or not session.events:
            st.error("재현할 세션 데이터가 없습니다.")
            return
        
        # 재현 시작 메시지
        with st.status("🎬 Replaying session...", expanded=True) as status:
            
            replay_messages = []
            terminal_messages = []
            event_history = []
            agent_activity = {}
            
            status.update(label=f"Processing {len(session.events)} events...", state="running")
            
            # 이벤트 처리
            for i, event in enumerate(session.events):
                try:
                    # 이벤트를 Executor 스타일 이벤트로 변환
                    executor_event = self._convert_to_executor_event(event)
                    
                    if executor_event:
                        # MessageProcessor를 사용하여 frontend 메시지로 변환
                        frontend_message = self.message_processor.process_cli_event(executor_event)
                        
                        # 중복 확인
                        if not self.message_processor.is_duplicate_message(
                            frontend_message, replay_messages
                        ):
                            replay_messages.append(frontend_message)
                            
                            # tool 메시지인 경우 터미널 메시지에도 추가
                            if frontend_message.get("type") == "tool":
                                terminal_messages.append(frontend_message)
                            
                            event_history.append(executor_event)
                            
                            # 에이전트 활동 추적
                            agent_name = executor_event.get("agent_name", "Unknown")
                            if agent_name not in agent_activity:
                                agent_activity[agent_name] = 0
                            agent_activity[agent_name] += 1
                    
                    # 진행 상황 업데이트
                    if (i + 1) % 10 == 0:
                        status.update(label=f"Processed {i + 1}/{len(session.events)} events...", state="running")
                        
                except Exception as e:
                    print(f"Error processing event {i}: {e}")
                    continue
            
            # 메시지들을 세션 상태에 설정
            st.session_state.frontend_messages = replay_messages
            st.session_state.structured_messages = replay_messages
            st.session_state.terminal_messages = terminal_messages
            st.session_state.event_history = event_history
            
            # 재현된 메시지들을 chat_area에 실제 표시
            if replay_messages:
                # 메시지 전체를 한 번에 표시하여 rerun 문제 방지
                with chat_area:
                    for message in replay_messages:
                        message_type = message.get("type", "")
                        if message_type == "user":
                            chat_ui.display_user_message(message)
                        elif message_type == "ai":
                            chat_ui.display_agent_message(message, streaming=False)  # 재현시 스트리밍 비활성화
                        elif message_type == "tool":
                            chat_ui.display_tool_message(message)
            
            # 터미널 UI 처리 (단순화됨)
            if terminal_ui and terminal_messages:
                try:
                    # 터미널 초기화
                    terminal_ui.clear_terminal()
                    
                    # 터미널 메시지 처리 - 단순화된 방식
                    terminal_ui.process_structured_messages(terminal_messages)
                    
                    # 디버그 정보
                    if st.session_state.get("debug_mode", False):
                        print(f"🎬 Replay: {len(terminal_messages)} terminal messages processed")
                    
                except Exception as term_error:
                    st.error(f"Terminal processing error during replay: {term_error}")
                    print(f"Terminal processing error during replay: {term_error}")
            
            # 에이전트 상태 업데이트
            if agent_activity:
                completed_agents = []
                active_agent = None
                
                agent_list = list(agent_activity.keys())
                if len(agent_list) > 1:
                    completed_agents = [agent.lower() for agent in agent_list[:-1]]
                    active_agent = agent_list[-1].lower()
                elif len(agent_list) == 1:
                    active_agent = agent_list[0].lower()
                
                st.session_state.completed_agents = completed_agents
                st.session_state.active_agent = active_agent
                
                # 에이전트 상태 표시
                if hasattr(chat_ui, 'display_agent_status'):
                    chat_ui.display_agent_status(
                        agents_container,
                        active_agent,
                        None,
                        completed_agents
                    )
            
            # 재현 완료 표시
            st.session_state.replay_completed = True
            
            # 완료
            status.update(
                label=f"✅ Replay Complete! Loaded {len(replay_messages)} messages, {len(terminal_messages)} terminal events, {len(agent_activity)} agents", 
                state="complete"
            )
    
    def _convert_to_executor_event(self, event) -> Optional[Dict[str, Any]]:
        """이벤트를 Executor 스타일 이벤트로 변환"""
        timestamp = datetime.now().isoformat()
        
        if event.event_type.value == "user_input":
            return {
                "type": "message",
                "message_type": "user",
                "agent_name": "User",
                "content": event.content,
                "timestamp": timestamp
            }
        
        elif event.event_type.value == "agent_response":
            executor_event = {
                "type": "message",
                "message_type": "ai",
                "agent_name": event.agent_name or "Agent",
                "content": event.content,
                "timestamp": timestamp
            }
            
            # Tool calls 정보 복원
            if hasattr(event, 'tool_calls') and event.tool_calls:
                executor_event["tool_calls"] = event.tool_calls
            
            return executor_event
        
        elif event.event_type.value == "tool_command":
            return {
                "type": "message",
                "message_type": "tool",
                "agent_name": "Tool",
                "tool_name": event.tool_name or "Unknown Tool",
                "content": f"Command: {event.content}",
                "timestamp": timestamp
            }
        
        elif event.event_type.value == "tool_output":
            return {
                "type": "message",
                "message_type": "tool",
                "agent_name": "Tool",
                "tool_name": event.tool_name or "Tool Output",
                "content": event.content,
                "timestamp": timestamp
            }
        
        return None
