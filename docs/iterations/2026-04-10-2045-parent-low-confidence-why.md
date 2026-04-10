# 작업 기록 2026-04-10-2045-parent-low-confidence-why

## 유형
feature expansion

## 요약
`/parent`가 low-confidence safe fallback으로 plan 모드에 들어간 경우, `--dry-run`과 `--why`에서도 그 이유를 더 직접적으로 설명하도록 개선했다.

## 배경
실행 성공 경로에는 이미 전환 힌트를 추가했지만, 사용자가 실행 전에 판단하려고 `--dry-run`이나 `--why`를 쓰는 경우에는 설명이 여전히 일반적일 수 있었다. 이 경우야말로 왜 execute 대신 plan이 선택됐는지 더 명확히 알려주는 것이 핵심 UX다.

## 변경 사항
- `scripts/parent.py`
  - `LOW_CONFIDENCE_SAFE_FALLBACK`가 포함된 route decision이면 `explain_decision()`이 broad/ambiguous risk 때문에 direct execution을 피했다고 더 직접적으로 설명하도록 조정했다.
- `tests/test_parent_router.py`
  - low-confidence fallback 설명 문구가 실제로 강화됐는지 검증하는 테스트를 추가했다.

## 검증
- `python3 -m unittest discover -s tests -p 'test_parent_router.py' -v`
  - 결과: low-confidence explanation을 포함한 router 테스트 통과.
- `python3 -m py_compile scripts/parent.py tests/test_parent_router.py`
  - 결과: 성공.
- `python3 scripts/parent.py` with stdin `--dry-run Help me improve the whole system somehow`
  - 결과: execute 대신 plan을 택한 이유가 broad/ambiguous risk라는 문구로 직접 설명되는 것을 확인했다.

## 다음 단계
다음에 바로 진행할 기능은 `/parent`가 `--why`를 켠 execute 경로에서도 reason code를 그대로 노출하지 않으면서 더 구체적인 plain-English justification을 주는 것이다.
