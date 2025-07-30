"""
Decepticon Agents Manager - 에이전트 정보 중앙 관리
디자인 요소는 static/config/agents.json에서 로드
순수 로직만 포함 (매칭, 정규화, 설정 관리)
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional


class AgentManager:
    """에이전트 정보 관리 클래스 - 설정 파일 기반"""
    
    _config = None
    _config_path = None
    
    @classmethod
    def _load_config(cls):
        """설정 파일 로드 (캐싱)"""
        if cls._config is None:
            # 프로젝트 루트에서 설정 파일 경로 찾기
            current_dir = Path(__file__).parent
            project_root = current_dir.parent.parent  # src/utils/agents.py -> project_root
            config_path = project_root / "static" / "config" / "agents.json"
            
            cls._config_path = config_path
            
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    cls._config = json.load(f)
            except FileNotFoundError:
                # 설정 파일이 없으면 기본값 사용
                cls._config = {
                    "colors": {"cli": {}, "frontend": {}},
                    "avatars": {},
                    "css_classes": {},
                    "display_names": {}
                }
        
        return cls._config
    
    @classmethod
    def normalize_agent_name(cls, agent_name: str) -> str:
        """
        에이전트 이름 정규화 - CLI와 Frontend 통일된 매칭 로직
        모든 플랫폼에서 동일한 정규화 결과 보장
        """
        if not agent_name or not isinstance(agent_name, str):
            return ""
        
        # 소문자로 변환
        agent_name_lower = agent_name.lower()
        
        # 통일된 매칭 로직 (우선순위 순)
        if "planner" in agent_name_lower:
            return "planner"
        elif "reconnaissance" in agent_name_lower:
            return "reconnaissance"  
        elif "initial_access" in agent_name_lower or "initial" in agent_name_lower:
            return "initial_access"  # 통일: initial_access로
        elif "execution" in agent_name_lower:
            return "execution"
        elif "persistence" in agent_name_lower:
            return "persistence"
        elif "privilege_escalation" in agent_name_lower or "privilege" in agent_name_lower:
            return "privilege_escalation"  # 통일: privilege_escalation로
        elif "defense_evasion" in agent_name_lower or "defense" in agent_name_lower or "evasion" in agent_name_lower:
            return "defense_evasion"  # 통일: defense_evasion로
        elif "summary" in agent_name_lower:
            return "summary"
        elif "tool" in agent_name_lower:
            return "tool"
        elif "supervisor" in agent_name_lower:
            return "supervisor"
        else:
            return ""
    
    @classmethod
    def get_cli_color(cls, agent_name: str) -> str:
        """CLI용 색상 반환 (Rich 색상명)"""
        config = cls._load_config()
        normalized = cls.normalize_agent_name(agent_name)
        
        if normalized:
            return config["colors"]["cli"].get(normalized, config["colors"]["cli"].get("default", "blue"))
        return config["colors"]["cli"].get("default", "blue")
    
    @classmethod 
    def get_frontend_color(cls, agent_name: str) -> str:
        """Frontend용 색상 반환 (Hex 코드)"""
        config = cls._load_config()
        normalized = cls.normalize_agent_name(agent_name)
        
        if normalized:
            return config["colors"]["frontend"].get(normalized, config["colors"]["frontend"].get("default", "#adb5bd"))
        return config["colors"]["frontend"].get("default", "#adb5bd")
    
    @classmethod
    def get_avatar(cls, agent_name: str) -> str:
        """에이전트 아바타 반환"""
        config = cls._load_config()
        normalized = cls.normalize_agent_name(agent_name)
        
        if normalized:
            return config["avatars"].get(normalized, config["avatars"].get("default", "🤖"))
        return config["avatars"].get("default", "🤖")
    
    @classmethod
    def get_css_class(cls, agent_name: str) -> str:
        """CSS 클래스명 반환"""
        config = cls._load_config()
        normalized = cls.normalize_agent_name(agent_name)
        
        if normalized:
            return config["css_classes"].get(normalized, config["css_classes"].get("default", "agent-message"))
        return config["css_classes"].get("default", "agent-message")
    
    @classmethod
    def get_display_name(cls, agent_name: str) -> str:
        """표시용 이름 반환"""
        if not agent_name or agent_name == "Unknown":
            config = cls._load_config()
            return config["display_names"].get("default", "Unknown Agent")
        
        config = cls._load_config()
        normalized = cls.normalize_agent_name(agent_name)
        
        if normalized:
            return config["display_names"].get(normalized, cls._format_fallback_name(agent_name))
        
        # 정규화된 이름이 없으면 원본을 포맷팅해서 반환
        return cls._format_fallback_name(agent_name)
    
    @classmethod
    def _format_fallback_name(cls, agent_name: str) -> str:
        """설정에 없는 에이전트 이름을 포맷팅"""
        if "_" in agent_name:
            return agent_name.replace("_", " ").title()
        return agent_name.capitalize()
    
    @classmethod
    def get_agent_info(cls, agent_name: str) -> Dict[str, str]:
        """에이전트의 모든 정보를 한 번에 반환"""
        return {
            "cli_color": cls.get_cli_color(agent_name),
            "frontend_color": cls.get_frontend_color(agent_name),
            "avatar": cls.get_avatar(agent_name),
            "css_class": cls.get_css_class(agent_name),
            "display_name": cls.get_display_name(agent_name),
            "normalized_name": cls.normalize_agent_name(agent_name)
        }
    
    @classmethod
    def list_all_agents(cls) -> Dict[str, Dict[str, str]]:
        """설정 파일에 정의된 모든 에이전트 정보 목록 반환"""
        config = cls._load_config()
        agents = {}
        
        # CLI 색상 키를 기준으로 에이전트 목록 구성
        for agent_key in config["colors"]["cli"].keys():
            if agent_key != "default":  # default는 제외
                agents[agent_key] = cls.get_agent_info(agent_key)
        
        return agents
    
    @classmethod
    def reload_config(cls):
        """설정 파일 강제 재로드"""
        cls._config = None
        return cls._load_config()
    
    @classmethod
    def get_config_path(cls) -> Optional[str]:
        """현재 사용 중인 설정 파일 경로 반환"""
        cls._load_config()  # 설정 로드해서 경로 설정
        return str(cls._config_path) if cls._config_path else None
