"""
메모리 기반 설정 관리자 - 파일 저장 없이 메모리에서만 관리
"""

from dataclasses import dataclass
from typing import Optional, Any
from .models import load_llm_model, ModelProvider


@dataclass
class LLMConfig:
    """LLM 설정"""
    model_name: str = "claude-3-5-sonnet-latest"
    provider: str = "anthropic"
    display_name: str = "Claude 3.5 Sonnet"
    temperature: float = 0.0


class MemoryConfigManager:
    """메모리 기반 설정 관리자 - 파일 저장하지 않음"""
    
    _instance: Optional['MemoryConfigManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not getattr(self, '_initialized', False):
            self._config: Optional[LLMConfig] = None
            self._llm_instance: Optional[Any] = None
            self._initialized = True
    
    @property
    def config(self) -> LLMConfig:
        """현재 설정 반환 (기본값 사용 가능)"""
        if self._config is None:
            self._config = LLMConfig()  # 기본값
        return self._config
    
    @property
    def llm_instance(self) -> Optional[Any]:
        """현재 LLM 인스턴스 반환"""
        return self._llm_instance
    
    def update_config(self, model_name: str, provider: str, display_name: str) -> None:
        """LLM 설정 업데이트 (메모리에만 저장)"""
        self._config = LLMConfig(
            model_name=model_name,
            provider=provider,
            display_name=display_name,
            temperature=0.0  # 고정값
        )
        
        # LLM 인스턴스도 새로 생성
        try:
            self._llm_instance = load_llm_model(
                model_name=model_name,
                provider=provider,
                temperature=0.0
            )
        except Exception as e:
            print(f"Warning: Failed to load LLM model: {e}")
            self._llm_instance = None
    
    def get_current_llm(self) -> Optional[Any]:
        """현재 LLM 인스턴스 반환 (없으면 기본값으로 생성)"""
        if self._llm_instance is None and self._config is not None:
            try:
                self._llm_instance = load_llm_model(
                    model_name=self._config.model_name,
                    provider=self._config.provider,
                    temperature=0.0
                )
            except Exception as e:
                print(f"Warning: Failed to load LLM model: {e}")
                return None
        
        return self._llm_instance
    
    def reset(self) -> None:
        """설정 초기화"""
        self._config = None
        self._llm_instance = None


# 전역 인스턴스 (싱글톤)
_memory_config_manager: Optional[MemoryConfigManager] = None


def get_memory_config_manager() -> MemoryConfigManager:
    """전역 메모리 설정 관리자 인스턴스 반환"""
    global _memory_config_manager
    if _memory_config_manager is None:
        _memory_config_manager = MemoryConfigManager()
    return _memory_config_manager


def get_current_llm_config() -> LLMConfig:
    """현재 LLM 설정 조회 (메모리에서)"""
    return get_memory_config_manager().config


def update_llm_config(model_name: str, provider: str, display_name: str, 
                     temperature: float = 0.0) -> None:
    """LLM 설정 업데이트 (메모리에만 저장)"""
    get_memory_config_manager().update_config(
        model_name=model_name,
        provider=provider,
        display_name=display_name
    )


def get_current_llm():
    """현재 LLM 인스턴스 반환"""
    return get_memory_config_manager().get_current_llm()


def reset_config() -> None:
    """설정 초기화"""
    get_memory_config_manager().reset()


# Export main functions
__all__ = [
    "LLMConfig",
    "MemoryConfigManager",
    "get_current_llm_config", 
    "update_llm_config",
    "get_current_llm",
    "reset_config"
]
