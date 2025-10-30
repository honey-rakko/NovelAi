"""
서사적 양극 분석 서브그래프
"""

from typing import Any, Dict
from langchain_core.messages import SystemMessage
from langgraph.graph import END, START, StateGraph

from character_network import CharacterNetwork
from nodes.stage1_nodes import analyze_narrative_poles_node
from states.stage1_plot_states import NarrativePolesState


def build_narrative_poles_graph():
    """서사적 양극을 분석하는 서브그래프 구성"""
    
    workflow = StateGraph(NarrativePolesState)
    
    # 노드 추가
    workflow.add_node("analyze_poles", analyze_narrative_poles_node)
    
    # 엣지 추가
    workflow.add_edge(START, "analyze_poles")
    workflow.add_edge("analyze_poles", END)
    
    return workflow.compile()


if __name__ == "__main__":
    # 테스트용 코드
    import json
    
    # 저장된 그래프 파일 로드 (테스트용)
    with open("saved_graphs/story_graph_example.json", "r", encoding="utf-8") as f:
        graph_data = json.load(f)
    
    # CharacterNetwork 재구성
    graph = CharacterNetwork(graph_data["topic"])
    # ... (그래프 재구성 로직)
    
    # 서브그래프 실행
    subgraph = build_narrative_poles_graph()
    
    test_state = {
        "graph": graph,
        "topic": "권력의 본질",
        "conflict": "개인과 집단",
        "vibe": "어둡고 냉소적",
        "model": "gpt-4o-mini",
        "extractor_type": "default"
    }
    
    result = subgraph.invoke(test_state)
    
    print("서사적 양극 분석 결과:")
    print(f"출발점: {result['narrative_poles'].starting_point.description}")
    print(f"종착점: {result['narrative_poles'].ending_point.description}")
    print(f"200화 지속 가능: {result['narrative_poles'].sustainability_200}")