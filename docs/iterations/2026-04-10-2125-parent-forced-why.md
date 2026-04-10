# 작업 기록 2026-04-10-2125-parent-forced-why

## 유형
feature expansion

## 요약
`/parent`와 `/parent-no-opus`가 user-forced model/mode/effort를 받은 경우, `--why`와 `--dry-run` 설명도 그 override를 직접 언급하도록 개선했다.

## 배경
직전 반복으로 일반 성공 경로에는 forced-route hint가 추가됐지만, 정작 설명이 중요한 `--why`/`--dry-run` 경로에서는 여전히 더 일반적인 문장이 나올 수 있었다. 사용자가 override를 명시했다면, 설명 경로에서도 그 사실이 바로 드러나야 UX가 일관된다.

## 변경 사항
- `scripts/parent.py`
  - `explain_decision()`이 explicit model/mode/effort를 먼저 감지하고, 있으면 그 override를 직접 언급하는 문장을 반환하도록 조정했다.
- `tests/test_parent_router.py`
  - forced override 설명 문구 자체를 검증하는 테스트를 추가했다.
  - `--why` 성공 경로에서 forced-route explanation이 실제 child 출력 앞에 붙는지 검증하는 테스트를 추가했다.

## 검증
- `python3 -m unittest discover -s tests -p 'test_parent_router.py' -v`
  - 결과: forced override explanation을 포함한 router 테스트 통과.
- `python3 -m py_compile scripts/parent.py tests/test_parent_router.py`
  - 결과: 성공.
- `python3 - <<'PY' ... parent.py with stdin `--why --model sonnet --mode execute ...` ... PY`
  - 결과: `I’m following your requested model sonnet, mode execute.` 문구와 child 출력이 함께 포함되는 것을 확인했다.

## 다음 단계
다음에 바로 진행할 기능은 `/parent`가 `--why` 없이도 명시적 `--effort` override가 실제로 clamp되지 않았음을 짧게 보여줄지 검토하는 것이다.
