"""
캐릭터 티어 시스템 마이그레이션 가이드

## 개요
기존 stage1_nodes.py의 캐릭터 생성 시스템을 티어 시스템으로 업그레이드하는 방법입니다.

## 수정이 필요한 파일들

### 1. stage1_nodes.py 수정
```python
# 기존 코드
from pydantics.stage1_pydantics import Character, Info, Infos

# 수정 후
from pydantics.stage1_pydantics_v3 import (
    Character, SimplifiedCharacter, CharacterTier, 
    InfoType, Info, Infos
)
from nodes.stage1_character_tiers import (
    determine_character_tier,
    create_main_character_node,
    create_supporting_character_node
)

# create_character_node 수정
def create_character_node(state: Dict[str, Any]) -> Dict[str, Any]:
    \"\"\"캐릭터 생성 노드 - 티어 시스템 적용\"\"\"
    
    # iteration 0 (첫 번째 루프) - 주연급
    if state.get("current_iteration", 0) == 0:
        return create_main_character_node(state)
    
    # 그 외 - 티어 자동 결정
    tier = determine_character_tier(state)
    
    if tier == "main":
        return create_main_character_node(state)
    elif tier == "supporting":
        return create_supporting_character_node(state)
    else:
        return create_minor_character_node(state)
```

### 2. stage1_placeholder_replace.py 수정
```python
# PlaceHolder를 Character로 전환할 때
def create_info_for_placeholder_node(state: Dict[str, Any]) -> Dict[str, Any]:
    \"\"\"PlaceHolder를 티어별 캐릭터로 전환\"\"\"
    
    # 티어 결정
    tier = determine_character_tier(state)
    
    if tier == "supporting":
        # 조연급 Info 생성 (4-6개)
        return create_supporting_character_info(state)
    else:
        # 단역 Info 생성 (2-3개)
        return create_minor_character_info(state)
```

### 3. CharacterNetwork 클래스 확장
```python
def add_character(self, role: str, created_at: int = 0, metadata: Dict = None):
    \"\"\"캐릭터 추가 - 티어 정보 포함\"\"\"
    char_id = self.add_node(
        NodeType.CHARACTER,
        {
            "role": role,
            "created_at": created_at,
            "metadata": metadata or {}  # tier 정보 저장
        }
    )
    return char_id
```

## 사용 예제

### 워크플로우에서 사용
```python
from nodes.stage1_character_tiers import get_character_tier_stats

# 워크플로우 완료 후 통계 출력
def print_character_stats(state):
    graph = state["graph"]
    stats = get_character_tier_stats(graph)
    
    print("\\n=== 캐릭터 티어 통계 ===")
    print(f"주연급: {stats['main']}명")
    print(f"조연급: {stats['supporting']}명")
    print(f"단역: {stats['minor']}명")
    print(f"총 캐릭터: {sum(stats.values())}명")
```

## 점진적 마이그레이션 전략

### Phase 1: 병렬 운영
- 기존 시스템과 새 시스템을 병렬로 운영
- feature flag로 전환 가능하도록 구성
```python
USE_TIER_SYSTEM = True  # 환경변수로 관리

if USE_TIER_SYSTEM:
    from pydantics.stage1_pydantics_v3 import Character
else:
    from pydantics.stage1_pydantics import Character
```

### Phase 2: 부분 적용
- 새로 생성되는 캐릭터에만 티어 시스템 적용
- 기존 캐릭터는 그대로 유지

### Phase 3: 전체 전환
- 모든 캐릭터 생성을 티어 시스템으로 전환
- 기존 데이터 마이그레이션

## 기존 데이터 마이그레이션

### 기존 캐릭터에 티어 할당
```python
def migrate_existing_characters(graph: CharacterNetwork):
    \"\"\"기존 캐릭터에 티어 정보 추가\"\"\"
    
    characters = graph.get_characters()
    for i, (char_id, char_node) in enumerate(characters):
        # Info 개수로 티어 추정
        info_count = len([e for e in char_node.edges if e.startswith("info_")])
        
        if i < 5:  # 처음 5명은 주연급
            tier = "main"
        elif info_count >= 4:
            tier = "supporting"
        else:
            tier = "minor"
        
        # metadata 업데이트
        if "metadata" not in char_node.data:
            char_node.data["metadata"] = {}
        char_node.data["metadata"]["tier"] = tier
```

## 호환성 유지

### InfoType Enum 확장
- 기존 type들과 호환 유지
- 새로운 type들 추가

### 프롬프트 버전 관리
```python
# prompts/__init__.py
from .stage1_prompts import CHARACTER_PROMPT as CHARACTER_PROMPT_V1
from .stage1_prompts import CHARACTER_PROMPT as CHARACTER_PROMPT_V2
from .stage1_character_tiers import (
    SUPPORTING_CHARACTER_PROMPT,
    MINOR_CHARACTER_PROMPT
)

# 버전별 사용
def get_character_prompt(version="v2", tier="main"):
    if version == "v1":
        return CHARACTER_PROMPT_V1
    elif tier == "main":
        return CHARACTER_PROMPT_V2
    elif tier == "supporting":
        return SUPPORTING_CHARACTER_PROMPT
    else:
        return MINOR_CHARACTER_PROMPT
```

## 테스트 및 검증

### 단위 테스트
```bash
python test_character_tiers.py
```

### 통합 테스트
```bash
python workflow_stage1.py --use-tier-system
```

### 성능 비교
- LLM 호출 횟수 감소 (조연/단역은 간소화)
- 생성 시간 단축
- 토큰 사용량 감소

## 롤백 계획

문제 발생 시:
1. USE_TIER_SYSTEM = False 설정
2. 기존 pydantics.stage1_pydantics 사용
3. 기존 프롬프트로 복원

## 모니터링

### 메트릭 수집
```python
def collect_metrics(graph):
    return {
        "total_characters": len(graph.get_characters()),
        "tier_distribution": get_character_tier_stats(graph),
        "avg_infos_per_character": calculate_avg_infos(graph),
        "llm_calls": count_llm_calls()
    }
```

## FAQ

Q: 기존 시스템과 호환되나요?
A: 네, InfoType enum을 확장했고 기존 필드들을 모두 포함합니다.

Q: 티어를 나중에 변경할 수 있나요?
A: 네, metadata를 수정하면 됩니다. 향후 티어 승격/강등 시스템 추가 예정입니다.

Q: 성능 개선 효과는 어느 정도인가요?
A: 조연/단역이 많은 경우 LLM 호출이 30-50% 감소할 것으로 예상됩니다.
"""