"""
OpenRouter API 지원 모듈
"""

from langchain_openai import ChatOpenAI
import os


def create_openrouter_model(model_name: str, temperature: float = 0.0):
    """
    OpenRouter 모델 생성 (temperature=0 고정)
    
    Args:
        model_name: OpenRouter 모델 이름 (예: "deepseek/deepseek-chat-v3-0324:free")
        temperature: 온도 설정 (고정값 0.0)
    
    Returns:
        ChatOpenAI: OpenRouter API를 사용하는 LangChain 모델
    
    Raises:
        ValueError: OPENROUTER_API_KEY가 설정되지 않은 경우
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY 환경변수가 설정되지 않았습니다. "
            ".env 파일에 OPENROUTER_API_KEY=your-key 를 추가하세요."
        )
    
    return ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        temperature=0,  # 고정값
        model_kwargs={
            "extra_headers": {
                "HTTP-Referer": "https://purplelab.framer.ai",
                "X-Title": "Decepticon",
            }
        }
    )


def get_openrouter_api_key() -> str:
    """OpenRouter API 키 조회"""
    return os.getenv("OPENROUTER_API_KEY", "")


def is_openrouter_available() -> bool:
    """OpenRouter 사용 가능 여부 확인"""
    return bool(get_openrouter_api_key())
