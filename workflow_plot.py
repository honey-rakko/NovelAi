"""
저장된 그래프 파일을 불러와서 플롯 생성 부분만 실험하기 위한 워크플로우
"""

import json
from typing import Optional

from langgraph.graph import END, START, StateGraph
from pydantic import Field

from character_network import CharacterNetwork, Node, NodeType
# from nodes.stage1_nodes import create_plot_candidates_node
from states.stage1_states import InputState, WorkflowState


# ============ Input State ============
class PlotInputState(InputState):
    """플롯 워크플로우 입력 상태"""

    topic: Optional[str] = Field(description="스토리 주제", default="")
    conflict: Optional[str] = Field(description="장르 내재 갈등", default="")
    vibe: Optional[str] = Field(description="핵심 분위기", default="")
    graph_file: Optional[str] = Field(
        description="로드할 그래프 JSON 파일 경로",
    )


# ============ 워크플로우 초기화 ============
def initialize_from_file(state: PlotInputState) -> WorkflowState:
    """그래프 파일 로드 및 초기화"""
    graph_file = state.graph_file

    graph = load_graph_from_file(graph_file)

    return {
        **state.model_dump(),
        "graph": graph,
        "topic": graph.topic,
    }


# ============ 유틸리티 함수 ============
def load_graph_from_file(filename: str) -> CharacterNetwork:
    """저장된 JSON 파일에서 CharacterNetwork 로드"""
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    graph = CharacterNetwork(data["topic"])

    if "_node_id" in data:
        graph._node_id = data["_node_id"]

    for node_id, node_data in data["nodes"].items():
        node = Node(
            id=node_data["id"],
            type=NodeType(node_data["type"]),
            data=node_data["data"],
        )
        node.edges = set(node_data["edges"])
        graph.nodes[node_id] = node

    return graph


# ============ 워크플로우 노드 함수들 ============
def finalize_plot(state: WorkflowState) -> WorkflowState:
    """플롯 생성 결과 출력"""
    if not state.get("plots"):
        return state

    print("\n=== 플롯 생성 완료 ===")
    print(f"생성된 플롯 후보: {len(state['plots'].plot_candidates)}개")

    return state


# ============ 워크플로우 구성 ============
def build_plot_workflow() -> StateGraph:
    """플롯 실험용 워크플로우 구성"""
    workflow = StateGraph(WorkflowState, input_schema=PlotInputState)

    workflow.add_node("initialize", initialize_from_file)
    # workflow.add_node("create_plot", create_plot_candidates_node)
    workflow.add_node("finalize", finalize_plot)

    workflow.add_edge(START, "initialize")
    workflow.add_edge("initialize", "create_plot")
    workflow.add_edge("create_plot", "finalize")
    workflow.add_edge("finalize", END)

    return workflow.compile()
