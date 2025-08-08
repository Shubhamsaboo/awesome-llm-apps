"""
채팅 메시지 렌더링 컴포넌트 (리팩토링됨 - 순수 UI 로직)
메시지 표시, 타이핑 애니메이션 등 순수 UI 렌더링만 담당
"""

import streamlit as st
import re
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from frontend.web.utils.constants import CSS_PATH_CHAT_UI, CSS_PATH_AGENT_STATUS
from src.utils.agents import AgentManager


class ChatMessagesComponent:
    """채팅 메시지 렌더링 컴포넌트"""
    
    def __init__(self):
        """컴포넌트 초기화"""
        self._setup_styles()
        # 메시지 고유 ID 카운터
        if "message_counter" not in st.session_state:
            st.session_state.message_counter = 0
    
    def _setup_styles(self):
        """CSS 스타일 설정"""
        try:
            # 채팅 UI CSS 로드
            with open(CSS_PATH_CHAT_UI, "r", encoding="utf-8") as f:
                chat_css = f.read()
            st.html(f"<style>{chat_css}</style>")
            
            # 에이전트 상태 CSS 로드
            with open(CSS_PATH_AGENT_STATUS, "r", encoding="utf-8") as f:
                agent_status_css = f.read()
            st.html(f"<style>{agent_status_css}</style>")
            
        except Exception as e:
            print(f"Error loading CSS: {e}")
    
    
    def simulate_typing(self, text: str, placeholder, speed: float = 0.005):
        """타이핑 애니메이션 시뮬레이션
        
        Args:
            text: 표시할 텍스트
            placeholder: Streamlit placeholder
            speed: 타이핑 속도
        """
        # 코드 블록 위치 찾기
        code_blocks = []
        code_block_pattern = r'```.*?```'
        for match in re.finditer(code_block_pattern, text, re.DOTALL):
            code_blocks.append((match.start(), match.end()))
        
        result = ""
        i = 0
        chars_per_update = 5  # 성능 최적화
        
        while i < len(text):
            # 현재 위치가 코드 블록 안에 있는지 확인
            code_block_to_add = None
            
            for start, end in code_blocks:
                if i == start:
                    code_block_to_add = text[start:end]
                    break
                elif start < i < end:
                    i += 1
                    continue
            
            if code_block_to_add:
                result += code_block_to_add
                i = end
                placeholder.markdown(result)
                time.sleep(speed * 2)
            else:
                end_pos = min(i + chars_per_update, len(text))
                
                # 다음 코드 블록 전까지만 추가
                for block_start, _ in code_blocks:
                    if block_start > i:
                        end_pos = min(end_pos, block_start)
                        break
                
                result += text[i:end_pos]
                i = end_pos
                
                placeholder.markdown(result)
                time.sleep(speed)
    
    def display_messages(self, structured_messages: List[Dict[str, Any]], container=None):
        """구조화된 메시지 목록을 UI에 표시
        
        Args:
            structured_messages: 표시할 메시지 목록
            container: 표시할 컨테이너 (기본값: st)
        """
        if container is None:
            container = st
            
        for message in structured_messages:
            message_type = message.get("type", "")
            
            if message_type == "user":
                self.display_user_message(message, container)
            elif message_type == "ai":
                self.display_agent_message(message, container, streaming=False)
            elif message_type == "tool":
                self.display_tool_message(message, container)
    
    def display_user_message(self, message: Dict[str, Any], container=None):
        """사용자 메시지 UI 표시
        
        Args:
            message: 사용자 메시지 데이터
            container: 표시할 컨테이너
        """
        if container is None:
            container = st
            
        content = message.get("content", "")
        
        with container.chat_message("user"):
            st.markdown(f'<div style="text-align: left;">{content}</div>', unsafe_allow_html=True)
    
    def display_agent_message(self, message: Dict[str, Any], container=None, streaming: bool = True):
        """AI 에이전트 메시지 UI 표시
        
        Args:
            message: 에이전트 메시지 데이터
            container: 표시할 컨테이너
            streaming: 스트리밍 모드 여부
        """
        if container is None:
            container = st
            
        display_name = message.get("display_name", "Agent")
        avatar = message.get("avatar", "🤖")
        
        # 재현 시스템과 일반 시스템 모두 호환
        if "data" in message and isinstance(message["data"], dict):
            content = message["data"].get("content", "")
            tool_calls = message.get("tool_calls", [])
        else:
            content = message.get("content", "")
            tool_calls = message.get("tool_calls", [])
        
        # 에이전트 색상 및 클래스 생성
        namespace = message.get("namespace", "")
        if namespace:
            if isinstance(namespace, str):
                namespace_list = [namespace]
            else:
                namespace_list = namespace
            
            from src.utils.message import get_agent_name
            agent_name_for_color = get_agent_name(namespace_list)
            if agent_name_for_color == "Unknown":
                agent_name_for_color = display_name
        else:
            agent_name_for_color = display_name
        
        agent_color = AgentManager.get_frontend_color(agent_name_for_color)
        agent_class = AgentManager.get_css_class(agent_name_for_color)
        
        # 고유한 메시지 ID 생성
        st.session_state.message_counter += 1
        
        # 메시지 표시
        with container.chat_message("assistant", avatar=avatar):
            # 에이전트 헤더
            st.markdown(
                f'<div class="agent-header {agent_class}"><strong style="color: {agent_color}">{display_name}</strong></div>', 
                unsafe_allow_html=True
            )
            
            # 컨텐츠 표시
            if content:
                text_placeholder = st.empty()
                
                # 재현 모드에서는 타이핑 애니메이션 비활성화
                is_replay_mode = st.session_state.get("replay_mode", False)
                if streaming and len(content) > 50 and not is_replay_mode:
                    self.simulate_typing(content, text_placeholder, speed=0.005)
                else:
                    text_placeholder.write(content)
            elif not tool_calls:
                st.write("No content available")
            
            # Tool calls 정보 표시
            if tool_calls:
                for i, tool_call in enumerate(tool_calls):
                    self._display_tool_call(tool_call)
    
    def _display_tool_call(self, tool_call: Dict[str, Any]):
        """Tool call 정보 표시
        
        Args:
            tool_call: Tool call 데이터
        """
        tool_name = tool_call.get("name", "Unknown Tool")
        tool_args = tool_call.get("args", {})
        
        # tool call 메시지 생성
        try:
            from src.utils.message import parse_tool_call
            tool_call_message = parse_tool_call(tool_call)
        except Exception as e:
            tool_call_message = f"Tool call error: {str(e)}"
        
        # 확장 가능한 UI
        with st.expander(f"**{tool_call_message}**", expanded=False):
            col1, col2 = st.columns([1, 3])
            
            with col1:
                st.markdown("**Tool:**")
                st.markdown("**ID:**")
                if tool_args:
                    st.markdown("**Arguments:**")
            
            with col2:
                st.markdown(f"`{tool_name}`")
                st.markdown(f"`{tool_call.get('id', 'N/A')}`")
                if tool_args:
                    import json
                    st.code(json.dumps(tool_args, indent=2), language="json")
                else:
                    st.markdown("`No arguments`")
    
    def display_tool_message(self, message: Dict[str, Any], container=None):
        """도구 메시지 UI 표시
        
        Args:
            message: 도구 메시지 데이터
            container: 표시할 컨테이너
        """
        if container is None:
            container = st
            
        tool_display_name = message.get("tool_display_name", "Tool")
        content = message.get("content", "")
        
        # tool 색상 사용
        tool_color = AgentManager.get_frontend_color("tool")
        tool_class = "tool-message"
        
        # 고유한 메시지 ID 생성
        st.session_state.message_counter += 1
        
        # 메시지 표시
        with container.chat_message("tool", avatar="🔧"):
            # tool 헤더
            st.markdown(
                f'<div class="agent-header {tool_class}"><strong style="color: {tool_color}">{tool_display_name}</strong></div>', 
                unsafe_allow_html=True
            )
            
            # 컨텐츠 표시
            if content:
                # 긴 출력은 제한
                if len(content) > 5000:
                    st.code(content[:5000] + "\n[Output truncated...]")
                    with st.expander("More.."):
                        st.text(content)
                else:
                    st.code(content)
    
    def show_processing_status(self, label: str = "Processing...", expanded: bool = True):
        """처리 중 상태 표시
        
        Args:
            label: 상태 라벨
            expanded: 확장 여부
            
        Returns:
            Streamlit status object
        """
        return st.status(label, expanded=expanded)
    
    def display_loading_message(self, message: str = "Loading..."):
        """로딩 메시지 표시
        
        Args:
            message: 로딩 메시지
        """
        with st.spinner(message):
            time.sleep(0.1)  # 최소 표시 시간
    
    def display_error_message(self, error_msg: str):
        """에러 메시지 표시
        
        Args:
            error_msg: 에러 메시지
        """
        st.error(error_msg)
    
    def display_success_message(self, success_msg: str):
        """성공 메시지 표시
        
        Args:
            success_msg: 성공 메시지
        """
        st.success(success_msg)
    
    def display_warning_message(self, warning_msg: str):
        """경고 메시지 표시
        
        Args:
            warning_msg: 경고 메시지
        """
        st.warning(warning_msg)
    
    def display_info_message(self, info_msg: str):
        """정보 메시지 표시
        
        Args:
            info_msg: 정보 메시지
        """
        st.info(info_msg)
