# 작업 기록 2026-04-10-1715-parent-stats-sort-control

## 유형
feature expansion

## 요약
`/parent-stats`와 `scripts/parent_stats.py`에 `--sort newest|oldest` 옵션을 추가했다. 이제 제한된 결과 집합이 최신 로그 우선인지 오래된 로그 우선인지 명시적으로 제어할 수 있다.

## 배경
기존 구현은 항상 최신 로그 우선으로만 동작해서, 과거의 특정 사례를 처음부터 순서대로 훑고 싶을 때는 직접 파일명을 정렬해서 추적해야 했다. sort 제어는 같은 필터 체인을 유지한 채 탐색 방향만 바꾸는 작지만 실용적인 확장이다.

## 변경 사항
- `scripts/parent_stats.py`
  - `--sort newest|oldest` 인자를 추가했다.
  - JSON 파일 탐색 정렬이 선택된 sort 방향을 따르도록 확장했다.
  - text/json 출력의 filter 메타데이터에 sort 정보를 포함했다.
- `tests/test_parent_stats.py`
  - stdin 파싱에 sort가 반영되는지 검증을 추가했다.
  - 잘못된 sort 값을 거부하는 검증을 추가했다.
  - `--sort oldest`가 실제로 오래된 로그를 먼저 선택하는지 검증하는 테스트를 추가했다.
- `.claude/commands/parent-stats.md`, `scripts/install_global_commands.py`
  - 새 옵션이 argument hint에 드러나도록 갱신했다.
- `README.md`, `docs/parent-routing.md`
  - sort 옵션과 사용 예시를 문서에 반영했다.

## 검증
- `python3 -m unittest discover -s tests -p 'test_parent_stats.py' -v`
  - 결과: sort 제어를 포함한 stats 테스트 통과.
- `python3 -m py_compile scripts/parent_stats.py tests/test_parent_stats.py scripts/install_global_commands.py`
  - 결과: 성공.
- `python3 - <<'PY' ... parent_stats.py --date 2026-04-10 --summary-only --show-paths --sort oldest --limit 1 ... PY`
  - 결과: 더 오래된 JSON 로그가 우선 선택되고, 그 경로가 `Included paths:`에 출력되는 것을 확인했다.

## 다음 단계
다음에 바로 진행할 기능은 `/parent-stats`에 `--after YYYY-MM-DD` 또는 `--since YYYY-MM-DD` 계열의 기간 필터를 추가해 날짜 범위를 더 유연하게 제어하는 것이다.
