# 작업 기록 2026-04-10-1745-parent-stats-window-filter

## 유형
feature expansion

## 요약
`/parent-stats`와 `scripts/parent_stats.py`에 `--window Nd` 필터를 추가했다. 이제 최근 N일 범위를 지정할 때 직접 `--since` 날짜를 계산하지 않아도 된다.

## 배경
`--since`와 `--until`이 추가되면서 날짜 범위 제어는 가능해졌지만, 자주 쓰이는 “최근 7일” 같은 질의는 여전히 사용자가 날짜를 직접 계산해야 했다. `--window Nd`는 그 반복을 없애는 가장 작은 상대 기간 확장이다.

## 변경 사항
- `scripts/parent_stats.py`
  - `--window Nd` 인자를 추가했다.
  - `7d` 같은 값을 현재 날짜 기준 lower bound로 변환하는 helper를 추가했다.
  - 날짜 디렉터리 탐색이 `--window`를 통해 계산된 lower bound를 반영하도록 확장했다.
  - text/json 출력의 filter 메타데이터에 window 정보를 포함했다.
- `tests/test_parent_stats.py`
  - stdin 파싱에 window가 반영되는지 검증을 추가했다.
  - 잘못된 window 형식을 거부하는 검증을 추가했다.
  - 현재 날짜를 고정한 상태에서 window 밖의 더 오래된 디렉터리가 제외되는지 검증하는 테스트를 추가했다.
- `.claude/commands/parent-stats.md`, `scripts/install_global_commands.py`
  - 새 옵션이 argument hint에 드러나도록 갱신했다.
- `README.md`, `docs/parent-routing.md`
  - window 옵션과 사용 예시를 문서에 반영했다.

## 검증
- `python3 -m unittest discover -s tests -p 'test_parent_stats.py' -v`
  - 결과: window 필터를 포함한 stats 테스트 통과.
- `python3 -m py_compile scripts/parent_stats.py tests/test_parent_stats.py scripts/install_global_commands.py`
  - 결과: 성공.
- `python3 - <<'PY' ... parent_stats.py --window 2d --summary-only --show-paths --sort oldest --limit 1 ... PY`
  - 결과: 현재 날짜 기준 window 밖인 오래된 디렉터리는 제외되고, 최근 2일 범위의 로그만 집계에 포함되는 것을 확인했다.

## 다음 단계
다음에 바로 진행할 기능은 `/parent-stats`에 `--limit 0`을 허용해 “전체 결과” 모드를 명시적으로 지원하는 것이다.
