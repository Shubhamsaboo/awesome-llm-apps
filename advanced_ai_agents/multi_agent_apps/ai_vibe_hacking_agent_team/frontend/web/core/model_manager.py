"""
Model Selection Business Logic (리팩토링됨)
모델 데이터 로드, 검증, 초기화 등 모델 관련 비즈니스 로직
"""

import time
import concurrent.futures
from typing import Dict, Any, List, Optional, Tuple
from frontend.web.utils.validation import validate_model_info
from frontend.web.utils.constants import PROVIDERS


class ModelManager:
    """모델 관리 비즈니스 로직"""
    
    def __init__(self):
        """모델 매니저 초기화"""
        self.models_cache = {}
        self.cache_timestamp = 0
        self.cache_duration = 300  # 5분 캐시
    
    def load_models_data(self) -> Dict[str, Any]:
        """모델 데이터 로드 및 검증
        
        Returns:
            Dict: 로드 결과
        """
        try:
            from src.utils.llm.models import list_available_models, check_ollama_connection
            
            # 병렬 처리로 모델 목록과 Ollama 연결 동시 체크
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                # 타임아웃을 짧게 설정하여 빠른 응답
                model_future = executor.submit(list_available_models)
                ollama_future = executor.submit(check_ollama_connection)
                
                try:
                    # 최대 5초 대기
                    models = model_future.result(timeout=5.0)
                    ollama_info = ollama_future.result(timeout=2.0)
                except concurrent.futures.TimeoutError:
                    # 타임아웃 시 기본값 사용
                    models = model_future.result() if model_future.done() else []
                    ollama_info = ollama_future.result() if ollama_future.done() else {"connected": False, "count": 0}
            
            available_models = [m for m in models if m.get("api_key_available", False)]
            
            if not available_models:
                return {
                    "success": False,
                    "error": "No models available. Please set up your API keys.",
                    "type": "error"
                }
            
            # Group models by provider
            self.models_cache = {}
            for model in available_models:
                provider = model.get('provider', 'Unknown')
                if provider not in self.models_cache:
                    self.models_cache[provider] = []
                self.models_cache[provider].append(model)
            
            # 캐시 시간 업데이트
            self.cache_timestamp = time.time()
            
            # Return success status with Ollama info if connected
            result = {"success": True, "type": "success", "models_by_provider": self.models_cache}
            if ollama_info.get("connected", False):
                result["ollama_message"] = f"Ollama Connected - {ollama_info.get('count', 0)} local models available"
            
            return result
            
        except ImportError as e:
            return {
                "success": False,
                "error": "Model selection feature unavailable",
                "info": "Setup Required: Please install CLI dependencies",
                "type": "import_error"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error loading models: {str(e)}",
                "type": "error"
            }
    
    def get_cached_models_data(self, force_refresh: bool = False) -> Dict[str, Any]:
        """캐시된 모델 데이터 반환
        
        Args:
            force_refresh: 강제 새로고침 여부
            
        Returns:
            Dict: 모델 데이터 또는 로드 결과
        """
        current_time = time.time()
        needs_refresh = (
            force_refresh or
            not self.models_cache or 
            current_time - self.cache_timestamp > self.cache_duration
        )
        
        if needs_refresh:
            return self.load_models_data()
        
        return {
            "success": True,
            "type": "cached",
            "models_by_provider": self.models_cache
        }
    
    def get_default_selection(self) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """기본 프로바이더 및 모델 선택 반환
        
        Returns:
            Tuple: (기본 프로바이더, 기본 모델)
        """
        # Default to Anthropic and Claude 3.5 Sonnet if available
        default_provider = None
        default_model = None
        
        # Look for Anthropic provider (case insensitive)
        anthropic_provider_key = None
        for provider_key in self.models_cache.keys():
            if provider_key.lower() == "anthropic":
                anthropic_provider_key = provider_key
                break
        
        if anthropic_provider_key:
            anthropic_models = self.models_cache[anthropic_provider_key]
            for model in anthropic_models:
                if "claude-3-5-sonnet" in model.get("model_name", "").lower():
                    default_provider = anthropic_provider_key
                    default_model = model
                    break
        
        # If Claude 3.5 Sonnet not found, use first available Anthropic model
        if not default_model and anthropic_provider_key:
            default_provider = anthropic_provider_key
            default_model = self.models_cache[anthropic_provider_key][0]
        
        # If no Anthropic models, use first available provider and model
        if not default_model:
            providers = list(self.models_cache.keys())
            if providers:
                default_provider = providers[0]
                default_model = self.models_cache[default_provider][0]
        
        return default_provider, default_model
    
    def validate_model_selection(self, model_info: Dict[str, Any]) -> Dict[str, Any]:
        """모델 선택 검증
        
        Args:
            model_info: 선택된 모델 정보
            
        Returns:
            Dict: 검증 결과
        """
        return validate_model_info(model_info)
    
    def prepare_model_initialization(self, model_info: Dict[str, Any]) -> Dict[str, Any]:
        """모델 초기화 준비
        
        Args:
            model_info: 모델 정보
            
        Returns:
            Dict: 초기화 준비 결과
        """
        # 모델 정보 검증
        validation_result = self.validate_model_selection(model_info)
        if not validation_result["valid"]:
            return {
                "ready": False,
                "errors": validation_result["errors"]
            }
        
        # 필요한 필드들이 모두 있는지 확인
        required_fields = ["model_name", "provider", "display_name"]
        missing_fields = [field for field in required_fields if not model_info.get(field)]
        
        if missing_fields:
            return {
                "ready": False,
                "errors": [f"Missing required fields: {', '.join(missing_fields)}"]
            }
        
        return {
            "ready": True,
            "model_info": model_info
        }
    
    def reset_cache(self):
        """모델 캐시 리셋"""
        self.models_cache = {}
        self.cache_timestamp = 0
    
    def get_provider_models(self, provider: str) -> List[Dict[str, Any]]:
        """특정 프로바이더의 모델 목록 반환
        
        Args:
            provider: 프로바이더 이름
            
        Returns:
            List: 모델 목록
        """
        return self.models_cache.get(provider, [])
    
    def get_available_providers(self) -> List[str]:
        """사용 가능한 프로바이더 목록 반환
        
        Returns:
            List: 프로바이더 목록
        """
        return list(self.models_cache.keys())
    
    def find_model_by_name(self, model_name: str, provider: str = None) -> Optional[Dict[str, Any]]:
        """모델 이름으로 모델 찾기
        
        Args:
            model_name: 찾을 모델 이름
            provider: 프로바이더 (선택적)
            
        Returns:
            Optional[Dict]: 찾은 모델 정보
        """
        if provider:
            models = self.get_provider_models(provider)
            for model in models:
                if model.get("model_name") == model_name:
                    return model
        else:
            # 모든 프로바이더에서 검색
            for provider_models in self.models_cache.values():
                for model in provider_models:
                    if model.get("model_name") == model_name:
                        return model
        
        return None


# 전역 모델 매니저 인스턴스
_model_manager = None

def get_model_manager() -> ModelManager:
    """모델 매니저 싱글톤 인스턴스 반환"""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager
