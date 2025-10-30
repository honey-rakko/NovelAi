"""
캐릭터 티어별 노드 함수 구현 (주연/조연/단역 구분)
"""

import warnings
from typing import Any, Dict, List

from langchain_core.messages import SystemMessage

from character_network import CharacterNetwork
from prompts.stage1_prompts import CHARACTER_PROMPT
from prompts.stage1_character_tiers import SUPPORTING_CHARACTER_PROMPT, MINOR_CHARACTER_PROMPT
from pydantics.stage1_pydantics_v3 import (
    Character,
    SimplifiedCharacter,
    CharacterTier,
    InfoType,
    Info,
    InfoWithEventId,
    Infos
)
from utils import create_unified_extractor


def create_main_character_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """주연급 캐릭터를 생성하는 노드 (모든 필드 포함)"""
    role = state["role"]
    topic = state["topic"]
    conflict = state["conflict"]
    role_info = state.get("role_info", {})
    
    # 주연급은 전체 CHARACTER_PROMPT 사용
    prompt = CHARACTER_PROMPT.format(
        topic=topic,
        role=role,
        conflict=conflict,
        role_info=role_info
    )
    
    extractor = create_unified_extractor(
        model_name=state.get("model"),
        extractor_type=state.get("extractor_type", "default"),
        tools=[Character],
        tool_choice="Character",
    )
    
    response = extractor.invoke([SystemMessage(content=prompt)])
    if hasattr(response, "responses") and response["responses"][0]:
        parsed = response["responses"][0]
    else:
        args = response["messages"][0].tool_calls[0]["args"]
        parsed = Character(**args)
    
    # tier 설정
    parsed.tier = CharacterTier.MAIN
    
    return {"generated_character": [parsed]}


def create_supporting_character_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """조연급 캐릭터를 생성하는 노드 (핵심 필드만)"""
    placeholder_role = state["placeholder_role"]
    event_contexts = state["event_contexts"]
    topic = state["topic"]
    conflict = state["conflict"]
    
    prompt = SUPPORTING_CHARACTER_PROMPT.format(
        placeholder_role=placeholder_role,
        event_contexts=event_contexts,
        topic=topic,
        conflict=conflict
    )
    
    extractor = create_unified_extractor(
        model_name=state.get("model"),
        extractor_type=state.get("extractor_type", "default"),
        tools=[SimplifiedCharacter],
        tool_choice="SimplifiedCharacter",
    )
    
    response = extractor.invoke([SystemMessage(content=prompt)])
    if hasattr(response, "responses") and response["responses"][0]:
        parsed = response["responses"][0]
    else:
        args = response["messages"][0].tool_calls[0]["args"]
        parsed = SimplifiedCharacter(**args)
    
    # tier 설정
    parsed.tier = CharacterTier.SUPPORTING
    
    return {"generated_character": parsed}


def create_minor_character_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """단역 캐릭터를 생성하는 노드 (최소 필드만)"""
    placeholder_role = state["placeholder_role"]
    event_context = state.get("event_contexts", [""])[0]  # 첫 번째 이벤트만
    
    prompt = MINOR_CHARACTER_PROMPT.format(
        placeholder_role=placeholder_role,
        event_context=event_context
    )
    
    extractor = create_unified_extractor(
        model_name=state.get("model"),
        extractor_type=state.get("extractor_type", "default"),
        tools=[SimplifiedCharacter],
        tool_choice="SimplifiedCharacter",
    )
    
    response = extractor.invoke([SystemMessage(content=prompt)])
    if hasattr(response, "responses") and response["responses"][0]:
        parsed = response["responses"][0]
    else:
        args = response["messages"][0].tool_calls[0]["args"]
        parsed = SimplifiedCharacter(**args)
    
    # tier 설정
    parsed.tier = CharacterTier.MINOR
    
    return {"generated_character": parsed}


def determine_character_tier(state: Dict[str, Any]) -> str:
    """PlaceHolder를 어떤 티어의 캐릭터로 만들지 결정하는 함수"""
    
    # 판단 기준
    current_iteration = state.get("current_iteration", 0)
    connected_events = state.get("connected_events", [])
    graph: CharacterNetwork = state.get("graph")
    
    # 현재 캐릭터 수
    character_count = len(graph.get_characters()) if graph else 0
    
    # 티어 결정 로직
    if current_iteration == 0:
        # 첫 번째 반복: 주연급
        return "main"
    elif current_iteration == 1 and character_count < 8:
        # 두 번째 반복이고 캐릭터가 적으면: 조연급
        return "supporting"
    elif len(connected_events) >= 3:
        # 많은 이벤트와 연결: 조연급
        return "supporting"
    elif len(connected_events) >= 2:
        # 중간 정도 연결: 조연급 또는 단역
        return "supporting" if character_count < 15 else "minor"
    else:
        # 적은 연결: 단역
        return "minor"


def create_placeholder_info_tiered(state: Dict[str, Any]) -> Dict[str, Any]:
    """PlaceHolder의 중요도에 따라 적절한 Info를 생성"""
    
    placeholder_id = state["placeholder_id"]
    placeholder_role = state["placeholder_role"]
    event_contexts = state["event_contexts"]
    valid_event_ids = state.get("valid_event_ids", [])
    
    # 티어 결정
    tier = determine_character_tier(state)
    
    # 티어에 따라 생성할 Info 개수 결정
    if tier == "main":
        # 주연급: 전체 필드
        required_types = [
            InfoType.DESIRE,
            InfoType.FEAR,
            InfoType.PARADOX,
            InfoType.MODUS_OPERANDI,
            InfoType.RHETORIC,
            InfoType.EMOTION,
            InfoType.GROWTH_POTENTIAL
        ]
    elif tier == "supporting":
        # 조연급: 핵심 필드만
        required_types = [
            InfoType.DESIRE,
            InfoType.FEAR,
            InfoType.PARADOX,
            InfoType.GROWTH_POTENTIAL
        ]
        # 선택적으로 1-2개 추가
        import random
        optional = [InfoType.MODUS_OPERANDI, InfoType.RHETORIC, InfoType.EMOTION]
        required_types.extend(random.sample(optional, min(1, len(optional))))
    else:
        # 단역: 최소 필드
        required_types = [
            InfoType.DESIRE,
            InfoType.FEAR
        ]
    
    # Info 생성
    infos = []
    for i, info_type in enumerate(required_types):
        # event_id 할당
        if i < len(valid_event_ids):
            event_id = valid_event_ids[i]
        else:
            event_id = "미정"
        
        # 내용 생성 (간단한 템플릿)
        content = f"{placeholder_role}의 {info_type.value}"
        
        infos.append(InfoWithEventId(
            type=info_type,
            content=content,
            event_id=event_id
        ))
    
    return {
        "generated_infos": [(placeholder_id, infos)],
        "character_tier": tier
    }


def update_graph_with_tiered_character(state: Dict[str, Any]) -> Dict[str, Any]:
    """티어별 캐릭터를 그래프에 추가"""
    
    graph: CharacterNetwork = state["graph"]
    character = state["generated_character"]
    current_iteration = state["current_iteration"]
    tier = character.tier if hasattr(character, "tier") else CharacterTier.MINOR
    
    # Character 또는 SimplifiedCharacter 처리
    if isinstance(character, list):
        character = character[0]
    
    # 그래프에 추가
    char_id = graph.add_character(
        role=character.role,
        created_at=current_iteration,
        metadata={"tier": tier.value}
    )
    
    # Info 노드들 추가
    for info in character.infos:
        info_id = graph.add_info(
            info_type=info.type,
            content=info.content,
            owner_id=char_id,
            created_at=current_iteration
        )
        graph.connect_nodes(info_id, char_id)
    
    # Analysis 추가 (주연급만)
    if hasattr(character, "analysis") and character.analysis:
        analysis_id = graph.add_node(
            node_type="analysis",
            data={
                "situation": character.analysis.situation,
                "question": character.analysis.question,
                "philosophy": character.analysis.philosophy,
                "owner_id": char_id
            }
        )
        graph.connect_nodes(analysis_id, char_id)
    
    return {"graph": graph}


def get_character_tier_stats(graph: CharacterNetwork) -> Dict[str, int]:
    """그래프에서 캐릭터 티어별 통계 반환"""
    
    characters = graph.get_characters()
    stats = {
        "main": 0,
        "supporting": 0,
        "minor": 0,
        "unknown": 0
    }
    
    for char_id, char_node in characters:
        metadata = char_node.data.get("metadata", {})
        tier = metadata.get("tier", "unknown")
        stats[tier] = stats.get(tier, 0) + 1
    
    return stats