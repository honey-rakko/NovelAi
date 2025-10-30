"""
LangGraph State 정의 - 워크플로우 상태 관리
"""

from typing import Annotated, Any, List, Optional

from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from pydantics.stage1_pydantics import (
    Character,
    ConsolidatedRole,
    Event,
    Plot,
    PlotCandidates,
)


class EssentialState(TypedDict):
    """필수 상태"""

    model: Optional[str]
    extractor_type: Optional[str]


class InputState(BaseModel):
    """워크플로우 입력 상태"""

    topic: str = Field(description="스토리 주제")
    conflict: str = Field(description="장르 내재 갈등")
    vibe: str = Field(description="핵심 분위기")
    max_iterations: Optional[int] = Field(
        default=2, description="최대 반복 횟수", ge=1, le=5
    )
    model: Optional[str] = Field(
        default="gpt-5-mini", description="모델 이름 (예: gpt-4o-mini, gpt-5-mini)"
    )
    extractor_type: Optional[str] = Field(
        default="default",
        description="Extractor 타입 (default, cot, plain)",
        examples=["default", "cot", "plain"],
    )


def merge_lists(left: Optional[List], right: Optional[List]) -> List:
    """리스트 병합 - Send에서 여러 리스트가 올 때 추가.

    규칙:
    - right가 None이면 변경 없음 (초기화)
    - 그 외에는 left와 right를 이어 붙임
    """
    # right가 None이면 초기화
    if right is None:
        return []

    # 기존이 없으면 새로 설정
    if left is None:
        return right

    return left + right


class WorkflowState(EssentialState):
    """간소화된 메인 워크플로우 State - 핵심 정보만 관리"""

    # 사용자 입력
    topic: str
    conflict: str
    vibe: str
    max_iterations: int

    # 핵심 데이터
    graph: Any

    # 반복 제어
    current_iteration: int
    roles: List[str]  # 첫 번째 반복용 역할들

    # 최종 출력
    plots: Optional[Plot]
    plot_candidates: Optional[PlotCandidates]


class CharacterCreationState(EssentialState):
    """캐릭터 생성용 임시 State"""

    topic: str
    roles: List[str]
    conflict: str
    # current_role: str
    # is_contextual: bool
    # event_contexts: Optional[List[str]]
    generated_character: Annotated[List[Character], merge_lists]
    # current_character_id: Optional[str]
    # current_info_ids: Optional[List[str]]
    current_iteration: int
    graph: Any


class EventCreationState(EssentialState):
    """이벤트 생성용 임시 State"""

    generated_event: Annotated[List[Event], merge_lists]
    current_iteration: int
    graph: Any
    topic: str
    conflict: str
    vibe: str


class ConsolidationState(EssentialState):
    """통합 작업용 임시 State"""

    graph: Any
    chunked_placeholders: List[List[str]]
    consolidated_roles: Annotated[List[ConsolidatedRole], merge_lists]
    current_iteration: int
    topic: str
    conflict: str
    vibe: str


class PlaceHolderReplaceState(EssentialState):
    """PlaceHolder 처리용 State"""

    graph: Any
    placeholders: List[str]  # PlaceHolder들
    generated_infos: Annotated[
        List, merge_lists
    ]  # (placeholder_id, infos: (event_id, info)) 형태
    current_iteration: int
    topic: str
    conflict: str
    vibe: str