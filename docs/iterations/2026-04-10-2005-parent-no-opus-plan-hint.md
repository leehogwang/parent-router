# 작업 기록 2026-04-10-2005-parent-no-opus-plan-hint

## 유형
feature expansion

## 요약
`/parent-no-opus`가 broad/high-risk 요청을 Sonnet plan으로 낮췄을 때, 성공 응답 앞에 짧은 전환 힌트를 추가했다. 사용자는 비용 제약 때문에 어떤 타협이 일어났는지 더 자연스럽게 이해할 수 있다.

## 배경
기존에는 `/parent-no-opus`가 Opus-class 요청을 Sonnet plan으로 처리해도, 사용자 입장에서는 왜 바로 실행이나 더 강한 모델이 아닌지 직접 추론해야 했다. 이 제약은 command의 핵심 UX 차이이므로 성공 응답에서 짧게 드러내는 편이 더 친절하다.

## 변경 사항
- `scripts/parent.py`
  - `/parent-no-opus`에서 `PROFILE_NO_OPUS` 이유 코드가 붙은 plan 성공 응답일 때 전환 힌트를 만드는 helper를 추가했다.
  - `--why`가 없는 일반 성공 응답에서 low-confidence fallback이 아닌 경우, 이 no-opus 전환 힌트를 child 출력 앞에 붙이도록 `main()`을 조정했다.
- `tests/test_parent_router.py`
  - `/parent-no-opus` broad-task 성공 경로에서 전환 힌트와 child 출력이 함께 노출되는지 검증하는 테스트를 추가했다.

## 검증
- `python3 -m unittest discover -s tests -p 'test_parent_router.py' -v`
  - 결과: `/parent-no-opus` 전환 힌트를 포함한 router 테스트 통과.
- `python3 -m py_compile scripts/parent.py tests/test_parent_router.py`
  - 결과: 성공.
- `python3 - <<'PY' ... parent.py for /parent-no-opus with stub child ... PY`
  - 결과: 성공 응답에 Sonnet plan 전환 힌트와 실제 child 출력이 함께 포함되는 것을 확인했다.

## 다음 단계
다음에 바로 진행할 기능은 `/parent`가 user-forced model/mode/effort 조합으로 clamping이 일어났을 때, 성공 응답에서 그 제약을 짧게 알려주는 것이다.
