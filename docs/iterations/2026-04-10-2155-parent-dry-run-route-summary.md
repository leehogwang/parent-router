# 작업 기록 2026-04-10-2155-parent-dry-run-route-summary

## 유형
feature expansion

## 요약
`/parent`와 `/parent-no-opus`의 dry-run 응답에 `model/mode/effort`를 한 줄로 요약한 route summary를 추가했다. 사용자는 설명 문장을 읽기 전에 핵심 route를 더 빨리 스캔할 수 있다.

## 배경
직전 반복에서 dry-run confidence는 드러나게 됐지만, 실제 route 구성(model/mode/effort)은 여전히 설명 문장 속에 섞여 있었다. dry-run은 route 확인 자체가 목적이므로, 핵심 구성을 한 줄로 먼저 보여주는 편이 더 직관적이다.

## 변경 사항
- `scripts/parent.py`
  - dry-run formatter가 `Route: model/mode/effort` 한 줄을 confidence line 앞에 먼저 출력하도록 조정했다.
- `tests/test_parent_router.py`
  - dry-run 응답에 새 route summary line이 포함되는지 검증하는 테스트를 갱신했다.

## 검증
- `python3 -m unittest discover -s tests -p 'test_parent_router.py' -v`
  - 결과: dry-run route summary를 포함한 router 테스트 통과.
- `python3 -m py_compile scripts/parent.py tests/test_parent_router.py`
  - 결과: 성공.
- `python3 scripts/parent.py` with stdin `--dry-run rename one variable`
  - 결과: dry-run 출력 상단에 `Route: haiku/execute/low`와 `Confidence: high`가 함께 표시되는 것을 확인했다.

## 다음 단계
다음에 바로 진행할 기능은 `/parent-no-opus` dry-run도 같은 route summary 형식을 유지하는지 별도 회귀 테스트로 고정하는 것이다.
