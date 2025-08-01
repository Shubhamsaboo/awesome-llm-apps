"""
검증 로직 (리팩토링됨)
다양한 입력값과 상태에 대한 검증 함수들
"""

import streamlit as st
from typing import Dict, Any, List, Optional
from frontend.web.utils.constants import (
    SESSION_KEY_CURRENT_MODEL,
    SESSION_KEY_EXECUTOR_READY,
    API_KEYS,
    PROVIDERS
)


def check_model_required() -> bool:
    """모델 선택 여부 검증
    
    Returns:
        bool: 모델이 선택되어 있으면 True, 없으면 False
    """
    return bool(st.session_state.get(SESSION_KEY_CURRENT_MODEL))


def validate_session_state() -> Dict[str, Any]:
    """세션 상태 검증
    
    Returns:
        Dict: 검증 결과
    """
    validation_result = {
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    # 필수 세션 상태 확인
    required_keys = [
        SESSION_KEY_EXECUTOR_READY,
        SESSION_KEY_CURRENT_MODEL
    ]
    
    for key in required_keys:
        if key not in st.session_state:
            validation_result["errors"].append(f"Missing session state: {key}")
            validation_result["valid"] = False
    
    # 실행기 준비 상태 확인
    if not st.session_state.get(SESSION_KEY_EXECUTOR_READY, False):
        validation_result["warnings"].append("Executor not ready")
    
    return validation_result


def validate_user_input(user_input: str) -> Dict[str, Any]:
    """사용자 입력 검증
    
    Args:
        user_input: 사용자 입력 텍스트
        
    Returns:
        Dict: 검증 결과
    """
    validation_result = {
        "valid": True,
        "errors": [],
        "cleaned_input": ""
    }
    
    if not user_input:
        validation_result["errors"].append("Empty input")
        validation_result["valid"] = False
        return validation_result
    
    # 입력 정리
    cleaned = user_input.strip()
    
    if not cleaned:
        validation_result["errors"].append("Input contains only whitespace")
        validation_result["valid"] = False
        return validation_result
    
    # 길이 확인
    if len(cleaned) > 5000:
        validation_result["errors"].append("Input too long (max 5000 characters)")
        validation_result["valid"] = False
        return validation_result
    
    validation_result["cleaned_input"] = cleaned
    return validation_result


def validate_model_info(model_info: Dict[str, Any]) -> Dict[str, Any]:
    """모델 정보 검증
    
    Args:
        model_info: 모델 정보 딕셔너리
        
    Returns:
        Dict: 검증 결과
    """
    validation_result = {
        "valid": True,
        "errors": []
    }
    
    if not isinstance(model_info, dict):
        validation_result["errors"].append("Model info must be a dictionary")
        validation_result["valid"] = False
        return validation_result
    
    # 필수 필드 확인
    required_fields = ["model_name", "provider", "display_name"]
    
    for field in required_fields:
        if field not in model_info:
            validation_result["errors"].append(f"Missing required field: {field}")
            validation_result["valid"] = False
        elif not model_info[field]:
            validation_result["errors"].append(f"Empty required field: {field}")
            validation_result["valid"] = False
    
    # 프로바이더 확인 (대소문자 무시)
    if "provider" in model_info:
        provider = model_info["provider"]
        # 대소문자를 무시하고 비교
        provider_found = any(provider.lower() == p.lower() for p in PROVIDERS)
        if not provider_found:
            validation_result["errors"].append(f"Unknown provider: {provider}")
            validation_result["valid"] = False
    
    return validation_result


def validate_message_format(message: Dict[str, Any]) -> Dict[str, Any]:
    """메시지 형식 검증
    
    Args:
        message: 메시지 딕셔너리
        
    Returns:
        Dict: 검증 결과
    """
    validation_result = {
        "valid": True,
        "errors": []
    }
    
    if not isinstance(message, dict):
        validation_result["errors"].append("Message must be a dictionary")
        validation_result["valid"] = False
        return validation_result
    
    # 필수 필드 확인
    required_fields = ["type", "content", "id"]
    
    for field in required_fields:
        if field not in message:
            validation_result["errors"].append(f"Missing required field: {field}")
            validation_result["valid"] = False
    
    # 메시지 타입 확인
    valid_types = ["user", "ai", "tool"]
    if "type" in message and message["type"] not in valid_types:
        validation_result["errors"].append(f"Invalid message type: {message['type']}")
        validation_result["valid"] = False
    
    return validation_result


def validate_terminal_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    """터미널 엔트리 검증
    
    Args:
        entry: 터미널 엔트리 딕셔너리
        
    Returns:
        Dict: 검증 결과
    """
    validation_result = {
        "valid": True,
        "errors": []
    }
    
    if not isinstance(entry, dict):
        validation_result["errors"].append("Terminal entry must be a dictionary")
        validation_result["valid"] = False
        return validation_result
    
    # 필수 필드 확인
    required_fields = ["type", "content", "timestamp"]
    
    for field in required_fields:
        if field not in entry:
            validation_result["errors"].append(f"Missing required field: {field}")
            validation_result["valid"] = False
    
    # 터미널 엔트리 타입 확인
    valid_types = ["command", "output"]
    if "type" in entry and entry["type"] not in valid_types:
        validation_result["errors"].append(f"Invalid terminal entry type: {entry['type']}")
        validation_result["valid"] = False
    
    return validation_result


def validate_file_path(file_path: str, required_extension: Optional[str] = None) -> Dict[str, Any]:
    """파일 경로 검증
    
    Args:
        file_path: 파일 경로
        required_extension: 필수 확장자 (선택적)
        
    Returns:
        Dict: 검증 결과
    """
    validation_result = {
        "valid": True,
        "errors": []
    }
    
    if not file_path:
        validation_result["errors"].append("Empty file path")
        validation_result["valid"] = False
        return validation_result
    
    # 확장자 확인
    if required_extension:
        if not file_path.endswith(required_extension):
            validation_result["errors"].append(f"File must have {required_extension} extension")
            validation_result["valid"] = False
    
    # 경로 안전성 확인
    if ".." in file_path:
        validation_result["errors"].append("Path traversal detected")
        validation_result["valid"] = False
    
    return validation_result


def is_safe_html_content(content: str) -> bool:
    """HTML 내용 안전성 확인
    
    Args:
        content: HTML 내용
        
    Returns:
        bool: 안전하면 True
    """
    # 위험한 HTML 태그 확인
    dangerous_tags = ["<script", "<iframe", "<object", "<embed", "<link", "<meta"]
    
    content_lower = content.lower()
    
    for tag in dangerous_tags:
        if tag in content_lower:
            return False
    
    return True


def validate_workflow_execution_state() -> Dict[str, Any]:
    """워크플로우 실행 상태 검증
    
    Returns:
        Dict: 검증 결과
    """
    validation_result = {
        "can_execute": True,
        "errors": []
    }
    
    # 실행기 준비 상태 확인
    if not st.session_state.get(SESSION_KEY_EXECUTOR_READY, False):
        validation_result["errors"].append("Executor not ready")
        validation_result["can_execute"] = False
    
    # 현재 실행 중인 워크플로우 확인
    if st.session_state.get("workflow_running", False):
        validation_result["errors"].append("Another workflow is already running")
        validation_result["can_execute"] = False
    
    # 모델 선택 확인
    if not st.session_state.get(SESSION_KEY_CURRENT_MODEL):
        validation_result["errors"].append("No model selected")
        validation_result["can_execute"] = False
    
    return validation_result
