"""
Direct Executor - CLI 로직을 프론트엔드에서 직접 실행하는 모듈 (수정 버전)
세션 상태와 연동하여 안정적인 상태 관리
"""

import asyncio
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, AsyncGenerator

# CLI 모듈들을 직접 import
from langchain_core.messages import HumanMessage
from src.graphs.swarm import create_dynamic_swarm
from src.utils.llm.config_manager import (
    update_llm_config, 
    get_current_llm_config,
    get_current_llm
)
from src.utils.message import (
    extract_message_content,
    get_message_type,
    get_agent_name,
    parse_tool_name
)


class Executor:
    """CLI의 swarm 실행 로직을 프론트엔드에서 직접 사용하는 클래스"""
    
    def __init__(self):
        # 초기화 상태
        self._initialized = False
        self._swarm = None
        self._config = None
        self._thread_id = None
        self._current_model = None
        self._current_llm = None
        self._processed_message_ids = set()
    
    @property
    def swarm(self):
        return self._swarm
    
    @property
    def thread_id(self):
        return self._thread_id
    
    @property
    def current_model(self):
        return self._current_model
    
    async def initialize_swarm(self, model_info: Optional[Dict[str, Any]] = None, thread_config: Optional[Dict[str, Any]] = None):
        """Swarm 초기화"""
        try:
            # 이전 상태 초기화
            self._initialized = False
            self._swarm = None
            
            # Thread config 처리 - 외부에서 제공되면 사용, 없으면 새로 생성
            if thread_config:
                self._config = thread_config
                self._thread_id = thread_config["configurable"]["thread_id"]
            else:
                # 기존 방식: 새로운 UUID 생성
                self._thread_id = str(uuid.uuid4())
                self._config = {
                    "configurable": {
                        "thread_id": self._thread_id,
                    }
                }
            
            # 모델 정보 설정
            if model_info:
                self._current_model = model_info
                
                # LLM 설정 업데이트
                update_llm_config(
                    model_name=model_info['model_name'],
                    provider=model_info['provider'],
                    display_name=model_info['display_name'],
                    temperature=0.0
                )
            
            # LLM 인스턴스 생성
            self._current_llm = get_current_llm()
            
            # 동적으로 swarm 생성 
            self._swarm = await create_dynamic_swarm()
            
            # 초기화 완료
            self._initialized = True
            
            return self._thread_id
            
        except Exception as e:
            self._initialized = False
            self._swarm = None
            raise Exception(f"Swarm initialization failed: {str(e)}")
    
    async def execute_workflow(self, user_input: str, config: Optional[Dict[str, Any]] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        워크플로우 실행 
        """
        if not self.is_ready():
            raise Exception("Executor not ready - swarm not initialized")
        
        # config가 제공되면 사용, 없으면 기본 config 사용
        execution_config = config if config else self._config
        
        # 메시지 ID 추적 초기화
        self._processed_message_ids = set()
        
        inputs = {"messages": [HumanMessage(content=user_input)]}
        
        try:
            step_count = 0
            
            async for namespace, output in self._swarm.astream(
                inputs,
                stream_mode="updates",
                config=execution_config,  # 업데이트된 config 사용
                subgraphs=True
            ):
                step_count += 1
                
                for node, value in output.items():
                    # 에이전트 이름 결정 
                    agent_name = get_agent_name(namespace)
                    
                    # 메시지 처리 
                    if "messages" in value and value["messages"]:
                        messages = value["messages"]
                        if messages:
                            latest_message = messages[-1]
                            should_display, message_type = self._should_display_message(
                                latest_message, agent_name, step_count
                            )
                            
                            if should_display:
                                # 프론트엔드에서 처리할 수 있는 형태로 이벤트 생성
                                event_data = {
                                    "type": "message",
                                    "message_type": message_type,
                                    "agent_name": agent_name,
                                    "namespace": namespace,
                                    "content": extract_message_content(latest_message),
                                    "raw_message": latest_message,
                                    "step_count": step_count,
                                    "timestamp": datetime.now().isoformat()
                                }
                                
                                # 툴 메시지인 경우 추가 정보
                                if message_type == "tool":
                                    tool_name = getattr(latest_message, 'name', 'Unknown Tool')
                                    event_data["tool_name"] = tool_name
                                    event_data["tool_display_name"] = parse_tool_name(tool_name)
                                
                                yield event_data
            
            # 완료 신호
            yield {
                "type": "workflow_complete",
                "step_count": step_count,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            yield {
                "type": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _should_display_message(self, message, agent_name: str, step_count: int):
        """메시지를 표시할지 결정 - CLI 로직과 완전히 동일"""
        # 메시지 ID 생성 
        message_id = None
        if hasattr(message, 'id') and message.id:
            message_id = message.id
        else:
            content = extract_message_content(message)
            message_id = f"{agent_name}_{hash(content)}"
        
        # 사용자 메시지는 최초 1회만 표시 
        if message.__class__.__name__ == 'HumanMessage':
            if message_id not in self._processed_message_ids:
                self._processed_message_ids.add(message_id)
                return True, "user"
            return False, None
        
        # AI 메시지는 새로운 것만 표시 
        elif message.__class__.__name__ == 'AIMessage':
            if message_id not in self._processed_message_ids:
                self._processed_message_ids.add(message_id)
                return True, "ai"
            return False, None
        
        # 도구 메시지는 새로운 것만 표시
        elif message.__class__.__name__ == 'ToolMessage':
            if message_id not in self._processed_message_ids:
                self._processed_message_ids.add(message_id)
                return True, "tool"
            return False, None
        
        return False, None
    
    def get_current_model_info(self):
        """현재 모델 정보 반환"""
        if self._current_model:
            return self._current_model
        
        try:
            config = get_current_llm_config()
            return {
                "display_name": config.display_name,
                "provider": config.provider,
                "model_name": config.model_name
            }
        except:
            return {
                "display_name": "Unknown Model",
                "provider": "Unknown",
                "model_name": "unknown"
            }
    
    async def change_model(self, model_info: Dict[str, Any]):
        """모델 변경"""
        try:
            self._current_model = model_info
            
            update_llm_config(
                model_name=model_info['model_name'],
                provider=model_info['provider'],
                display_name=model_info['display_name'],
                temperature=0.0
            )
            
            # 새로운 LLM 인스턴스 생성
            self._current_llm = get_current_llm()
            
            # 새로운 모델로 에이전트들 재생성
            self._swarm = await create_dynamic_swarm()
            
            return True
            
        except Exception as e:
            raise Exception(f"Model change failed: {str(e)}")
    
    def is_ready(self):
        """실행 준비 상태 확인"""
        ready = self._initialized and self._swarm is not None
        return ready
    
    def reset_session(self):
        """세션 초기화"""
        self._thread_id = None
        self._config = None
        self._processed_message_ids = set()
        self._initialized = False
    
    def get_state_dict(self):
        """상태를 딕셔너리로 반환 (세션 저장용)"""
        return {
            "initialized": self._initialized,
            "thread_id": self._thread_id,
            "current_model": self._current_model,
            "has_swarm": self._swarm is not None
        }
