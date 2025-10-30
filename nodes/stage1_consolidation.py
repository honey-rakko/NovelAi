import warnings
from typing import Any, Dict, List

from langchain_core.messages import SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from character_network import CharacterNetwork
from nodes.stage1_nodes import initialize_accumulated_state, save_graph_to_file
from prompts.stage1_prompts import CONSOLIDATION_PREPARE_PROMPT, CONSOLIDATION_PROMPT
from pydantics.stage1_pydantics import ConsolidationPrepareResult, ConsolidationResult
from states.stage1_states import ConsolidationState
from utils import create_unified_extractor


# ============ 노드 함수들 ============

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


# ============ 조건부 엣지 함수들 ============
def distribute_consolidation(state: ConsolidationState) -> List[Send]:
    """Consolidation을 위한 Send 분배"""
    graph: CharacterNetwork = state["graph"]
    chunked_placeholders = state["chunked_placeholders"]
    sends = []
    for chunked_placeholder in chunked_placeholders:
        # PlaceHolder 정보 수집
        placeholder_info = []
        for ph_id in chunked_placeholder:
            ph_node = graph.nodes[ph_id]
            role = ph_node.data.get("role", "Unknown")
            event_node = graph.nodes[ph_node.data.get("owner_id", "Unknown")]
            owner_id = event_node.data.get("owner_id", "Unknown")
            owner_role = graph.nodes[owner_id].data.get("role", "Unknown")
            summary = event_node.data.get("summary", "Unknown event")
            placeholder_info.append(
                f"- {role} (id: {ph_id}) (중심 인물: {owner_role} (id: {owner_id}), 관련 사건 요약: {summary})"
            )
        placeholder_info = "\n".join(placeholder_info)
        send_state = {
            "placeholder_info": placeholder_info,
            "model": state.get("model"),
            "extractor_type": state.get("extractor_type"),
        }
        sends.append(Send("consolidate", send_state))
    return sends


# ============ 서브그래프 구현 ============
def build_consolidation_subgraph():
    """Consolidation 서브그래프"""
    subgraph = StateGraph(ConsolidationState)

    subgraph.add_node("initialize_accumulated_state", initialize_accumulated_state)
    subgraph.add_node("prepare_consolidation", prepare_consolidation_node)
    subgraph.add_node("consolidate", consolidate_node)
    subgraph.add_node("update_consolidation_graph", update_graph_after_consolidation)
    subgraph.add_node("save_graph_to_file", save_graph_to_file)

    subgraph.add_edge(START, "initialize_accumulated_state")
    subgraph.add_edge("initialize_accumulated_state", "prepare_consolidation")
    subgraph.add_conditional_edges(
        "prepare_consolidation", distribute_consolidation, ["consolidate"]
    )
    subgraph.add_edge("consolidate", "update_consolidation_graph")
    subgraph.add_edge("update_consolidation_graph", "save_graph_to_file")
    subgraph.add_edge("save_graph_to_file", END)
    return subgraph.compile()
