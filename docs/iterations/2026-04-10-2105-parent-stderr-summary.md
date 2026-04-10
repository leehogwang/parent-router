# 작업 기록 2026-04-10-2105-parent-stderr-summary

## 유형
feature expansion

## 요약
`/parent`와 `/parent-no-opus`가 child 실행 실패를 보여줄 때, stderr 전체 앞에 핵심 한 줄 요약을 먼저 보여주도록 개선했다. 사용자는 긴 실패 출력에서도 원인을 더 빨리 파악할 수 있다.

## 배경
기존 failure 출력은 route 정보 뒤에 stderr를 그대로 붙여서, stderr가 길거나 여러 줄이면 핵심 원인을 빠르게 읽기 어려울 수 있었다. 첫 줄 기준의 짧은 summary를 앞에 두면 읽기 순서가 훨씬 자연스러워진다.

## 변경 사항
- `scripts/parent.py`
  - stderr 첫 줄을 요약하는 helper를 추가했다.
  - `format_failure()`가 route 정보 뒤에 `Failure summary:` 라인을 먼저 출력하고, 그 다음 기존 stderr excerpt와 recovery hint를 이어붙이도록 조정했다.
- `tests/test_parent_router.py`
  - 다중 줄 stderr가 있을 때 첫 줄 요약과 상세 stderr가 함께 출력되는지 검증하는 테스트를 추가했다.

## 검증
- `python3 -m unittest discover -s tests -p 'test_parent_router.py' -v`
  - 결과: stderr summary를 포함한 router 테스트 통과.
- `python3 -m py_compile scripts/parent.py tests/test_parent_router.py`
  - 결과: 성공.
- `python3 - <<'PY' ... parent.py with failing child stub emitting multiple stderr lines ... PY`
  - 결과: failure 출력에 `Failure summary:` 첫 줄 요약과 원본 stderr excerpt가 함께 포함되는 것을 확인했다.

## 다음 단계
다음에 바로 진행할 기능은 `/parent`가 child stdout이 완전히 비어 있을 때도 성공으로 끝났다는 짧은 확인 문구를 출력해 사용자 혼란을 줄이는 것이다.
