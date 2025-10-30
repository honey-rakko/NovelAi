"""
CoT(Chain of Thought) Extractor - 서브그래프 없는 단순 구현
Pickle 가능하도록 설계
"""

from typing import Any, Dict, List, Type

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, SystemMessage
from pydantic import BaseModel
from trustcall import create_extractor


class CoTExtractor:
    """
    Chain of Thought 추론을 지원하는 Extractor (서브그래프 없는 구현)

    trustcall의 create_extractor와 호환되는 인터페이스 제공
    """

    def __init__(
        self,
        model: BaseChatModel,
        tools: List[Type[BaseModel]],
        tool_choice: str,
        max_thinking_steps: int = 10,
        convergence_threshold: float = 0.85,
        **kwargs,
    ):
        """
        Args:
            model: 사용할 LLM 모델
            tools: Pydantic 모델 리스트 (출력 스키마)
            tool_choice: 사용할 tool 이름
            max_thinking_steps: 최대 사고 단계 수 (기본값: 10)
            convergence_threshold: 수렴 임계값 (기본값: 0.85)
            **kwargs: trustcall create_extractor의 추가 파라미터
        """
        self.model = model
        self.tools = tools
        self.tool_choice = tool_choice
        self.max_thinking_steps = max_thinking_steps
        self.convergence_threshold = convergence_threshold
        self.extra_kwargs = kwargs

    def invoke(self, messages: List[BaseMessage]) -> Dict[str, Any]:
        """
        CoT 추론을 수행하고 결과 반환

        Args:
            messages: 입력 메시지 리스트

        Returns:
            Dict with:
                - responses: 추출된 응답 리스트
                - messages: 메시지 히스토리
                - thinking_process: CoT 사고 과정
                - convergence_scores: 각 단계의 수렴 점수
                - total_steps: 실제 수행한 단계 수
        """
        original_prompt = messages[0].content if messages else ""

        # 1단계: CoT 초기 프롬프트
        current_thought = f"""
다음 문제를 단계적으로 해결하세요.

문제: {original_prompt}

먼저 문제를 분석하고, 필요한 정보를 파악한 후, 단계별로 사고하세요.
"""

        # 2단계: 사고 단계 반복
        thinking_process = []
        convergence_scores = []

        for step in range(self.max_thinking_steps):
            step_prompt = f"""
Step {step + 1}/{self.max_thinking_steps} (최대):
{current_thought}

이전 단계의 사고를 바탕으로 다음 단계를 진행하세요.
만약 충분히 깊이 사고했다면, 결론을 정리하세요.
"""
            # LLM 호출
            thinking_response = self.model.invoke([SystemMessage(content=step_prompt)])
            thinking_content = thinking_response.content
            thinking_process.append(thinking_content)

            # 수렴 점수 계산
            convergence_score = self._calculate_convergence(thinking_process, thinking_content)
            convergence_scores.append(convergence_score)

            # 수렴 판단
            if step >= 1 and len(convergence_scores) >= 2:
                recent_scores = convergence_scores[-2:]
                if all(score >= self.convergence_threshold for score in recent_scores):
                    break  # 수렴 완료

            current_thought = thinking_content

        # 3단계: 최종 답변 생성 (tool call)
        formatted_thinking = "\n\n".join(
            [f"[단계 {i + 1}]\n{thought}" for i, thought in enumerate(thinking_process)]
        )

        final_prompt = f"""
다음은 단계별 사고 과정입니다:
{formatted_thinking}

위 사고 과정을 바탕으로 최종 답변을 구조화된 형식으로 제공하세요.
원래 질문: {original_prompt}
"""

        # Tool binding으로 최종 답변 생성
        extractor = create_extractor(
            self.model,
            tools=self.tools,
            tool_choice=self.tool_choice,
            **self.extra_kwargs,
        )
        final_response = extractor.invoke([SystemMessage(content=final_prompt)])

        # 파싱
        if hasattr(final_response, "responses") and final_response["responses"][0]:
            parsed = final_response["responses"][0]
        else:
            args = final_response["messages"][0].tool_calls[0]["args"]
            tool_model = next(t for t in self.tools if t.__name__ == self.tool_choice)
            parsed = tool_model(**args)

        return {
            "responses": [parsed],
            "messages": final_response.get("messages", []),
            "thinking_process": thinking_process,
            "convergence_scores": convergence_scores,
            "total_steps": len(thinking_process),
        }

    def _calculate_convergence(self, thinking_process: List[str], new_thought: str) -> float:
        """수렴 점수 계산 (Jaccard similarity 기반)"""
        if len(thinking_process) < 2:
            return 0.0

        last_thought = thinking_process[-2]  # 이전 사고

        # 길이 비율
        length_ratio = min(len(new_thought), len(last_thought)) / max(
            len(new_thought), len(last_thought), 1
        )

        # 공통 단어 비율
        last_words = set(last_thought.split())
        new_words = set(new_thought.split())
        if not last_words or not new_words:
            return 0.0

        intersection = len(last_words & new_words)
        union = len(last_words | new_words)
        word_similarity = intersection / union if union > 0 else 0.0

        # 종합 점수
        return (length_ratio + word_similarity) / 2


def create_cot_extractor(
    model: BaseChatModel,
    tools: List[Type[BaseModel]],
    tool_choice: str,
    max_thinking_steps: int = 10,
    convergence_threshold: float = 0.85,
    **kwargs,
) -> CoTExtractor:
    """
    Chain of Thought Extractor 생성

    Args:
        model: 사용할 LLM 모델
        tools: Pydantic 모델 리스트
        tool_choice: 사용할 tool 이름
        max_thinking_steps: 최대 사고 단계 수
        convergence_threshold: 수렴 임계값 (0~1)
        **kwargs: trustcall create_extractor의 추가 파라미터

    Returns:
        CoTExtractor 인스턴스
    """
    return CoTExtractor(
        model, tools, tool_choice, max_thinking_steps, convergence_threshold, **kwargs
    )