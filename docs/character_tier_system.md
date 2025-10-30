"""
캐릭터 티어 시스템 통합 가이드

## 개요
새로운 캐릭터 설계 시스템은 주연급/조연급/단역을 구분하여 효율적으로 캐릭터를 생성합니다.

## 캐릭터 티어별 필드

### 주연급 (Main) - 전체 필드
```
1. Analysis 섹션:
   - situation: 근본적 상황
   - question: 근본적 질문  
   - philosophy: 핵심 신념

2. Infos 섹션 (8-10개):
   - desire (필수)
   - fear (필수)
   - paradox (필수)
   - modus_operandi (필수)
   - rhetoric (필수)
   - emotion (필수)
   - talent/symbol (선택)
   - growth_potential (필수)
```

### 조연급 (Supporting) - 핵심 필드
```
Infos 섹션 (4-6개):
- desire (필수)
- fear (필수)
- paradox (필수)
- growth_potential (필수)
- modus_operandi/rhetoric/emotion 중 1-2개 (선택)
```

### 단역 (Minor) - 최소 필드
```
Infos 섹션 (2-3개):
- desire (필수)
- fear (필수)
- 특징 1개 (선택)
```

## 티어 결정 로직

### 자동 판단 기준
1. **iteration 0** (첫 번째 루프): 주연급
2. **iteration 1** + 캐릭터 수 < 8: 조연급
3. **연결된 이벤트 3개 이상**: 조연급
4. **연결된 이벤트 2개**: 조연급 또는 단역 (캐릭터 수에 따라)
5. **연결된 이벤트 1개**: 단역

## 사용 방법

### 1. Pydantic 모델 임포트
```python
from pydantics.stage1_pydantics_v3 import (
    Character,  # 주연급용
    SimplifiedCharacter,  # 조연/단역용
    CharacterTier,
    InfoType,
    CharacterAnalysis
)
```

### 2. 노드 함수 사용
```python
from nodes.stage1_character_tiers import (
    create_main_character_node,      # 주연급 생성
    create_supporting_character_node, # 조연급 생성
    create_minor_character_node,      # 단역 생성
    determine_character_tier,         # 티어 자동 결정
    get_character_tier_stats          # 통계 확인
)
```

### 3. 워크플로우에서 사용
```python
# 첫 번째 iteration - 주연급
if state["current_iteration"] == 0:
    character = create_main_character_node(state)
else:
    # 티어 자동 결정
    tier = determine_character_tier(state)
    if tier == "main":
        character = create_main_character_node(state)
    elif tier == "supporting":
        character = create_supporting_character_node(state)
    else:
        character = create_minor_character_node(state)
```

## 프롬프트 파일

### 주연급
- `prompts/stage1_prompts.py`: CHARACTER_PROMPT

### 조연급/단역
- `prompts/stage1_character_tiers.py`:
  - SUPPORTING_CHARACTER_PROMPT
  - MINOR_CHARACTER_PROMPT

## 장점

1. **효율성**: 중요도에 따라 필드 수를 조절하여 LLM 호출 비용 절감
2. **일관성**: 티어별로 명확한 규칙 적용
3. **확장성**: 200화 장편에 필요한 다양한 캐릭터 레벨 지원
4. **품질**: 주연급은 깊이 있게, 조연/단역은 간결하게

## 통계 확인
```python
# 생성된 캐릭터 티어별 통계
stats = get_character_tier_stats(graph)
print(f"주연급: {stats['main']}명")
print(f"조연급: {stats['supporting']}명")  
print(f"단역: {stats['minor']}명")
```

## 주의사항

1. **역호환성**: 기존 시스템과 호환되도록 InfoType enum 확장
2. **검증**: Character 모델의 validator가 티어별 필수 필드 검사
3. **메타데이터**: 그래프에 tier 정보를 metadata로 저장

## 향후 개선 방향

1. 티어 승격/강등 시스템 (조연→주연 등)
2. 동적 티어 결정 (스토리 진행에 따라)
3. 티어별 상호작용 규칙 정의