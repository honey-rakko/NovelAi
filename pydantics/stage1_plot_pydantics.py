"""
Pydantic 모델 정의 - 플롯 생성 v2를 위한 추가 모델
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum


# ============ 서사적 양극 설정 ============
class NarrativeState(BaseModel):
    """서사의 시작점 또는 종착점 상태"""
    
    description: str = Field(
        description="세계와 캐릭터들의 상태 (2-3문장)",
        min_length=20,
        max_length=500
    )
    
    key_element: str = Field(
        description="핵심 요소 (결핍/정체/변화 등)",
        max_length=100
    )
    
    tension_seeds: Optional[str] = Field(
        default=None,
        description="잠재된 긴장이나 균열의 징조",
        max_length=200
    )


class CharacterAnalysisSummary(BaseModel):
    """캐릭터 네트워크 분석 요약"""
    
    common_desires: List[str] = Field(
        description="주연들의 공통된 욕망 패턴",
        min_length=1,
        max_length=5
    )
    
    common_fears: List[str] = Field(
        description="주연들의 공통된 두려움 패턴", 
        min_length=1,
        max_length=5
    )
    
    conflict_points: List[str] = Field(
        description="잠재적 충돌 지점들",
        min_length=2,
        max_length=8
    )
    
    narrative_drive: str = Field(
        description="서사를 추진하는 핵심 동력",
        max_length=200
    )


class NarrativePoles(BaseModel):
    """서사의 양극 (출발점과 종착점)"""
    
    character_analysis: CharacterAnalysisSummary = Field(
        description="캐릭터 분석 요약"
    )
    
    starting_point: NarrativeState = Field(
        description="출발점 - 결핍과 정체의 상태"
    )
    
    ending_point: NarrativeState = Field(
        description="종착점 - 변증법적 극복의 상태"
    )
    
    narrative_distance: Dict[str, int] = Field(
        description="양극 사이의 거리 측정 (각 항목 1-10점)",
        default={
            "psychological": 0,  # 심리적 거리
            "physical": 0,       # 물리적 거리
            "complexity": 0,     # 복잡도
            "emotional": 0       # 감정 진폭
        }
    )
    
    sustainability_200: bool = Field(
        description="200화 지속 가능 여부"
    )
    
    sustainability_reason: str = Field(
        description="지속가능성 판단 이유",
        max_length=300
    )


# ============ Sub-theme 선정 ============
class SubThemeSelection(BaseModel):
    """Act별 Sub-theme 선정 결과"""
    
    theme: str = Field(
        description="선정된 sub-theme (theme_list에서 선택)",
        max_length=100
    )
    
    relationship_to_core: str = Field(
        description="Core theme과의 관계 (보완/긴장/통합)",
        max_length=50
    )
    
    character_impact: str = Field(
        description="캐릭터 Desire/Fear에 미치는 영향",
        max_length=300
    )
    
    vibe_strategy: str = Field(
        description="분위기 활용 전략 (강화/대비)",
        max_length=200
    )
    
    expected_narrative_effect: str = Field(
        description="이 Act에서 예상되는 서사 효과",
        max_length=300
    )


class ActSubThemes(BaseModel):
    """3막 구조의 Sub-theme 할당"""
    
    act1_theme: SubThemeSelection = Field(
        description="Act 1 (설정과 촉발)의 sub-theme"
    )
    
    act2_theme: SubThemeSelection = Field(
        description="Act 2 (갈등 심화)의 sub-theme"
    )
    
    act3_theme: SubThemeSelection = Field(
        description="Act 3 (절정과 해결)의 sub-theme"
    )
    
    theme_progression: str = Field(
        description="Act 1→2→3 주제 진행의 시너지 효과",
        max_length=500
    )


# ============ 기폭사건 및 Macro Cliffhanger ============
class MacroCliffhangerType(str, Enum):
    """Macro Cliffhanger 유형"""
    MYSTERY = "mystery"        # 진실은 무엇인가?
    CONFLICT = "conflict"      # 누가 승리할 것인가?
    CHOICE = "choice"         # 어떤 결정을 내릴 것인가?
    TRANSFORMATION = "transformation"  # 어떻게 변할 것인가?


class IncitingIncident(BaseModel):
    """기폭 사건"""
    
    event_description: str = Field(
        description="구체적인 사건 내용 (2-3문장)",
        min_length=50,
        max_length=500
    )
    
    destroyed_element: str = Field(
        description="출발점에서 파괴되는 요소",
        max_length=200
    )
    
    thematic_question: str = Field(
        description="이 사건이 던지는 핵심 질문",
        max_length=200
    )
    
    character_impacts: Dict[str, str] = Field(
        description="각 주연에게 미치는 즉각적 영향",
        default={}
    )
    
    first_chapter_hook: str = Field(
        description="첫 화를 시작하는 훅",
        max_length=300
    )


class MacroCliffhanger(BaseModel):
    """장기적 긴장 구조를 만드는 Macro Cliffhanger"""
    
    title: str = Field(
        description="Cliffhanger 제목",
        max_length=100
    )
    
    type: MacroCliffhangerType = Field(
        description="Cliffhanger 유형"
    )
    
    core_question: str = Field(
        description="독자가 궁금해할 핵심 질문",
        max_length=200
    )
    
    trigger_point: str = Field(
        description="발생 시점 (기폭사건 후 언제)",
        max_length=100
    )
    
    involved_characters: List[str] = Field(
        description="주요 관련 캐릭터 역할들",
        min_length=1,
        max_length=8
    )
    
    duration_estimate: str = Field(
        description="예상 지속 기간 (화수)",
        max_length=50
    )
    
    causal_chain: Dict[str, str] = Field(
        description="인과관계 (어디서 파생되고 어디로 이어지는지)",
        default={"from": "", "to": ""}
    )


class IncitingAndMacroStructure(BaseModel):
    """기폭사건과 Macro Cliffhanger 구조"""
    
    inciting_incident: IncitingIncident = Field(
        description="기폭 사건"
    )
    
    macro_cliffhangers: List[MacroCliffhanger] = Field(
        description="Macro Cliffhanger 목록 (3-10개)",
        min_length=3,
        max_length=10
    )
    
    chain_diagram: str = Field(
        description="연쇄반응 다이어그램 (텍스트로 표현)",
        max_length=1000
    )
    
    tension_graph: str = Field(
        description="긴장도 그래프 (텍스트로 표현)",
        max_length=500
    )


# ============ 구조적 템포 설정 ============
class IntermediateArcType(str, Enum):
    """중간 아크 유형"""
    BREATHER = "breather"       # 숨고르기형
    GROWTH = "growth"           # 성장형
    EXPLORATION = "exploration" # 탐색형
    RELATIONSHIP = "relationship" # 관계형
    MINI_CRISIS = "mini_crisis"  # 미니 위기형


class StructuralSegment(BaseModel):
    """구조적 구간 (MC 사이)"""
    
    segment_name: str = Field(
        description="구간 이름 (예: MC1 → MC2)",
        max_length=100
    )
    
    episode_range: str = Field(
        description="화수 범위 (예: 31-60화)",
        max_length=50
    )
    
    intermediate_arc_count: int = Field(
        description="중간 아크 개수",
        ge=0,
        le=5
    )
    
    arc_types: List[IntermediateArcType] = Field(
        description="중간 아크들의 유형",
        max_length=5
    )
    
    arc_descriptions: Optional[List[str]] = Field(
        default=None,
        description="각 중간 아크의 간단한 설명",
        max_length=5
    )


class StructuralTempo(BaseModel):
    """전체 서사의 구조적 템포"""
    
    total_episodes: int = Field(
        default=200,
        description="총 화수"
    )
    
    segments: List[StructuralSegment] = Field(
        description="구조적 구간들",
        min_length=5,
        max_length=15
    )
    
    episode_distribution: Dict[str, int] = Field(
        description="요소별 화수 배분",
        default={
            "inciting": 3,
            "macro_cliffhangers": 0,
            "intermediate_arcs": 0,
            "climax": 15
        }
    )
    
    reader_experience_flow: str = Field(
        description="독자 경험 흐름 설명",
        max_length=500
    )


# ============ 통합 플롯 생성 ============
class ActStructure(BaseModel):
    """막 구조"""
    
    act_number: int = Field(
        description="막 번호 (1, 2, 3)",
        ge=1,
        le=3
    )
    
    subtitle: str = Field(
        description="막의 부제목",
        max_length=100
    )
    
    episode_range: str = Field(
        description="화수 범위",
        max_length=50
    )
    
    sub_theme: str = Field(
        description="이 막의 sub-theme",
        max_length=100
    )
    
    macro_cliffhangers: List[str] = Field(
        description="이 막에 포함된 Macro Cliffhanger들",
        min_length=1,
        max_length=5
    )
    
    intermediate_arc_summary: Dict[str, int] = Field(
        description="구간별 중간 아크 개수",
        default={}
    )
    
    key_transition: Optional[str] = Field(
        default=None,
        description="다음 막으로의 전환점",
        max_length=300
    )


class IntegratedPlot(BaseModel):
    """통합된 최종 플롯 뼈대"""
    
    plot_summary: str = Field(
        description="전체 이야기 한 줄 요약",
        max_length=200
    )
    
    core_question: str = Field(
        description="독자가 끝까지 궁금해할 핵심 질문",
        max_length=200
    )
    
    thematic_statement: str = Field(
        description="이 이야기가 말하고자 하는 것",
        max_length=300
    )
    
    act_structures: List[ActStructure] = Field(
        description="3막 구조 상세",
        min_length=3,
        max_length=3
    )
    
    macro_cliffhanger_flow: str = Field(
        description="Macro Cliffhanger 연결도",
        max_length=1000
    )
    
    episode_tension_map: str = Field(
        description="화수별 긴장도 맵",
        max_length=500
    )
    
    key_character_placement: Dict[str, List[str]] = Field(
        description="핵심 캐릭터 배치 (MC별 주요 캐릭터)",
        default={}
    )
    
    required_additions: Optional[List[str]] = Field(
        default=None,
        description="기존 네트워크에 추가 필요한 요소들",
        max_length=10
    )