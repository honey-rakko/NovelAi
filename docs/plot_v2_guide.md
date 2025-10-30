# Plot Generation v2 사용 가이드

## 개요
새로운 플롯 생성 시스템은 기존 Stage1에서 생성한 CharacterNetwork를 바탕으로 200화 장편 웹소설의 플롯을 체계적으로 생성합니다.

## 실행 방법

### 1. langgraph dev 서버 실행
```bash
langgraph dev
```

### 2. API 호출 예시

#### Stage1으로 캐릭터 네트워크 생성
```python
import requests
import json

# Stage1 실행 (캐릭터 네트워크 생성)
stage1_input = {
    "topic": "권력의 본질",
    "conflict": "개인과 집단",
    "vibe": "어둡고 냉소적",
    "max_iterations": 2,
    "model": "gpt-4o-mini",
    "extractor_type": "default"
}

response = requests.post(
    "http://localhost:8000/runs/stream",
    json={
        "assistant_id": "stage1",
        "input": stage1_input,
        "stream_mode": "values"
    }
)

# 결과에서 graph 추출
result = response.json()
graph = result[-1]["graph"]  # 마지막 state의 graph
```

#### Plot v2로 플롯 생성
```python
# Plot v2 실행 (플롯 생성)
plot_input = {
    "topic": "권력의 본질",
    "conflict": "개인과 집단",
    "vibe": "어둡고 냉소적",
    "graph": graph,  # Stage1에서 생성한 graph
    "model": "gpt-4o-mini",
    "extractor_type": "default"
}

response = requests.post(
    "http://localhost:8000/runs/stream",
    json={
        "assistant_id": "plot",
        "input": plot_input,
        "stream_mode": "values"
    }
)

# 최종 플롯 결과
final_result = response.json()[-1]
integrated_plot = final_result["integrated_plot"]

print("플롯 요약:", integrated_plot["plot_summary"])
print("핵심 질문:", integrated_plot["core_question"])
print("주제 진술:", integrated_plot["thematic_statement"])
```

## 플롯 생성 프로세스

### 5단계 순차 진행
1. **서사적 양극 분석**: 캐릭터의 Desire/Fear 분석하여 출발점과 종착점 설정
2. **Sub-theme 선정**: Act 1/2/3 각각에 적합한 sub-theme 할당
3. **기폭사건 및 Macro Cliffhanger**: 강력한 초반 훅과 장기적 긴장 구조 설계
4. **구조적 템포**: MC 사이 중간 아크 개수와 배치 결정
5. **통합 플롯 생성**: 모든 요소를 통합하여 최종 플롯 뼈대 완성

## 출력 결과

### IntegratedPlot 구조
```json
{
    "plot_summary": "한 줄 요약",
    "core_question": "독자가 끝까지 궁금해할 핵심 질문",
    "thematic_statement": "이야기가 말하고자 하는 것",
    "act_structures": [
        {
            "act_number": 1,
            "subtitle": "막 부제목",
            "episode_range": "1-65화",
            "sub_theme": "Act 1 sub-theme",
            "macro_cliffhangers": ["MC1", "MC2"],
            "intermediate_arc_summary": {"구간": 개수}
        }
        // Act 2, Act 3...
    ],
    "macro_cliffhanger_flow": "MC 연결도",
    "episode_tension_map": "화수별 긴장도",
    "key_character_placement": {
        "MC1": ["관련 캐릭터들"],
        // ...
    },
    "required_additions": ["추가 필요 요소들"]
}
```

## 결과 저장
- 플롯 결과는 `saved_plots/` 디렉토리에 JSON 형식으로 자동 저장
- 파일명: `plot_YYYYMMDD_HHMMSS.json`
- 전체 분석 과정이 포함된 완전한 결과 저장

## 주의사항
1. Stage1 실행 후 생성된 graph를 그대로 전달해야 함
2. topic, conflict, vibe는 Stage1과 동일하게 유지 권장
3. 각 단계는 순차적으로 실행되며, 중간 결과도 확인 가능

## 트러블슈팅

### CharacterNetwork 타입 에러
- `model_config = ConfigDict(arbitrary_types_allowed=True)` 설정 확인
- graph를 Dict로 전달하는지 확인

### Import 에러  
- 모든 파일이 올바른 위치에 있는지 확인
- `__init__.py` 파일 존재 여부 확인

### LLM 호출 실패
- API 키 설정 확인 (.env 파일)
- 모델명이 올바른지 확인 (gpt-4o-mini 등)