# 작업 기록 2026-04-10-1825-parent-stats-fields-core-preset

## 유형
feature expansion

## 요약
`/parent-stats`의 `--fields`에 `core` preset을 추가했다. 이제 자주 쓰는 최소 TSV/JSON export를 위해 컬럼 목록을 반복 입력하지 않아도 된다.

## 배경
직전 반복에서 `--fields ...` 자체는 추가됐지만, 공통적인 핵심 컬럼 조합을 매번 다시 적는 건 여전히 반복 작업이었다. `core` preset은 가장 자주 쓰일 가능성이 높은 최소 투영을 한 단어로 제공하는 작은 생산성 확장이다.

## 변경 사항
- `scripts/parent_stats.py`
  - `FIELD_PRESETS`에 `core`를 추가했다.
  - `--fields core`가 `timestamp,model,mode,status,confidence`로 확장되도록 parser를 확장했다.
- `tests/test_parent_stats.py`
  - stdin 파싱에 `core` preset이 반영되는지 검증을 추가했다.
  - preset parser가 기대하는 필드 묶음으로 확장되는지 검증을 추가했다.
- `.claude/commands/parent-stats.md`, `scripts/install_global_commands.py`
  - argument hint에 `core` preset을 반영했다.
- `README.md`, `docs/parent-routing.md`
  - preset 사용 예시와 설명을 문서에 반영했다.

## 검증
- `python3 -m unittest discover -s tests -p 'test_parent_stats.py' -v`
  - 결과: fields core preset을 포함한 stats 테스트 통과.
- `python3 -m py_compile scripts/parent_stats.py tests/test_parent_stats.py scripts/install_global_commands.py`
  - 결과: 성공.
- `python3 - <<'PY' ... parent_stats.py --window 7d --format tsv --fields core --limit 0 ... PY`
  - 결과: `timestamp,model,mode,status,confidence` 순서의 TSV 헤더와 값이 출력되는 것을 확인했다.

## 다음 단계
다음에 바로 진행할 기능은 `/parent-stats`에 `--fields debug` 같은 더 넓은 preset을 추가해 source_path와 reason_codes 중심 디버깅 export를 빠르게 만드는 것이다.
