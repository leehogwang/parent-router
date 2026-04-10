# 작업 기록 2026-04-10-1615-parent-stats-format-mode

## 유형
feature expansion

## 요약
`/parent-stats`와 `scripts/parent_stats.py`에 `--format text|tsv` 출력 모드를 추가했다. 이제 필터링된 실행 결과를 사람이 읽는 요약뿐 아니라 TSV 형태로도 바로 내보낼 수 있다.

## 배경
기존 `/parent-stats`는 사람이 읽기 좋은 요약에는 적합했지만, 스프레드시트나 외부 분석 도구로 옮길 때는 다시 가공이 필요했다. `--format tsv`는 이미 있는 필터 체인을 그대로 활용하면서 machine-friendly export 경로를 제공한다.

## 변경 사항
- `scripts/parent_stats.py`
  - `--format text|tsv` 인자를 추가했다.
  - TSV 헤더와 행 출력을 생성하는 formatter를 추가했다.
  - TSV 모드에서는 timestamp, profile, model, mode, status, confidence, reason_codes, request_text를 탭 구분으로 출력한다.
- `tests/test_parent_stats.py`
  - stdin 파싱에 format이 반영되는지 검증을 추가했다.
  - 잘못된 format 값을 거부하는 검증을 추가했다.
  - TSV 출력 포맷이 실제 행 데이터를 포함하는지 검증하는 테스트를 추가했다.
- `.claude/commands/parent-stats.md`, `scripts/install_global_commands.py`
  - 새 format 옵션이 argument hint에 드러나도록 갱신했다.
- `README.md`, `docs/parent-routing.md`
  - TSV 출력 모드와 사용 예시를 문서에 반영했다.

## 검증
- `python3 -m unittest discover -s tests -p 'test_parent_stats.py' -v`
  - 결과: format 모드를 포함한 stats 테스트 통과.
- `python3 -m py_compile scripts/parent_stats.py tests/test_parent_stats.py scripts/install_global_commands.py`
  - 결과: 성공.
- `python3 - <<'PY' ... parent_stats.py --date 2026-04-10 --model sonnet --format tsv --limit 5 ... PY`
  - 결과: TSV 헤더와 함께 `sonnet` 필터에 맞는 단일 실행 행이 탭 구분으로 출력되는 것을 확인했다.

## 다음 단계
다음에 바로 진행할 기능은 `/parent-stats`에 `--reasons-only` 같은 축약 모드를 추가해 reason code 집계만 빠르게 확인하는 요약 경로를 만드는 것이다.
