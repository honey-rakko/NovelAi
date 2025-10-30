"""
Unified Extractor Factory
모델명과 extractor 타입으로 최적의 extractor 반환
"""

from typing import Any, Dict, List, Optional, Type, Union

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from pydantic import BaseModel
from trustcall import create_extractor

from utils.cot import create_cot_extractor


class PlainLLMWrapper:
    """
    Structured output 없이 일반 LLM 응답을 반환하는 Wrapper
    create_extractor와 동일한 인터페이스 제공
    """

    def __init__(self, model: BaseChatModel):
        self.model = model

    def invoke(self, messages: List[BaseMessage]) -> Dict[str, Any]:
        """
        일반 LLM 호출

        Args:
            messages: 입력 메시지 리스트

        Returns:
            Dict with:
                - responses: None (structured output 없음)
                - messages: LLM 응답 메시지
                - content: 응답 텍스트
        """
        response = self.model.invoke(messages)
        return {
            "responses": None,
            "messages": [response],
            "content": response.content,
        }


def create_unified_extractor(
    model_name: Optional[str] = None,
    model: Optional[BaseChatModel] = None,
    extractor_type: str = "default",
    tools: Optional[List[Type[BaseModel]]] = None,
    tool_choice: Optional[str] = None,
    **kwargs,
) -> Union[Any, PlainLLMWrapper]:
    """
    통합 Extractor Factory

    Args:
        model_name: 모델 이름 (예: "gpt-4o-mini", "gpt-5-mini")
        model: 이미 생성된 LLM 객체 (model_name과 함께 사용 불가)
        extractor_type: Extractor 타입
            - "default": trustcall의 create_extractor
            - "cot": Chain of Thought extractor
            - "plain": structured output 없이 일반 LLM
        tools: Pydantic 모델 리스트 (structured output용)
        tool_choice: 사용할 tool 이름
        **kwargs: 추가 파라미터
            - CoT용: max_thinking_steps, convergence_threshold
            - trustcall용: enable_inserts 등

    Returns:
        Extractor 인스턴스

    Raises:
        ValueError: 잘못된 파라미터 조합

    Examples:
        >>> # Plain LLM (no structured output)
        >>> extractor = create_unified_extractor(
        ...     model_name="gpt-4o-mini",
        ...     extractor_type="plain"
        ... )
        >>>
        >>> # Default extractor (trustcall)
        >>> extractor = create_unified_extractor(
        ...     model_name="gpt-5-mini",
        ...     extractor_type="default",
        ...     tools=[Character],
        ...     tool_choice="Character"
        ... )
        >>>
        >>> # CoT extractor
        >>> extractor = create_unified_extractor(
        ...     model_name="gpt-5-mini",
        ...     extractor_type="cot",
        ...     tools=[Character],
        ...     tool_choice="Character",
        ...     max_thinking_steps=5
        ... )
        >>>
        >>> # State에서 직접 사용
        >>> state = {"model": "gpt-4o-mini", "extractor_type": "cot"}
        >>> extractor = create_unified_extractor(
        ...     model_name=state.get("model"),
        ...     extractor_type=state.get("extractor_type", "default"),
        ...     tools=[Character],
        ...     tool_choice="Character"
        ... )
    """
    # 모델 준비
    if model is not None and model_name is not None:
        raise ValueError("model과 model_name을 동시에 지정할 수 없습니다")

    if model is None:
        from utils.model_factory import create_model

        model = create_model(model_name)

    # Extractor 타입별 생성
    if extractor_type == "plain":
        # Plain LLM (no structured output)
        if tools is not None:
            raise ValueError("plain 타입에서는 tools를 사용할 수 없습니다")
        return PlainLLMWrapper(model)

    elif extractor_type == "default":
        # Trustcall extractor
        if tools is None or tool_choice is None:
            raise ValueError("default 타입에서는 tools와 tool_choice가 필요합니다")
        return create_extractor(model, tools=tools, tool_choice=tool_choice, **kwargs)

    elif extractor_type == "cot":
        # CoT extractor
        if tools is None or tool_choice is None:
            raise ValueError("cot 타입에서는 tools와 tool_choice가 필요합니다")

        # CoT 전용 파라미터 분리
        max_thinking_steps = kwargs.pop("max_thinking_steps", 10)
        convergence_threshold = kwargs.pop("convergence_threshold", 0.85)

        return create_cot_extractor(
            model,
            tools=tools,
            tool_choice=tool_choice,
            max_thinking_steps=max_thinking_steps,
            convergence_threshold=convergence_threshold,
            **kwargs,  # 나머지는 trustcall 옵션
        )

    else:
        raise ValueError(
            f"지원하지 않는 extractor_type: {extractor_type}. "
            f"지원 타입: 'default', 'cot', 'plain'"
        )
