"""
모델 선택 UI 컴포넌트 (리팩토링됨 - 순수 UI 로직)
모델 선택 인터페이스 렌더링만 담당
"""

import streamlit as st
import time
from typing import Dict, Any, List, Optional, Tuple, Callable
from frontend.web.utils.constants import PROVIDERS


class ModelSelectionComponent:
    """모델 선택 UI 컴포넌트"""
    
    def __init__(self):
        """컴포넌트 초기화"""
        pass
    
    def get_provider_info(self, provider: str) -> Dict[str, str]:
        """프로바이더 정보 반환
        
        Args:
            provider: 프로바이더 이름
            
        Returns:
            Dict: 프로바이더 정보
        """
        provider_info = {
            "Anthropic": {"name": "Anthropic"},
            "OpenAI": {"name": "OpenAI"},
            "DeepSeek": {"name": "DeepSeek"},
            "Gemini": {"name": "Gemini"},
            "Groq": {"name": "Groq"},
            "Ollama": {"name": "Ollama"}
        }
        return provider_info.get(provider, {"name": provider})
    
    def display_loading_state(self, message: str = "Loading available models..."):
        """로딩 상태 표시
        
        Args:
            message: 로딩 메시지
        """
        with st.spinner(message):
            time.sleep(0.1)  # 최소 표시 시간
    
    def display_error_state(self, error_msg: str, info_msg: str = None):
        """에러 상태 표시
        
        Args:
            error_msg: 에러 메시지
            info_msg: 추가 정보 메시지
        """
        st.error(error_msg)
        if info_msg:
            st.info(info_msg)
    
    def display_success_message(self, message: str):
        """성공 메시지 표시
        
        Args:
            message: 성공 메시지
        """
        st.success(message)
    
    def render_page_header(self):
        """페이지 헤더 렌더링"""
        st.markdown("### Select AI Model")
        st.markdown("Choose the AI model for your red team operations")
    
    def render_current_model_info(self, current_model: Optional[Dict[str, Any]] = None):
        """현재 선택된 모델 정보 표시
        
        Args:
            current_model: 현재 모델 정보
            
        Returns:
            bool: 모델 변경 버튼이 클릭되었는지 여부
        """
        if current_model:
            model_name = current_model.get('display_name', 'Unknown')
            st.success(f"✅ Current Model: {model_name}")
            
            # 모델 변경 확인
            if st.button("🔄 Change Model", use_container_width=True):
                return True
            
            st.divider()
        
        return False
    
    def render_provider_selection(
        self, 
        providers: List[str], 
        default_index: int = 0
    ) -> str:
        """프로바이더 선택 UI 렌더링
        
        Args:
            providers: 사용 가능한 프로바이더 목록
            default_index: 기본 선택 인덱스
            
        Returns:
            str: 선택된 프로바이더
        """
        provider_options = []
        provider_mapping = {}
        
        for provider_key in providers:
            provider_info = self.get_provider_info(provider_key)
            display_text = provider_info['name']
            provider_options.append(display_text)
            provider_mapping[display_text] = provider_key
        
        selected_provider_display = st.selectbox(
            "Provider",
            options=provider_options,
            index=default_index,
            help="Choose your service provider",
            key="provider_selection"
        )
        
        return provider_mapping[selected_provider_display]
    
    def render_model_selection(
        self,
        models: List[Dict[str, Any]],
        selected_provider: str,
        default_index: int = 0
    ) -> Optional[str]:
        """모델 선택 UI 렌더링
        
        Args:
            models: 사용 가능한 모델 목록
            selected_provider: 선택된 프로바이더
            default_index: 기본 선택 인덱스
            
        Returns:
            Optional[str]: 선택된 모델 표시 이름
        """
        if not models:
            st.warning(f"No models available for {selected_provider}")
            return None
        
        model_options = []
        model_mapping = {}
        
        for model in models:
            # Clean model name - remove provider prefix and simplify
            display_name = model.get('display_name', 'Unknown Model')
            
            # Clean up display name
            for prefix in [f"[{selected_provider}]", f"[{selected_provider.lower()}]", 
                         f"{selected_provider}", f"{selected_provider.lower()}"]:
                if prefix in display_name:
                    display_name = display_name.replace(f"{prefix} ", "").replace(prefix, "")
            
            model_options.append(display_name)
            model_mapping[display_name] = model
        
        selected_model_display = st.selectbox(
            "Model",
            options=model_options,
            index=default_index,
            help="Choose the specific model variant",
            key="model_selection"
        )
        
        return selected_model_display
    
    def render_initialize_button(self) -> bool:
        """초기화 버튼 렌더링
        
        Returns:
            bool: 버튼이 클릭되었는지 여부
        """
        return st.button("Initialize AI Agents", type="primary", use_container_width=True)
    
    def render_complete_selection_ui(
        self,
        providers_data: Dict[str, List[Dict[str, Any]]],
        current_model: Optional[Dict[str, Any]] = None,
        default_provider: Optional[str] = None,
        default_model: Optional[Dict[str, Any]] = None,
        callbacks: Optional[Dict[str, Callable]] = None
    ) -> Optional[Dict[str, Any]]:
        """완전한 모델 선택 UI 렌더링
        
        Args:
            providers_data: 프로바이더별 모델 데이터
            current_model: 현재 선택된 모델
            default_provider: 기본 프로바이더
            default_model: 기본 모델
            callbacks: 콜백 함수들
            
        Returns:
            Optional[Dict]: 선택된 모델 정보
        """
        if callbacks is None:
            callbacks = {}
        
        # 페이지 헤더
        self.render_page_header()
        
        # 현재 모델 정보
        if self.render_current_model_info(current_model):
            if "on_model_change" in callbacks:
                callbacks["on_model_change"]()
            return None
        
        # 프로바이더 목록 준비
        providers = list(providers_data.keys())
        
        # 기본 프로바이더 인덱스 찾기
        default_provider_index = 0
        if default_provider and default_provider in providers:
            default_provider_index = providers.index(default_provider)
        
        # 프로바이더 선택
        selected_provider = self.render_provider_selection(providers, default_provider_index)
        
        # 모델 선택
        if selected_provider in providers_data:
            models = providers_data[selected_provider]
            
            # 기본 모델 인덱스 찾기
            default_model_index = 0
            if default_model and models:
                for idx, model in enumerate(models):
                    if model.get('model_name') == default_model.get('model_name'):
                        default_model_index = idx
                        break
            
            # 모델 선택 UI
            selected_model_display = self.render_model_selection(
                models, selected_provider, default_model_index
            )
            
            if selected_model_display:
                # 선택된 모델 찾기
                selected_model = None
                for model in models:
                    display_name = model.get('display_name', 'Unknown Model')
                    # 동일한 정리 로직 적용
                    for prefix in [f"[{selected_provider}]", f"[{selected_provider.lower()}]", 
                                 f"{selected_provider}", f"{selected_provider.lower()}"]:
                        if prefix in display_name:
                            display_name = display_name.replace(f"{prefix} ", "").replace(prefix, "")
                    
                    if display_name == selected_model_display:
                        selected_model = model
                        break
                
                # 초기화 버튼
                if self.render_initialize_button():
                    return selected_model
        
        return None
    
    def show_loading_screen(self, model_info: Dict[str, Any]):
        """로딩 화면 표시
        
        Args:
            model_info: 모델 정보
        """
        provider_info = self.get_provider_info(model_info.get('provider', 'Unknown'))
        
        # 중앙 정렬 로딩 컨텐츠
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown(f"""
            <div style="text-align: center; padding: 60px 0;">
                <h2>Setting up {model_info.get('display_name', 'Model')}</h2>
                <p style="opacity: 0.7;">Initializing AI agents for red team operations...</p>
            </div>
            """, unsafe_allow_html=True)
            
            # 진행률 표시
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(0.01)
                progress_bar.progress(i + 1)
        
        return st.empty()
    
    def render_initialization_ui(
        self, 
        model_info: Dict[str, Any],
        status: str = "initializing",
        error_message: str = None
    ):
        """초기화 UI 렌더링
        
        Args:
            model_info: 모델 정보
            status: 초기화 상태 ("initializing", "success", "error")
            error_message: 에러 메시지 (에러 상태인 경우)
            
        Returns:
            str: 사용자 액션 ("retry", "back", None)
        """
        model_name = model_info.get('display_name', 'Model')
        
        if status == "initializing":
            with st.spinner(f"Initializing {model_name}..."):
                time.sleep(0.1)
        
        elif status == "success":
            st.success(f"✅ {model_name} initialized successfully!")
            time.sleep(1.0)
            return "success"
        
        elif status == "error":
            st.error(f"❌ Initialization failed: {error_message or 'Unknown error'}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Retry", use_container_width=True):
                    return "retry"
            with col2:
                if st.button("⬅️ Back", use_container_width=True):
                    return "back"
        
        return None
    
    def display_provider_status(self, status_info: Dict[str, Any]):
        """프로바이더 상태 정보 표시
        
        Args:
            status_info: 상태 정보
        """
        if status_info.get("type") == "success" and "ollama_message" in status_info:
            st.success(status_info["ollama_message"])
