from typing import Any, Dict, List

from langchain_core.messages import SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from nodes.stage1_nodes import create_character_node, update_graph_with_character

from character_network import CharacterNetwork
from prompts.stage1_prompts import CHARACTER_PROMPT
from pydantics.stage1_pydantics import Character
from states.stage1_states import CharacterCreationState
from utils import create_unified_extractor


# ============ 노드 함수들 ============
def initialize_accumulated_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """누적 State 초기화 - model, extractor_type도 유지"""
    new_state = {}
    for key, value in state.items():
        if key in [
            "graph",
            "current_iteration",
            "topic",
            "roles",
            "conflict",
            "model",
            "extractor_type",
        ]:
            new_state[key] = value
        else:
            new_state[key] = None
    return new_state


#삭제하고 ipmort로 대체

# def create_character_node(state: Dict[str, Any]) -> Dict[str, Any]:
#     """CharacterCreationState를 받아서 Character와 Info를 생성하는 LLM 노드"""
#     role = state["role"]
#     topic = state["topic"]
#     conflict = state["conflict"]
#     role_info = state["role_info"]
#     # Pydantic 모델을 dict로 받았으므로, 보기 좋게 포매팅합니다.
#     role_info_str = "\n".join([f"- {key}: {value}" for key, value in role_info.items()])
#     # 초기 캐릭터 생성
#     prompt = CHARACTER_PROMPT.format(topic=topic, role=role, conflict=conflict, role_info=role_info_str)

#     extractor = create_unified_extractor(
#         model_name=state.get("model"),
#         extractor_type=state.get("extractor_type", "default"),
#         tools=[Character],
#         tool_choice="Character",
#     )
#     response = extractor.invoke([SystemMessage(content=prompt)])
#     if hasattr(response, "responses") and response["responses"][0]:
#         parsed = response["responses"][0]
#     else:  # trustcall의 emtpy response 문제 때문에 임시 처리
#         args = response["messages"][0].tool_calls[0]["args"]
#         parsed = Character(**args)
#     character = parsed

#     return {"generated_character": [character]}


# def update_graph_with_character(state: Dict[str, Any]) -> Dict[str, Any]:
#     """CharacterCreationState에서 생성된 Character와 Info를 Graph에 추가"""
#     graph: CharacterNetwork = state["graph"]
#     characters = state["generated_character"]
#     current_iteration = state["current_iteration"]

#     for character in characters:
#         char_id = graph.add_character(role=character.role, created_at=current_iteration)

#         # Info 노드들 추가 및 연결
#         info_ids = []
#         for info in character.infos:
#             info_id = graph.add_info(
#                 info_type=info.type,
#                 content=info.content,
#                 owner_id=char_id,
#                 created_at=current_iteration,
#             )
#             graph.connect_nodes(info_id, char_id)
#             info_ids.append(info_id)
#     return {
#         "graph": graph,
#     }


# ============ 조건부 엣지 함수들 ============
def distribute_character_creation(state: CharacterCreationState) -> List[Send]:
    """캐릭터 생성을 위한 Send 분배"""
    # roles = state.get("roles", [])
    # roles는 이제 단순 문자열 리스트가 아닌 RoleInfo 객체의 리스트입니다.
    roles_info = state.get("roles", []) # 타입 힌트를 RoleInfo로 명확히 합니다.

    sends = []
    # for role in roles:
    for role_info in roles_info:
        # 각 역할별로 독립적인 서브그래프 실행
        send_state = {
            "topic": state["topic"],
            "conflict": state["conflict"],
            # "role": role,
            # 'role'뿐만 아니라 'role_info' 객체 전체를 전달합니다.
            "role": role_info.role_name, # 기존 'role' 키는 role_name으로 유지합니다.
            "role_info": role_info.model_dump(), # Pydantic 모델을 dict로 변환하여 전달합니다.
            "model": state.get("model"),
            "extractor_type": state.get("extractor_type"),
        }
        sends.append(Send("create_character", send_state))

    return sends


# ============ 서브그래프 구현 ============
def build_character_subgraph():
    """캐릭터 생성 서브그래프 (이벤트는 메인에서 처리)"""
    subgraph = StateGraph(CharacterCreationState)

    subgraph.add_node("initialize_accumulated_state", initialize_accumulated_state)
    subgraph.add_node("create_character", create_character_node)
    subgraph.add_node("update_character_graph", update_graph_with_character)

    subgraph.add_edge(START, "initialize_accumulated_state")
    subgraph.add_conditional_edges(
        "initialize_accumulated_state",
        distribute_character_creation,
        ["create_character"],
    )
    subgraph.add_edge("create_character", "update_character_graph")
    subgraph.add_edge("update_character_graph", END)
    return subgraph.compile()
