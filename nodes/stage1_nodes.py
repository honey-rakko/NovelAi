"""
LangGraph 노드 구현 - 단일 책임 원칙에 따라 각 노드는 하나의 역할만 수행
"""

import os
import warnings
from datetime import datetime
from typing import Any, Dict

from langchain_core.messages import SystemMessage

from character_network import CharacterNetwork
from prompts.stage1_prompts import (
    CHARACTER_PROMPT,
    CONSOLIDATION_PREPARE_PROMPT,
    CONSOLIDATION_PROMPT,
    EVENT_PROMPT,
    PLACEHOLDER_INFO_PROMPT,
    # PLOT_CANDIDATES_PROMPT,
    # PLOT_PROMPT,
    ROLES_PROMPT,
)
from pydantics.stage1_pydantics import (
    Character,
    ConsolidationPrepareResult,
    ConsolidationResult,
    Event,
    Infos,
    # Plot,
    # PlotCandidates,
    Roles,
)

# LLM 설정
from utils import create_unified_extractor

# ============ LLM 호출 노드들 (Input/Output 명시) ============

# 지금 버전에서 플롯 후보 필요 없음
# def create_plot_candidates_node(state: Dict[str, Any]) -> Dict[str, Any]:
#     """Topic을 받아서 Plot Candidates를 생성하는 LLM 노드"""
#     topic = get_state_value(state, "topic")
#     conflict = get_state_value(state, "conflict")
#     vibe = get_state_value(state, "vibe")
#     prompt = PLOT_CANDIDATES_PROMPT.format(topic=topic, conflict=conflict, vibe=vibe)

#     # State에서 extractor 생성
#     extractor = create_unified_extractor(
#         model_name=state.get("model"),
#         extractor_type=state.get("extractor_type", "default"),
#         tools=[PlotCandidates],
#         tool_choice="PlotCandidates",
#     )
#     response = extractor.invoke([SystemMessage(content=prompt)])
#     if hasattr(response, "responses") and response["responses"][0]:
#         parsed = response["responses"][0]
#     else:  # trustcall의 emtpy response 문제 때문에 임시 처리
#         args = response["messages"][0].tool_calls[0]["args"]
#         parsed = PlotCandidates(**args)

#     plot_candidates = parsed

#     return {"plot_candidates": plot_candidates.plot_candidates}


# def select_plot_node(state: Dict[str, Any]) -> Dict[str, Any]:
#     """Plot Candidates를 받아서 Plot을 선택하는 LLM 노드"""
#     plot_candidates = state["plot_candidates"]
#     prompt = PLOT_PROMPT.format(plot_candidates=plot_candidates)
#     extractor = create_unified_extractor(
#         model_name=state.get("model"),
#         extractor_type=state.get("extractor_type", "default"),
#         tools=[Plot],
#         tool_choice="Plot",
#     )
#     response = extractor.invoke([SystemMessage(content=prompt)])
#     if hasattr(response, "responses") and response["responses"][0]:
#         parsed = response["responses"][0]
#     else:  # trustcall의 emtpy response 문제 때문에 임시 처리
#         args = response["messages"][0].tool_calls[0]["args"]
#         parsed = Plot(**args)
#     plot = parsed

#     return {"plot": plot}


def define_main_character_roles(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    legacy : Topic을 받아서 Roles를 생성하는 LLM 노드
    현재는 RoleInfo를 생성해야함.
    """
    topic = state["topic"]
    conflict = state["conflict"]
    vibe = state["vibe"]

    prompt = ROLES_PROMPT.format(topic=topic, conflict=conflict, vibe=vibe)

    extractor = create_unified_extractor(
        model_name=state.get("model"),
        extractor_type=state.get("extractor_type", "default"),
        tools=[Roles],
        tool_choice="Roles",
    )
    response = extractor.invoke([SystemMessage(content=prompt)])
    if hasattr(response, "responses") and response["responses"][0]:
        parsed = response["responses"][0]
    else:  # trustcall의 emtpy response 문제 때문에 임시 처리
        args = response["messages"][0].tool_calls[0]["args"]
        parsed = Roles(**args)
    roles = parsed

    return {"roles": roles.roles}


def create_character_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """CharacterCreationState를 받아서 Character와 Info를 생성하는 LLM 노드"""
    role = state["role"]
    topic = state["topic"]
    conflict = state["conflict"]
    role_info = state["role_info"]
    # Pydantic 모델을 dict로 받았으므로, 보기 좋게 포매팅합니다.
    role_info_str = "\n".join([f"- {key}: {value}" for key, value in role_info.items()])
    #Chracter는 Vibe 고착화될까봐 쓰지 않음.

    # 초기 캐릭터 생성
    prompt = CHARACTER_PROMPT.format(topic=topic, role=role, conflict=conflict, role_info=role_info_str)

    extractor = create_unified_extractor(
        model_name=state.get("model"),
        extractor_type=state.get("extractor_type", "default"),
        tools=[Character],
        tool_choice="Character",
    )
    response = extractor.invoke([SystemMessage(content=prompt)])
    if hasattr(response, "responses") and response["responses"][0]:
        parsed = response["responses"][0]
    else:  # trustcall의 emtpy response 문제 때문에 임시 처리
        args = response["messages"][0].tool_calls[0]["args"]
        parsed = Character(**args)
    character = parsed

    return {"generated_character": [character]}


def create_event_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """EventCreationState를 받아서 Event와 PlaceHolder를 생성하는 LLM 노드"""
    role = state["role"]
    conflict = state["conflict"]
    vibe = state["vibe"]
    char_id = state["char_id"]
    info_id = state["info_id"]
    current_info_type = state["current_info_type"]
    current_info_content = state["current_info_content"]

    prompt = EVENT_PROMPT.format(
        character_role=role,
        info_type=current_info_type,
        info_content=current_info_content,
        conflict=conflict,
        vibe=vibe,
    )

    extractor = create_unified_extractor(
        model_name=state.get("model"),
        extractor_type=state.get("extractor_type", "default"),
        tools=[Event],
        tool_choice="Event",
    )
    response = extractor.invoke([SystemMessage(content=prompt)])
    if hasattr(response, "responses") and response["responses"][0]:
        parsed = response["responses"][0]
    else:  # trustcall의 emtpy response 문제 때문에 임시 처리
        args = response["messages"][0].tool_calls[0]["args"]
        parsed = Event(**args)
    event = parsed

    return {"generated_event": [(char_id, info_id, event)]}

def prepare_consolidation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """PlaceHolder들을 받아서 헷갈릴 수 있는 Role들을 선별하는 LLM 노드"""
    graph: CharacterNetwork = state["graph"]
    placeholders = graph.get_placeholders()
    placeholder_list = []
    for placeholder_id, placeholder_node in placeholders:
        placeholder_list.append(
            f"- {placeholder_node.data.get('role', 'Unknown')} (id: {placeholder_id})"
        )
    placeholder_list = "\n".join(placeholder_list)
    prompt = CONSOLIDATION_PREPARE_PROMPT.format(placeholder_list=placeholder_list)
    extractor = create_unified_extractor(
        model_name=state.get("model"),
        extractor_type=state.get("extractor_type", "default"),
        tools=[ConsolidationPrepareResult],
        tool_choice="ConsolidationPrepareResult",
    )
    response = extractor.invoke([SystemMessage(content=prompt)])
    if hasattr(response, "responses") and response["responses"][0]:
        parsed = response["responses"][0]
    else:  # trustcall의 emtpy response 문제 때문에 임시 처리
        args = response["messages"][0].tool_calls[0]["args"]
        parsed = ConsolidationPrepareResult(**args)
    result = parsed
    return {"chunked_placeholders": result.chunked_placeholders}


def consolidate_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """PlaceHolder들을 받아서 통합된 Role들을 생성하는 LLM 노드"""
    placeholder_info = state["placeholder_info"]

    prompt = CONSOLIDATION_PROMPT.format(placeholder_info=placeholder_info)

    extractor = create_unified_extractor(
        model_name=state.get("model"),
        extractor_type=state.get("extractor_type", "default"),
        tools=[ConsolidationResult],
        tool_choice="ConsolidationResult",
    )
    response = extractor.invoke([SystemMessage(content=prompt)])
    if hasattr(response, "responses") and response["responses"][0]:
        parsed = response["responses"][0]
    else:  # trustcall의 emtpy response 문제 때문에 임시 처리
        args = response["messages"][0].tool_calls[0]["args"]
        parsed = ConsolidationResult(**args)
    result = parsed
    return {"consolidated_roles": result.consolidated_roles}


def create_info_for_placeholder_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """PlaceHolder와 연결된 Event context로 Info 생성 (LLM 호출)"""
    placeholder_id = state["placeholder_id"]
    placeholder_role = state["placeholder_role"]
    event_contexts = state["event_contexts"]
    valid_event_ids = state.get("valid_event_ids", [])  # 유효한 event_id 목록 가져오기

    # 프롬프트 생성 (유효한 event_id 목록 포함)
    prompt = PLACEHOLDER_INFO_PROMPT.format(
        placeholder_role=placeholder_role,
        event_contexts=event_contexts,
        valid_event_ids=valid_event_ids,  # 유효한 event_id 명시
    )

    # LLM 호출하여 Info 생성
    extractor = create_unified_extractor(
        model_name=state.get("model"),
        extractor_type=state.get("extractor_type", "default"),
        tools=[Infos],
        tool_choice="Infos",
    )
    response = extractor.invoke([SystemMessage(content=prompt)])
    if hasattr(response, "responses") and response["responses"][0]:
        parsed = response["responses"][0]
    else:  # trustcall의 emtpy response 문제 때문에 임시 처리
        args = response["messages"][0].tool_calls[0]["args"]
        parsed = Infos(**args)
    infos = parsed

    return {
        "generated_infos": [(placeholder_id, infos.infos)],
    }


# ============ 일반 노드들 (LLM 호출 없음) ============


def prepare_placeholders_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """PlaceHolder들의 연결된 Event들을 찾아서 반환"""
    graph: CharacterNetwork = state["graph"]

    placeholders = []

    # 모든 PlaceHolder 노드 찾기
    for node_id, node in graph.nodes.items():
        if node.type.value == "placeholder":
            connected_events = []
            for edge_id in node.edges:
                if (
                    edge_id in graph.nodes
                    and graph.nodes[edge_id].type.value == "event"
                ):
                    connected_events.append(edge_id)
            placeholders.append((node_id, connected_events))
    return {
        "placeholders": placeholders,
    }


def update_graph_with_character(state: Dict[str, Any]) -> Dict[str, Any]:
    """CharacterCreationState에서 생성된 Character와 Info를 Graph에 추가"""
    graph: CharacterNetwork = state["graph"]
    characters = state["generated_character"]
    current_iteration = state["current_iteration"]

    for character in characters:
        char_id = graph.add_character(role=character.role, created_at=current_iteration)

        # Info 노드들 추가 및 연결
        info_ids = []
        for info in character.infos:
            info_id = graph.add_info(
                info_type=info.type,
                content=info.content,
                owner_id=char_id,
                created_at=current_iteration,
            )
            graph.connect_nodes(info_id, char_id)
            info_ids.append(info_id)
    return {
        "graph": graph,
    }


def update_graph_with_event(state: Dict[str, Any]) -> Dict[str, Any]:
    """생성된 Event와 PlaceHolder를 Graph에 추가"""
    graph: CharacterNetwork = state["graph"]
    events = state["generated_event"]
    current_iteration = state["current_iteration"]
    for char_id, info_id, event in events:
        event_id = graph.add_event(
            summary=event.summary,
            target_info_type=event.target_info_type,
            owner_id=char_id,
            created_at=current_iteration,
        )
        graph.connect_nodes(info_id, event_id)
        # PlaceHolder 노드들 추가 및 Event와 연결
        for placeholder in event.placeholders:
            ph_id = graph.add_placeholder(
                role=placeholder.role,
                owner_id=event_id,
                created_at=current_iteration,
            )
            graph.connect_nodes(event_id, ph_id)
    return {"graph": graph}


def update_graph_after_consolidation(state: Dict[str, Any]) -> Dict[str, Any]:
    """Consolidation 결과를 Graph에 반영"""
    graph: CharacterNetwork = state["graph"]
    consolidated_roles = state["consolidated_roles"]
    current_iteration = state["current_iteration"]
    # 노드 통합
    for role in consolidated_roles:
        original_ids = list(role.original_placeholders.keys())
        owner_ids = []
        for original_id in original_ids:
            if original_id not in graph.nodes:
                raise ValueError(f"Original id {original_id} not found in graph")
            owner_ids.append(graph.nodes[original_id].data.get("owner_id", "Unknown"))
            original_role = graph.nodes[original_id].data.get("role", "Unknown")
            if original_role != role.original_placeholders[original_id]:
                warnings.warn(
                    f"Warning: Original role {original_role} does not match {role.original_placeholders[original_id]}"
                )

        # Event summary 업데이트: 원본 PlaceHolder 역할명을 통합된 역할명으로 치환
        for original_id, original_role_name in role.original_placeholders.items():
            event_id = graph.nodes[original_id].data.get("owner_id")
            if event_id in graph.nodes:
                event_node = graph.nodes[event_id]
                old_summary = event_node.data.get("summary", "")
                # 원본: "(엄격한 아버지)" → 통합: "(권위적인 조언자)" (모두 괄호 포함)
                new_summary = old_summary.replace(original_role_name, role.unified_role)
                event_node.data["summary"] = new_summary

        unified_id = graph.add_placeholder(
            role.unified_role, owner_ids, created_at=current_iteration
        )
        graph.merge_nodes(original_ids, unified_id)
    return {"graph": graph}


def update_graph_with_infos(state: Dict[str, Any]) -> Dict[str, Any]:
    """새로운 Character를 생성하고 입력받은 Info들을 연결하고 PlaceHolder 제거"""
    graph: CharacterNetwork = state["graph"]
    generated_infos = state["generated_infos"]
    current_iteration = state["current_iteration"]

    for placeholder_id, infos in generated_infos:
        placeholder_node = graph.nodes[placeholder_id]
        placeholder_role = placeholder_node.data.get("role", "Unknown")

        # PlaceHolder와 연결된 유효한 Event 목록 수집
        valid_event_ids = set()
        for edge_id in placeholder_node.edges:
            if edge_id.startswith("event_"):
                valid_event_ids.add(edge_id)

        char_id = graph.add_character(
            role=placeholder_role, created_at=current_iteration
        )
        for info in infos:
            info_id = graph.add_info(
                info_type=info.type,
                content=info.content,
                owner_id=char_id,
                created_at=current_iteration,
            )
            if info.event_id != "미정":
                # 검증: event_id가 실제로 Graph에 존재하는지 확인
                if info.event_id not in graph.nodes:
                    warnings.warn(
                        f"Warning: {placeholder_role}의 Info가 존재하지 않는 event_id '{info.event_id}'를 참조합니다. 연결하지 않습니다."
                    )
                    continue

                # 검증: event_id가 PlaceHolder와 실제로 연결되어 있는지 확인
                if info.event_id not in valid_event_ids:
                    warnings.warn(
                        f"""Warning: {placeholder_role}의 Info가 연결되지 않은 event_id '{info.event_id}'를 참조합니다.
                        유효한 event_id: {list(valid_event_ids)}
                        연결하지 않습니다."""
                    )
                    continue

                graph.connect_nodes(info_id, info.event_id)
            graph.connect_nodes(info_id, char_id)
        graph.remove_node(placeholder_id)
    return {"graph": graph}


def save_graph_to_file(state: Dict[str, Any]) -> Dict[str, Any]:
    """Graph를 파일에 저장"""
    graph: CharacterNetwork = state["graph"]
    current_iteration = state["current_iteration"]
    output_dir = "saved_graphs"
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    graph.save_to_file(f"{output_dir}/story_graph_{timestamp}_{current_iteration}.json")

    stats = graph.get_statistics()
    print("\n=== 워크플로우 완료 ===")
    print(f"주제: {state['topic']}")
    print(f"총 노드: {stats['total_nodes']}")
    print(f"- Characters: {stats['characters']}")
    print(f"- Events: {stats['events']}")
    print(f"- Infos: {stats['infos']}")
    print(f"- PlaceHolders: {stats['placeholders']}")
    print(f"총 연결: {stats['total_edges']}")
    return state


# ============ 누적 State 초기화 노드들 ============


def initialize_accumulated_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """누적 State 초기화 - model, extractor_type도 유지"""
    new_state = {}
    for key, value in state.items():
        if key in [
            "graph",
            "current_iteration",
            "topic",
            "roles",
            "model",
            "extractor_type",
        ]:
            new_state[key] = value
        else:
            new_state[key] = None
    return new_state


# ============ Plot v2 노드들 (새로 추가) ============

from prompts.stage1_plot_prompts import (
    NARRATIVE_POLES_PROMPT,
    SUB_THEME_SELECTION_PROMPT,
    INCITING_INCIDENT_AND_MACRO_CLIFFHANGERS_PROMPT,
    STRUCTURAL_TEMPO_PROMPT,
    INTEGRATED_PLOT_GENERATION_PROMPT,
)
from pydantics.stage1_plot_pydantics import (
    NarrativePoles,
    ActSubThemes,
    IncitingAndMacroStructure,
    StructuralTempo,
    IntegratedPlot,
)


def analyze_narrative_poles_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """캐릭터 네트워크를 분석하여 서사적 양극을 설정하는 노드"""
    graph: CharacterNetwork = state["graph"]
    topic = state["topic"]
    conflict = state["conflict"]
    vibe = state["vibe"]
    
    # 캐릭터 네트워크 분석 정보 추출
    character_analysis = []
    characters = graph.get_characters()
    
    for char_id, char_node in characters:
        role = char_node.data.get("role", "Unknown")
        # --- [핵심 수정] ---
        # 1. 캐릭터 노드에서 'analysis' 데이터를 가져옵니다.
        analysis_data = char_node.data.get("analysis", {})
        analysis_str = (
            f"  [핵심 분석]\n"
            f"  - 상황: {analysis_data.get('situation', 'N/A')}\n"
            f"  - 질문: {analysis_data.get('question', 'N/A')}\n"
            f"  - 철학: {analysis_data.get('philosophy', 'N/A')}"
        )
        # --------------------
        infos = []
        for edge_id in char_node.edges:
            if edge_id.startswith("info_"):
                info_node = graph.nodes[edge_id]
                info_type = info_node.data.get("info_type", "")
                content = info_node.data.get("content", "")
                infos.append(f"{info_type}: {content}")
        
        # character_analysis.append(f"\n{role}:\n" + "\n".join(infos))
        # --- [핵심 수정] ---
        # 2. 'analysis' 정보를 'infos'와 함께 최종 분석 자료에 포함시킵니다.
        character_analysis.append(f"\n{role}:\n{analysis_str}\n  [세부 속성]\n" + "\n".join(infos))
        # --------------------
    
    character_network_analysis = "\n".join(character_analysis)
    
    prompt = NARRATIVE_POLES_PROMPT.format(
        topic=topic,
        conflict=conflict,
        vibe=vibe,
        character_network_analysis=character_network_analysis
    )
    
    extractor = create_unified_extractor(
        model_name=state.get("model"),
        extractor_type=state.get("extractor_type", "default"),
        tools=[NarrativePoles],
        tool_choice="NarrativePoles",
    )
    
    response = extractor.invoke([SystemMessage(content=prompt)])
    if hasattr(response, "responses") and response["responses"][0]:
        parsed = response["responses"][0]
    else:
        args = response["messages"][0].tool_calls[0]["args"]
        parsed = NarrativePoles(**args)
    
    return {"narrative_poles": parsed}


def select_sub_themes_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Act별 Sub-theme을 선정하는 노드"""
    topic = state["topic"]
    conflict = state["conflict"]
    vibe = state["vibe"]
    narrative_poles = state["narrative_poles"]

    # 주연 캐릭터 정보 요약
    graph: CharacterNetwork = state["graph"]
    main_characters = []
    for char_id, char_node in graph.get_characters()[:5]:  # 주연 5명까지
        role = char_node.data.get("role", "Unknown")
        # Desire와 Fear 정보 찾기
        for edge_id in char_node.edges:
            if edge_id.startswith("info_"):
                info_node = graph.nodes[edge_id]
                if info_node.data.get("info_type") in ["desire", "fear"]:
                    main_characters.append(f"{role} - {info_node.data.get('info_type')}: {info_node.data.get('content')}")
    
    main_characters_summary = "\n".join(main_characters)
    
    # theme_list.txt 읽기
    with open("utils/theme_list.txt", "r", encoding="utf-8") as f:
        theme_list = f.read()
    
    prompt = SUB_THEME_SELECTION_PROMPT.format(
        topic=topic,
        conflict=conflict,
        vibe=vibe,
        starting_point=narrative_poles.starting_point.description,
        ending_point=narrative_poles.ending_point.description,
        main_characters_summary=main_characters_summary,
        theme_list=theme_list
    )
    
    extractor = create_unified_extractor(
        model_name=state.get("model"),
        extractor_type=state.get("extractor_type", "default"),
        tools=[ActSubThemes],
        tool_choice="ActSubThemes",
    )
    
    response = extractor.invoke([SystemMessage(content=prompt)])
    if hasattr(response, "responses") and response["responses"][0]:
        parsed = response["responses"][0]
    else:
        args = response["messages"][0].tool_calls[0]["args"]
        parsed = ActSubThemes(**args)
    
    return {"sub_themes": parsed}


def create_inciting_and_macro_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """기폭사건과 Macro Cliffhanger를 생성하는 노드"""
    topic = state["topic"]
    conflict = state["conflict"]
    vibe = state["vibe"]
    narrative_poles = state["narrative_poles"]
    sub_themes = state["sub_themes"]


    # 캐릭터 충돌 분석
    graph: CharacterNetwork = state["graph"]
    conflict_analysis = []
    
    # Event 패턴 분석
    events = graph.get_events()
    for event_id, event_node in events[:10]:  # 최대 10개 이벤트 분석
        summary = event_node.data.get("summary", "")
        conflict_analysis.append(f"과거 사건 패턴: {summary}")
    
    # PlaceHolder 분석
    placeholders = graph.get_placeholders()
    for ph_id, ph_node in placeholders[:5]:  # 최대 5개 PlaceHolder
        role = ph_node.data.get("role", "")
        conflict_analysis.append(f"잠재적 갈등 인물: {role}")
    
    character_conflict_analysis = "\n".join(conflict_analysis)
    
    # Sub-themes 정보 포매팅
    sub_themes_text = f"""Act 1: {sub_themes.act1_theme.theme}
Act 2: {sub_themes.act2_theme.theme}
Act 3: {sub_themes.act3_theme.theme}"""
    
    prompt = INCITING_INCIDENT_AND_MACRO_CLIFFHANGERS_PROMPT.format(
        topic=topic,
        conflict=conflict,
        vibe=vibe,
        starting_point=narrative_poles.starting_point.description,
        ending_point=narrative_poles.ending_point.description,
        sub_themes=sub_themes_text,
        character_conflict_analysis=character_conflict_analysis
    )
    
    extractor = create_unified_extractor(
        model_name=state.get("model"),
        extractor_type=state.get("extractor_type", "default"),
        tools=[IncitingAndMacroStructure],
        tool_choice="IncitingAndMacroStructure",
    )
    
    response = extractor.invoke([SystemMessage(content=prompt)])
    if hasattr(response, "responses") and response["responses"][0]:
        parsed = response["responses"][0]
    else:
        args = response["messages"][0].tool_calls[0]["args"]
        parsed = IncitingAndMacroStructure(**args)
    
    return {"inciting_and_macro": parsed}


def design_structural_tempo_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """구조적 템포를 설계하는 노드"""
    narrative_poles = state["narrative_poles"]
    inciting_and_macro = state["inciting_and_macro"]
    sub_themes = state["sub_themes"]

    # Macro Cliffhanger 정보 포매팅
    macro_cliffhangers = []
    for mc in inciting_and_macro.macro_cliffhangers:
        macro_cliffhangers.append(
            f"{mc.title} ({mc.type.value}): {mc.core_question} - {mc.duration_estimate}"
        )
    macro_cliffhangers_text = "\n".join(macro_cliffhangers)
    
    # Sub-themes 정보 포매팅  
    sub_themes_text = f"""Act 1: {sub_themes.act1_theme.theme}
Act 2: {sub_themes.act2_theme.theme}
Act 3: {sub_themes.act3_theme.theme}"""
    
    prompt = STRUCTURAL_TEMPO_PROMPT.format(
        starting_point=narrative_poles.starting_point.description,
        ending_point=narrative_poles.ending_point.description,
        inciting_incident=inciting_and_macro.inciting_incident.event_description,
        macro_cliffhangers=macro_cliffhangers_text,
        sub_themes=sub_themes_text
    )
    
    extractor = create_unified_extractor(
        model_name=state.get("model"),
        extractor_type=state.get("extractor_type", "default"),
        tools=[StructuralTempo],
        tool_choice="StructuralTempo",
    )
    
    response = extractor.invoke([SystemMessage(content=prompt)])
    if hasattr(response, "responses") and response["responses"][0]:
        parsed = response["responses"][0]
    else:
        args = response["messages"][0].tool_calls[0]["args"]
        parsed = StructuralTempo(**args)
    
    return {"structural_tempo": parsed}


def generate_integrated_plot_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """통합 플롯을 생성하는 노드"""
    narrative_poles = state["narrative_poles"]
    sub_themes = state["sub_themes"]
    inciting_and_macro = state["inciting_and_macro"]
    structural_tempo = state["structural_tempo"]

    # 각 단계 결과 텍스트화
    narrative_poles_text = f"""출발점: {narrative_poles.starting_point.description}
종착점: {narrative_poles.ending_point.description}
서사 거리: 심리적={narrative_poles.narrative_distance['psychological']}, 복잡도={narrative_poles.narrative_distance['complexity']}"""
    
    sub_themes_result_text = f"""Act 1: {sub_themes.act1_theme.theme} ({sub_themes.act1_theme.relationship_to_core})
Act 2: {sub_themes.act2_theme.theme} ({sub_themes.act2_theme.relationship_to_core})
Act 3: {sub_themes.act3_theme.theme} ({sub_themes.act3_theme.relationship_to_core})
진행 시너지: {sub_themes.theme_progression}"""
    
    inciting_and_macro_text = f"""기폭사건: {inciting_and_macro.inciting_incident.event_description}
주제적 질문: {inciting_and_macro.inciting_incident.thematic_question}
\nMacro Cliffhangers:
{inciting_and_macro.chain_diagram}"""
    
    structural_tempo_text = f"""총 화수: {structural_tempo.total_episodes}화
구간 수: {len(structural_tempo.segments)}개
중간아크 총 화수: {structural_tempo.episode_distribution.get('intermediate_arcs', 0)}화
독자 경험: {structural_tempo.reader_experience_flow}"""
    
    prompt = INTEGRATED_PLOT_GENERATION_PROMPT.format(
        narrative_poles=narrative_poles_text,
        sub_themes_result=sub_themes_result_text,
        inciting_and_macro=inciting_and_macro_text,
        structural_tempo=structural_tempo_text
    )
    
    extractor = create_unified_extractor(
        model_name=state.get("model"),
        extractor_type=state.get("extractor_type", "default"),
        tools=[IntegratedPlot],
        tool_choice="IntegratedPlot",
    )
    
    response = extractor.invoke([SystemMessage(content=prompt)])
    if hasattr(response, "responses") and response["responses"][0]:
        parsed = response["responses"][0]
    else:
        args = response["messages"][0].tool_calls[0]["args"]
        parsed = IntegratedPlot(**args)
    
    return {"integrated_plot": parsed}


def save_plot_to_file(state: Dict[str, Any]) -> Dict[str, Any]:
    """플롯 결과를 파일에 저장"""
    import json
    from datetime import datetime
    
    output_dir = "saved_plots"
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 통합 플롯 저장
    plot = state["integrated_plot"]
    plot_dict = plot.model_dump() if hasattr(plot, "model_dump") else plot.dict()
    
    # 전체 분석 결과도 함께 저장
    full_analysis = {
        "topic": state["topic"],
        "conflict": state["conflict"],
        "vibe": state["vibe"],
        "narrative_poles": state["narrative_poles"].model_dump() if hasattr(state["narrative_poles"], "model_dump") else state["narrative_poles"].dict(),
        "sub_themes": state["sub_themes"].model_dump() if hasattr(state["sub_themes"], "model_dump") else state["sub_themes"].dict(),
        "inciting_and_macro": state["inciting_and_macro"].model_dump() if hasattr(state["inciting_and_macro"], "model_dump") else state["inciting_and_macro"].dict(),
        "structural_tempo": state["structural_tempo"].model_dump() if hasattr(state["structural_tempo"], "model_dump") else state["structural_tempo"].dict(),
        "integrated_plot": plot_dict
    }
    
    filename = f"{output_dir}/plot_{timestamp}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(full_analysis, f, ensure_ascii=False, indent=2)
    
    print(f"\n=== 플롯 생성 완료 ===")
    print(f"플롯 파일 저장: {filename}")
    print(f"\n한 줄 요약: {plot.plot_summary}")
    print(f"핵심 질문: {plot.core_question}")
    print(f"\n3막 구조:")
    for act in plot.act_structures:
        print(f"  Act {act.act_number}: {act.subtitle} ({act.episode_range})")
        print(f"    Sub-theme: {act.sub_theme}")
        print(f"    Macro Cliffhangers: {', '.join(act.macro_cliffhangers)}")
    
    return state
