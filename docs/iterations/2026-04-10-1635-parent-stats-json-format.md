# 작업 기록 2026-04-10-1635-parent-stats-json-format

## 유형
feature expansion

## 요약
`/parent-stats`와 `scripts/parent_stats.py`에 `--format json` 출력 모드를 추가했다. 이제 필터된 실행 결과나 reason code 집계를 구조화된 JSON으로 바로 받아 외부 자동화에서 직접 파싱할 수 있다.

## 배경
TSV 출력은 스프레드시트 친화적이지만, 키 기반 자동화나 스크립트 연동에는 여전히 후처리가 필요했다. JSON 출력은 이미 있는 필터 체인과 reasons-only 요약을 그대로 재사용하면서 더 안정적인 자동화 인터페이스를 제공한다.

## 변경 사항
- `scripts/parent_stats.py`
  - `--format json` 인자를 추가했다.
  - JSON formatter를 추가해 기본 모드에서는 `records`, reasons-only 모드에서는 `reason_codes` 집계를 구조화해서 출력한다.
  - 출력에 선택된 filter 정보와 `runs_analyzed`를 포함했다.
- `tests/test_parent_stats.py`
  - stdin 파싱에 JSON format이 반영되는지 검증을 추가했다.
  - 일반 JSON 출력과 reasons-only JSON 출력이 모두 올바른 구조를 반환하는지 검증하는 테스트를 추가했다.
- `.claude/commands/parent-stats.md`, `scripts/install_global_commands.py`
  - 새 format 값이 argument hint에 드러나도록 갱신했다.
- `README.md`, `docs/parent-routing.md`
  - JSON 출력 모드와 사용 예시를 문서에 반영했다.

## 검증
- `python3 -m unittest discover -s tests -p 'test_parent_stats.py' -v`
  - 결과: JSON format을 포함한 stats 테스트 통과.
- `python3 -m py_compile scripts/parent_stats.py tests/test_parent_stats.py scripts/install_global_commands.py`
  - 결과: 성공.
- `python3 - <<'PY' ... parent_stats.py --date 2026-04-10 --model opus --format json --limit 5 ... PY`
  - 결과: 필터 정보, runs_analyzed, records 배열이 포함된 유효한 JSON이 출력되는 것을 확인했다.

## 다음 단계
다음에 바로 진행할 기능은 `/parent-stats`에 `--fail-if-empty`를 추가해 자동화 스크립트에서 조건부 실패를 쉽게 다루게 만드는 것이다.
