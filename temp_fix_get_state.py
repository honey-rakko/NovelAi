# 임시 스크립트: get_state_value를 state["key"]로 일괄 치환

import re

with open("nodes/stage1_nodes.py", "r", encoding="utf-8") as f:
    content = f.read()

# get_state_value(state, "key") -> state["key"] 패턴 치환
content = re.sub(
    r'get_state_value\(state, "([^"]+)"\)',
    r'state["\1"]',
    content
)

with open("nodes/stage1_nodes.py", "w", encoding="utf-8") as f:
    f.write(content)

print("✓ 모든 get_state_value를 state['key'] 방식으로 변경완료!")
