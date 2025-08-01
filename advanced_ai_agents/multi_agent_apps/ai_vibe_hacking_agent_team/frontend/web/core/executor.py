"""
Direct Executor - CLI 로직을 프론트엔드에서 직접 실행하는 모듈 (리팩토링됨)
세션 상태와 연동하여 안정적인 상태 관리
"""

import asyncio
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, AsyncGenerator, Union, List, Tuple

# CLI 모듈들을 직접 import
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
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
    def __init__(self):
        # 초기화 상태
        self._initialized = False
        self._swarm = None
        self._config: Optional[RunnableConfig] = None
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
                # thread_config가 이미 RunnableConfig 형태라면 사용
                if isinstance(thread_config, dict) and "configurable" in thread_config:
                    self._config = RunnableConfig(configurable=thread_config["configurable"])
                    self._thread_id = thread_config["configurable"]["thread_id"]
                else:
                    # 다른 형태라면 기본값 사용
                    self._thread_id = str(uuid.uuid4())
                    self._config = RunnableConfig(configurable={"thread_id": self._thread_id})
            else:
                # 기존 방식: 새로운 UUID 생성
                self._thread_id = str(uuid.uuid4())
                self._config = RunnableConfig(configurable={"thread_id": self._thread_id})
            
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
    
    async def execute_workflow(self, user_input: str, config: Optional[RunnableConfig] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        워크플로우 실행 
        """
        if not self.is_ready():
            raise Exception("Executor not ready - swarm not initialized")
        
        # 추가 안전 체크
        if self._swarm is None:
            raise Exception("Swarm is None - initialization failed")
        
        # config 타입 안전하게 처리
        execution_config: Optional[RunnableConfig] = None
        if config is not None:
            execution_config = config
        else:
            execution_config = self._config
        
        # 메시지 ID 추적 초기화
        self._processed_message_ids = set()
        
        inputs = {"messages": [HumanMessage(content=user_input)]}
        
        try:
            step_count = 0
            
            # 이제 타입이 안전함
            stream_result = self._swarm.astream(
                inputs,
                stream_mode="updates",
                config=execution_config,
                subgraphs=True
            )
            
            async for stream_item in stream_result:
                # stream_item이 튜플인지 확인
                if not isinstance(stream_item, tuple) or len(stream_item) != 2:
                    continue
                    
                namespace, output = stream_item
                step_count += 1
                
                # output이 딕셔너리인지 확인
                if not isinstance(output, dict):
                    continue
                    
                for node, value in output.items():
                    # 에이전트 이름 결정 
                    agent_name = get_agent_name(namespace)
                    
                    # 메시지 처리 - value가 딕셔너리이고 messages 키가 있는지 확인
                    if isinstance(value, dict) and "messages" in value and value["messages"]:
                        messages = value["messages"]
                        if messages and isinstance(messages, list):
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
    
    def _should_display_message(self, message, agent_name: str, step_count: int) -> Tuple[bool, Optional[str]]:
        """메시지를 표시할지 결정"""
        # 메시지 ID 생성 - 수정된 부분
        message_id = getattr(message, 'id', None)
        if not message_id:
            content = extract_message_content(message)
            # content를 문자열로 변환 후 해시
            message_id = f"{agent_name}_{hash(str(content))}"
        
        # isinstance를 사용한 타입 체크 - 수정된 부분
        if isinstance(message, HumanMessage):
            if message_id not in self._processed_message_ids:
                self._processed_message_ids.add(message_id)
                return True, "user"
            return False, None
        
        elif isinstance(message, AIMessage):
            if message_id not in self._processed_message_ids:
                self._processed_message_ids.add(message_id)
                return True, "ai"
            return False, None
        
        elif isinstance(message, ToolMessage):
            if message_id not in self._processed_message_ids:
                self._processed_message_ids.add(message_id)
                return True, "tool"
            return False, None
        
        return False, None
    
    def get_current_model_info(self) -> Dict[str, str]:
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
    
    async def change_model(self, model_info: Dict[str, Any]) -> bool:
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
    
    def is_ready(self) -> bool:
        """실행 준비 상태 확인"""
        return (self._initialized and 
                self._swarm is not None and 
                hasattr(self._swarm, 'astream'))
    
    def reset_session(self) -> None:
        """세션 초기화"""
        self._thread_id = None
        self._config = None
        self._processed_message_ids = set()
        self._initialized = False
    
    def get_state_dict(self) -> Dict[str, Any]:
        """상태를 딕셔너리로 반환 (세션 저장용)"""
        return {
            "initialized": self._initialized,
            "thread_id": self._thread_id,
            "current_model": self._current_model,
            "has_swarm": self._swarm is not None
        }