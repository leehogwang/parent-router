# 작업 기록 2026-04-10-1645-parent-stats-fail-if-empty

## 유형
feature expansion

## 요약
`/parent-stats`와 `scripts/parent_stats.py`에 `--fail-if-empty` 플래그를 추가했다. 이제 자동화 스크립트가 빈 필터 결과를 성공으로 넘기지 않고 바로 실패로 처리할 수 있다.

## 배경
JSON/TSV 출력과 각종 필터가 추가되면서 `/parent-stats`는 자동화에 쓸 수 있는 도구가 되었지만, 결과가 비어 있을 때는 호출한 쪽에서 다시 조건 검사를 해야 했다. `--fail-if-empty`는 이런 조건부 스크립트 분기를 더 직접적으로 만든다.

## 변경 사항
- `scripts/parent_stats.py`
  - `--fail-if-empty` boolean 플래그를 추가했다.
  - 필터 결과가 비어 있으면 기존 출력은 유지하되 exit code 1을 반환하도록 `main()`을 확장했다.
  - JSON 출력의 `filters`에도 `fail_if_empty` 값을 포함시켰다.
- `tests/test_parent_stats.py`
  - stdin 파싱에 `--fail-if-empty`가 반영되는지 검증을 추가했다.
  - 빈 결과에서 exit code 1을 반환하는지 검증하는 테스트를 추가했다.
  - reasons-only JSON 출력의 filter 메타데이터 검증을 강화했다.
- `.claude/commands/parent-stats.md`, `scripts/install_global_commands.py`
  - 새 플래그가 argument hint에 드러나도록 갱신했다.
- `README.md`, `docs/parent-routing.md`
  - 새 옵션과 자동화용 사용 예시를 문서에 반영했다.

## 검증
- `python3 -m unittest discover -s tests -p 'test_parent_stats.py' -v`
  - 결과: fail-if-empty를 포함한 stats 테스트 통과.
- `python3 -m py_compile scripts/parent_stats.py tests/test_parent_stats.py scripts/install_global_commands.py`
  - 결과: 성공.
- `python3 - <<'PY' ... parent_stats.py --date 2026-04-10 --status failed --fail-if-empty ... PY`
  - 결과: `No run logs found.` 출력과 함께 exit code 1이 반환되는 것을 확인했다.
- `python3 - <<'PY' ... parent_stats.py --date 2026-04-10 --model opus --format json --limit 5 ... PY`
  - 결과: JSON filter 메타데이터에 `fail_if_empty`가 포함되는 것을 확인했다.

## 다음 단계
다음에 바로 진행할 기능은 `/parent-stats`에 `--summary-only`를 추가해 status/profile/model/mode/confidence/reason_codes 집계만 보고 최근 실행 목록은 숨기는 압축 요약 모드를 만드는 것이다.
