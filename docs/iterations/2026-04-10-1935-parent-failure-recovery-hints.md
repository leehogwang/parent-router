# 작업 기록 2026-04-10-1935-parent-failure-recovery-hints

## 유형
feature expansion

## 요약
`/parent`와 `/parent-no-opus`가 child 실행 실패 시 exit code와 stderr만 던지지 않고, 현재 라우팅 결정과 함께 다음 행동 힌트를 보여주도록 개선했다. 실패 이후 사용자가 바로 다음 선택을 하기 쉬워진다.

## 배경
기존 실패 메시지는 "실패했다"는 사실과 stderr만 전달해서, 사용자가 다음에 무엇을 해야 할지 직접 해석해야 했다. 특히 execute 경로와 plan 경로는 실패 이후의 좋은 다음 행동이 다르므로, 라우터가 그 차이를 간단히 안내하는 편이 실제 UX에 도움이 된다.

## 변경 사항
- `scripts/parent.py`
  - 라우팅 결정에 따라 서로 다른 recovery hint를 고르는 helper를 추가했다.
  - 실패 메시지에 selected model/mode/effective effort를 함께 포함하고, 이어서 다음 행동 힌트를 출력하도록 `format_failure()`를 확장했다.
- `tests/test_parent_router.py`
  - execute 실패 메시지가 `--mode plan` 재시도를 제안하는지 검증하는 테스트를 추가했다.
  - plan 실패 메시지가 `--dry-run --why` 재시도를 제안하는지 검증하는 테스트를 추가했다.

## 검증
- `python3 -m unittest discover -s tests -p 'test_parent_router.py' -v`
  - 결과: failure recovery hint를 포함한 router 테스트 통과.
- `python3 -m py_compile scripts/parent.py tests/test_parent_router.py`
  - 결과: 성공.
- `python3 - <<'PY' ... parent.py with failing child stub ... PY`
  - 결과: 실패 출력에 route 정보와 `Next step:` 제안이 함께 포함되는 것을 확인했다.

## 다음 단계
다음에 바로 진행할 기능은 `/parent`가 low-confidence safe fallback으로 plan 모드로 바뀐 경우, 성공 응답에도 짧은 transition hint를 추가해 왜 바로 실행 대신 계획을 받았는지 더 자연스럽게 느끼게 만드는 것이다.
