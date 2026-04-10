# 작업 기록 2026-04-10-1915-parent-stdin-fast-anchor

## 유형
feature expansion

## 요약
`/parent`와 `/parent-no-opus`가 stdin으로 현재 요청을 이미 받은 경우에는 transcript anchor를 빠르게 1회만 확인하고, 더 이상 긴 polling을 하지 않도록 바꿨다. 같은 요청에서도 체감 지연이 줄어든다.

## 배경
기존 구현은 stdin에 현재 slash-command 인자가 이미 있어도 session transcript에서 anchor를 찾기 위해 재시도 루프를 돌 수 있었다. transcript가 아직 기록되지 않았거나 anchor가 늦게 보이면 실제 사용자 요청은 이미 확보했는데도 `/parent`가 불필요하게 느려질 수 있었다.

## 변경 사항
- `scripts/parent.py`
  - session transcript를 한 번만 읽어서 현재 anchor index를 확인하는 helper를 추가했다.
  - stdin prompt가 이미 있을 때는 이 1회 확인만 수행하고, retry polling 경로는 사용하지 않도록 `load_request_text()`를 조정했다.
- `tests/test_parent_router.py`
  - stdin 경로 테스트를 새 helper 기준으로 갱신했다.
  - stdin prompt가 있을 때 기존 retry 기반 `extract_prompt_from_session()`이 호출되지 않는다는 회귀 테스트를 추가했다.

## 검증
- `python3 -m unittest discover -s tests -p 'test_parent_router.py' -v`
  - 결과: stdin anchor 경로를 포함한 router 테스트 통과.
- `python3 -m py_compile scripts/parent.py tests/test_parent_router.py`
  - 결과: 성공.
- `python3 - <<'PY' ... parent.py --session-id missing ... PY`
  - 결과: 빈 session store에서도 stdin으로 받은 요청이 즉시 처리되고, elapsed time이 polling 없이 짧게 유지되는 것을 확인했다.

## 다음 단계
다음에 바로 진행할 기능은 `/parent`가 current command anchor를 찾지 못해도 최근 transcript 일부를 안전하게 fallback context로 활용하도록 만들어 follow-up 맥락 보존을 더 잘하는 것이다.
