# 작업 기록 2026-04-10-2135-parent-recursion-recovery

## 유형
feature expansion

## 요약
`/parent`와 `/parent-no-opus`가 nested invocation을 막았을 때, 일반 재시도 힌트 대신 현재 Claude turn에서 직접 이어서 작업하라는 구체적인 recovery 안내를 보여주도록 개선했다.

## 배경
기존 recursion block은 실제로는 route 재시도 문제가 아니라 사용 방식 문제인데도, 일반 failure recovery 흐름 안에 묻혀 있었다. 이 경우에는 사용자가 현재 turn에서 바로 계속하면 되므로, recovery 안내도 그 상황에 맞게 달라져야 한다.

## 변경 사항
- `scripts/parent.py`
  - recursion block stderr를 식별하는 helper를 추가했다.
  - `format_failure()`가 recursion block일 때는 일반 recovery보다 현재 Claude turn에서 직접 이어서 하라는 안내를 우선 출력하도록 조정했다.
- `tests/test_parent_router.py`
  - recursion block failure가 전용 recovery hint를 출력하는지 검증하는 테스트를 추가했다.

## 검증
- `python3 -m unittest discover -s tests -p 'test_parent_router.py' -v`
  - 결과: recursive-invocation recovery hint를 포함한 router 테스트 통과.
- `python3 -m py_compile scripts/parent.py tests/test_parent_router.py`
  - 결과: 성공.
- `python3 - <<'PY' ... parent.format_failure(...) with recursive block stderr ... PY`
  - 결과: 현재 Claude turn에서 직접 이어서 작업하라는 recovery 문구가 포함되는 것을 확인했다.

## 다음 단계
다음에 바로 진행할 기능은 `/parent`가 dry-run 출력에서도 selected model/mode/effort를 더 구조적으로 한 줄에 보여줘 사용자가 route를 더 빨리 스캔하게 만드는 것이다.
