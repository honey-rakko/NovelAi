"""
Plot v2 테스트 스크립트
Stage1 결과를 사용하여 플롯을 생성하는 테스트
"""

import json
import os
from character_network import CharacterNetwork, Node, NodeType


def load_latest_graph():
    """가장 최근의 그래프 파일 로드"""
    graph_dir = "saved_graphs"
    if not os.path.exists(graph_dir):
        print(f"디렉토리 {graph_dir}가 없습니다.")
        return None
    
    graph_files = [f for f in os.listdir(graph_dir) if f.endswith(".json")]
    if not graph_files:
        print("저장된 그래프 파일이 없습니다.")
        return None
    
    # 최신 파일 선택
    latest_file = sorted(graph_files)[-1]
    filepath = os.path.join(graph_dir, latest_file)
    
    print(f"로드할 파일: {filepath}")
    
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # CharacterNetwork 재구성
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
    
    return graph, data.get("topic", "")


def test_plot_generation():
    """플롯 생성 테스트 (로컬)"""
    from workflow_plot_v2 import plot
    
    # 그래프 로드
    graph, topic = load_latest_graph()
    if not graph:
        print("테스트를 위한 그래프를 먼저 생성하세요.")
        print("python workflow_stage1.py 실행 후 다시 시도하세요.")
        return
    
    # 테스트 입력
    test_input = {
        "topic": topic or "권력의 본질",
        "conflict": "개인과 집단",
        "vibe": "어둡고 냉소적",
        "graph": graph,
        "model": "gpt-4o-mini",
        "extractor_type": "default"
    }
    
    print("\n" + "="*60)
    print("플롯 생성 테스트 시작")
    print("="*60)
    print(f"주제: {test_input['topic']}")
    print(f"갈등: {test_input['conflict']}")
    print(f"분위기: {test_input['vibe']}")
    print(f"캐릭터 수: {len(graph.get_characters())}")
    print(f"이벤트 수: {len(graph.get_events())}")
    
    # 워크플로우 실행
    try:
        result = plot.invoke(test_input)
        
        if result.get("integrated_plot"):
            integrated = result["integrated_plot"]
            
            print("\n" + "="*60)
            print("플롯 생성 완료!")
            print("="*60)
            print(f"\n📖 한 줄 요약: {integrated.plot_summary}")
            print(f"❓ 핵심 질문: {integrated.core_question}")
            print(f"💭 주제 진술: {integrated.thematic_statement}")
            
            print("\n📊 3막 구조:")
            for act in integrated.act_structures:
                print(f"\nAct {act.act_number}: {act.subtitle}")
                print(f"  화수: {act.episode_range}")
                print(f"  Sub-theme: {act.sub_theme}")
                print(f"  Macro Cliffhangers: {', '.join(act.macro_cliffhangers)}")
            
            print("\n✅ 결과가 saved_plots 디렉토리에 저장되었습니다.")
        else:
            print("\n❌ 플롯 생성 실패")
            print("결과:", result)
            
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_plot_generation()