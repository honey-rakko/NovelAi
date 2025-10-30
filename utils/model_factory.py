"""
Model Factory - 문자열 model name에서 실제 LLM 객체 생성
"""

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

# 지원하는 모델 목록
SUPPORTED_MODELS = {
    # OpenAI models
    "gpt-4o": {"provider": "openai", "model": "gpt-4o"},
    "gpt-4o-mini": {"provider": "openai", "model": "gpt-4o-mini"},
    "gpt-5-mini": {"provider": "openai", "model": "gpt-5-mini"},
    "gpt-4-turbo": {"provider": "openai", "model": "gpt-4-turbo"},
    "gpt-3.5-turbo": {"provider": "openai", "model": "gpt-3.5-turbo"},
    # Anthropic models (추후 확장)
    # "claude-3-5-sonnet": {"provider": "anthropic", "model": "claude-3-5-sonnet-20241022"},
}


def create_model(model_name: str, **kwargs) -> BaseChatModel:
    """
    문자열 model name으로부터 LLM 객체 생성

    Args:
        model_name: 모델 이름 (예: "gpt-4o-mini", "gpt-5-mini")
        **kwargs: 모델 생성 시 추가 파라미터 (temperature, max_tokens 등)

    Returns:
        BaseChatModel 인스턴스

    Raises:
        ValueError: 지원하지 않는 모델인 경우

    Example:
        >>> model = create_model("gpt-4o-mini")
        >>> model = create_model("gpt-5-mini", temperature=0.7)
    """

    if model_name not in SUPPORTED_MODELS:
        raise ValueError(
            f"Unsupported model: {model_name}. "
            f"Supported models: {list(SUPPORTED_MODELS.keys())}"
        )

    model_config = SUPPORTED_MODELS[model_name]
    provider = model_config["provider"]

    if provider == "openai":
        return ChatOpenAI(model=model_config["model"], **kwargs)
    # elif provider == "anthropic":
    #     from langchain_anthropic import ChatAnthropic
    #     return ChatAnthropic(model=model_config["model"], **kwargs)
    else:
        raise ValueError(f"Unsupported provider: {provider}")
