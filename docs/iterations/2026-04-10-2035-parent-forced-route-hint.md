# 작업 기록 2026-04-10-2035-parent-forced-route-hint

## 유형
feature expansion

## 요약
`/parent`와 `/parent-no-opus`가 user-forced model/mode/effort를 그대로 반영한 경우, `--why` 없이도 짧은 성공 힌트로 그 선택을 알려주도록 개선했다.

## 배경
기존에는 사용자가 명시적으로 `--model`, `--mode`, `--effort`를 줘도 성공 응답에서는 child 출력만 보여주기 때문에, 라우터가 정말 그 override를 존중했는지 한 번 더 확인하고 싶어질 수 있었다. 이건 이미 사용자가 의도를 명확히 표현한 상황이므로, 짧은 확인 문구를 붙여주는 것이 자연스럽다.

## 변경 사항
- `scripts/parent.py`
  - explicit model/mode/effort가 있는 경우에만 짧은 forced-route hint를 만드는 helper를 추가했다.
  - `--why`, low-confidence fallback, no-opus downgrade, clamp hint보다 낮은 우선순위로 이 forced-route hint를 일반 성공 응답 앞에 붙이도록 `main()`을 조정했다.
- `tests/test_parent_router.py`
  - explicit `--model sonnet --mode execute` 성공 경로에서 forced-route hint와 child 출력이 함께 노출되는지 검증하는 테스트를 추가했다.

## 검증
- `python3 -m unittest discover -s tests -p 'test_parent_router.py' -v`
  - 결과: forced-route hint를 포함한 router 테스트 통과.
- `python3 -m py_compile scripts/parent.py tests/test_parent_router.py`
  - 결과: 성공.
- `python3 - <<'PY' ... parent.py with stdin `--model sonnet --mode execute ...` ... PY`
  - 결과: 성공 응답에 `Using your requested model sonnet, mode execute.` 문구와 child 출력이 함께 포함되는 것을 확인했다.

## 다음 단계
다음에 바로 진행할 기능은 `/parent`가 explicit `--effort`만 강제된 경우에도 current clamp/no-clamp 상태를 더 짧고 일관되게 보여주도록 success hint 문구를 다듬는 것이다.
