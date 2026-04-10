# 작업 기록 2026-04-10-2025-parent-invalid-flag-guidance

## 유형
feature expansion

## 요약
`/parent`와 `/parent-no-opus`가 잘못된 explicit model/mode 조합을 받았을 때, 단순 거절 대신 바로 고칠 수 있는 구체적인 재시도 힌트를 보여주도록 개선했다.

## 배경
기존 오류 메시지는 어떤 값이 안 되는지만 알려주고, 사용자가 어떤 조합으로 다시 시도해야 하는지는 직접 추측하게 했다. 명시적 override는 사용자가 의도를 강하게 표현한 경우이므로, 실패 시에도 복구 경로를 곧바로 주는 편이 핵심 UX에 더 맞다.

## 변경 사항
- `scripts/parent.py`
  - `/parent-no-opus --model opus ...` 오류 메시지에 `/parent --model opus ...` 재시도 예시를 추가했다.
  - `--model haiku --mode plan ...` 오류 메시지에 `--model sonnet`, `--model opus`, 또는 `--mode execute`로의 구체적인 복구 옵션을 추가했다.
- `tests/test_parent_router.py`
  - no-opus Opus 거절 메시지에 재시도 예시가 포함되는지 검증하는 테스트를 추가했다.
  - haiku+plan 오류가 구체적인 복구 조합을 안내하는지 검증하는 테스트를 추가했다.

## 검증
- `python3 -m unittest discover -s tests -p 'test_parent_router.py' -v`
  - 결과: invalid flag guidance를 포함한 router 테스트 통과.
- `python3 -m py_compile scripts/parent.py tests/test_parent_router.py`
  - 결과: 성공.
- `python3 scripts/parent.py` with `--command-name /parent-no-opus` and stdin `--model opus implement the task`
  - 결과: `/parent --model opus ...` 재시도 예시가 포함된 오류를 확인했다.
- `python3 scripts/parent.py` with stdin `--model haiku --mode plan design an auth migration`
  - 결과: sonnet/opus/execute 대안이 포함된 오류를 확인했다.

## 다음 단계
다음에 바로 진행할 기능은 `/parent`가 user-forced model/mode/effort를 이미 설명 가능한 조합으로 넣었을 때, `--why` 없이도 너무 장황하지 않은 짧은 route explanation을 opt-in 없이 보여줄지 검토하는 것이다.
