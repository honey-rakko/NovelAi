"""
LLM 프롬프트 템플릿 - 간소화된 캐릭터 생성 (조연급/단역용)
"""

# ============ 조연급 캐릭터 생성 프롬프트 ============
SUPPORTING_CHARACTER_PROMPT = """
# 역할: 조연급 캐릭터 설계자

PlaceHolder를 조연급 캐릭터로 전환합니다.
핵심적인 특성만 간결하게 설계합니다.

## 입력
역할: {placeholder_role}
관련 사건들: {event_contexts}
주제: {topic}
갈등: {conflict}

## 설계 원칙

### 핵심만 추출
조연급 캐릭터는 주연을 보조하는 역할이므로, 복잡한 내면보다는 명확한 기능과 동기를 중심으로 설계합니다.

### 필수 요소 (4개)
1. **Desire** (욕망): 이 캐릭터가 추구하는 것
2. **Fear** (두려움): 이 캐릭터가 회피하는 것
3. **Paradox** (딜레마): 욕망과 두려움 사이의 모순
4. **Growth Potential** (성장 가능성): 변화의 여지

### 선택 요소 (최대 2개 추가)
상황에 따라 다음 중 1-2개를 추가할 수 있습니다:
- **M.O.** (행동 방식): 특징적인 행동 패턴
- **Rhetoric** (화법): 특징적인 말하기 방식
- **Emotion** (감정 표현): 감정을 다루는 방식

## 출력 형식
```json
{
  "role": "{placeholder_role}",
  "tier": "supporting",
  "infos": [
    {"type": "desire", "content": "추구하는 것"},
    {"type": "fear", "content": "회피하는 것"},
    {"type": "paradox", "content": "내적 모순"},
    {"type": "growth_potential", "content": "변화 가능성"},
    // 선택적 추가 (최대 2개)
    {"type": "modus_operandi", "content": "행동 방식"} // 선택
  ]
}
```
"""

# ============ 단역 캐릭터 생성 프롬프트 ============
MINOR_CHARACTER_PROMPT = """
# 역할: 단역 캐릭터 설계자

PlaceHolder를 단순한 기능적 캐릭터로 전환합니다.
최소한의 특성만 부여합니다.

## 입력
역할: {placeholder_role}
관련 사건: {event_context}

## 설계 원칙

### 최소 요소만 (2-3개)
1. **Desire** (욕망): 단순하고 명확한 동기
2. **Fear** (두려움): 기본적인 회피 성향
3. **특징 1개** (선택): 역할 수행에 필요한 경우만

## 출력 형식
```json
{
  "role": "{placeholder_role}",
  "tier": "minor",
  "infos": [
    {"type": "desire", "content": "단순한 동기"},
    {"type": "fear", "content": "기본적 두려움"}
  ]
}
```
"""