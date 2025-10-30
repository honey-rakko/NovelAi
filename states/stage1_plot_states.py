"""
Stage 1 플롯 생성 v2를 위한 State 정의
TypedDict 기반으로 workflow_stage1.py와 일관성 유지
"""

from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict
from pydantic import BaseModel, Field

from pydantics.stage1_plot_pydantics import (
    NarrativePoles,
    ActSubThemes,
    IncitingAndMacroStructure,
    StructuralTempo,
    IntegratedPlot,
)


# ============ 입력 State (Pydantic 유지 - 검증용) ============
class PlotInputState(BaseModel):
    """플롯 생성 워크플로우 입력 State"""
    graph_filepath: str = Field(description="불러올 그래프 JSON 파일의 경로")
    topic: str
    conflict: str
    vibe: str
    model: Optional[str] = Field(
        default="gpt-4o-mini",
        description="모델 이름 (예: gpt-4o-mini, gpt-5-mini)"
    )
    extractor_type: Optional[str] = Field(
        default="default",
        description="Extractor 타입 (default, cot, plain)",
        examples=["default", "cot", "plain"]
    )


# ============ 워크플로우 State (TypedDict) ============
class PlotWorkflowState(TypedDict, total=False):
    """플롯 생성 전체 워크플로우 State - TypedDict 기반"""
    
    # 기본 정보
    topic: str
    conflict: str
    vibe: str
    model: Optional[str]
    extractor_type: Optional[str]
    
    # 캐릭터 네트워크 그래프
    graph: Any
    
    # 각 단계 결과들
    narrative_poles: Optional[NarrativePoles]
    sub_themes: Optional[ActSubThemes]
    inciting_and_macro: Optional[IncitingAndMacroStructure]
    structural_tempo: Optional[StructuralTempo]
    integrated_plot: Optional[IntegratedPlot]


# ============ 각 단계별 State (서브그래프용 - TypedDict) ============
class NarrativePolesState(TypedDict, total=False):
    """서사적 양극 분석 State"""
    
    topic: str
    conflict: str
    vibe: str
    model: Optional[str]
    extractor_type: Optional[str]
    
    graph: Any
    narrative_poles: Optional[NarrativePoles]


class SubThemeState(TypedDict, total=False):
    """Sub-theme 선정 State"""
    
    topic: str
    conflict: str
    vibe: str
    model: Optional[str]
    extractor_type: Optional[str]
    
    graph: Any
    narrative_poles: Optional[NarrativePoles]
    sub_themes: Optional[ActSubThemes]


class IncitingMacroState(TypedDict, total=False):
    """기폭사건 및 Macro Cliffhanger State"""
    
    topic: str
    conflict: str
    vibe: str
    model: Optional[str]
    extractor_type: Optional[str]
    
    graph: Any
    narrative_poles: Optional[NarrativePoles]
    sub_themes: Optional[ActSubThemes]
    inciting_and_macro: Optional[IncitingAndMacroStructure]


class StructuralTempoState(TypedDict, total=False):
    """구조적 템포 State"""
    
    topic: str
    conflict: str
    vibe: str
    model: Optional[str]
    extractor_type: Optional[str]
    
    narrative_poles: Optional[NarrativePoles]
    inciting_and_macro: Optional[IncitingAndMacroStructure]
    sub_themes: Optional[ActSubThemes]
    structural_tempo: Optional[StructuralTempo]


class IntegratedPlotState(TypedDict, total=False):
    """통합 플롯 State"""
    
    topic: str
    conflict: str
    vibe: str
    model: Optional[str]
    extractor_type: Optional[str]
    
    narrative_poles: Optional[NarrativePoles]
    sub_themes: Optional[ActSubThemes]
    inciting_and_macro: Optional[IncitingAndMacroStructure]
    structural_tempo: Optional[StructuralTempo]
    integrated_plot: Optional[IntegratedPlot]
