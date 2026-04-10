# 작업 기록 2026-04-10-1925-parent-fallback-context

## 유형
feature expansion

## 요약
`/parent`와 `/parent-no-opus`가 현재 command anchor를 아직 찾지 못해도 session transcript가 있으면 최근 대화 맥락을 fallback으로 유지하도록 개선했다. follow-up 요청에서 맥락이 비는 상황이 줄어든다.

## 배경
직전 반복으로 stdin 경로의 불필요한 polling은 제거됐지만, 그 결과 current anchor가 아직 기록되지 않은 타이밍에서는 최근 대화가 통째로 빠질 수 있었다. 사용자는 같은 흐름의 후속 요청인데도 맥락이 비어 있는 답을 받을 수 있으므로, 이 fallback은 실제 체감 품질에 직접 연결된다.

## 변경 사항
- `scripts/parent.py`
  - `build_recent_context()`가 session transcript는 존재하지만 current anchor가 없는 경우, transcript의 최신 visible 블록을 fallback anchor로 사용하도록 확장했다.
  - session transcript 자체가 없을 때만 빈 맥락을 유지한다.
- `tests/test_parent_router.py`
  - anchor가 `-1`이어도 최신 transcript 블록이 recent context로 유지되는 회귀 테스트를 추가했다.

## 검증
- `python3 -m unittest discover -s tests -p 'test_parent_router.py' -v`
  - 결과: fallback recent context 경로를 포함한 router 테스트 통과.
- `python3 -m py_compile scripts/parent.py tests/test_parent_router.py`
  - 결과: 성공.
- `python3 - <<'PY' ... parent.py with captured child prompt ... PY`
  - 결과: 현재 anchor가 없어도 child prompt 안에 이전 user/assistant 대화가 포함되는 것을 확인했다.

## 다음 단계
다음에 바로 진행할 기능은 `/parent`가 child 실행 실패 시 원래 라우팅 결정과 함께 간단한 recovery next step을 제안하도록 만들어 사용자가 다음 행동을 더 쉽게 선택하게 하는 것이다.
