"""
통합 플롯 생성 서브그래프
"""

from typing import Any, Dict
from langgraph.graph import END, START, StateGraph

from nodes.stage1_nodes import generate_integrated_plot_node, save_plot_to_file
from states.stage1_plot_states import IntegratedPlotState


def build_integrated_plot_graph():
    """통합 플롯을 생성하는 서브그래프 구성"""
    
    workflow = StateGraph(IntegratedPlotState)
    
    # 노드 추가
    workflow.add_node("generate_plot", generate_integrated_plot_node)
    workflow.add_node("save_plot", save_plot_to_file)
    
    # 엣지 추가
    workflow.add_edge(START, "generate_plot")
    workflow.add_edge("generate_plot", "save_plot")
    workflow.add_edge("save_plot", END)
    
    return workflow.compile()


if __name__ == "__main__":
    # 테스트용 코드
    print("통합 플롯 생성 서브그래프 구성 완료")