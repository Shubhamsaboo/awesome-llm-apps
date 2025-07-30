"""
터미널 데이터 처리 로직 (리팩토링됨 - 순수 비즈니스 로직)
터미널 메시지의 변환, 정리, 처리 로직
"""

import re
from datetime import datetime
from typing import Dict, Any, List
import streamlit as st


class TerminalProcessor:
    """터미널 데이터 처리 핵심 로직"""
    
    def __init__(self):
        """터미널 프로세서 초기화"""
        self.processed_messages = set()  # 처리된 메시지 추적
    
    def clean_command(self, command: str) -> str:
        """명령어 정리 로직
        
        Args:
            command: 원본 명령어
            
        Returns:
            str: 정리된 명령어
        """
        if not isinstance(command, str):
            command = str(command)
        
        # 앞뒤 공백 제거
        command = command.strip()
        
        # 여러 줄인 경우 첫 번째 줄만 사용
        if '\n' in command:
            command = command.split('\n')[0].strip()
        
        # 불필요한 프리픽스 제거
        prefixes_to_remove = [
            'Running command:',
            'Executing:',
            'Command:',
            'Execute:',
            '$',
            '# '
        ]
        
        for prefix in prefixes_to_remove:
            if command.startswith(prefix):
                command = command[len(prefix):].strip()
        
        return command
    
    def sanitize_output(self, output: str) -> str:
        """출력 내용 정리 로직
        
        Args:
            output: 원본 출력
            
        Returns:
            str: 정리된 출력
        """
        if not isinstance(output, str):
            output = str(output)
        
        # HTML 이스케이프 처리
        output = output.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        # 줄바꿈 처리
        output = output.replace("\n", "<br>")
        
        return output
    
    def extract_command_from_line(self, line: str) -> str:
        """라인에서 실제 명령어 추출
        
        Args:
            line: 명령어가 포함된 라인
            
        Returns:
            str: 추출된 명령어
        """
        line = line.strip()
        
        # 여러 패턴으로 명령어 추출 시도
        patterns = [
            r'(?:command|executing|running):\s*(.+)',
            r'\$\s*(.+)',
            r'#\s*(.+)',
            r'^(.+?)\s*$'  # 마지막으로 전체 라인 사용
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                command = match.group(1).strip()
                if command:
                    return command
        
        return line
    
    def process_frontend_messages(self, frontend_messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """프론트엔드 메시지를 터미널 히스토리로 처리
        
        Args:
            frontend_messages: 처리할 메시지 목록
            
        Returns:
            List[Dict]: 터미널 히스토리 엔트리 목록
        """
        terminal_entries = []
        
        if not frontend_messages:
            return terminal_entries
        
        for message in frontend_messages:
            message_id = message.get("id")
            
            # 이미 처리한 메시지는 건너뛰기
            if message_id in self.processed_messages:
                continue
                
            message_type = message.get("type")
            
            # 도구 메시지 처리
            if message_type == "tool":
                tool_display_name = message.get("tool_display_name", "Tool")
                content = message.get("content", "")
                
                # 터미널 관련 도구 식별
                is_terminal_tool = self._is_terminal_tool(tool_display_name)
                
                if is_terminal_tool:
                    entries = self._process_terminal_tool_message(tool_display_name, content)
                    terminal_entries.extend(entries)
                else:
                    # 비-터미널 도구
                    if content and content.strip():
                        terminal_entries.append({
                            "type": "command",
                            "content": tool_display_name,
                            "timestamp": datetime.now().strftime("%H:%M:%S")
                        })
                        terminal_entries.append({
                            "type": "output",
                            "content": self.sanitize_output(content),
                            "timestamp": datetime.now().strftime("%H:%M:%S")
                        })
                
                # 처리된 메시지로 표시
                self.processed_messages.add(message_id)
        
        return terminal_entries
    
    def _is_terminal_tool(self, tool_display_name: str) -> bool:
        """터미널 도구인지 확인
        
        Args:
            tool_display_name: 도구 표시 이름
            
        Returns:
            bool: 터미널 도구 여부
        """
        return (
            "terminal" in tool_display_name.lower() or 
            "command" in tool_display_name.lower() or
            "exec" in tool_display_name.lower() or
            "shell" in tool_display_name.lower()
        )
    
    def _process_terminal_tool_message(self, tool_display_name: str, content: str) -> List[Dict[str, Any]]:
        """터미널 도구 메시지 처리
        
        Args:
            tool_display_name: 도구 표시 이름
            content: 메시지 내용
            
        Returns:
            List[Dict]: 터미널 엔트리 목록
        """
        entries = []
        
        # 내용에서 명령어와 출력 분리 시도
        lines = content.split('\n') if content else []
        
        # 명령어 찾기 시도
        command_found = False
        for i, line in enumerate(lines):
            line = line.strip()
            # 명령어 패턴 확인
            if any(indicator in line.lower() for indicator in ['$', '#', 'command:', 'executing:', 'running:']):
                # 이 라인을 명령어로 처리
                cleaned_command = self.extract_command_from_line(line)
                if cleaned_command:
                    entries.append({
                        "type": "command",
                        "content": self.clean_command(cleaned_command),
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
                    command_found = True
                    
                    # 나머지 라인들을 출력으로 처리
                    remaining_output = '\n'.join(lines[i+1:])
                    if remaining_output.strip():
                        entries.append({
                            "type": "output",
                            "content": self.sanitize_output(remaining_output.strip()),
                            "timestamp": datetime.now().strftime("%H:%M:%S")
                        })
                    break
        
        # 명령어를 찾지 못한 경우 전체를 출력으로 처리
        if not command_found and content.strip():
            # 도구 이름을 명령어로 추가
            entries.append({
                "type": "command",
                "content": self.clean_command(f"{tool_display_name.lower()}"),
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })
            entries.append({
                "type": "output",
                "content": self.sanitize_output(content),
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })
        
        return entries
    
    def process_structured_messages(self, structured_messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """구조화된 메시지를 터미널 히스토리로 처리
        
        Args:
            structured_messages: 구조화된 메시지 목록
            
        Returns:
            List[Dict]: 터미널 히스토리 엔트리 목록
        """
        terminal_entries = []
        
        if not structured_messages:
            return terminal_entries
        
        # 메시지 순회 및 처리
        for message in structured_messages:
            message_id = message.get("id")
            
            # 이미 처리한 메시지는 건너뜀
            if message_id in self.processed_messages:
                continue
                
            message_type = message.get("type")
            
            # 도구 메시지 처리
            if message_type == "tool":
                tool_display_name = message.get("tool_display_name", "Tool")
                content = message.get("content", "")
                
                if tool_display_name and content:
                    # 도구 이름을 명령어로 표시
                    terminal_entries.append({
                        "type": "command",
                        "content": self.clean_command(tool_display_name),
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
                    # 출력 추가
                    terminal_entries.append({
                        "type": "output",
                        "content": self.sanitize_output(content),
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
                    
                    self.processed_messages.add(message_id)
        
        return terminal_entries
    
    def initialize_terminal_state(self):
        """터미널 상태 초기화"""
        if "terminal_history" not in st.session_state:
            st.session_state.terminal_history = []
    
    def clear_terminal_state(self):
        """터미널 상태 완전 초기화"""
        self.processed_messages = set()
        st.session_state.terminal_history = []
    
    def get_terminal_history(self) -> List[Dict[str, Any]]:
        """현재 터미널 히스토리 반환"""
        return st.session_state.get("terminal_history", [])
    
    def update_terminal_history_realtime(self, new_entries: List[Dict[str, Any]]):
        """터미널 히스토리 실시간 업데이트 (더 이상 사용 안함)
        
        Args:
            new_entries: 새로 추가할 터미널 엔트리
        """
        # 단순한 히스토리 업데이트로 대체
        self.update_terminal_history(new_entries)
    
    def update_terminal_history(self, new_entries: List[Dict[str, Any]]):
        """터미널 히스토리 업데이트 (기본 버전)
        
        Args:
            new_entries: 새로 추가할 터미널 엔트리
        """
        if "terminal_history" not in st.session_state:
            st.session_state.terminal_history = []
        
        st.session_state.terminal_history.extend(new_entries)
    
    def _trigger_terminal_ui_update(self):
        """터미널 UI 실시간 업데이트 트리거 (더 이상 사용 안함)"""
        # 더 이상 실시간 업데이트 트리거 안함
        pass


# 전역 터미널 프로세서 인스턴스
_terminal_processor = None

def get_terminal_processor() -> TerminalProcessor:
    """터미널 프로세서 싱글톤 인스턴스 반환"""
    global _terminal_processor
    if _terminal_processor is None:
        _terminal_processor = TerminalProcessor()
    return _terminal_processor
