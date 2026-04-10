# 작업 기록 2026-04-10-2115-parent-empty-success-message

## 유형
feature expansion

## 요약
`/parent`와 `/parent-no-opus`가 child 실행은 성공했지만 visible stdout이 비어 있을 때, 빈 응답 대신 짧은 성공 확인 문구를 출력하도록 개선했다.

## 배경
기존 구현은 exit code 0이어도 child stdout이 비면 사용자에게 사실상 빈 응답이 보일 수 있었다. 사용자는 성공인지 실패인지 헷갈릴 수 있으므로, 이 경우에는 최소한의 확인 문구를 주는 편이 핵심 UX에 더 적합하다.

## 변경 사항
- `scripts/parent.py`
  - child stdout이 비어 있는 성공 경로에서 출력할 기본 확인 문구 helper를 추가했다.
  - 성공 출력이 완전히 비는 경우, 그 helper 메시지를 대신 출력하도록 `main()`을 조정했다.
- `tests/test_parent_router.py`
  - child stdout이 빈 성공 경로에서 확인 문구가 실제로 출력되는지 검증하는 테스트를 추가했다.

## 검증
- `python3 -m unittest discover -s tests -p 'test_parent_router.py' -v`
  - 결과: empty-success confirmation을 포함한 router 테스트 통과.
- `python3 -m py_compile scripts/parent.py tests/test_parent_router.py`
  - 결과: 성공.
- `python3 - <<'PY' ... parent.py with child stdout empty and exit 0 ... PY`
  - 결과: 빈 출력 대신 성공 확인 문구가 출력되는 것을 확인했다.

## 다음 단계
다음에 바로 진행할 기능은 `/parent`가 dry-run에서도 현재 route confidence를 더 직관적으로 짧은 문구로 보여주는 것이다.
