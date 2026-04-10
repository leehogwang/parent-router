# 작업 기록 2026-04-10-1955-parent-capture-guidance

## 유형
feature expansion

## 요약
`/parent`와 `/parent-no-opus`가 현재 command arguments를 캡처하지 못했을 때, 단순 실패 문구 대신 바로 재시도할 수 있는 구체적인 입력 예시를 함께 보여주도록 개선했다.

## 배경
기존 메시지는 "캡처하지 못했다"는 사실만 알려줘서 사용자가 다음에 어떤 형태로 다시 입력해야 하는지 추측해야 했다. 입력 캡처는 core entry path이므로, 실패 시에도 바로 복구 가능한 안내를 주는 편이 실제 UX에 더 도움이 된다.

## 변경 사항
- `scripts/parent.py`
  - command name을 반영한 capture failure helper를 추가했다.
  - request capture가 비어 있을 때 command-specific retry example을 포함한 메시지를 반환하도록 `main()`을 조정했다.
- `tests/test_parent_router.py`
  - 빈 stdin과 session-less 경로에서 concrete retry guidance가 출력되는 회귀 테스트를 추가했다.

## 검증
- `python3 -m unittest discover -s tests -p 'test_parent_router.py' -v`
  - 결과: capture guidance를 포함한 router 테스트 통과.
- `python3 -m py_compile scripts/parent.py tests/test_parent_router.py`
  - 결과: 성공.
- `python3 scripts/parent.py` with empty stdin
  - 결과: 단순 오류 대신 `/parent fix the flaky integration test` 형태의 재시도 예시가 함께 출력되는 것을 확인했다.

## 다음 단계
다음에 바로 진행할 기능은 `/parent-no-opus`가 high-risk broad task를 sonnet plan으로 낮출 때, 비용 제약 때문에 그렇게 조정됐다는 짧은 성공 힌트를 더 자연스럽게 보여주는 것이다.
