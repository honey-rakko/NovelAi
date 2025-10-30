"""
메인 LangGraph 워크플로우 구현
"""

from typing import Any, Dict

from langgraph.graph import END, START, StateGraph

from character_network import CharacterNetwork
from nodes import (
    build_character_subgraph,
    build_consolidation_subgraph,
    build_event_subgraph,
    build_placeholder_replace_subgraph,
)
# from nodes.stage1_nodes import create_plot_candidates_node, define_main_character_roles
from nodes.stage1_nodes import define_main_character_roles
from states.stage1_states import (
    CharacterCreationState,
    ConsolidationState,
    EventCreationState,
    InputState,
    PlaceHolderReplaceState,
    WorkflowState,
)


# ============ 워크플로우 초기화 ============
def initialize_workflow(state: InputState) -> WorkflowState:
    """워크플로우 초기화"""

    return WorkflowState(
        topic=state.topic,
        max_iterations=state.max_iterations,
        model=state.model,
        extractor_type=state.extractor_type,
        graph=CharacterNetwork(state.topic),
        current_iteration=0,
        roles=[],
        plots=None,
    )


# ============ 조건부 엣지 함수들 ============
def should_continue(state: WorkflowState):
    """반복 계속 여부 결정"""
    current_iteration = state["current_iteration"]
    max_iterations = state["max_iterations"]
    if current_iteration >= max_iterations:
        return "end"
    return "continue"


# ============ 서브그래프 구현 ============
character_subgraph = build_character_subgraph()
event_subgraph = build_event_subgraph()
consolidation_subgraph = build_consolidation_subgraph()
placeholder_replace_subgraph = build_placeholder_replace_subgraph()


def run_character_subgraph(state: CharacterCreationState) -> Dict[str, Any]:
    """캐릭터 서브그래프 실행"""
    result = character_subgraph.invoke(state)
    return result


def run_event_subgraph(state: EventCreationState) -> Dict[str, Any]:
    """이벤트 서브그래프 실행"""
    result = event_subgraph.invoke(state)
    return result


def run_consolidation_subgraph(state: ConsolidationState) -> Dict[str, Any]:
    """Consolidation 서브그래프 실행"""
    result = consolidation_subgraph.invoke(state)
    return result


def run_placeholder_replace_subgraph(
    state: PlaceHolderReplaceState,
) -> Dict[str, Any]:
    """PlaceHolder 분석 및 처리 서브그래프 실행"""
    result = placeholder_replace_subgraph.invoke(state)
    return result


# ============ 워크플로우 노드 래퍼 함수들 ============
def increment_iteration(state: WorkflowState) -> WorkflowState:
    """반복 카운터 증가"""
    return {
        **state,
        "current_iteration": state["current_iteration"] + 1,
    }


def finalize_workflow(state: WorkflowState) -> WorkflowState:
    """워크플로우 종료 처리"""
    # 통계 출력
    stats = state["graph"].get_statistics()
    print("\n=== 워크플로우 완료 ===")
    print(f"주제: {state['topic']}")
    print(f"총 노드: {stats['total_nodes']}")
    print(f"- Characters: {stats['characters']}")
    print(f"- Events: {stats['events']}")
    print(f"- Infos: {stats['infos']}")
    print(f"- PlaceHolders: {stats['placeholders']}")
    print(f"총 연결: {stats['total_edges']}")

    if state.get("plots"):
        print(f"\n생성된 플롯 포인트: {len(state['plots'].plot_points)}개")

    return state


# ============ 메인 워크플로우 구성 ============
def build_workflow() -> StateGraph:
    """메인 워크플로우 구성"""
    configs = {"configurable": {"max_retries": 10}}
    workflow = StateGraph(WorkflowState, input_schema=InputState, config=configs)

    # 노드 추가
    workflow.add_node("initialize", initialize_workflow)
    workflow.add_node("define_roles", define_main_character_roles)
    workflow.add_node("run_character_subgraph", run_character_subgraph)
    workflow.add_node("run_event_subgraph", run_event_subgraph)
    workflow.add_node("run_consolidation_subgraph", run_consolidation_subgraph)
    workflow.add_node(
        "run_placeholder_replace_subgraph", run_placeholder_replace_subgraph
    )
    workflow.add_node("increment_iteration", increment_iteration)
    workflow.add_node("finalize", finalize_workflow)
    # workflow.add_node("create_plot_candidates", create_plot_candidates_node)
    # candidate 어차피 안씀

    # 엣지 구성
    workflow.add_edge(START, "initialize")
    workflow.add_edge("initialize", "define_roles")
    # workflow.add_edge("initialize", "create_plot_candidates")

    # 첫 번째 iteration: 캐릭터 생성
    workflow.add_edge("define_roles", "run_character_subgraph")
    workflow.add_edge("run_character_subgraph", "run_event_subgraph")
    workflow.add_edge("run_event_subgraph", "run_consolidation_subgraph")
    workflow.add_edge("run_consolidation_subgraph", "increment_iteration")

    # iteration 분기점
    workflow.add_conditional_edges(
        "increment_iteration",
        should_continue,
        {
            "continue": "run_placeholder_replace_subgraph",
            "end": "finalize",
        },
    )
    # PlaceHolder 처리 후 다시 Event 생성 사이클로
    workflow.add_edge("run_placeholder_replace_subgraph", "run_event_subgraph")
    # Event 생성 후 다시 consolidation으로 (순환 구조 완성)

    # # Consolidation 처리
    # workflow.add_edge("prepare_consolidation", "consolidate")

    # # Consolidation 후 새 역할이 있으면 반복, 없으면 Plot 생성
    # workflow.add_conditional_edges(
    #     "consolidate",
    #     lambda s: "increment_iteration"
    #     if s.get("roles") and s["current_iteration"] < s["max_iterations"]
    #     else "create_plot",
    #     ["increment_iteration", "create_plot"],
    # )

    # workflow.add_edge("create_plot", "finalize")
    workflow.add_edge("finalize", END)

    return workflow.compile()
