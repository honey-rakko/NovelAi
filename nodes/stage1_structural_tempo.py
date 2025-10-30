"""
구조적 템포 설계 서브그래프
"""

from typing import Any, Dict
from langgraph.graph import END, START, StateGraph

from nodes.stage1_nodes import design_structural_tempo_node
from states.stage1_plot_states import StructuralTempoState


def build_structural_tempo_graph():
    """구조적 템포를 설계하는 서브그래프 구성"""
    
    workflow = StateGraph(StructuralTempoState)
    
    # 노드 추가
    workflow.add_node("design_tempo", design_structural_tempo_node)
    
    # 엣지 추가
    workflow.add_edge(START, "design_tempo")
    workflow.add_edge("design_tempo", END)
    
    return workflow.compile()


if __name__ == "__main__":
    # 테스트용 코드
    print("구조적 템포 설계 서브그래프 구성 완료")