"""
메시지 처리 로직 (리팩토링됨 - 순수 비즈니스 로직)
CLI 메시지를 프론트엔드 메시지로 변환하는 핵심 로직
"""

from datetime import datetime
from typing import Dict, Any, List
import os
import sys

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# CLI 메시지 유틸리티 직접 import
from src.utils.message import parse_tool_name, extract_tool_calls
# 리팩토링된 에이전트 관리자
from src.utils.agents import AgentManager


class MessageProcessor:
    """메시지 처리 핵심 로직 클래스"""
    
    def __init__(self):
        """메시지 프로세서 초기화"""
        self.default_avatar = "🤖"
    
    def process_cli_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """CLI 이벤트를 프론트엔드 메시지로 변환
        
        Args:
            event_data: CLI에서 온 이벤트 데이터
            
        Returns:
            Dict: 변환된 프론트엔드 메시지
        """
        message_type = event_data.get("message_type", "")
        agent_name = event_data.get("agent_name", "Unknown")
        content = event_data.get("content", "")
        raw_message = event_data.get("raw_message")
        
        # 에이전트 표시 정보 생성
        display_name = AgentManager.get_display_name(agent_name)
        avatar = AgentManager.get_avatar(agent_name)
        
        if message_type == "ai":
            return self._create_ai_message(
                agent_name, display_name, avatar, content, raw_message, event_data
            )
        elif message_type == "tool":
            return self._create_tool_message(event_data, content)
        elif message_type == "user":
            return self._create_user_message(content)
        
        # 기본 메시지 - AI로 처리
        return self._create_ai_message(
            agent_name, display_name, avatar, content, raw_message, event_data
        )
    
    def _create_ai_message(
        self, 
        agent_name: str, 
        display_name: str, 
        avatar: str, 
        content: str, 
        raw_message: Any,
        event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """AI 메시지 생성"""
        message = {
            "type": "ai",
            "agent_id": agent_name.lower(),
            "display_name": display_name,
            "avatar": avatar,
            "content": content,
            "id": f"ai_{agent_name.lower()}_{hash(content[:100])}_{datetime.now().timestamp()}"
        }
        
        # Tool calls 정보 추출
        tool_calls = extract_tool_calls(raw_message, event_data)
        if tool_calls:
            message["tool_calls"] = tool_calls
        
        return message
    
    def _create_tool_message(self, event_data: Dict[str, Any], content: str) -> Dict[str, Any]:
        """도구 메시지 생성"""
        tool_name = event_data.get("tool_name", "Unknown Tool")
        tool_display_name = event_data.get("tool_display_name", parse_tool_name(tool_name))
        
        return {
            "type": "tool",
            "tool_name": tool_name,
            "tool_display_name": tool_display_name,
            "content": content,
            "id": f"tool_{tool_name}_{hash(content[:100])}_{datetime.now().timestamp()}"
        }
    
    def _create_user_message(self, content: str) -> Dict[str, Any]:
        """사용자 메시지 생성"""
        return {
            "type": "user",
            "content": content,
            "id": f"user_{hash(content)}_{datetime.now().timestamp()}"
        }
    
    def extract_agent_status(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """이벤트들에서 에이전트 상태 정보 추출"""
        status = {
            "active_agent": None,
            "completed_agents": [],
            "current_step": 0
        }
        
        # 최근 이벤트에서 활성 에이전트 찾기
        for event in reversed(events):
            if event.get("type") == "message" and event.get("message_type") == "ai":
                agent_name = event.get("agent_name")
                if agent_name and agent_name != "Unknown":
                    status["active_agent"] = agent_name.lower()
                    break
        
        # 총 스텝 수 계산
        status["current_step"] = len([e for e in events if e.get("type") == "message"])
        
        return status
    
    def is_duplicate_message(
        self, 
        new_message: Dict[str, Any], 
        existing_messages: List[Dict[str, Any]]
    ) -> bool:
        """메시지 중복 검사"""
        new_id = new_message.get("id")
        if not new_id:
            return False
        
        # ID 기반 중복 검사
        for msg in existing_messages:
            if msg.get("id") == new_id:
                return True
        
        # 내용 기반 중복 검사 (같은 에이전트의 같은 내용)
        new_agent = new_message.get("agent_id")
        new_content = new_message.get("content", "")
        
        for msg in existing_messages:
            if (msg.get("agent_id") == new_agent and 
                msg.get("type") == new_message.get("type") and
                msg.get("content") == new_content):
                return True
        
        return False


# 전역 메시지 프로세서 인스턴스
_message_processor = None

def get_message_processor() -> MessageProcessor:
    """메시지 프로세서 싱글톤 인스턴스 반환"""
    global _message_processor
    if _message_processor is None:
        _message_processor = MessageProcessor()
    return _message_processor
