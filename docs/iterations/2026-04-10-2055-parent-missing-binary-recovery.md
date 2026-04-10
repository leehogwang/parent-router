# 작업 기록 2026-04-10-2055-parent-missing-binary-recovery

## 유형
feature expansion

## 요약
`/parent`와 `/parent-no-opus`가 child Claude binary 자체를 실행하지 못했을 때, 일반 실패 힌트 대신 Claude CLI 설치와 `PARENTS_CLAUDE_BIN` 확인을 직접 안내하도록 개선했다.

## 배경
기존 failure recovery는 실행 실패 전체를 plan/dry-run 재시도 쪽으로만 안내했지만, binary가 아예 없거나 실행 불가능한 경우에는 그 조언이 핵심 문제를 해결하지 못한다. 이 경우에는 사용자가 먼저 설치/경로 문제를 바로 고칠 수 있어야 한다.

## 변경 사항
- `scripts/parent.py`
  - exit code `127`을 child launch failure로 보고, Claude CLI 설치 또는 `PARENTS_CLAUDE_BIN` 경로 확인을 안내하는 전용 recovery hint를 추가했다.
  - 일반 failure recovery보다 이 launch-failure hint를 우선 적용하도록 `format_failure()`를 조정했다.
- `tests/test_parent_router.py`
  - missing binary 상황에서 failure message가 `PARENTS_CLAUDE_BIN`과 Claude CLI 설치 확인을 직접 안내하는지 검증하는 테스트를 추가했다.

## 검증
- `python3 -m unittest discover -s tests -p 'test_parent_router.py' -v`
  - 결과: missing-binary recovery hint를 포함한 router 테스트 통과.
- `python3 -m py_compile scripts/parent.py tests/test_parent_router.py`
  - 결과: 성공.
- `python3 scripts/parent.py` with invalid `PARENTS_CLAUDE_BIN`
  - 결과: route 정보와 함께 Claude CLI 설치 / `PARENTS_CLAUDE_BIN` 확인 안내가 출력되는 것을 확인했다.

## 다음 단계
다음에 바로 진행할 기능은 `/parent`가 child stderr를 너무 길게 돌려줄 때 핵심 한 줄 요약을 먼저 보여주도록 만들어 실패 출력의 가독성을 더 높이는 것이다.
