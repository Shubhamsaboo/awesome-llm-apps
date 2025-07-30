# DecepticonV2 LLM Module

이 모듈은 DecepticonV2 프로젝트에서 다양한 LLM 모델을 통합적으로 관리하고 사용할 수 있도록 설계된 통합 인터페이스입니다. langchain의 `init_chat_model`을 기반으로 하여 여러 provider를 지원합니다.

## 지원하는 Provider

- **OpenAI**: GPT-4o, GPT-4o Mini, O1 Preview, O1 Mini
- **Anthropic**: Claude 3.5 Sonnet, Claude 3.5 Haiku
- **Google**: Gemini 2.0 Flash, Gemini 1.5 Pro
- **Groq**: Llama 3.1 모델들 (고속 추론)
- **Mistral AI**: Mistral Large, Mistral Small
- **xAI (Grok)**: Grok Beta
- **Perplexity**: 온라인 검색 기능이 있는 Sonar 모델들
- **DeepSeek**: DeepSeek V3, DeepSeek R1 (추론 모델)
- **Azure OpenAI**: Azure 환경의 OpenAI 모델들
- **Ollama**: 로컬 모델들

## 설치 및 설정

### 1. 필요한 패키지 설치

```bash
# 기본 패키지
pip install langchain langchain-core

# Provider별 패키지 (필요한 것만 설치)
pip install langchain-openai        # OpenAI
pip install langchain-anthropic     # Anthropic
pip install langchain-google-genai  # Google Gemini
pip install langchain-groq          # Groq
pip install langchain-mistralai     # Mistral AI
pip install langchain-xai           # xAI (Grok)
pip install langchain-perplexity    # Perplexity
pip install langchain-deepseek      # DeepSeek
pip install langchain-ollama        # Ollama
```

### 2. API 키 설정

`.env` 파일에 필요한 API 키를 설정하세요:

```env
# OpenAI
OPENAI_API_KEY=sk-...

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Google
GOOGLE_API_KEY=AIza...

# Groq
GROQ_API_KEY=gsk_...

# Mistral AI
MISTRAL_API_KEY=...

# xAI (Grok)
XAI_API_KEY=xai-...

# Perplexity
PPLX_API_KEY=pplx-...

# DeepSeek
DEEPSEEK_API_KEY=sk-...

# Azure OpenAI (추가로 AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT_NAME 필요)
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment
OPENAI_API_VERSION=2024-02-15-preview
```

### 3. Ollama 설정 (로컬 모델)

Ollama는 로컬에서 실행되는 모델들을 지원합니다. API 키가 필요하지 않지만, Ollama 서비스가 실행 중이어야 합니다.

#### Ollama 설치

```bash
# Windows/Mac/Linux
# https://ollama.ai/ 에서 다운로드

# 또는 curl로 설치 (Linux/Mac)
curl -fsSL https://ollama.ai/install.sh | sh
```

#### Ollama 실행

```bash
# Ollama 서비스 시작
ollama serve
```

#### 모델 다운로드

```bash
# 추천 모델들
ollama pull llama3.3:70b      # Meta의 최신 모델
ollama pull deepseek-r1:7b    # DeepSeek 추론 모델
ollama pull gemma3:27b        # Google Gemma 3
ollama pull phi4:14b          # Microsoft Phi-4
ollama pull qwen3:30b         # Alibaba Qwen 3

# 설치된 모델 확인
ollama list
```

#### 선택적 환경변수 설정

```env
# Ollama 호스트 설정 (기본값: localhost)
OLLAMA_HOST=localhost
OLLAMA_BASE_URL=http://localhost:11434
```

## 기본 사용법

### 1. 특정 모델 로드

```python
from src.utils.llm import load_llm

# Claude 3.5 Sonnet 로드
llm = load_llm("claude-3-5-sonnet-latest", "anthropic")

# GPT-4o 로드 (온도 설정)
llm = load_llm("gpt-4o", "openai", temperature=0.7)

# Ollama 모델 로드
llm = load_llm("llama3.3:70b", "ollama")

# DeepSeek 추론 모델 로드
llm = load_llm("deepseek-reasoner", "deepseek")

# 추가 파라미터와 함께
llm = load_llm(
    "gpt-4o-mini", 
    "openai",
    temperature=0.5,
    max_tokens=1000
)

# 모델 사용
response = llm.invoke("안녕하세요! 보안 테스트에 대해 설명해주세요.")
print(response.content)
```

### 2. 런타임에 모델 변경 가능한 설정

```python
from src.utils.llm import load_llm

# 모델을 지정하지 않으면 런타임에 변경 가능
llm = load_llm()

# Claude로 응답
response = llm.invoke(
    "보안 취약점 스캔에 대해 설명해주세요.",
    config={
        "configurable": {
            "model": "claude-3-5-sonnet-latest",
            "model_provider": "anthropic"
        }
    }
)

# GPT-4o로 응답
response = llm.invoke(
    "침투 테스트 방법론을 알려주세요.",
    config={
        "configurable": {
            "model": "gpt-4o",
            "model_provider": "openai"
        }
    }
)
```

### 3. 에이전트에서 사용

```python
from langgraph.prebuilt import create_react_agent
from src.utils.llm import load_llm

# 에이전트 생성
agent = create_react_agent(
    load_llm("claude-3-5-sonnet-latest", "anthropic"),
    tools=your_tools,
    name="SecurityAgent"
)
```

## 고급 사용법

### 1. 사용 가능한 모델 조회

```python
from src.utils.llm import list_available_models, list_available_providers

# 모든 모델 조회
models = list_available_models()
for model in models:
    status = "✅" if model["api_key_available"] else "❌"
    print(f"{status} {model['display_name']} - {model['description']}")

# Provider별 모델 조회
openai_models = list_available_models(provider="openai")

# Provider 목록 조회
providers = list_available_providers()
for provider in providers:
    print(f"{provider['display_name']}: {provider['model_count']} models")
```

### 2. 모델 선택 UI

```python
from src.utils.llm.selection import (
    create_model_selection_menu,
    get_model_from_selection,
    load_model_from_config
)

# UI용 모델 메뉴 생성
menu = create_model_selection_menu()
for item in menu:
    print(f"{item['display']}: {item['description']}")

# 사용자 선택 처리
selection = "anthropic:claude-3-5-sonnet-latest"
model_info = get_model_from_selection(selection)
llm = load_llm(model_info["model_name"], model_info["provider"])
```

### 4. Ollama 전용 기능

```python
from src.utils.llm import get_ollama_info, get_installed_ollama_models, check_ollama_connection

# Ollama 상태 확인
status = get_ollama_info()
print(f"Connected: {status['connected']}")
print(f"URL: {status['url']}")
print(f"Installed models: {status['installed_models']}")

# 연결 상태만 확인
connection = check_ollama_connection()
if connection["connected"]:
    print("✅ Ollama is running")
else:
    print(f"❌ Ollama error: {connection['error']}")

# 설치된 모델 목록
models = get_installed_ollama_models()
for model in models:
    print(f"  • {model}")

# Ollama 모델 사용 예시
if "llama3.3:70b" in models:
    llm = load_llm("llama3.3:70b", "ollama")
    response = llm.invoke("안녕하세요! 사이버 보안에 대해 설명해주세요.")
    print(response.content)
```

### 3. 설정 검증

```python
from src.utils.llm.selection import validate_model_config

config = {
    "model": "claude-3-5-sonnet-latest",
    "provider": "anthropic",
    "temperature": 0.0
}

result = validate_model_config(config)
if result["valid"]:
    print("✅ 설정이 유효합니다")
else:
    print(f"❌ 오류: {result['error']}")
    if "missing_env_var" in result:
        print(f"환경변수 설정 필요: {result['missing_env_var']}")
```

## CLI 도구

### 모델 테스트

```bash
# 대화형 모델 선택
python src/utils/llm/test_llm.py

# 특정 모델 테스트
python src/utils/llm/test_llm.py -m "claude-3-5-sonnet-latest" -p "anthropic"

# Ollama 모델 테스트
python src/utils/llm/test_llm.py -m "llama3.3:70b" -p "ollama"

# DeepSeek 모델 테스트
python src/utils/llm/test_llm.py -m "deepseek-chat" -p "deepseek"

# 채팅 모드
python src/utils/llm/test_llm.py -m "gpt-4o" -p "openai" --chat

# 사용 가능한 모델 목록
python src/utils/llm/test_llm.py --list

# 모델 정보 (Ollama 상태 포함)
python src/utils/llm/test_llm.py --info

# Ollama 상태만 확인
python src/utils/llm/test_llm.py --ollama
```

### 도움말 출력

```python
from src.utils.llm import print_model_selection_help

print_model_selection_help()
```

## 기존 코드 마이그레이션

### Before (기존 코드)

```python
from src.utils.llm1 import CLAUDE_AGENT_LLM

agent = create_react_agent(
    CLAUDE_AGENT_LLM,
    tools=tools
)
```

### After (새로운 코드)

```python
from src.utils.llm import load_llm

agent = create_react_agent(
    load_llm("claude-3-5-sonnet-latest", "anthropic"),
    tools=tools
)
```

### 런타임 모델 변경

```python
from src.utils.llm import load_llm

# 설정 가능한 에이전트
agent = create_react_agent(
    load_llm(),  # 모델 미지정 = 런타임 설정 가능
    tools=tools
)

# 실행 시 모델 지정
response = agent.invoke(
    {"messages": [("user", "침투 테스트 계획을 세워주세요")]},
    config={
        "configurable": {
            "model": "gpt-4o",
            "model_provider": "openai"
        }
    }
)
```

## 설정 파일

모델 설정은 `src/utils/llm/llm_models_config.json`에 저장됩니다. 사용자 정의 모델을 추가하려면:

```python
from src.utils.llm import LLMModelManager, LLMModelConfig, ModelProvider

manager = LLMModelManager()
custom_model = LLMModelConfig(
    display_name="Custom GPT-4",
    model_name="gpt-4-custom",
    provider=ModelProvider.OPENAI,
    description="커스텀 GPT-4 모델",
    context_length=128000,
    supports_tools=True,
    supports_streaming=True
)

manager.add_custom_model(custom_model)
```

## 문제 해결

### 1. API 키 오류

```
ValueError: API key not found for anthropic. Please set ANTHROPIC_API_KEY in your environment.
```

**해결책**: `.env` 파일에 해당 API 키를 추가하거나 환경변수로 설정

### 2. 패키지 누락 오류

```
ImportError: langchain-anthropic package not installed
```

**해결책**: 필요한 패키지 설치
```bash
pip install langchain-anthropic
```

### 3. 모델 추론 실패

대부분의 경우 API 키 문제이거나 모델명이 잘못된 경우입니다. `validate_model_config()`를 사용해 설정을 검증하세요.

### 4. Ollama 관련 문제

```
ValueError: Ollama is not running or not accessible
```

**해결책**:
1. Ollama 서비스 시작: `ollama serve`
2. Ollama 설치 확인: https://ollama.ai/
3. 모델 설치: `ollama pull llama3.1`
4. 연결 상태 확인: `python src/utils/llm/test_llm.py --ollama`

```
Model 'llama3.3:70b' not found
```

**해결책**: 모델 설치
```bash
ollama pull llama3.3:70b
ollama list  # 설치된 모델 확인
```

## 향후 계획

- [ ] 로컬 모델 지원 확대 (Ollama 최적화)
- [ ] 모델 성능 비교 도구
- [ ] 자동 모델 선택 (작업 유형별)
- [ ] 비용 추적 기능
- [ ] 배치 처리 최적화

## 기여하기

새로운 provider나 기능을 추가하고 싶다면:

1. `ModelProvider` enum에 새 provider 추가
2. `validate_api_key()` 함수에 API 키 검증 로직 추가
3. 기본 모델 설정에 새 모델 추가
4. 테스트 코드 작성

## 라이선스

이 모듈은 DecepticonV2 프로젝트의 라이선스를 따릅니다.
