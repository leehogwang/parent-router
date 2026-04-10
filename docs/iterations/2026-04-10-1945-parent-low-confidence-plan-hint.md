# 작업 기록 2026-04-10-1945-parent-low-confidence-plan-hint

## 유형
feature expansion

## 요약
`/parent`가 low-confidence safe fallback으로 plan 모드에 들어간 경우, 성공 응답 앞에 짧은 전환 힌트를 추가했다. 사용자는 왜 바로 실행 대신 계획을 받았는지 더 자연스럽게 이해할 수 있다.

## 배경
기존 구현은 low-confidence safe fallback으로 내부적으로 plan 모드로 바꿔도, 성공 응답 자체는 그 이유를 거의 드러내지 않았다. 사용자는 실행을 기대했는데 계획이 돌아오면 이유를 추측해야 했고, 이는 체감 UX를 흐릴 수 있었다.

## 변경 사항
- `scripts/parent.py`
  - `LOW_CONFIDENCE_SAFE_FALLBACK`가 선택된 경우에만 짧은 전환 설명을 만드는 helper를 추가했다.
  - 일반 성공 응답에서 `--why`가 없는 경우에도, 해당 fallback 상황이면 child 출력 앞에 전환 힌트를 붙이도록 `main()`을 조정했다.
- `tests/test_parent_router.py`
  - low-confidence fallback 성공 경로에서 전환 힌트와 child 출력이 함께 노출되는지 검증하는 테스트를 추가했다.

## 검증
- `python3 -m unittest discover -s tests -p 'test_parent_router.py' -v`
  - 결과: low-confidence 전환 힌트를 포함한 router 테스트 통과.
- `python3 -m py_compile scripts/parent.py tests/test_parent_router.py`
  - 결과: 성공.
- `python3 - <<'PY' ... parent.py with stub child plan output ... PY`
  - 결과: 성공 응답에 "I started with a plan..." 전환 힌트와 실제 child 출력이 함께 포함되는 것을 확인했다.

## 다음 단계
다음에 바로 진행할 기능은 `/parent`가 current command arguments를 캡처하지 못했을 때, 사용자가 바로 고칠 수 있는 입력 예시를 포함한 더 구체적인 안내를 보여주는 것이다.
