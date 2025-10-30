# CharacterNetwork 노드 명세

이 문서는 CharacterNetwork의 4가지 노드 타입(Character, Info, Event, PlaceHolder)에 저장되는 데이터 구조를 명세합니다.

## 노드 공통 구조

모든 노드는 다음 기본 구조를 가집니다:

```python
@dataclass
class Node:
    id: str                     # 노드 고유 ID (예: "character_1", "info_5")
    type: NodeType              # 노드 타입 (CHARACTER, INFO, EVENT, PLACEHOLDER)
    data: Dict[str, Any]        # 노드별 실제 데이터 (아래에서 상세 설명)
    edges: Set[str]             # 연결된 노드 ID 집합
```

## 1. Character 노드

### data 필드 구조

```python
{
    "role": str,              # 필수: 캐릭터의 역할 (예: "절대적 지배자")
    "name": Optional[str],    # 선택: Stage 2+에서 추가되는 실제 이름
    "created_at": int,        # 필수: 생성된 iteration 번호
    # 추가 메타데이터는 **kwargs로 확장 가능
}
```

### 생성 코드 예시

**Stage 1에서의 생성** (이름 없음):
```python
# nodes/stage1_nodes.py:276
char_id = graph.add_character(
    role=character.role,
    created_at=current_iteration
)
```

**Stage 2+에서의 생성** (이름 추가 예정):
```python
char_id = graph.add_character(
    role="절대적 지배자",
    name="카이엔",  # Stage 2에서 구체화
    created_at=current_iteration
)
```

### 연결 규칙

- **Character ↔ Info**: Character는 자신의 속성을 나타내는 여러 Info 노드와 연결됩니다.

```python
# Info 연결 예시 (nodes/stage1_nodes.py:287)
graph.connect_nodes(info_id, char_id)
```

## 2. Info 노드

### data 필드 구조

```python
{
    "type": str,              # 필수: InfoType Enum 값 (personality, desire, fear 등)
    "content": str,           # 필수: 속성의 구체적 내용
    "owner_id": str,          # 필수: 소유 Character 노드 ID
    "created_at": int,        # 필수: 생성된 iteration 번호
    "severity": Optional[int] # 선택: 속성의 강도 (1-10)
}
```

### 생성 코드 예시

```python
# nodes/stage1_nodes.py:281-286
info_id = graph.add_info(
    info_type=info.type,      # "desire", "fear" 등
    content=info.content,      # "타인의 진정성을 의심하고..."
    owner_id=char_id,          # 소유 Character ID
    created_at=current_iteration
)
```

### 연결 규칙

- **Character ↔ Info**: Character와 양방향 연결
- **Info ↔ Event**: Info의 원인이 되는 과거 Event와 연결

```python
# Event 연결 예시 (nodes/stage1_nodes.py:306)
graph.connect_nodes(info_id, event_id)
```

### owner_id 의미

Info의 `owner_id`는 **이 속성을 가진 Character**를 가리킵니다. Info 노드는 항상 하나의 Character에 소속됩니다.

## 3. Event 노드

### data 필드 구조

```python
{
    "summary": str,           # 필수: 과거 사건의 요약
    "target_info_type": str,  # 필수: 이 사건이 형성한 Info의 타입
    "owner_id": str,          # 필수: 중심 인물 Character 노드 ID
    "created_at": int,        # 필수: 생성된 iteration 번호
}
```

### 생성 코드 예시

```python
# nodes/stage1_nodes.py:300-305
event_id = graph.add_event(
    summary=event.summary,
    target_info_type=event.target_info_type,
    owner_id=char_id,          # Event의 중심 인물
    created_at=current_iteration
)
```

### 연결 규칙

- **Info ↔ Event**: Event는 특정 Info의 원인 사건
- **Event ↔ PlaceHolder**: Event에 등장하는 미확정 인물들

```python
# PlaceHolder 연결 예시 (nodes/stage1_nodes.py:308-314)
for placeholder in event.placeholders:
    ph_id = graph.add_placeholder(
        role=placeholder.role,
        owner_id=event_id,
        created_at=current_iteration
    )
    graph.connect_nodes(event_id, ph_id)
```

### owner_id 의미

Event의 `owner_id`는 **이 사건의 중심 인물(주인공)**을 가리킵니다. Event는 항상 특정 Character의 관점에서 기술됩니다.

예: "절대적 지배자가 (믿었던 동료)에게 배신당한 사건" → owner_id = "절대적 지배자"의 Character ID

## 4. PlaceHolder 노드

### data 필드 구조

```python
{
    "role": str,                      # 필수: PlaceHolder 역할 (괄호 포함, 예: "(믿었던 동료)")
    "owner_id": Union[str, List[str]], # 필수: 소속 Event ID(들)
    "created_at": int,                # 필수: 생성된 iteration 번호
}
```

### 생성 코드 예시

**초기 생성** (단일 Event 소속):
```python
# nodes/stage1_nodes.py:309-314
ph_id = graph.add_placeholder(
    role="(믿었던 동료)",
    owner_id=event_id,          # 단일 Event ID
    created_at=current_iteration
)
```

**Consolidation 후** (여러 Event 통합):
```python
# nodes/stage1_nodes.py:336-338
unified_id = graph.add_placeholder(
    role="권위적인 조언자",    # 통합된 역할명
    owner_id=[event_1, event_2, event_3],  # 여러 Event ID
    created_at=current_iteration
)
```

### 연결 규칙

- **Event ↔ PlaceHolder**: PlaceHolder는 항상 하나 이상의 Event와 연결

### owner_id 의미

PlaceHolder의 `owner_id`는 **이 PlaceHolder가 등장하는 Event ID(들)**을 가리킵니다.
- 초기 생성 시: 단일 str (하나의 Event)
- Consolidation 후: List[str] (통합된 여러 Event)

### PlaceHolder → Character 전환

PlaceHolder Replace 서브그래프에서 PlaceHolder는 Character로 전환됩니다:

```python
# nodes/stage1_nodes.py:349-365
for placeholder_id, infos in generated_infos:
    placeholder_node = graph.nodes[placeholder_id]
    placeholder_role = placeholder_node.data.get("role", "Unknown")

    # 1. 새 Character 생성
    char_id = graph.add_character(
        role=placeholder_role,  # 괄호 제거된 역할명
        created_at=current_iteration
    )

    # 2. Info 생성 및 연결
    for info in infos:
        info_id = graph.add_info(...)
        if info.event_id != "미정":
            graph.connect_nodes(info_id, info.event_id)  # 기존 Event와 연결
        graph.connect_nodes(info_id, char_id)

    # 3. PlaceHolder 제거
    graph.remove_node(placeholder_id)
```

## 메타데이터 필드 정리

### created_at

- **타입**: int
- **의미**: 노드가 생성된 iteration 번호 (메인 워크플로우의 `current_iteration`)
- **용도**:
  - 디버깅 시 생성 순서 추적
  - 시각화 시 레이어 구분
  - 향후 시간적 일관성 검증

### owner_id

| 노드 타입 | owner_id 의미 | 타입 |
|-----------|---------------|------|
| Character | (없음, Character는 최상위 노드) | - |
| Info | 소유 Character ID | str |
| Event | 중심 인물 Character ID | str |
| PlaceHolder | 소속 Event ID(들) | str 또는 List[str] |

## Stage별 데이터 진화

### Stage 1 (현재 구현)

```python
Character {
    "role": "절대적 지배자",
    "created_at": 1
}

Info {
    "type": "desire",
    "content": "완벽한 통제를 추구함",
    "owner_id": "character_1",
    "created_at": 1
}

Event {
    "summary": "(믿었던 동료)가 배신하여 큰 손실을 입음",
    "target_info_type": "fear",
    "owner_id": "character_1",
    "created_at": 1
}

PlaceHolder {
    "role": "(믿었던 동료)",
    "owner_id": "event_1",
    "created_at": 1
}
```

### Stage 2+ (예상 확장)

```python
Character {
    "role": "절대적 지배자",
    "name": "카이엔",              # 이름 추가
    "age": 42,                    # 장르별 구체화
    "appearance": "냉철한 눈빛",  # 시각적 정보
    "created_at": 1
}

Info {
    "type": "desire",
    "content": "완벽한 통제를 추구함",
    "owner_id": "character_1",
    "created_at": 1,
    "manifestation": "부하들의 일정을 분 단위로 관리함"  # 구체적 행동 양식
}

Event {
    "summary": "카이엔이 최측근 '리안'에게 배신당함",
    "target_info_type": "fear",
    "owner_id": "character_1",
    "episode_range": [15, 18],    # 이 사건이 다뤄지는 에피소드
    "created_at": 1
}
```

## 실제 워크플로우에서의 생성 시점

### Character 생성

1. **첫 번째 iteration**: `define_roles` → Character 서브그래프
2. **이후 iteration**: PlaceHolder Replace 서브그래프

### Info 생성

1. Character 생성과 동시 (Character 서브그래프)
2. PlaceHolder Replace 시 (새 Character의 Info 생성)

### Event 생성

- Event 서브그래프에서 **Event 없는 모든 Info**에 대해 생성

```python
# nodes/stage1_create_event.py:17-52
def distribute_event_creation(state: EventCreationState) -> List[Send]:
    graph: CharacterNetwork = state["graph"]
    sends = []

    for char_id, char_node in graph.nodes.items():
        if char_node.type.value == "character":
            infos = graph.get_character_infos(char_id)

            for info in infos:
                # Info와 연결된 Event가 없으면 생성
                event_connected = False
                for edge_id in graph.nodes[info["id"]].edges:
                    if graph.nodes[edge_id].type.value == "event":
                        event_connected = True
                        break

                if not event_connected:
                    sends.append(Send("create_event", event_state))
    return sends
```

### PlaceHolder 생성

- Event 생성 시 함께 생성 (Event의 참여자로)

```python
# nodes/stage1_nodes.py:307-314
for placeholder in event.placeholders:
    ph_id = graph.add_placeholder(
        role=placeholder.role,
        owner_id=event_id,
        created_at=current_iteration
    )
    graph.connect_nodes(event_id, ph_id)
```

## CharacterNetwork 헬퍼 메서드

### 노드 추가 메서드

```python
# character_network.py:104-125
def add_character(self, role: str, name: Optional[str] = None, **kwargs) -> str:
    """Character 노드 추가 (이름은 선택)"""
    data = {"role": role, "name": name, **kwargs}
    return self.add_node(NodeType.CHARACTER, data)

def add_info(self, info_type: str, content: str, owner_id: str, **kwargs) -> str:
    """Info 노드 추가"""
    data = {"type": info_type, "content": content, "owner_id": owner_id, **kwargs}
    info_id = self.add_node(NodeType.INFO, data)
    return info_id

def add_event(self, summary: str, owner_id: str, **kwargs) -> str:
    """Event 노드 추가"""
    data = {"summary": summary, "owner_id": owner_id, **kwargs}
    return self.add_node(NodeType.EVENT, data)

def add_placeholder(self, role: str, owner_id: Union[str, List[str]], **kwargs) -> str:
    """PlaceHolder 노드 추가"""
    data = {"role": role, "owner_id": owner_id, **kwargs}
    return self.add_node(NodeType.PLACEHOLDER, data)
```

### 탐색 메서드

```python
# character_network.py:186-207
def get_character_infos(self, character_id: str) -> List[Dict[str, Any]]:
    """Character에 연결된 모든 Info 노드 정보 반환"""
    # 반환 형식: [{"id": "info_1", "type": "desire", "content": "..."}, ...]

# character_network.py:209-228
def get_event_participants(self, event_id: str) -> Dict[str, List[str]]:
    """Event에 연결된 참여자들 반환 (Info와 PlaceHolder 구분)"""
    # 반환 형식: {"infos": ["info_1", "info_2"], "placeholders": ["placeholder_1"]}

# character_network.py:127-135
def get_placeholders_with_event(self) -> List:
    """PlaceHolder와 연결된 Event들 반환 (Consolidation 입력용)"""
    # 반환 형식: [(placeholder_id, event_node), ...]
```

## 참고사항

1. **모든 노드는 생성 시 자동으로 고유 ID 부여**
   ```python
   # character_network.py:50-54
   def _generate_node_id(self, node_type: NodeType) -> str:
       type_key = node_type.value
       self._node_id[type_key] += 1
       return f"{type_key}_{self._node_id[type_key]}"
   ```

2. **연결 규칙은 자동 검증**
   ```python
   # character_network.py:87-102
   def connect_nodes(self, node1_id: str, node2_id: str) -> bool:
       if not self._validate_connection(node1, node2):
           raise ValueError(f"Invalid connection: {node1.type.value} cannot connect to {node2.type.value}")
   ```

3. **PlaceHolder는 Consolidation 후 통합되거나, PlaceHolder Replace 후 Character로 전환됨**
   - Consolidation: 여러 PlaceHolder → 하나의 PlaceHolder (역할명 통합)
   - Replace: PlaceHolder → Character + Info

4. **JSON 저장 형식**
   ```python
   # character_network.py:262-281
   def save_to_file(self, filename: str):
       serializable_nodes = {}
       for node_id, node in self.nodes.items():
           serializable_nodes[node_id] = {
               "id": node.id,
               "type": node.type.value,  # Enum → str
               "data": node.data,
               "edges": list(node.edges)  # set → list
           }
   ```
