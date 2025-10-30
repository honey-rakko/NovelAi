# Stage1 구현 가이드

이 문서는 Stage1 워크플로우의 구체적인 구현 세부사항을 설명합니다.
새로운 Stage를 구현하거나 Stage1을 수정할 때 참고하세요.

## 전체 아키텍처

### 파일 구조
```
workflow_stage1.py           # 메인 워크플로우 정의
states/stage1_states.py      # State 정의 (WorkflowState, 임시 State들)
nodes/stage1_nodes.py        # 공통 노드 함수들 (initialize_accumulated_state, save_graph_to_file 등)
nodes/stage1_create_character.py    # Character 생성 서브그래프 (노드 + 조건부 엣지 + 빌드 함수)
nodes/stage1_create_event.py        # Event 생성 서브그래프 (노드 + 조건부 엣지 + 빌드 함수)
nodes/stage1_consolidation.py       # Consolidation 서브그래프 (노드 + 조건부 엣지 + 빌드 함수)
nodes/stage1_placeholder_replace.py # PlaceHolder 처리 서브그래프 (노드 + 조건부 엣지 + 빌드 함수)
pydantics/stage1_pydantics.py      # Pydantic 모델 (LLM 출력 스키마)
prompts/stage1_prompts.py   # 프롬프트 템플릿
character_network.py        # CharacterNetwork 클래스 (도메인 객체)
```

**서브그래프 파일 구조 원칙**:
- 각 서브그래프 파일은 해당 서브그래프의 모든 노드를 직접 포함
- 공통 노드(initialize_accumulated_state, save_graph_to_file)만 stage1_nodes.py에서 import
- 한 파일만 읽으면 서브그래프 전체 로직을 파악할 수 있도록 자기완결적 구조 유지

## State 설계

### 1. WorkflowState (메인 워크플로우)
메인 워크플로우를 통해 유지되는 핵심 상태
```python
class WorkflowState(TypedDict):
    # 입력
    topic: str
    max_iterations: int

    # 핵심 데이터
    graph: CharacterNetwork           # 캐릭터 풀 (노드 그래프)

    # 반복 제어
    current_iteration: int
    roles: List[str]            # 첫 번째 iteration용 역할들

    # 출력
    plots: Optional[Plot]
    plot_candidates: Optional[PlotCandidates]
```

### 2. 임시 State들 (서브그래프 전용)

#### CharacterCreationState
```python
class CharacterCreationState(TypedDict):
    topic: str
    roles: List[str]
    generated_character: Annotated[List[Character], merge_lists]  # 누적
    current_iteration: int
    graph: CharacterNetwork
```

#### EventCreationState
```python
class EventCreationState(TypedDict):
    generated_event: Annotated[List[Event], merge_lists]  # 누적
    current_iteration: int
    graph: CharacterNetwork
    topic: str
```

#### ConsolidationState
```python
class ConsolidationState(TypedDict):
    graph: CharacterNetwork
    chunked_placeholders: List[List[str]]  # 통합 대상 그룹들
    consolidated_roles: Annotated[List[ConsolidatedRole], merge_lists]  # 누적
    current_iteration: int
    topic: str
```

#### PlaceHolderReplaceState
```python
class PlaceHolderReplaceState(TypedDict):
    graph: CharacterNetwork
    placeholders: List[str]     # PlaceHolder 목록
    generated_infos: Annotated[List, merge_lists]  # 누적: (placeholder_id, infos)
    current_iteration: int
    topic: str
```

### 3. merge_lists 함수
Send로 병렬 처리된 결과를 누적하는 핵심 함수
```python
def merge_lists(left: Optional[List], right: Optional[List]) -> List:
    """
    규칙:
    - right가 None이면 초기화 (서브그래프 시작시)
    - 그 외에는 left + right (누적)
    """
    if right is None:
        return []
    if left is None:
        return right
    return left + right
```

## 워크플로우 흐름

### 메인 워크플로우
```
START
  ↓
initialize (InputState → WorkflowState)
  ↓ (병렬)
  ├─→ define_roles (roles 생성)
  └─→ create_plot_candidates (plot_candidates 생성)
      ↓
define_roles 완료 후
  ↓
run_character_subgraph (첫 번째 iteration)
  ↓
run_event_subgraph
  ↓
run_consolidation_subgraph
  ↓
increment_iteration
  ↓
should_continue? ──→ [end] → finalize → END
  ↓ [continue]
run_placeholder_replace_subgraph
  ↓
run_event_subgraph ←──┐
  ↓                   │
run_consolidation_subgraph
  ↓                   │
increment_iteration   │
  ↓                   │
should_continue? ─────┘
```

### 반복 구조의 핵심
- **첫 번째 iteration**: `define_roles` → Character 생성
- **이후 iteration**: PlaceHolder Replace → Character 생성
- **공통 사이클**: Event 생성 → Consolidation → iteration 증가

## 서브그래프 상세

### 1. Character 생성 서브그래프
**목적**: 역할(role)별로 Character와 Info 생성

**흐름**:
```
START
  ↓
initialize_accumulated_state (누적 State 초기화)
  ↓
distribute_character_creation (Send 분배)
  ↓ (병렬: 역할별)
create_character (LLM 호출)
  ↓
update_character_graph (Graph에 추가)
  ↓
END
```

**핵심 로직**:
- `distribute_character_creation`: 각 role별로 Send 생성
- `create_character`: Role → Character(role, infos) 생성
- `update_character_graph`: Character/Info 노드 추가 및 연결

### 2. Event 생성 서브그래프
**목적**: Event가 없는 모든 Info에 대해 Event 생성

**흐름**:
```
START
  ↓
initialize_accumulated_state
  ↓
distribute_event_creation (Graph에서 Info 탐색)
  ↓ (병렬: Info별)
create_event (LLM 호출)
  ↓
update_event_graph (Graph에 추가)
  ↓
save_graph_to_file
  ↓
END
```

**핵심 로직**:
- `distribute_event_creation`: Graph의 모든 Character 순회 → Info 찾기 → Event 없는 Info만 선별
- `create_event`: Info → Event(summary, placeholders) 생성
- `update_event_graph`: Event/PlaceHolder 노드 추가 및 연결

### 3. Consolidation 서브그래프
**목적**: 유사한 PlaceHolder들을 통합

**흐름**:
```
START
  ↓
initialize_accumulated_state
  ↓
prepare_consolidation (LLM 호출: 통합 대상 그룹화)
  ↓
distribute_consolidation (Send 분배)
  ↓ (병렬: 그룹별)
consolidate (LLM 호출: 통합 역할명 생성)
  ↓
update_consolidation_graph (Graph에서 노드 병합)
  ↓
save_graph_to_file
  ↓
END
```

**핵심 로직**:
- `prepare_consolidation`: 모든 PlaceHolder → LLM이 유사한 것들 그룹화
- `consolidate`: 각 그룹 → 통합 역할명 생성
- `update_consolidation_graph`: Graph.merge_nodes로 PlaceHolder 통합

### 4. PlaceHolder Replace 서브그래프
**목적**: 통합된 PlaceHolder를 Character로 전환

**흐름**:
```
START
  ↓
initialize_accumulated_state
  ↓
prepare_placeholders (Graph에서 PlaceHolder와 연결된 Event 찾기)
  ↓
distribute_placeholder_info_creation (Send 분배)
  ↓ (병렬: PlaceHolder별)
create_info_for_placeholder (LLM 호출: Event 맥락으로 Info 생성)
  ↓
update_graph_with_infos (Character 생성, PlaceHolder 제거)
  ↓
save_graph_to_file
  ↓
END
```

**핵심 로직**:
- `prepare_placeholders`: PlaceHolder → 연결된 Event들 수집
- `create_info_for_placeholder`: Event 맥락 → Info 생성
- `update_graph_with_infos`: PlaceHolder 제거 → Character/Info 추가

## 노드 분류

### 서브그래프별 노드 (각 서브그래프 파일에 포함)

#### stage1_create_character.py
- `create_character_node` (LLM): role → Character
- `update_graph_with_character` (Graph 업데이트): Character → Graph에 추가

#### stage1_create_event.py
- `create_event_node` (LLM): info → Event
- `update_graph_with_event` (Graph 업데이트): Event → Graph에 추가

#### stage1_consolidation.py
- `prepare_consolidation_node` (LLM): placeholders → chunked_placeholders
- `consolidate_node` (LLM): placeholder_info → ConsolidatedRole
- `update_graph_after_consolidation` (Graph 업데이트): ConsolidatedRole → Graph 병합

#### stage1_placeholder_replace.py
- `prepare_placeholders_node` (유틸리티): PlaceHolder-Event 연결 수집
- `create_info_for_placeholder_node` (LLM): event_contexts → Infos
- `update_graph_with_infos` (Graph 업데이트): Infos → Character 생성, PlaceHolder 제거

### 공통 노드 (stage1_nodes.py)
1. `initialize_accumulated_state`: State 초기화 (누적 필드만 None으로)
2. `save_graph_to_file`: Graph → JSON 파일 저장
3. `define_main_character_roles` (LLM): topic → roles
4. `create_plot_candidates_node` (LLM): topic → PlotCandidates
5. `increment_iteration`: current_iteration += 1

## 병렬 처리 패턴

### Send 분배 함수 구조
모든 `distribute_*` 함수는 동일한 패턴을 따름:
```python
def distribute_*(state: State) -> List[Send]:
    sends = []
    for item in items_to_process:
        send_state = {
            # 필요한 정보만 선별
        }
        sends.append(Send("target_node", send_state))
    return sends
```

### 누적 패턴
1. 서브그래프 시작: `initialize_accumulated_state`로 누적 필드를 None으로 초기화
2. Send 분배: 각 item별로 독립 실행
3. 자동 병합: `merge_lists(left, right)`가 각 결과를 누적
4. 다음 노드: 모든 병렬 실행 완료 후 누적 결과로 진행

## Graph 업데이트 타이밍

### 저장 시점
- Event 생성 후
- Consolidation 후
- PlaceHolder Replace 후
- 워크플로우 종료시

### 연결 규칙
```
Character ↔ Info
Info ↔ Event
Event ↔ PlaceHolder
```

### 주의사항
- Graph 업데이트 노드는 반드시 Graph 업데이트만 수행
- LLM 호출과 Graph 업데이트를 한 노드에서 처리 금지 (단일 책임 원칙)
- Graph 업데이트 후 save_graph_to_file 노드 연결 권장

## 확장 가이드

새로운 Stage를 구현할 때:

1. **State 정의**: 메인 State와 임시 State 분리
2. **서브그래프 설계**: 병렬 처리가 필요한 부분 식별
3. **서브그래프 파일 구조**:
   - 각 서브그래프를 개별 파일로 분리 (nodes/stage*_*.py)
   - 해당 서브그래프의 모든 노드를 파일 내에 직접 선언
   - 공통 노드만 별도 파일(stage*_nodes.py)에서 import
4. **노드 분리**: LLM 호출 / Graph 업데이트 / 유틸리티 노드 명확히 구분
5. **Pydantic 모델**: LLM 출력 스키마 정의 (validator 활용)
6. **프롬프트**: 명확한 입출력 명시

### 체크리스트
- [ ] 모든 LLM 노드는 Input/Output이 명시되었는가?
- [ ] 하나의 노드가 하나의 역할만 수행하는가?
- [ ] Send 병렬 처리시 임시 State + Subgraph 구조인가?
- [ ] Graph 업데이트 후 save 노드가 연결되었는가?
- [ ] merge_lists 패턴이 올바르게 적용되었는가?
- [ ] iteration 관리가 명확한가?
- [ ] 서브그래프별 노드가 해당 파일 내에 선언되어 자기완결적인가?
- [ ] 공통 노드만 별도 파일에서 import하는가?