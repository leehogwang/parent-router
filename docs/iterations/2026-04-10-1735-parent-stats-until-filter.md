# 작업 기록 2026-04-10-1735-parent-stats-until-filter

## 유형
feature expansion

## 요약
`/parent-stats`와 `scripts/parent_stats.py`에 `--until YYYY-MM-DD` 필터를 추가했다. 이제 날짜 범위의 상한을 지정해 특정 시점 이전 로그까지만 집계할 수 있다.

## 배경
직전 반복에서 `--since`를 추가하면서 날짜 범위의 하한은 제어할 수 있게 됐지만, 상한은 여전히 없었다. `--until`은 같은 날짜 범위 기능을 대칭적으로 완성하는 가장 작은 확장이다.

## 변경 사항
- `scripts/parent_stats.py`
  - `--until YYYY-MM-DD` 인자를 추가했다.
  - 날짜 디렉터리 탐색이 upper bound 이전의 디렉터리만 포함하도록 확장했다.
  - text/json 출력의 filter 메타데이터에 until 정보를 포함했다.
- `tests/test_parent_stats.py`
  - stdin 파싱에 until이 반영되는지 검증을 추가했다.
  - 잘못된 until 값을 거부하는 검증을 추가했다.
  - until 필터가 더 새로운 날짜 디렉터리를 제외하는지 검증하는 테스트를 추가했다.
- `.claude/commands/parent-stats.md`, `scripts/install_global_commands.py`
  - 새 옵션이 argument hint에 드러나도록 갱신했다.
- `README.md`, `docs/parent-routing.md`
  - until 옵션과 사용 예시를 문서에 반영했다.

## 검증
- `python3 -m unittest discover -s tests -p 'test_parent_stats.py' -v`
  - 결과: until 필터를 포함한 stats 테스트 통과.
- `python3 -m py_compile scripts/parent_stats.py tests/test_parent_stats.py scripts/install_global_commands.py`
  - 결과: 성공.
- `python3 - <<'PY' ... parent_stats.py --until 2026-04-09 --summary-only --show-paths --sort newest --limit 1 ... PY`
  - 결과: 2026-04-10 로그는 제외되고 2026-04-09 로그만 집계에 포함되는 것을 확인했다.

## 다음 단계
다음에 바로 진행할 기능은 `/parent-stats`에 `--window 7d` 같은 상대 기간 필터를 추가해 최근 N일 범위를 더 쉽게 지정하는 것이다.
