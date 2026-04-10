# 작업 기록 2026-04-10-2015-parent-clamp-hints

## 유형
feature expansion

## 요약
`/parent`와 `/parent-no-opus`가 user-forced setting을 model/mode 제약 때문에 clamp했을 때, 성공 응답 앞에 짧은 전환 힌트를 추가했다. 사용자는 요청한 effort가 왜 그대로 반영되지 않았는지 더 쉽게 이해할 수 있다.

## 배경
기존 구현은 `--effort`를 강제로 준 경우에도 haiku나 plan/execute 제약 때문에 내부적으로 effort를 조정할 수 있었지만, 성공 응답에서는 그 사실이 거의 드러나지 않았다. 이건 사용자가 "내 설정이 무시됐나?"라고 느끼게 할 수 있는 UX 빈틈이었다.

## 변경 사항
- `scripts/parent.py`
  - user-forced effort가 model constraint 또는 mode constraint로 clamp된 경우를 설명하는 helper를 추가했다.
  - 일반 성공 응답에서 low-confidence fallback과 no-opus 전환 힌트보다 뒤 순위로, clamp 상황이면 child 출력 앞에 해당 안내를 붙이도록 `main()`을 조정했다.
- `tests/test_parent_router.py`
  - haiku model cap으로 `max -> medium` clamp가 발생할 때 힌트가 출력되는지 검증하는 테스트를 추가했다.
  - plan mode cap으로 `low -> high` clamp가 발생할 때 힌트가 출력되는지 검증하는 테스트를 추가했다.

## 검증
- `python3 -m unittest discover -s tests -p 'test_parent_router.py' -v`
  - 결과: clamp hint를 포함한 router 테스트 통과.
- `python3 -m py_compile scripts/parent.py tests/test_parent_router.py`
  - 결과: 성공.
- `python3 - <<'PY' ... parent.py with forced effort scenarios ... PY`
  - 결과: 성공 응답에 requested/effective effort 차이와 clamp 이유가 함께 포함되는 것을 확인했다.

## 다음 단계
다음에 바로 진행할 기능은 `/parent`가 user-forced mode/model/effort를 이미 설명 가능한 조합으로 넣었을 때, `--why` 없이도 너무 장황하지 않은 짧은 route explanation을 opt-in 없이 보여줄지 검토하는 것이다.
