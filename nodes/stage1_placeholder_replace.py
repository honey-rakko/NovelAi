import warnings
from typing import Any, Dict, List

from langchain_core.messages import SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from character_network import CharacterNetwork
from nodes.stage1_nodes import initialize_accumulated_state, save_graph_to_file
from prompts.stage1_prompts import PLACEHOLDER_INFO_PROMPT
from pydantics.stage1_pydantics import Infos
from states.stage1_states import PlaceHolderReplaceState
from utils import create_unified_extractor


# ============ 노드 함수들 ============
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


# ============ 조건부 엣지 함수들 ============
def distribute_placeholder_info_creation(state: PlaceHolderReplaceState) -> List[Send]:
    """Consolidate된 PlaceHolder들의 Info 생성을 위한 Send 분배"""
    graph: CharacterNetwork = state["graph"]
    placeholders = state["placeholders"]

    sends = []
    for placeholder_id, connected_events in placeholders:
        placeholder_node = graph.nodes[placeholder_id]
        placeholder_role = placeholder_node.data.get("role", "Unknown")

        event_contexts = []
        valid_event_ids = []  # 유효한 event_id 목록 수집
        for event_id in connected_events:
            event_node = graph.nodes[event_id]
            event_summary = event_node.data.get("summary", "Unknown event")

            # Event owner (원 캐릭터) 정보
            owner_id = event_node.data.get("owner_id", "Unknown")
            if owner_id in graph.nodes:
                owner_role = graph.nodes[owner_id].data.get("role", "Unknown")
                event_contexts.append(
                    f"- {event_id}: {event_summary} (중심 인물: {owner_role})"
                )
                valid_event_ids.append(event_id)  # 유효한 event_id 저장
        event_contexts = "\n".join(event_contexts)
        send_state = {
            "placeholder_id": placeholder_id,
            "placeholder_role": placeholder_role,
            "event_contexts": event_contexts,
            "valid_event_ids": valid_event_ids,  # 유효한 event_id 전달
            "model": state.get("model"),
            "extractor_type": state.get("extractor_type"),
        }

        sends.append(Send("create_info_for_placeholder", send_state))

    return sends


# ============ 서브그래프 구현 ============
def build_placeholder_replace_subgraph():
    """PlaceHolder 처리 서브그래프"""
    subgraph = StateGraph(PlaceHolderReplaceState)

    # 노드 추가
    subgraph.add_node("initialize_accumulated_state", initialize_accumulated_state)
    subgraph.add_node("prepare_placeholders", prepare_placeholders_node)
    subgraph.add_node("create_info_for_placeholder", create_info_for_placeholder_node)
    subgraph.add_node("update_graph_with_infos", update_graph_with_infos)
    subgraph.add_node("save_graph_to_file", save_graph_to_file)

    # # 엣지 구성
    subgraph.add_edge(START, "initialize_accumulated_state")
    subgraph.add_edge("initialize_accumulated_state", "prepare_placeholders")

    # Consolidate된 PlaceHolder들 처리
    subgraph.add_conditional_edges(
        "prepare_placeholders",
        distribute_placeholder_info_creation,
        ["create_info_for_placeholder"],
    )
    subgraph.add_edge("create_info_for_placeholder", "update_graph_with_infos")
    subgraph.add_edge("update_graph_with_infos", "save_graph_to_file")
    subgraph.add_edge("save_graph_to_file", END)
    return subgraph.compile()
