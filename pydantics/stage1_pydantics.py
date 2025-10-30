"""
Pydantic 모델 정의 - 워크플로우의 입출력 데이터 구조
"""

import re
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ============ 공통 Enum 정의 ============
class InfoType(str, Enum):
    """캐릭터 정보의 유형 분류"""
    # --- 1단계: 핵심 엔진 (WHY) ---
    DESIRE = "desire"  # 욕구와 동기
    FEAR = "fear"  # 두려움과 회피
    PARADOX = "paradox"  # 내적 모순, 딜레마

    # --- 2단계: 표현 시스템 (HOW) - 아키타이프 DNA ---
    MODUS_OPERANDI = "modus_operandi" # 행동 원리 (M.O.)
    RHETORIC = "rhetoric" # 핵심 화법
    EMOTION = "emotion" # 감정 표현

    # --- 2단계: 표현 시스템 (WHAT) - 핵심 역량 ---
    TALENT = "talent" # 재능 (기존 Capability의 핵심)
    SYMBOL = "symbol" # 상징 (기존 Capability에서 분리)

    # --- 3단계: 미래 잠재력 (FUTURE) ---
    GROWTH_POTENTIAL = "growth_potential" # 잠재된 가능성

    # --- 기타/레거시 타입 ---
    PERSONALITY = "personality"  # 성격적 특성
    CAPABILITY = "capability"  # 능력이나 재능
    BACKGROUND = "background"  # 배경 정보


class PlotFunction(str, Enum):
    """플롯 포인트의 서사적 기능"""

    SETUP = "setup"  # 설정과 도입
    CONFRONTATION = "confrontation"  # 대립과 갈등
    RESOLUTION = "resolution"  # 해결과 정리
    REVELATION = "revelation"  # 폭로와 반전
    ESCALATION = "escalation"  # 긴장 고조




# ============ Roles 노드 (v2 확장) ============
class RoleInfo(BaseModel):
    """
    주제로부터 도출된 단일 핵심 역할의 상세 정보.
    단순한 역할명을 넘어, 캐릭터의 철학적 씨앗을 포함합니다.
    """
    role_name: str = Field(
        description="스토리의 핵심 캐릭터 역할. 반드시 괄호 포함",
        pattern=r"^\(.+\)$"
    )
    theme_exploration: str = Field(description="이 역할이 탐구하는 주제의 특정 측면")
    core_direction: str = Field(description="이 역할이 근본적으로 추구하는 가치나 방향성")
    initial_belief: str = Field(description="이 역할이 가질 법한, 행동으로 이어지는 뾰족한 신념의 초기 아이디어")
    conflict_prediction: str = Field(description="다른 역할과 어떻게 충돌하거나 상호작용할지에 대한 예상")

# ============ Define Main Character 노드 ============
class Roles(BaseModel):
    """
    주제로부터 도출된 핵심 캐릭터 역할 목록.

    각 역할은 주제를 탐구하는 독특한 렌즈이며,
    서로 갈등과 협력 관계를 형성합니다.
    200화 이상의 장편에서 지속 가능한 깊이를 가져야 합니다.
    """

    roles: List[RoleInfo] = Field(
        description="스토리의 핵심 캐릭터 역할들. 각 역할은 주제에 대한 고유한 관점을 대변",
        min_length=3,
        max_length=5,
        examples=[
            # 형식 참고용 (내용 복사 금지)
            ["(역할 유형 A)", "(역할 유형 B)", "(역할 유형 C)"],
        ],
    )


# ============ Create Character 노드 ============
class Info(BaseModel):
    """
    캐릭터의 단일 속성 정보.

    각 속성은 과거 사건으로 설명 가능해야 하며,
    캐릭터의 행동과 선택에 영향을 미칩니다.
    """

    type: InfoType = Field(description="속성의 유형 분류")

    content: str = Field(
        description="구체적인 속성 내용. 행동으로 드러날 수 있는 구체성 필요",
        min_length=10,
        max_length=200,
        examples=[
            "행동으로 드러나는 심리적 특성 설명 (구체적 예시 아님)",
            ],
    )

    severity: Optional[int] = Field(
        default=5,
        description="속성의 강도 (1-10). 캐릭터에게 미치는 영향력",
        ge=1,
        le=10,
    )


class InfoWithEventId(Info):
    """
    원인 사건과 연결된 캐릭터 속성.

    속성이 특정 사건의 결과로 형성되었음을 추적합니다.
    """

    event_id: str = Field(
        description="원인이 된 사건의 ID. 중복 될 수 없음. 주어진 사건이 하나 밖에 없는 경우, 나머지는 '미정'으로 처리",
        pattern=r"^(event_\d+|미정)$",
        examples=["event_001", "event_042", "미정"],
    )


class Infos(BaseModel):
    """캐릭터나 이벤트의 속성 정보들"""

    infos: List[InfoWithEventId] = Field(
        description="캐릭터 속성 정보들과 원인 사건 id. 연결된 Event 개수에 따라: 1개 Event → 최대 2개 Info, 2개 Event → 2개 Info, N개 Event → N개 Info",
        min_length=2,
    )

    # event_id가 중복되지 않는지 검증
    @model_validator(mode="after")
    def validate_event_id(self) -> "Infos":
        """event_id가 중복되지 않는지 검증"""
        event_ids = [info.event_id for info in self.infos]
        if len(event_ids) != len(set(event_ids)):
            raise ValueError("event_id가 중복되었습니다")
        return self

# ============ Create Character 노드 (v2 확장) ============
class CharacterAnalysis(BaseModel):
    """
    캐릭터의 내면 세계를 구성하는 분석 결과.
    캐릭터의 모든 행동과 심리의 근원이 되는 '엔진' 파트입니다.
    """
    situation: str = Field(description="캐릭터가 인식하는 근본적인 상황")
    question: str = Field(description="캐릭터가 세상에 던지는 근본적인 질문")
    philosophy: str = Field(description="질문에 대한 캐릭터의 독단적인 해답이자 핵심 신념(행동 원리)")
    
class Character(BaseModel):
    """
    생성된 캐릭터 - Stage 1에서는 이름 없이 역할만 존재.

    다층적이고 모순적인 속성을 가진 입체적 캐릭터.
    200화 동안 탐구할 만한 깊이와 성장 가능성을 보유.
    """

    role: str = Field(
        description="캐릭터의 핵심 역할. 주제와 직접 연관",
        pattern=r"^\(.+\)$",
        examples=["(주제 관련 역할)"],
    )
    analysis: CharacterAnalysis = Field(description="캐릭터의 심리적 엔진을 설명하는 핵심 분석 결과")
    infos: List[Info] = Field(
        description="캐릭터의 핵심 속성들. 서로 연결되면서도 때로는 모순적",
        min_length=7,
        max_length=10,
    )




# ============ Create Event 노드 ============
class PlaceHolder(BaseModel):
    """
    이벤트에 등장하는 미확정 캐릭터.

    Stage 2에서 장르별로 구체화될 예정.
    중심 캐릭터와의 관계로 정의됩니다.
    """

    role: str = Field(
        description="PlaceHolder의 역할. 반드시 괄호 포함",
        pattern=r"^\(.+\)$",
        examples=["(믿었던 동료)", "(엄격한 스승)", "(자상한 조력자)"],
    )


class Event(BaseModel):
    """
    캐릭터 속성을 형성한 과거 사건.

    장르 독립적이고 보편적인 인간 경험으로 표현.
    명확한 인과관계와 감정적 영향을 포함합니다.
    """

    target_role: str = Field(
        description="이 사건이 형성한 속성의 대상 캐릭터 역할",
        pattern=r"^\(.+\)$",
    )
    target_info_type: InfoType = Field(description="이 사건이 형성한 속성의 유형")

    summary: str = Field(
        description="사건의 핵심 내용. PlaceHolder와 행동 포함",
        min_length=20,
        max_length=300,
        examples=[
            "(PlaceHolder)가 행동하여 (대상)이 영향받음 (구체적 예시 아님)"
        ],
    )

    placeholders: List[PlaceHolder] = Field(
        description="사건에 등장하는 PlaceHolder 캐릭터들", min_length=0, max_length=4
    )

    @model_validator(mode="after")
    def validate_summary(self) -> "Event":
        """사건 요약이 충분한 정보를 담고 있는지 검증"""
        if self.target_role not in self.summary:
            raise ValueError(
                f"사건 요약에 target_role({self.target_role})가 포함되어야 합니다"
            )
        for placeholder in self.placeholders:
            if placeholder.role not in self.summary:
                raise ValueError(
                    f"사건 요약에 PlaceHolder({placeholder.role})가 포함되어야 합니다"
                )
        return self


# ============ Consolidate 노드 ============
class ConsolidationPrepareResult(BaseModel):
    """
    PlaceHolder 통합 준비 단계의 결과.

    의미적으로 유사한 PlaceHolder들을 그룹화합니다.
    """

    chunked_placeholders: List[List[str]] = Field(
        description="유사한 역할들의 ID 그룹. 각 그룹은 하나로 통합될 후보",
        examples=[
            [
                ["placeholder_1", "placeholder_5"],
                ["placeholder_2", "placeholder_3", "placeholder_7"],
            ]
        ],
    )

    @field_validator("chunked_placeholders")
    @classmethod
    def validate_placeholder_format(cls, v: List[List[str]]) -> List[List[str]]:
        """PlaceHolder ID 형식 및 중복 그룹 포함 검증"""
        pattern = re.compile(r"^placeholder_\d+$")
        seen = set()
        for group in v:
            if len(group) < 2:
                raise ValueError(
                    "각 그룹은 최소 2개 이상의 PlaceHolder를 포함해야 합니다"
                )
            for ph_id in group:
                if not pattern.match(ph_id):
                    raise ValueError(f"잘못된 PlaceHolder ID 형식: {ph_id}")
                if ph_id in seen:
                    raise ValueError(
                        f"PlaceHolder ID가 여러 그룹에 중복 포함됨: {ph_id}"
                    )
                seen.add(ph_id)
        # 그룹 내 중복 제거
        return v


class ConsolidatedRole(BaseModel):
    """
    통합된 PlaceHolder 역할.

    여러 유사한 PlaceHolder를 하나의 캐릭터로 통합한 결과.
    """

    unified_role: Optional[str] = Field(
        default=None,
        description="통합된 역할명. 원본들의 공통 속성을 포괄. 반드시 괄호 포함",
        pattern=r"^\(.+\)$",
        examples=["(권위적인 조언자)", "(배신한 동료)", "(충실한 조력자)"],
    )

    original_placeholders: Optional[Dict[str, str]] = Field(
        default=None,
        description="통합된 원본 PlaceHolder들. key: ID, value: 원래 역할명",
        examples=[
            {"placeholder_1": "(엄격한 아버지)", "placeholder_5": "(권위적인 부모)"}
        ],
    )

    @field_validator("original_placeholders")
    @classmethod
    def validate_consolidation(cls, v: Dict[str, str]) -> Dict[str, str]:
        if v is None:
            return v
        key_pattern = re.compile(r"^placeholder_\d+$")
        value_pattern = re.compile(r"^\(.+\)$")
        for key, value in v.items():
            if not key_pattern.match(key):
                raise ValueError(f"Wrong PlaceHolder ID: {key}")
            if not value_pattern.match(value):
                raise ValueError(f"Wrong PlaceHolder role name: {value}")
        return v


class ConsolidationResult(BaseModel):
    """PlaceHolder 통합 결과"""

    consolidated_roles: List[ConsolidatedRole] = Field(
        description="통합된 역할 목록", min_length=0
    )

    @model_validator(mode="after")
    def check_duplicate_placeholders(self) -> "ConsolidationResult":
        """여러 ConsolidatedRole에서 동일한 PlaceHolder ID가 중복되는지 검증"""
        seen = set()
        for role in self.consolidated_roles:
            for ph_id in role.original_placeholders.keys():
                if ph_id in seen:
                    raise ValueError(
                        f"PlaceHolder ID가 여러 통합 그룹에 중복 포함됨: {ph_id}"
                    )
                seen.add(ph_id)
        return self


# ============ Create Plot 노드 ============
class PlotPoint(BaseModel):
    """
    스토리의 주요 전환점.

    각 포인트는 전체 서사에 필수적이며,
    독자의 긴장감을 유지하는 역할을 합니다.
    """

    sequence: int = Field(description="시간 순서상 위치 (1부터 시작)", ge=1, le=10)

    description: str = Field(
        description="플롯 포인트의 핵심 사건", min_length=20, max_length=300
    )

    macro_cliffhanger: str = Field(
        description="이 시점에서 제기되는 거대한 미해결 문제",
        min_length=10,
        max_length=200,
        examples=[
            "진정한 적의 정체는 무엇인가?",
            "주인공은 자신의 운명을 바꿀 수 있을 것인가?",
        ],
    )

    involved_characters: List[str] = Field(
        description="이 플롯 포인트에 관련된 캐릭터 역할들", min_length=1, max_length=8
    )

    plot_function: PlotFunction = Field(description="서사 구조상 기능")

    tension_level: int = Field(description="긴장감 수준 (1-10)", ge=1, le=10)

    expansion_potential: Optional[str] = Field(
        default=None,
        description="이 포인트를 확장할 수 있는 서브플롯 아이디어",
        max_length=200,
    )


class Plot(BaseModel):
    """
    완성된 플롯 구조.

    200화 이상으로 확장 가능한 탄탄한 서사 골격.
    주제를 효과적으로 탐구하는 플롯 포인트들의 연쇄.
    """

    theme: str = Field(
        description="플롯이 탐구하는 중심 주제",
        examples=["권력의 부패", "사랑의 양면성", "정체성의 탐구"],
    )

    plot_points: List[PlotPoint] = Field(
        description="핵심 플롯 포인트들. 시간 순서로 배열", min_length=3, max_length=10
    )

    end_direction: str = Field(
        description="결말의 톤과 방향성. 구체적 사건이 아닌 정서적 귀결",
        examples=[
            "희생을 통한 구원과 새로운 시작",
            "파멸적 결말 속에서 발견하는 진실",
            "화해와 용서를 통한 치유",
        ],
    )

    narrative_strategy: Optional[str] = Field(
        default=None,
        description="이 플롯의 독특한 서사 전략",
        examples=["신뢰할 수 없는 화자", "시간 역행 구조", "다중 관점"],
    )

    @model_validator(mode="after")
    def validate_plot_coherence(self) -> "Plot":
        """플롯의 구조적 완성도 검증"""
        sequences = [pp.sequence for pp in self.plot_points]
        if sequences != sorted(sequences):
            raise ValueError("플롯 포인트는 시간 순서대로 배열되어야 합니다")

        tension_levels = [pp.tension_level for pp in self.plot_points]
        if max(tension_levels) < 8:
            raise ValueError(
                "최소 하나의 플롯 포인트는 8 이상의 긴장감을 가져야 합니다"
            )

        return self


class PlotCandidates(BaseModel):
    """
    플롯 후보군.

    동일한 주제를 다른 방식으로 탐구하는 여러 플롯 옵션.
    """

    plot_candidates: List[Plot] = Field(
        description="서로 다른 서사 전략을 가진 플롯 후보들", min_length=2, max_length=5
    )

    recommendation: Optional[str] = Field(
        default=None, description="가장 추천하는 플롯과 그 이유", max_length=300
    )
