"""
기폭사건 및 Macro Cliffhanger 생성 서브그래프
"""

from typing import Any, Dict
from langgraph.graph import END, START, StateGraph

from nodes.stage1_nodes import create_inciting_and_macro_node
from states.stage1_plot_states import IncitingMacroState


def build_inciting_macro_graph():
    """기폭사건과 Macro Cliffhanger를 생성하는 서브그래프 구성"""
    
    workflow = StateGraph(IncitingMacroState)
    
    # 노드 추가
    workflow.add_node("create_inciting_macro", create_inciting_and_macro_node)
    
    # 엣지 추가
    workflow.add_edge(START, "create_inciting_macro")
    workflow.add_edge("create_inciting_macro", END)
    
    return workflow.compile()


if __name__ == "__main__":
    # 테스트용 코드
    print("기폭사건 및 Macro Cliffhanger 생성 서브그래프 구성 완료")