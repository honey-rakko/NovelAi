"""
CharacterNetwork - 캐릭터 네트워크 구조
Info와 PlaceHolder 노드 타입을 포함한 캐릭터 관계망

연결 규칙:
- Character ↔ Info
- Info ↔ Character or Event
- Event ↔ Info or PlaceHolder
- PlaceHolder ↔ Event
"""
import os
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union


class NodeType(Enum):
    CHARACTER = "character"
    EVENT = "event"
    INFO = "info"
    PLACEHOLDER = "placeholder"


@dataclass
class Node:
    """모든 노드의 기본 클래스"""

    id: str
    type: NodeType
    data: Dict[str, Any] = field(default_factory=dict)
    edges: Set[str] = field(default_factory=set)


class CharacterNetwork:
    """Info와 PlaceHolder를 지원하는 캐릭터 네트워크"""

    def __init__(self, topic: str):
        self.topic = topic
        self.nodes: Dict[str, Node] = {}
        self._node_id = {"character": 0, "event": 0, "info": 0, "placeholder": 0}

    @property
    def _node_counter(self) -> Dict[str, int]:
        node_counter = {"character": 0, "event": 0, "info": 0, "placeholder": 0}
        for node in self.nodes.values():
            node_counter[node.type.value] += 1
        return node_counter

    def _generate_node_id(self, node_type: NodeType) -> str:
        """노드 타입별로 고유 ID 생성"""
        type_key = node_type.value
        self._node_id[type_key] += 1
        return f"{type_key}_{self._node_id[type_key]}"

    def _validate_connection(self, node1: Node, node2: Node) -> bool:
        """연결 규칙 검증"""
        type1, type2 = node1.type, node2.type

        # Character ↔ Info
        if type1 == NodeType.CHARACTER and type2 == NodeType.INFO:
            return True
        if type1 == NodeType.INFO and type2 == NodeType.CHARACTER:
            return True

        # Info ↔ Event
        if type1 == NodeType.INFO and type2 == NodeType.EVENT:
            return True
        if type1 == NodeType.EVENT and type2 == NodeType.INFO:
            return True

        # Event ↔ PlaceHolder
        if type1 == NodeType.EVENT and type2 == NodeType.PLACEHOLDER:
            return True
        if type1 == NodeType.PLACEHOLDER and type2 == NodeType.EVENT:
            return True

        return False

    def add_node(self, node_type: NodeType, data: Dict[str, Any]) -> str:
        """노드 추가"""
        node_id = self._generate_node_id(node_type)
        node = Node(id=node_id, type=node_type, data=data)
        self.nodes[node_id] = node
        return node_id

    def connect_nodes(self, node1_id: str, node2_id: str) -> bool:
        """두 노드 연결 (규칙 검증 포함)"""
        if node1_id not in self.nodes or node2_id not in self.nodes:
            return False

        node1 = self.nodes[node1_id]
        node2 = self.nodes[node2_id]

        if not self._validate_connection(node1, node2):
            raise ValueError(
                f"Invalid connection: {node1.type.value} cannot connect to {node2.type.value}"
            )

        node1.edges.add(node2_id)
        node2.edges.add(node1_id)
        return True

    def add_character(self, role: str, name: Optional[str] = None, **kwargs) -> str:
        """캐릭터 노드 추가 (이름은 선택)"""
        data = {"role": role, "name": name, **kwargs}
        return self.add_node(NodeType.CHARACTER, data)

    def add_info(self, info_type: str, content: str, owner_id: str, **kwargs) -> str:
        """Info 노드 추가"""
        data = {"type": info_type, "content": content, "owner_id": owner_id, **kwargs}
        info_id = self.add_node(NodeType.INFO, data)
        return info_id

    def add_event(self, summary: str, owner_id: str, **kwargs) -> str:
        """이벤트 노드 추가"""
        data = {"summary": summary, "owner_id": owner_id, **kwargs}
        return self.add_node(NodeType.EVENT, data)

    def add_placeholder(
        self, role: str, owner_id: Union[str, List[str]], **kwargs
    ) -> str:
        """PlaceHolder 노드 추가"""
        data = {"role": role, "owner_id": owner_id, **kwargs}
        return self.add_node(NodeType.PLACEHOLDER, data)

    def get_placeholders_with_event(self) -> List:
        """PlaceHolder와 연결된 Event들 반환 (Consolidation 입력용)"""
        result = []

        for node_id, node in self.nodes.items():
            if node.type == NodeType.PLACEHOLDER:
                event = self.nodes[node.data.get("owner_id", "Unknown")]
                result.append((node_id, event))
        return result

    def merge_nodes(self, node_ids: List[str], target_id: str) -> bool:
        """여러 노드를 하나로 통합 (Consolidation용)

        Args:
            node_ids: 통합할 노드 ID 리스트
            target_id: 통합 대상 노드 ID (이미 존재하거나 새로 생성)
        """
        if not node_ids:
            return False

        # target_id가 node_ids에 포함된 경우 제외
        source_ids = [nid for nid in node_ids if nid != target_id]

        if target_id not in self.nodes:
            return False

        target_node = self.nodes[target_id]

        # 모든 source 노드들의 연결을 target으로 이동
        for source_id in source_ids:
            if source_id not in self.nodes:
                continue

            source_node = self.nodes[source_id]

            # 순회 중 변경 안전성을 위해 snapshot 사용
            for edge_id in list(source_node.edges):
                if edge_id not in self.nodes:
                    continue
                if edge_id == target_id:
                    # self-loop 방지: source -> target 기존 연결은 source 삭제 시 자연 제거됨
                    continue

                edge_node = self.nodes[edge_id]

                # 먼저 기존 연결(source) 제거하여 고아 참조 방지
                edge_node.edges.discard(source_id)

                # 연결 규칙 검증 후 재배선
                if self._validate_connection(target_node, edge_node):
                    edge_node.edges.add(target_id)
                    target_node.edges.add(edge_id)

            # source 노드 제거 (양방향 참조 정리 포함)
            self.remove_node(source_id)
        self.clean_redundant_nodes()

        return True

    def get_character_infos(self, character_id: str) -> List[Dict[str, Any]]:
        """캐릭터에 연결된 모든 Info 노드 정보 반환"""
        if character_id not in self.nodes:
            return []

        char_node = self.nodes[character_id]
        if char_node.type != NodeType.CHARACTER:
            return []

        infos = []
        for edge_id in char_node.edges:
            if edge_id in self.nodes and self.nodes[edge_id].type == NodeType.INFO:
                info_node = self.nodes[edge_id]
                infos.append(
                    {
                        "id": edge_id,
                        "type": info_node.data.get("type"),
                        "content": info_node.data.get("content"),
                    }
                )

        return infos

    def get_event_participants(self, event_id: str) -> Dict[str, List[str]]:
        """이벤트에 연결된 참여자들 반환 (Info와 PlaceHolder 구분)"""
        if event_id not in self.nodes:
            return {"infos": [], "placeholders": []}

        event_node = self.nodes[event_id]
        if event_node.type != NodeType.EVENT:
            return {"infos": [], "placeholders": []}

        result = {"infos": [], "placeholders": []}

        for edge_id in event_node.edges:
            if edge_id in self.nodes:
                edge_node = self.nodes[edge_id]
                if edge_node.type == NodeType.INFO:
                    result["infos"].append(edge_id)
                elif edge_node.type == NodeType.PLACEHOLDER:
                    result["placeholders"].append(edge_id)

        return result

    def remove_node(self, node_id: str):
        """노드와 관련 연결 제거"""
        if node_id not in self.nodes:
            return

        # 연결된 노드들의 edges에서 이 노드 제거
        for other_node in self.nodes.values():
            if node_id in other_node.edges:
                other_node.edges.remove(node_id)

        # 노드 자체 제거
        del self.nodes[node_id]

    def get_statistics(self) -> Dict[str, Any]:
        """그래프 통계 정보"""
        total_edges = sum(len(node.edges) for node in self.nodes.values()) // 2

        placeholder_count = len(
            [n for n in self.nodes.values() if n.type == NodeType.PLACEHOLDER]
        )

        return {
            "total_nodes": len(self.nodes),
            "node_counts": self._node_counter,
            "total_edges": total_edges,
            "placeholder_count": placeholder_count,
            "characters": self._node_counter.get("character", 0),
            "events": self._node_counter.get("event", 0),
            "infos": self._node_counter.get("info", 0),
            "placeholders": self._node_counter.get("placeholder", 0),
        }

    def save_to_file(self, filename: str):
        """그래프를 JSON 파일에 저장 (직렬화 가능하도록 수정)"""
        serializable_nodes = {}
        for node_id, node in self.nodes.items():
            serializable_nodes[node_id] = {
                "id": node.id,
                "type": node.type.value,  # Enum -> str
                "data": node.data,
                "edges": list(node.edges),  # set -> list
            }

        graph_data = {
            "topic": self.topic,
            "_node_counter": self._node_counter,
            "_node_id": self._node_id,
            "nodes": serializable_nodes,
        }

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(graph_data, f, indent=4, ensure_ascii=False)

    @classmethod
    def load_from_file(cls, filepath: str) -> "CharacterNetwork":
        """JSON 파일에서 CharacterNetwork 객체를 로드합니다."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        topic = data.get("topic", "Unknown Topic")
        graph_instance = cls(topic)
        graph_instance._node_id = data.get("_node_id", {"character": 0, "event": 0, "info": 0, "placeholder": 0})
        
        loaded_nodes = {}
        for node_id, node_data in data.get("nodes", {}).items():
            loaded_nodes[node_id] = Node(
                id=node_data["id"],
                type=NodeType(node_data["type"]),
                data=node_data["data"],
                edges=set(node_data["edges"])
            )
        graph_instance.nodes = loaded_nodes
        
        return graph_instance

    def get_placeholders(self) -> List[str]:
        """PlaceHolder 노드들 반환"""
        return [
            (node_id, node)
            for node_id, node in self.nodes.items()
            if node.type == NodeType.PLACEHOLDER
        ]

    def get_characters(self) -> List:
        """캐릭터 노드들 반환"""
        return [
            (node_id, node)
            for node_id, node in self.nodes.items()
            if node.type == NodeType.CHARACTER
        ]

    def get_events(self) -> List:
        """이벤트 노드들 반환"""
        return [
            (node_id, node)
            for node_id, node in self.nodes.items()
            if node.type == NodeType.EVENT
        ]

    def clean_redundant_nodes(self):
        """엣지가 없는 노드들 제거"""
        for node_id, node in list(self.nodes.items()):
            if not node.edges:
                del self.nodes[node_id]
