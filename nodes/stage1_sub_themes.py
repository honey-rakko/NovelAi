"""
Sub-theme 선정 서브그래프
"""

from typing import Any, Dict
from langgraph.graph import END, START, StateGraph

from nodes.stage1_nodes import select_sub_themes_node
from states.stage1_plot_states import SubThemeState


def build_sub_theme_graph():
    """Act별 Sub-theme을 선정하는 서브그래프 구성"""
    
    workflow = StateGraph(SubThemeState)
    
    # 노드 추가
    workflow.add_node("select_themes", select_sub_themes_node)
    
    # 엣지 추가  
    workflow.add_edge(START, "select_themes")
    workflow.add_edge("select_themes", END)
    
    return workflow.compile()


if __name__ == "__main__":
    # 테스트용 코드
    print("Sub-theme 선정 서브그래프 구성 완료")