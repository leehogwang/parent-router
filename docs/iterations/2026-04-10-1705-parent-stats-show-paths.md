# 작업 기록 2026-04-10-1705-parent-stats-show-paths

## 유형
feature expansion

## 요약
`/parent-stats`와 `scripts/parent_stats.py`에 `--show-paths` 플래그를 추가했다. 이제 현재 필터 결과가 어떤 `.parent/runs/...json` 파일들로부터 만들어졌는지 바로 확인할 수 있다.

## 배경
지금까지 `/parent-stats`는 요약과 export는 잘 해줬지만, 실제로 어떤 로그 파일이 집계에 포함됐는지는 별도로 파일 시스템을 살펴봐야 했다. `--show-paths`는 결과의 근거가 되는 원본 로그 경로를 직접 드러내는 작은 관측 기능 확장이다.

## 변경 사항
- `scripts/parent_stats.py`
  - `--show-paths` boolean 플래그를 추가했다.
  - 로드된 각 record에 source path를 붙이고, text/summary/reasons-only 출력에서 `Included paths:` 블록으로 노출하도록 확장했다.
  - JSON output의 record에도 `source_path`를 포함하고 filter 메타데이터에 `show_paths`를 추가했다.
- `tests/test_parent_stats.py`
  - stdin 파싱에 `--show-paths`가 반영되는지 검증을 추가했다.
  - summary-only 출력에 included path가 나타나는지 검증하는 테스트를 추가했다.
  - 로드된 레코드의 source path가 실제 출력에 반영되는지 검증을 추가했다.
- `.claude/commands/parent-stats.md`, `scripts/install_global_commands.py`
  - 새 플래그가 argument hint에 드러나도록 갱신했다.
- `README.md`, `docs/parent-routing.md`
  - 새 옵션과 사용 예시를 문서에 반영했다.

## 검증
- `python3 -m unittest discover -s tests -p 'test_parent_stats.py' -v`
  - 결과: show-paths를 포함한 stats 테스트 통과.
- `python3 -m py_compile scripts/parent_stats.py tests/test_parent_stats.py scripts/install_global_commands.py`
  - 결과: 성공.
- `python3 - <<'PY' ... parent_stats.py --date 2026-04-10 --summary-only --show-paths --limit 5 ... PY`
  - 결과: 집계 카운터와 함께 `Included paths:` 블록이 출력되고 포함된 JSON 경로가 표시되는 것을 확인했다.

## 다음 단계
다음에 바로 진행할 기능은 `/parent-stats`에 `--sort newest|oldest`를 추가해 최근 로그와 오래된 로그 우선 탐색을 명시적으로 제어하는 것이다.
