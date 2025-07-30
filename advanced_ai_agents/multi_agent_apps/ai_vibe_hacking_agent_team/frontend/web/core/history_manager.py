"""
Chat History Business Logic (리팩토링됨)
세션 로그 관리, 필터링, 익스포트 등 히스토리 관련 비즈니스 로직
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from frontend.web.utils.validation import validate_file_path


class ChatHistoryManager:
    """채팅 히스토리 관리 비즈니스 로직"""
    
    def __init__(self):
        """히스토리 매니저 초기화"""
        self.logger = None
        self._initialize_logger()
    
    def _initialize_logger(self):
        """로거 초기화"""
        try:
            from src.utils.logging.logger import get_logger
            self.logger = get_logger()
        except ImportError:
            self.logger = None
    
    def load_sessions(self, limit: int = 20) -> Dict[str, Any]:
        """세션 목록 로드
        
        Args:
            limit: 로드할 세션 수 제한
            
        Returns:
            Dict: 로드 결과
        """
        if not self.logger:
            return {
                "success": False,
                "error": "Logger not available",
                "sessions": []
            }
        
        try:
            sessions = self.logger.list_sessions(limit=limit)
            
            # 세션 데이터 처리
            processed_sessions = []
            for session in sessions:
                processed_session = self._process_session_data(session)
                processed_sessions.append(processed_session)
            
            return {
                "success": True,
                "sessions": processed_sessions,
                "total_count": len(sessions)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "sessions": []
            }
    
    def _process_session_data(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """세션 데이터 처리
        
        Args:
            session: 원본 세션 데이터
            
        Returns:
            Dict: 처리된 세션 데이터
        """
        processed = session.copy()
        
        # 시간 포맷팅
        if 'start_time' in session:
            processed['formatted_time'] = self._format_session_time(session['start_time'])
        
        # 미리보기 텍스트 처리
        if 'preview' in session and session['preview']:
            preview = session['preview']
            if len(preview) > 100:
                processed['preview'] = preview[:100] + "..."
            else:
                processed['preview'] = preview
        else:
            processed['preview'] = "No user input found"
        
        # 세션 ID 단축
        if 'session_id' in session:
            processed['short_session_id'] = session['session_id'][:16] + "..."
        
        return processed
    
    def _format_session_time(self, time_str: str) -> str:
        """세션 시간 포맷팅
        
        Args:
            time_str: 원본 시간 문자열
            
        Returns:
            str: 포맷된 시간 문자열
        """
        try:
            dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return time_str[:19] if len(time_str) > 19 else time_str
    
    def filter_sessions(
        self, 
        sessions: List[Dict[str, Any]], 
        date_filter: str = "All",
        sort_option: str = "Newest First"
    ) -> List[Dict[str, Any]]:
        """세션 필터링 및 정렬
        
        Args:
            sessions: 세션 목록
            date_filter: 날짜 필터 ("All", "Today", "Last 7 days", "Last 30 days")
            sort_option: 정렬 옵션 ("Newest First", "Oldest First", "Most Events")
            
        Returns:
            List: 필터링된 세션 목록
        """
        filtered_sessions = sessions.copy()
        
        # 날짜 필터링
        if date_filter != "All":
            filtered_sessions = self._apply_date_filter(filtered_sessions, date_filter)
        
        # 정렬
        filtered_sessions = self._apply_sorting(filtered_sessions, sort_option)
        
        return filtered_sessions
    
    def _apply_date_filter(self, sessions: List[Dict[str, Any]], date_filter: str) -> List[Dict[str, Any]]:
        """날짜 필터 적용
        
        Args:
            sessions: 세션 목록
            date_filter: 날짜 필터
            
        Returns:
            List: 필터링된 세션 목록
        """
        now = datetime.now()
        filtered = []
        
        for session in sessions:
            try:
                session_time = datetime.fromisoformat(session['start_time'].replace('Z', '+00:00'))
                days_diff = (now - session_time).days
                
                if date_filter == "Today" and days_diff == 0:
                    filtered.append(session)
                elif date_filter == "Last 7 days" and days_diff <= 7:
                    filtered.append(session)
                elif date_filter == "Last 30 days" and days_diff <= 30:
                    filtered.append(session)
                    
            except:
                # 날짜 파싱 실패 시 포함
                filtered.append(session)
        
        return filtered
    
    def _apply_sorting(self, sessions: List[Dict[str, Any]], sort_option: str) -> List[Dict[str, Any]]:
        """정렬 적용
        
        Args:
            sessions: 세션 목록
            sort_option: 정렬 옵션
            
        Returns:
            List: 정렬된 세션 목록
        """
        if sort_option == "Newest First":
            return sorted(sessions, key=lambda x: x.get('start_time', ''), reverse=True)
        elif sort_option == "Oldest First":
            return sorted(sessions, key=lambda x: x.get('start_time', ''))
        elif sort_option == "Most Events":
            return sorted(sessions, key=lambda x: x.get('event_count', 0), reverse=True)
        
        return sessions
    
    def prepare_export_data(self, session_id: str) -> Optional[str]:
        """세션 익스포트 데이터 준비
        
        Args:
            session_id: 세션 ID
            
        Returns:
            Optional[str]: JSON 형태의 익스포트 데이터
        """
        if not self.logger:
            return None
        
        try:
            # 세션 데이터 로드
            session = self.logger.load_session(session_id)
            if not session:
                # 직접 파일 검색 시도
                session = self._load_session_from_file(session_id)
                
                if not session:
                    return None
            
            # session이 MinimalSession 객체인 경우와 dict인 경우 모두 처리
            if hasattr(session, 'events'):  # MinimalSession 객체
                events_data = [
                    event.to_dict() if hasattr(event, 'to_dict') else event 
                    for event in session.events
                ]
                session_info = {
                    "session_id": session.session_id,
                    "start_time": session.start_time,
                    "total_events": len(session.events)
                }
                # 모델 정보 추가
                if hasattr(session, 'model') and session.model:
                    session_info["model"] = session.model
            else:  # dict 데이터
                events_data = session.get('events', [])
                session_info = {
                    "session_id": session.get('session_id', session_id),
                    "start_time": session.get('start_time', 'Unknown'),
                    "total_events": len(events_data)
                }
                # 모델 정보 추가
                if session.get('model'):
                    session_info["model"] = session.get('model')
            
            # 익스포트용 데이터 구조 생성
            export_data = {
                "session_info": session_info,
                "events": events_data,
                "export_metadata": {
                    "exported_at": datetime.now().isoformat(),
                    "exported_by": "Decepticon Log Manager",
                    "version": "1.0"
                }
            }
            
            # JSON 문자열로 변환
            return json.dumps(export_data, indent=2, ensure_ascii=False)
            
        except Exception as e:
            print(f"Export error: {e}")
            return None
    
    def _load_session_from_file(self, session_id: str) -> Optional[Dict[str, Any]]:
        """파일에서 세션 데이터 직접 로드
        
        Args:
            session_id: 세션 ID
            
        Returns:
            Optional[Dict]: 세션 데이터
        """
        try:
            # logs 폴더에서 세션 파일 검색
            logs_path = Path("logs")
            for session_file in logs_path.rglob(f"session_{session_id}.json"):
                with open(session_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading session file: {e}")
        
        return None
    
    def start_replay(self, session_id: str) -> Dict[str, Any]:
        """세션 재현 시작
        
        Args:
            session_id: 재현할 세션 ID
            
        Returns:
            Dict: 재현 시작 결과
        """
        # 세션 존재 여부 확인
        session_data = self._load_session_from_file(session_id)
        if not session_data and self.logger:
            session_data = self.logger.load_session(session_id)
        
        if not session_data:
            return {
                "success": False,
                "error": f"Session {session_id} not found"
            }
        
        return {
            "success": True,
            "session_id": session_id,
            "message": f"Starting replay for session {session_id[:16]}..."
        }
    
    def get_session_details(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 상세 정보 가져오기
        
        Args:
            session_id: 세션 ID
            
        Returns:
            Optional[Dict]: 세션 상세 정보
        """
        if not self.logger:
            return None
        
        try:
            session = self.logger.load_session(session_id)
            if session:
                return self._process_session_data(session.__dict__ if hasattr(session, '__dict__') else session)
        except Exception as e:
            print(f"Error loading session details: {e}")
        
        return None
    
    def validate_session_id(self, session_id: str) -> bool:
        """세션 ID 유효성 검증
        
        Args:
            session_id: 검증할 세션 ID
            
        Returns:
            bool: 유효성 여부
        """
        if not session_id or len(session_id) < 8:
            return False
        
        # UUID 형태인지 간단히 확인
        return len(session_id) >= 32 and all(c.isalnum() or c == '-' for c in session_id)


# 전역 히스토리 매니저 인스턴스
_history_manager = None

def get_history_manager() -> ChatHistoryManager:
    """히스토리 매니저 싱글톤 인스턴스 반환"""
    global _history_manager
    if _history_manager is None:
        _history_manager = ChatHistoryManager()
    return _history_manager
