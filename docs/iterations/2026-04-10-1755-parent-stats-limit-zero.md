# 작업 기록 2026-04-10-1755-parent-stats-limit-zero

## 유형
feature expansion

## 요약
`/parent-stats`가 이제 `--limit 0`을 “전체 결과” 의미로 받아들인다. 더 이상 충분히 큰 수를 임의로 고르지 않아도 전체 필터 결과를 명시적으로 요청할 수 있다.

## 배경
지금까지는 전체 결과가 필요할 때 사용자가 적당히 큰 `--limit` 값을 골라야 했다. `--limit 0`은 의도를 더 명확히 표현하고, 자동화 스크립트에서도 “모든 결과”를 안전하게 요청하게 해준다.

## 변경 사항
- `scripts/parent_stats.py`
  - `--limit` 검증을 조정해 0을 허용하도록 변경했다.
  - record 로더가 `limit == 0`일 때는 truncation 없이 모든 매칭 결과를 유지하도록 확장했다.
- `tests/test_parent_stats.py`
  - 음수 limit만 거부하도록 검증을 갱신했다.
  - `limit=0`일 때 모든 매칭 레코드가 유지되는지 검증하는 테스트를 추가했다.
- `.claude/commands/parent-stats.md`, `scripts/install_global_commands.py`
  - argument hint에서 `--limit N|0` 형태로 반영했다.
- `README.md`, `docs/parent-routing.md`
  - 전체 결과 모드와 사용 예시를 문서에 반영했다.

## 검증
- `python3 -m unittest discover -s tests -p 'test_parent_stats.py' -v`
  - 결과: limit 0을 포함한 stats 테스트 통과.
- `python3 -m py_compile scripts/parent_stats.py tests/test_parent_stats.py scripts/install_global_commands.py`
  - 결과: 성공.
- `python3 - <<'PY' ... parent_stats.py --window 7d --summary-only --show-paths --sort oldest --limit 0 ... PY`
  - 결과: 매칭되는 여러 로그가 모두 집계에 남고 truncation 없이 출력되는 것을 확인했다.

## 다음 단계
다음에 바로 진행할 기능은 `/parent-stats`에 `--count-only`를 추가해 수치 집계만 빠르게 출력하는 더욱 축약된 경로를 만드는 것이다.
