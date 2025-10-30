from typing import Any, Dict, List

from langchain_core.messages import SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from character_network import CharacterNetwork
from nodes.stage1_nodes import initialize_accumulated_state, save_graph_to_file
from prompts.stage1_prompts import EVENT_PROMPT
from pydantics.stage1_pydantics import Event
from states.stage1_states import EventCreationState
from utils import create_unified_extractor


# ============ 노드 함수들 ============
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
        conflict=conflict,
        vibe=vibe,
        info_type=current_info_type,
        info_content=current_info_content,
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


# ============ 조건부 엣지 함수들 ============
def distribute_event_creation(state: EventCreationState) -> List[Send]:
    """그래프의 모든 캐릭터-Info 쌍에 대해 이벤트 생성을 위한 Send 분배"""
    graph: CharacterNetwork = state["graph"]

    sends = []
    # 모든 캐릭터 노드에 대해
    for char_id, char_node in graph.nodes.items():
        if char_node.type.value == "character":
            # 해당 캐릭터의 Info들 찾기
            infos = graph.get_character_infos(char_id)
            character_role = char_node.data.get("role", "")

            for info in infos:
                edges = graph.nodes[info["id"]].edges
                # info와 연결된 노드중에 event가 없는 경우 이벤트 생성
                # info와 연결된 노드들 중에서 event 타입이 하나도 없으면 True
                event_connected = False
                for edge_id in edges:
                    if (
                        edge_id in graph.nodes
                        and graph.nodes[edge_id].type.value == "event"
                    ):
                        event_connected = True
                        break
                if not event_connected:
                    event_state = {
                        "char_id": char_id,
                        "info_id": info["id"],
                        "role": character_role,
                        "conflict": state["conflict"],
                        "vibe": state["vibe"],
                        "current_info_type": info["type"],
                        "current_info_content": info["content"],
                        "model": state.get("model"),
                        "extractor_type": state.get("extractor_type"),
                    }
                    sends.append(Send("create_event", event_state))
    return sends


# ============ 서브그래프 구현 ============
def build_event_subgraph():
    """이벤트 생성 서브그래프"""
    subgraph = StateGraph(EventCreationState)

    subgraph.add_node("initialize_accumulated_state", initialize_accumulated_state)
    subgraph.add_node("create_event", create_event_node)
    subgraph.add_node("update_event_graph", update_graph_with_event)
    subgraph.add_node("save_graph_to_file", save_graph_to_file)

    subgraph.add_edge(START, "initialize_accumulated_state")
    subgraph.add_conditional_edges(
        "initialize_accumulated_state",
        distribute_event_creation,
        ["create_event"],
    )
    subgraph.add_edge("create_event", "update_event_graph")
    subgraph.add_edge("update_event_graph", "save_graph_to_file")
    subgraph.add_edge("save_graph_to_file", END)
    return subgraph.compile()
