# 작업 기록 2026-04-10-1725-parent-stats-since-filter

## 유형
feature expansion

## 요약
`/parent-stats`와 `scripts/parent_stats.py`에 `--since YYYY-MM-DD` 필터를 추가했다. 이제 단일 날짜나 전체 히스토리만이 아니라, 특정 날짜 이후의 로그 범위를 기준으로 집계를 시작할 수 있다.

## 배경
기존에는 `--date`로 하루를 고정하거나 전체 히스토리를 읽는 두 극단만 가능했다. `--since`는 최근 며칠 또는 특정 시점 이후의 로그를 빠르게 좁혀보는 데 필요한 가장 작은 날짜 범위 확장이다.

## 변경 사항
- `scripts/parent_stats.py`
  - `--since YYYY-MM-DD` 인자를 추가했다.
  - 날짜 디렉터리 탐색이 lower bound 이후의 디렉터리만 포함하도록 확장했다.
  - text/json 출력의 filter 메타데이터에 since 정보를 포함했다.
- `tests/test_parent_stats.py`
  - stdin 파싱에 since가 반영되는지 검증을 추가했다.
  - 잘못된 since 값을 거부하는 검증을 추가했다.
  - since 필터가 더 오래된 날짜 디렉터리를 제외하는지 검증하는 테스트를 추가했다.
- `.claude/commands/parent-stats.md`, `scripts/install_global_commands.py`
  - 새 옵션이 argument hint에 드러나도록 갱신했다.
- `README.md`, `docs/parent-routing.md`
  - since 옵션과 사용 예시를 문서에 반영했다.

## 검증
- `python3 -m unittest discover -s tests -p 'test_parent_stats.py' -v`
  - 결과: since 필터를 포함한 stats 테스트 통과.
- `python3 -m py_compile scripts/parent_stats.py tests/test_parent_stats.py scripts/install_global_commands.py`
  - 결과: 성공.
- `python3 - <<'PY' ... parent_stats.py --since 2026-04-10 --summary-only --show-paths --sort oldest --limit 1 ... PY`
  - 결과: 2026-04-09 로그는 제외되고 2026-04-10 이후 로그만 집계에 포함되는 것을 확인했다.

## 다음 단계
다음에 바로 진행할 기능은 `/parent-stats`에 `--until YYYY-MM-DD`를 추가해 날짜 범위의 상한도 제어할 수 있게 만드는 것이다.
