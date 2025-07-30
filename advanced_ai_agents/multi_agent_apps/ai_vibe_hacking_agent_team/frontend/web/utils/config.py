"""
환경 설정 및 시스템 검증 로직 (리팩토링됨)
순수 비즈니스 로직만 포함
"""

from dotenv import load_dotenv
from typing import Dict, Any, List
import os
import sys

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))


def get_env_config() -> Dict[str, Any]:
    """환경 설정 로드 및 파싱
    
    Returns:
        Dict: 환경 설정 딕셔너리
    """
    load_dotenv()
    
    return {
        "debug_mode": os.getenv("DEBUG_MODE", "false").lower() == "true",
        "theme": os.getenv("THEME", "dark"),
        "docker_container": os.getenv("DOCKER_CONTAINER", "decepticon-kali"),
        "chat_height": int(os.getenv("CHAT_HEIGHT", "700"))
    }


def validate_environment() -> Dict[str, Any]:
    """환경 설정 검증 로직
    
    Returns:
        Dict: 검증 결과
    """
    config = get_env_config()
    validation_result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "config": config
    }
    
    # API 키 확인
    api_keys = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "OPENROUTER_API_KEY"]
    available_keys = []
    
    for key in api_keys:
        value = os.getenv(key)
        if value and value != "your-api-key":
            available_keys.append(key)
    
    if not available_keys:
        validation_result["errors"].append("No API keys configured")
        validation_result["valid"] = False
    else:
        validation_result["warnings"].append(f"Available API keys: {', '.join(available_keys)}")
    
    # CLI 모듈 확인
    try:
        from src.graphs.swarm import create_dynamic_swarm
        from src.utils.message import extract_message_content
    except ImportError as e:
        validation_result["errors"].append(f"CLI modules not available: {str(e)}")
        validation_result["valid"] = False
    
    return validation_result


def validate_model_selection(model_info: Dict[str, Any]) -> Dict[str, Any]:
    """모델 선택 검증 로직
    
    Args:
        model_info: 모델 정보
        
    Returns:
        Dict: 검증 결과
    """
    validation_result = {
        "valid": True,
        "errors": []
    }
    
    required_fields = ["model_name", "provider", "display_name"]
    
    for field in required_fields:
        if field not in model_info or not model_info[field]:
            validation_result["errors"].append(f"Missing required field: {field}")
            validation_result["valid"] = False
    
    return validation_result


def log_debug(message: str, data: Any = None):
    """디버그 로깅 로직
    
    Args:
        message: 로그 메시지
        data: 추가 데이터
    """
    config = get_env_config()
    if config.get("debug_mode", False):
        print(f"[DEBUG] {message}")
        if data:
            print(f"[DEBUG] Data: {data}")


def get_project_paths() -> Dict[str, str]:
    """프로젝트 경로 반환
    
    Returns:
        Dict: 주요 경로들
    """
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    
    return {
        "base": base_path,
        "frontend": os.path.join(base_path, "frontend"),
        "static": os.path.join(base_path, "frontend", "static"),
        "css": os.path.join(base_path, "frontend", "static", "css"),
        "logs": os.path.join(base_path, "logs"),
        "src": os.path.join(base_path, "src")
    }
