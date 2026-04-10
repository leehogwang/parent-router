# 작업 기록 2026-04-10-1655-parent-stats-summary-only

## 유형
feature expansion

## 요약
`/parent-stats`와 `scripts/parent_stats.py`에 `--summary-only` 플래그를 추가했다. 이제 사람 친화적인 text 모드에서도 최근 실행 목록 없이 집계 카운터만 빠르게 볼 수 있다.

## 배경
`--reasons-only`는 reason code 중심 분석에는 좋지만, status/profile/model/mode/confidence 카운터까지 함께 보고 싶을 때는 너무 좁았다. 반대로 기본 text 모드는 최근 실행 목록까지 포함해서 짧게 훑기에는 길 수 있었다. `--summary-only`는 이 둘 사이의 빠른 요약 경로다.

## 변경 사항
- `scripts/parent_stats.py`
  - `--summary-only` boolean 플래그를 추가했다.
  - text 모드에서 이 플래그가 켜지면 aggregate counters까지만 출력하고 `Recent runs:` 블록은 생략하도록 분기했다.
  - JSON filter 메타데이터에도 `summary_only` 값을 포함시켰다.
- `tests/test_parent_stats.py`
  - stdin 파싱에 `--summary-only`가 반영되는지 검증을 추가했다.
  - summary-only 출력이 recent-run 상세를 숨기고 집계 카운터만 남기는지 검증하는 테스트를 추가했다.
  - reasons-only JSON 출력의 filter 메타데이터 검증을 강화했다.
- `.claude/commands/parent-stats.md`, `scripts/install_global_commands.py`
  - 새 플래그가 argument hint에 드러나도록 갱신했다.
- `README.md`, `docs/parent-routing.md`
  - 새 옵션과 compact summary 사용 예시를 문서에 반영했다.

## 검증
- `python3 -m unittest discover -s tests -p 'test_parent_stats.py' -v`
  - 결과: summary-only를 포함한 stats 테스트 통과.
- `python3 -m py_compile scripts/parent_stats.py tests/test_parent_stats.py scripts/install_global_commands.py`
  - 결과: 성공.
- `python3 - <<'PY' ... parent_stats.py --date 2026-04-10 --summary-only --limit 5 ... PY`
  - 결과: 집계 카운터는 유지되고 `Recent runs:`와 개별 요청 요약이 출력되지 않는 것을 확인했다.

## 다음 단계
다음에 바로 진행할 기능은 `/parent-stats`에 `--show-paths`를 추가해 어떤 JSON 로그 파일들이 집계에 포함됐는지 직접 확인할 수 있게 하는 것이다.
