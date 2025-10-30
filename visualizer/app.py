"""Flask application for CharacterNetwork visualization"""

import glob
import json
import os
from typing import Any, Dict, Optional

from flask import Flask, jsonify, render_template, request

from character_network import CharacterNetwork, Node, NodeType


class WebStoryGraphVisualizer:
    """CharacterNetwork를 위한 웹 기반 시각화 도구"""

    def __init__(
        self,
        story_graph: Optional[CharacterNetwork] = None,
        load_from_file: Optional[str] = None,
    ):
        if load_from_file:
            self.story_graph = self.load_graph_from_file(load_from_file)
            self.file_data = self.load_file_metadata(load_from_file)
        else:
            self.story_graph = story_graph
            self.file_data = None

        self.app = Flask(__name__, template_folder="templates", static_folder="static")
        self.setup_routes()

    def load_graph_from_file(self, filename: str) -> CharacterNetwork:
        """저장된 JSON 파일에서 CharacterNetwork 로드"""
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)

        # CharacterNetwork 인스턴스 생성
        graph = CharacterNetwork(data["topic"])

        # 노드 복원
        for node_id, node_data in data["nodes"].items():
            # Node 객체로 변환
            node = Node(
                id=node_data["id"],
                type=NodeType(node_data["type"]),  # str -> Enum
                data=node_data["data"],
            )
            # edges는 set으로 변환
            node.edges = set(node_data["edges"])
            graph.nodes[node_id] = node

        return graph

    def load_file_metadata(self, filename: str) -> Dict[str, Any]:
        """파일 메타데이터 로드"""
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            "topic": data.get("topic", "Unknown"),
            "filename": os.path.basename(filename),
            "node_count": len(data.get("nodes", {})),
        }

    def setup_routes(self):
        """Flask 라우트 설정"""

        @self.app.route("/")
        def index():
            return render_template("graph_viewer.html")

        @self.app.route("/api/saved-graphs")
        def get_saved_graphs():
            """저장된 그래프 파일 목록 반환"""
            saved_dir = "saved_graphs"
            if not os.path.exists(saved_dir):
                return jsonify([])

            files = []
            for filename in glob.glob(f"{saved_dir}/*.json"):
                try:
                    with open(filename, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        files.append(
                            {
                                "filename": os.path.basename(filename),
                                "path": filename,
                                "topic": data.get("topic", "Unknown"),
                                "node_count": len(data.get("nodes", {})),
                                "node_counter": data.get("_node_counter", {}),
                            }
                        )
                except Exception as e:
                    print(f"Error reading {filename}: {e}")

            # 파일명으로 정렬
            files.sort(key=lambda x: x["filename"], reverse=True)
            return jsonify(files)

        @self.app.route("/api/load-graph", methods=["POST"])
        def load_graph():
            """특정 그래프 파일 로드"""
            data = request.get_json()
            filename = data.get("filename")

            if not filename or not os.path.exists(filename):
                return jsonify({"error": "File not found"}), 404

            try:
                self.story_graph = self.load_graph_from_file(filename)
                self.file_data = self.load_file_metadata(filename)
                return jsonify({"success": True, "message": f"Loaded {filename}"})
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/graph-data")
        def get_graph_data():
            if not self.story_graph:
                return jsonify({"error": "No graph loaded"}), 404

            graph_data = self.prepare_graph_data()

            # 파일 메타데이터 추가
            if self.file_data:
                graph_data["metadata"] = self.file_data

            return jsonify(graph_data)

        @self.app.route("/api/node/<node_id>")
        def get_node_details(node_id):
            if not self.story_graph or node_id not in self.story_graph.nodes:
                return jsonify({"error": "Node not found"}), 404

            node = self.story_graph.nodes[node_id]

            # Node details
            node_details = {
                "id": node_id,
                "type": node.type.value,
                "data": node.data,
                "connections": len(node.edges),
                "connected_nodes": list(node.edges),
            }

            # 타입별 추가 정보
            if node.type == NodeType.CHARACTER:
                node_details["infos"] = self.story_graph.get_character_infos(node_id)
            elif node.type == NodeType.EVENT:
                node_details["participants"] = self.story_graph.get_event_participants(
                    node_id
                )

            return jsonify(node_details)

        @self.app.route("/api/statistics")
        def get_statistics():
            if not self.story_graph:
                return jsonify({"error": "No graph loaded"}), 404
            return jsonify(self.story_graph.get_statistics())

    def prepare_graph_data(self) -> Dict[str, Any]:
        """D3.js에서 사용할 수 있는 형태로 그래프 데이터 변환"""
        nodes = []
        links = []

        # 노드 타입별 색상 정의
        color_map = {
            "character": "#FF6B6B",
            "event": "#4ECDC4",
            "info": "#FFD93D",
            "placeholder": "#95E1D3",
        }

        # 노드 데이터 준비
        for node_id, node in self.story_graph.nodes.items():
            # 노드 이름 결정
            if node.type == NodeType.CHARACTER:
                name = node.data.get("name") or node.data.get("role", node_id)
            elif node.type == NodeType.EVENT:
                name = node.data.get("summary", node_id)[:50]
            elif node.type == NodeType.INFO:
                name = f"{node.data.get('type', 'Info')}: {node.data.get('content', '')[:30]}"
            elif node.type == NodeType.PLACEHOLDER:
                name = f"[{node.data.get('role', 'Unknown')}]"
            else:
                name = node_id

            nodes.append(
                {
                    "id": node_id,
                    "name": name,
                    "type": node.type.value,
                    "color": color_map.get(node.type.value, "#999999"),
                    "size": len(node.edges) * 3 + 10,
                    "data": node.data,
                }
            )

        # 링크 데이터 준비 (중복 제거)
        processed_edges = set()
        for node_id, node in self.story_graph.nodes.items():
            for connected_id in node.edges:
                edge = tuple(sorted([node_id, connected_id]))
                if (
                    edge not in processed_edges
                    and connected_id in self.story_graph.nodes
                ):
                    links.append({"source": node_id, "target": connected_id})
                    processed_edges.add(edge)

        return {
            "nodes": nodes,
            "links": links,
            "topic": self.story_graph.topic,
            "statistics": self.story_graph.get_statistics(),
        }

    def run(self, host="127.0.0.1", port=5000, debug=True):
        """웹 서버 실행"""
        print(f"CharacterNetwork Visualizer running at http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug)


def run_visualizer(json_file_path=None):
    """시각화 도구 실행 함수"""
    if json_file_path:
        visualizer = WebStoryGraphVisualizer(load_from_file=json_file_path)
    else:
        visualizer = WebStoryGraphVisualizer()

    visualizer.run()
