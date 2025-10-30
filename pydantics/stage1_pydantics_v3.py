"""
Pydantic 모델 정의 - 개선된 캐릭터 시스템 v3
주연급과 조연급 캐릭터를 구분하여 처리
"""

import re
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


# ============ 공통 Enum 정의 ============
class InfoType(str, Enum):
    """캐릭터 정보의 유형 분류 (확장된 버전)"""
    
    # 핵심 심리 (필수)
    DESIRE = "desire"              # 욕구와 열망
    FEAR = "fear"                  # 두려움과 회피
    PARADOX = "paradox"            # 내적 모순과 딜레마
    
    # 표현 시스템 (필수)
    MODUS_OPERANDI = "modus_operandi"  # 행동 원리 (M.O.)
    RHETORIC = "rhetoric"          # 핵심 화법
    EMOTION = "emotion"            # 감정 표현 방식
    
    # 특별 요소 (선택)
    TALENT = "talent"              # 특별한 재능
    SYMBOL = "symbol"              # 상징적 요소
    
    # 성장 가능성 (필수)
    GROWTH_POTENTIAL = "growth_potential"  # 성장/변화 잠재력
    
    # 기타 (호환성)
    CAPABILITY = "capability"      # 능력이나 재능 (기존 호환)
    PERSONALITY = "personality"    # 성격적 특성 (기존 호환)
    BACKGROUND = "background"      # 배경 정보 (기존 호환)


class CharacterTier(str, Enum):
    """캐릭터 중요도 계층"""
    MAIN = "main"          # 주연급 (모든 필드)
    SUPPORTING = "supporting"  # 조연급 (핵심 필드만)
    MINOR = "minor"        # 단역 (최소 필드)


class PlotFunction(str, Enum):
    """플롯 포인트의 서사적 기능"""
    SETUP = "setup"
    CONFRONTATION = "confrontation"
    RESOLUTION = "resolution"
    REVELATION = "revelation"
    ESCALATION = "escalation"


# ============ Define Main Character 노드 ============
class RoleDetail(BaseModel):
    """역할의 상세 정보"""
    
    role_name: str = Field(
        description="역할 이름",
        pattern=r"^\(.+\)$"
    )
    
    theme_exploration: str = Field(
        description="이 역할이 탐구하는 주제의 측면"
    )
    
    core_direction: str = Field(
        description="근본적으로 추구하는 가치나 방향성"
    )
    
    initial_belief: str = Field(
        description="행동으로 이어지는 뾰족한 신념의 초기 아이디어"
    )
    
    conflict_prediction: str = Field(
        description="다른 역할과의 충돌/상호작용 예상"
    )


class Roles(BaseModel):
    """주제로부터 도출된 핵심 캐릭터 역할 목록"""
    
    roles: List[RoleDetail] = Field(
        description="스토리의 핵심 캐릭터 역할들",
        min_length=3,
        max_length=5
    )


# ============ Create Character 노드 ============
class CharacterAnalysis(BaseModel):
    """캐릭터의 근본적 분석 (주연급만)"""
    
    situation: str = Field(
        description="캐릭터가 마주한 근본적 상황",
        max_length=300
    )
    
    question: str = Field(
        description="그 상황에서 던지는 근본적 질문",
        max_length=200
    )
    
    philosophy: str = Field(
        description="질문에 대한 독단적 해답이자 핵심 신념",
        max_length=300
    )


class Info(BaseModel):
    """캐릭터의 단일 속성 정보"""
    
    type: InfoType = Field(
        description="속성의 유형"
    )
    
    content: str = Field(
        description="구체적인 속성 내용",
        min_length=10,
        max_length=300
    )
    
    severity: Optional[int] = Field(
        default=5,
        description="속성의 강도 (1-10)",
        ge=1,
        le=10
    )


class InfoWithEventId(Info):
    """원인 사건과 연결된 캐릭터 속성"""
    
    event_id: str = Field(
        description="원인이 된 사건의 ID",
        pattern=r"^(event_\d+|미정)$"
    )


class Infos(BaseModel):
    """캐릭터의 속성 정보들"""
    
    infos: List[InfoWithEventId] = Field(
        description="캐릭터 속성 정보들",
        min_length=2
    )
    
    @model_validator(mode="after")
    def validate_event_id(self) -> "Infos":
        """event_id 중복 검증"""
        event_ids = [info.event_id for info in self.infos if info.event_id != "미정"]
        if len(event_ids) != len(set(event_ids)):
            raise ValueError("event_id가 중복되었습니다")
        return self


class Character(BaseModel):
    """생성된 캐릭터 (주연급 전용)"""
    
    role: str = Field(
        description="캐릭터의 핵심 역할",
        pattern=r"^\(.+\)$"
    )
    
    tier: CharacterTier = Field(
        default=CharacterTier.MAIN,
        description="캐릭터 중요도"
    )
    
    analysis: Optional[CharacterAnalysis] = Field(
        default=None,
        description="캐릭터 분석 (주연급만)"
    )
    
    infos: List[Info] = Field(
        description="캐릭터의 속성들",
        min_length=3,
        max_length=12
    )
    
    @model_validator(mode="after")
    def validate_character_completeness(self) -> "Character":
        """캐릭터 완성도 검증"""
        info_types = [info.type for info in self.infos]
        
        if self.tier == CharacterTier.MAIN:
            # 주연급 필수 필드
            required = [
                InfoType.DESIRE,
                InfoType.FEAR, 
                InfoType.PARADOX,
                InfoType.MODUS_OPERANDI,
                InfoType.RHETORIC,
                InfoType.EMOTION,
                InfoType.GROWTH_POTENTIAL
            ]
            missing = [r.value for r in required if r not in info_types]
            if missing:
                raise ValueError(f"주연급 캐릭터 필수 필드 누락: {missing}")
            
            if not self.analysis:
                raise ValueError("주연급 캐릭터는 analysis가 필수입니다")
                
        elif self.tier == CharacterTier.SUPPORTING:
            # 조연급 필수 필드
            required = [
                InfoType.DESIRE,
                InfoType.FEAR,
                InfoType.PARADOX,
                InfoType.GROWTH_POTENTIAL
            ]
            missing = [r.value for r in required if r not in info_types]
            if missing:
                raise ValueError(f"조연급 캐릭터 필수 필드 누락: {missing}")
                
        elif self.tier == CharacterTier.MINOR:
            # 단역 필수 필드
            required = [InfoType.DESIRE, InfoType.FEAR]
            missing = [r.value for r in required if r not in info_types]
            if missing:
                raise ValueError(f"단역 캐릭터 필수 필드 누락: {missing}")
        
        return self


class SimplifiedCharacter(BaseModel):
    """간소화된 캐릭터 (조연급/단역용)"""
    
    role: str = Field(
        description="캐릭터의 역할",
        pattern=r"^\(.+\)$"
    )
    
    tier: CharacterTier = Field(
        description="캐릭터 중요도"
    )
    
    infos: List[Info] = Field(
        description="캐릭터의 핵심 속성들",
        min_length=2,
        max_length=6
    )


# ============ Create Event 노드 ============
class PlaceHolder(BaseModel):
    """이벤트에 등장하는 미확정 캐릭터"""
    
    role: str = Field(
        description="PlaceHolder의 역할",
        pattern=r"^\(.+\)$"
    )


class Event(BaseModel):
    """캐릭터 속성을 형성한 과거 사건"""
    
    target_role: str = Field(
        description="대상 캐릭터 역할",
        pattern=r"^\(.+\)$"
    )
    
    target_info_type: InfoType = Field(
        description="형성한 속성 유형"
    )
    
    summary: str = Field(
        description="사건의 핵심 내용",
        min_length=20,
        max_length=300
    )
    
    placeholders: List[PlaceHolder] = Field(
        description="사건에 등장하는 PlaceHolder들",
        min_length=0,
        max_length=4
    )
    
    @model_validator(mode="after")
    def validate_summary(self) -> "Event":
        """사건 요약 검증"""
        if self.target_role not in self.summary:
            raise ValueError(f"사건 요약에 target_role({self.target_role})이 포함되어야 합니다")
        for placeholder in self.placeholders:
            if placeholder.role not in self.summary:
                raise ValueError(f"사건 요약에 PlaceHolder({placeholder.role})가 포함되어야 합니다")
        return self


# ============ Consolidate 노드 ============
class ConsolidationPrepareResult(BaseModel):
    """PlaceHolder 통합 준비 결과"""
    
    chunked_placeholders: List[List[str]] = Field(
        description="유사한 역할들의 ID 그룹"
    )
    
    @field_validator("chunked_placeholders")
    @classmethod
    def validate_placeholder_format(cls, v: List[List[str]]) -> List[List[str]]:
        """PlaceHolder ID 형식 검증"""
        pattern = re.compile(r"^placeholder_\d+$")
        seen = set()
        for group in v:
            if len(group) < 2:
                raise ValueError("각 그룹은 최소 2개 이상의 PlaceHolder를 포함해야 합니다")
            for ph_id in group:
                if not pattern.match(ph_id):
                    raise ValueError(f"잘못된 PlaceHolder ID 형식: {ph_id}")
                if ph_id in seen:
                    raise ValueError(f"PlaceHolder ID가 여러 그룹에 중복: {ph_id}")
                seen.add(ph_id)
        return v


class ConsolidatedRole(BaseModel):
    """통합된 PlaceHolder 역할"""
    
    unified_role: Optional[str] = Field(
        default=None,
        description="통합된 역할명",
        pattern=r"^\(.+\)$"
    )
    
    original_placeholders: Optional[Dict[str, str]] = Field(
        default=None,
        description="통합된 원본 PlaceHolder들"
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
        description="통합된 역할 목록",
        min_length=0
    )
    
    @model_validator(mode="after")
    def check_duplicate_placeholders(self) -> "ConsolidationResult":
        """중복 검증"""
        seen = set()
        for role in self.consolidated_roles:
            if role.original_placeholders:
                for ph_id in role.original_placeholders.keys():
                    if ph_id in seen:
                        raise ValueError(f"PlaceHolder ID 중복: {ph_id}")
                    seen.add(ph_id)
        return self


# ============ Create Plot 노드 ============
class PlotPoint(BaseModel):
    """스토리의 주요 전환점"""
    
    sequence: int = Field(
        description="시간 순서상 위치",
        ge=1,
        le=10
    )
    
    description: str = Field(
        description="플롯 포인트 설명",
        min_length=20,
        max_length=300
    )
    
    macro_cliffhanger: str = Field(
        description="미해결 문제",
        min_length=10,
        max_length=200
    )
    
    involved_characters: List[str] = Field(
        description="관련 캐릭터 역할들",
        min_length=1,
        max_length=8
    )
    
    plot_function: PlotFunction = Field(
        description="서사 구조상 기능"
    )
    
    tension_level: int = Field(
        description="긴장감 수준",
        ge=1,
        le=10
    )
    
    expansion_potential: Optional[str] = Field(
        default=None,
        description="확장 가능한 서브플롯",
        max_length=200
    )


class Plot(BaseModel):
    """완성된 플롯 구조"""
    
    theme: str = Field(
        description="플롯이 탐구하는 중심 주제"
    )
    
    plot_points: List[PlotPoint] = Field(
        description="핵심 플롯 포인트들",
        min_length=3,
        max_length=10
    )
    
    end_direction: str = Field(
        description="결말의 방향성"
    )
    
    narrative_strategy: Optional[str] = Field(
        default=None,
        description="독특한 서사 전략"
    )
    
    @model_validator(mode="after")
    def validate_plot_coherence(self) -> "Plot":
        """플롯 구조 검증"""
        sequences = [pp.sequence for pp in self.plot_points]
        if sequences != sorted(sequences):
            raise ValueError("플롯 포인트는 시간 순서대로 배열되어야 합니다")
        
        tension_levels = [pp.tension_level for pp in self.plot_points]
        if max(tension_levels) < 8:
            raise ValueError("최소 하나의 플롯 포인트는 8 이상의 긴장감을 가져야 합니다")
        
        return self


class PlotCandidates(BaseModel):
    """플롯 후보군"""
    
    plot_candidates: List[Plot] = Field(
        description="서로 다른 서사 전략을 가진 플롯 후보들",
        min_length=2,
        max_length=5
    )
    
    recommendation: Optional[str] = Field(
        default=None,
        description="가장 추천하는 플롯과 이유",
        max_length=300
    )