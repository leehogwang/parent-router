# 작업 기록 2026-04-10-2145-parent-dry-run-confidence

## 유형
feature expansion

## 요약
`/parent`와 `/parent-no-opus`의 `--dry-run` 응답에 route confidence를 명시적으로 추가했다. 사용자는 실행 전에 선택된 route에 대한 확신 정도를 더 빨리 파악할 수 있다.

## 배경
기존 dry-run은 설명 문장만 보여줘서, route confidence를 알고 싶으면 그 문장을 해석하거나 내부 로그를 열어야 했다. dry-run은 원래 라우팅 판단을 확인하려는 흐름이므로, confidence를 한 줄로 바로 보여주는 편이 훨씬 자연스럽다.

## 변경 사항
- `scripts/parent.py`
  - dry-run 전용 메시지 formatter를 추가했다.
  - dry-run 응답이 기존 설명 앞에 `Confidence: <level>` 한 줄을 먼저 출력하도록 조정했다.
- `tests/test_parent_router.py`
  - dry-run 응답에 confidence line이 포함되는지 검증하는 테스트를 추가했다.

## 검증
- `python3 -m unittest discover -s tests -p 'test_parent_router.py' -v`
  - 결과: dry-run confidence를 포함한 router 테스트 통과.
- `python3 -m py_compile scripts/parent.py tests/test_parent_router.py`
  - 결과: 성공.
- `python3 scripts/parent.py` with stdin `--dry-run rename one variable`
  - 결과: dry-run 출력 첫 부분에 `Confidence: high`가 표시되는 것을 확인했다.

## 다음 단계
다음에 바로 진행할 기능은 `/parent --dry-run --why`에서 confidence와 explanation 사이에 route summary 한 줄을 넣어 model/mode/effort를 더 빠르게 스캔하게 만드는 것이다.
