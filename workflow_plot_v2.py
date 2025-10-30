"""
플롯 생성 v2 워크플로우
새로운 플롯 생성 프롬프트를 사용하여 단계별로 플롯을 구성
TypedDict 기반으로 workflow_stage1.py와 일관성 유지
"""
import os
from typing import Any, Dict

from langgraph.graph import END, START, StateGraph

from nodes.stage1_narrative_poles import build_narrative_poles_graph
from nodes.stage1_sub_themes import build_sub_theme_graph  
from nodes.stage1_inciting_macro import build_inciting_macro_graph
from nodes.stage1_structural_tempo import build_structural_tempo_graph
from nodes.stage1_integrated_plot import build_integrated_plot_graph
from states.stage1_plot_states import PlotInputState, PlotWorkflowState
from nodes.stage1_nodes import save_plot_to_file
from character_network import CharacterNetwork

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

narrative_poles_subgraph = build_narrative_poles_graph()
sub_themes_subgraph = build_sub_theme_graph()
inciting_macro_subgraph = build_inciting_macro_graph()
structural_tempo_subgraph = build_structural_tempo_graph()
integrated_plot_subgraph = build_integrated_plot_graph()

def initialize_and_load_graph(state: PlotInputState) -> Dict[str, Any]:
    """파일 경로에서 그래프를 로드하고, 전체 워크플로우 State를 초기화합니다."""
    # Pydantic 입력이므로 속성 접근
    filepath = state.graph_filepath
    if not filepath:
        raise ValueError("그래프 파일 경로(graph_filepath)가 입력되지 않았습니다.")
    
    # 1. 파일 경로 정규화
    if not os.path.dirname(filepath):
        filepath = os.path.join(BASE_DIR, "saved_graphs", filepath)
    elif not os.path.isabs(filepath):
        filepath = os.path.join(BASE_DIR, filepath)
    
    # 2. 파일 존재 확인
    if not os.path.exists(filepath):
        saved_graphs_path = os.path.join(BASE_DIR, "saved_graphs", os.path.basename(filepath))
        if os.path.exists(saved_graphs_path):
            filepath = saved_graphs_path
        else:
            saved_graphs_dir = os.path.join(BASE_DIR, "saved_graphs")
            if os.path.exists(saved_graphs_dir):
                available_files = [f for f in os.listdir(saved_graphs_dir) if f.endswith('.json')]
                error_msg = f"그래프 파일을 찾을 수 없습니다: {filepath}\n\n사용 가능한 파일 목록:\n"
                error_msg += "\n".join(f"  - {f}" for f in available_files[:10])
                if len(available_files) > 10:
                    error_msg += f"\n  ... 외 {len(available_files) - 10}개"
            else:
                error_msg = f"그래프 파일을 찾을 수 없습니다: {filepath}\nsaved_graphs 디렉토리도 존재하지 않습니다."
            raise FileNotFoundError(error_msg)
    
    print(f"\n{'='*60}")
    print(f"그래프 로딩 중...")
    print(f"파일 경로: {filepath}")
    print(f"{'='*60}\n")
    
    # 3. 파일 경로로 객체를 로드합니다.
    try:
        graph_object = CharacterNetwork.load_from_file(filepath)
        print(f"✓ 그래프 로드 성공!")
        print(f"  - Topic: {graph_object.topic}")
        stats = graph_object.get_statistics()
        print(f"  - 총 노드: {stats['total_nodes']}개")
        print(f"  - Characters: {stats['characters']}개")
        print(f"  - Events: {stats['events']}개")
        print(f"  - Infos: {stats['infos']}개")
        print(f"  - PlaceHolders: {stats['placeholders']}개\n")
    except Exception as e:
        raise ValueError(f"그래프 파일 로드 중 오류 발생: {filepath}\n오류 내용: {str(e)}")

    # TypedDict로 반환
    return {
        "graph": graph_object,
        "topic": state.topic,
        "conflict": state.conflict,
        "vibe": state.vibe,
        "model": state.model,
        "extractor_type": state.extractor_type,
    }

# ============ 워크플로우 노드 함수들 ============
def run_narrative_poles(state: PlotWorkflowState) -> Dict[str, Any]:
    """서사적 양극 분석 서브그래프 실행"""
    subgraph_input = {
        "graph": state["graph"],
        "topic": state["topic"],
        "conflict": state["conflict"],
        "vibe": state["vibe"],
        "model": state["model"],
        "extractor_type": state["extractor_type"]
    }
    return narrative_poles_subgraph.invoke(subgraph_input)


def run_sub_themes(state: PlotWorkflowState) -> Dict[str, Any]:
    """Sub-theme 선정 서브그래프 실행"""
    subgraph_input = {
        "topic": state["topic"],
        "conflict": state["conflict"],
        "vibe": state["vibe"],
        "narrative_poles": state["narrative_poles"],
        "graph": state["graph"],
        "model": state["model"],
        "extractor_type": state["extractor_type"]
    }
    return sub_themes_subgraph.invoke(subgraph_input)


def run_inciting_macro(state: PlotWorkflowState) -> Dict[str, Any]:
    """기폭사건 및 Macro Cliffhanger 서브그래프 실행"""
    subgraph_input = {
        "topic": state["topic"],
        "conflict": state["conflict"],
        "vibe": state["vibe"],
        "narrative_poles": state["narrative_poles"],
        "graph": state["graph"],
        "model": state["model"],
        "extractor_type": state["extractor_type"]
    }
    return inciting_macro_subgraph.invoke(subgraph_input)


def run_structural_tempo(state: PlotWorkflowState) -> Dict[str, Any]:
    """구조적 템포 서브그래프 실행"""
    subgraph_input = {
        "topic": state["topic"],
        "conflict": state["conflict"],
        "vibe": state["vibe"],
        "narrative_poles": state["narrative_poles"],
        "graph": state["graph"],
        "model": state["model"],
        "extractor_type": state["extractor_type"]
    }
    return structural_tempo_subgraph.invoke(subgraph_input)


def run_integrated_plot(state: PlotWorkflowState) -> Dict[str, Any]:
    """통합 플롯 서브그래프 실행"""
    subgraph_input = {
        "topic": state["topic"],
        "conflict": state["conflict"],
        "vibe": state["vibe"],
        "narrative_poles": state["narrative_poles"],
        "graph": state["graph"],
        "model": state["model"],
        "extractor_type": state["extractor_type"]
    }
    return integrated_plot_subgraph.invoke(subgraph_input)


def print_progress(stage: str):
    """진행 상황 출력 함수"""
    def progress_node(state: PlotWorkflowState) -> Dict[str, Any]:
        print(f"\n{'='*50}")
        print(f">>> {stage} 완료")
        print(f"{'='*50}")
        
        # 중간 결과 출력
        if "양극 분석" in stage and state.get("narrative_poles"):
            poles = state["narrative_poles"]
            print(f"출발점: {poles.starting_point.description[:100]}...")
            print(f"종착점: {poles.ending_point.description[:100]}...")
            print(f"200화 지속 가능: {poles.sustainability_200}")
        elif "Sub-theme" in stage and state.get("sub_themes"):
            themes = state["sub_themes"]
            print(f"Act 1: {themes.act1_theme.theme}")
            print(f"Act 2: {themes.act2_theme.theme}")
            print(f"Act 3: {themes.act3_theme.theme}")
        elif "기폭사건" in stage and state.get("inciting_and_macro"):
            im = state["inciting_and_macro"]
            print(f"기폭사건: {im.inciting_incident.event_description[:100]}...")
            print(f"Macro Cliffhanger 수: {len(im.macro_cliffhangers)}개")
        elif "템포" in stage and state.get("structural_tempo"):
            tempo = state["structural_tempo"]
            print(f"총 화수: {tempo.total_episodes}화")
            print(f"구간 수: {len(tempo.segments)}개")
        elif "통합" in stage and state.get("integrated_plot"):
            plot = state["integrated_plot"]
            print(f"한 줄 요약: {plot.plot_summary}")
            print(f"핵심 질문: {plot.core_question}")
            
        return {}
    return progress_node


# ============ 메인 워크플로우 구성 ============
def build_plot_workflow() -> StateGraph:
    """플롯 v2 워크플로우 구성"""
    workflow = StateGraph(PlotWorkflowState, input_schema=PlotInputState)

    # 노드 추가
    workflow.add_node("initialize_and_load", initialize_and_load_graph)
    workflow.add_node("analyze_poles", run_narrative_poles)
    workflow.add_node("select_themes", run_sub_themes)
    workflow.add_node("create_inciting", run_inciting_macro)
    workflow.add_node("design_tempo", run_structural_tempo)
    workflow.add_node("generate_plot", run_integrated_plot)
    workflow.add_node("save_plot", save_plot_to_file)

    # 엣지 추가 (순차 실행)
    workflow.add_edge(START, "initialize_and_load")
    workflow.add_edge("initialize_and_load", "analyze_poles")
    workflow.add_edge("analyze_poles", "select_themes")
    workflow.add_edge("select_themes", "create_inciting")
    workflow.add_edge("create_inciting", "design_tempo")
    workflow.add_edge("design_tempo", "generate_plot")
    workflow.add_edge("generate_plot", "save_plot")
    workflow.add_edge("save_plot", END)

    return workflow.compile()

# ============ langgraph dev용 export ============
plot = build_plot_workflow()
