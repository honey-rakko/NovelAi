"""
테스트 스크립트 - 새로운 캐릭터 티어 시스템
"""

from character_network import CharacterNetwork
from nodes.stage1_character_tiers import (
    create_main_character_node,
    create_supporting_character_node,
    create_minor_character_node,
    determine_character_tier,
    get_character_tier_stats
)


def test_main_character():
    """주연급 캐릭터 생성 테스트"""
    print("\n" + "="*60)
    print("주연급 캐릭터 생성 테스트")
    print("="*60)
    
    state = {
        "topic": "권력의 본질",
        "conflict": "개인과 집단",
        "role": "(권력을 추구하는 자)",
        "role_info": {
            "theme_exploration": "권력의 유혹과 타락",
            "core_direction": "절대적 지배를 통한 질서",
            "initial_belief": "강한 자만이 세상을 바꿀 수 있다",
            "conflict_prediction": "이상주의자와 충돌"
        },
        "model": "gpt-4o-mini",
        "extractor_type": "default"
    }
    
    try:
        result = create_main_character_node(state)
        character = result["generated_character"][0]
        
        print(f"\n✅ 주연급 캐릭터 생성 성공!")
        print(f"역할: {character.role}")
        print(f"티어: {character.tier.value}")
        
        if character.analysis:
            print(f"\n📊 분석:")
            print(f"  상황: {character.analysis.situation[:50]}...")
            print(f"  질문: {character.analysis.question[:50]}...")
            print(f"  철학: {character.analysis.philosophy[:50]}...")
        
        print(f"\n📝 속성 ({len(character.infos)}개):")
        for info in character.infos[:3]:
            print(f"  - {info.type.value}: {info.content[:50]}...")
        
        return character
    except Exception as e:
        print(f"❌ 오류: {e}")
        return None


def test_supporting_character():
    """조연급 캐릭터 생성 테스트"""
    print("\n" + "="*60)
    print("조연급 캐릭터 생성 테스트")
    print("="*60)
    
    state = {
        "placeholder_role": "(믿었던 동료)",
        "event_contexts": [
            "중요한 순간에 배신하여 주인공에게 큰 상처를 남김",
            "과거에는 함께 이상을 꿈꿨으나 현실에 굴복함"
        ],
        "topic": "권력의 본질",
        "conflict": "개인과 집단",
        "model": "gpt-4o-mini",
        "extractor_type": "default"
    }
    
    try:
        result = create_supporting_character_node(state)
        character = result["generated_character"]
        
        print(f"\n✅ 조연급 캐릭터 생성 성공!")
        print(f"역할: {character.role}")
        print(f"티어: {character.tier.value}")
        
        print(f"\n📝 속성 ({len(character.infos)}개):")
        for info in character.infos:
            print(f"  - {info.type.value}: {info.content[:50]}...")
        
        return character
    except Exception as e:
        print(f"❌ 오류: {e}")
        return None


def test_minor_character():
    """단역 캐릭터 생성 테스트"""
    print("\n" + "="*60)
    print("단역 캐릭터 생성 테스트")
    print("="*60)
    
    state = {
        "placeholder_role": "(무관심한 방관자)",
        "event_contexts": ["주인공의 고통을 목격하고도 외면함"],
        "model": "gpt-4o-mini",
        "extractor_type": "default"
    }
    
    try:
        result = create_minor_character_node(state)
        character = result["generated_character"]
        
        print(f"\n✅ 단역 캐릭터 생성 성공!")
        print(f"역할: {character.role}")
        print(f"티어: {character.tier.value}")
        
        print(f"\n📝 속성 ({len(character.infos)}개):")
        for info in character.infos:
            print(f"  - {info.type.value}: {info.content}")
        
        return character
    except Exception as e:
        print(f"❌ 오류: {e}")
        return None


def test_tier_determination():
    """티어 자동 결정 테스트"""
    print("\n" + "="*60)
    print("티어 자동 결정 테스트")
    print("="*60)
    
    graph = CharacterNetwork("권력의 본질")
    
    test_cases = [
        {"current_iteration": 0, "connected_events": [], "expected": "main"},
        {"current_iteration": 1, "connected_events": ["e1", "e2", "e3"], "expected": "supporting"},
        {"current_iteration": 2, "connected_events": ["e1"], "expected": "minor"},
    ]
    
    for i, case in enumerate(test_cases, 1):
        state = {
            "current_iteration": case["current_iteration"],
            "connected_events": case["connected_events"],
            "graph": graph
        }
        
        tier = determine_character_tier(state)
        status = "✅" if tier == case["expected"] else "❌"
        print(f"{status} 테스트 {i}: iteration={case['current_iteration']}, "
              f"events={len(case['connected_events'])} → {tier} "
              f"(예상: {case['expected']})")


def main():
    """전체 테스트 실행"""
    print("\n" + "="*70)
    print(" 캐릭터 티어 시스템 테스트 ")
    print("="*70)
    
    # 각 티어별 테스트
    main_char = test_main_character()
    supporting_char = test_supporting_character()
    minor_char = test_minor_character()
    
    # 티어 결정 로직 테스트
    test_tier_determination()
    
    # 결과 요약
    print("\n" + "="*60)
    print("테스트 결과 요약")
    print("="*60)
    
    results = [
        ("주연급", main_char is not None),
        ("조연급", supporting_char is not None),
        ("단역", minor_char is not None)
    ]
    
    for tier, success in results:
        status = "✅ 성공" if success else "❌ 실패"
        print(f"{tier}: {status}")
    
    # 통계 시뮬레이션
    print("\n📊 예상 캐릭터 분포 (200화 기준):")
    print("  주연급: 3-5명 (핵심 인물)")
    print("  조연급: 8-12명 (중요 조연)")
    print("  단역: 15-25명 (기능적 역할)")
    print("\n이 분포는 스토리와 설정에 따라 조정 가능합니다.")


if __name__ == "__main__":
    main()