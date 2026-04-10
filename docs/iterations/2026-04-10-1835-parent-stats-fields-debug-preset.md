# 작업 기록 2026-04-10-1835-parent-stats-fields-debug-preset

## 유형
feature expansion

## 요약
`/parent-stats`의 `--fields`에 `debug` preset을 추가했다. 이제 디버깅에 자주 필요한 컬럼 조합을 한 단어로 바로 요청할 수 있다.

## 배경
`core` preset은 최소 export에는 좋지만, 실제 디버깅에서는 reason code와 source path까지 함께 보는 경우가 많다. `debug` preset은 그런 조사형 워크플로를 위한 더 넓은 기본 projection이다.

## 변경 사항
- `scripts/parent_stats.py`
  - `FIELD_PRESETS`에 `debug`를 추가했다.
  - `--fields debug`가 `timestamp,model,mode,status,reason_codes,source_path`로 확장되도록 parser를 확장했다.
- `tests/test_parent_stats.py`
  - stdin 파싱에 `debug` preset이 반영되는지 검증을 추가했다.
  - preset parser가 기대하는 디버깅용 필드 묶음으로 확장되는지 검증을 추가했다.
- `.claude/commands/parent-stats.md`, `scripts/install_global_commands.py`
  - argument hint에 `debug` preset을 반영했다.
- `README.md`, `docs/parent-routing.md`
  - debug preset 사용 예시와 설명을 문서에 반영했다.

## 검증
- `python3 -m unittest discover -s tests -p 'test_parent_stats.py' -v`
  - 결과: fields debug preset을 포함한 stats 테스트 통과.
- `python3 -m py_compile scripts/parent_stats.py tests/test_parent_stats.py scripts/install_global_commands.py`
  - 결과: 성공.
- `python3 - <<'PY' ... parent_stats.py --window 7d --format tsv --fields debug --limit 0 ... PY`
  - 결과: `timestamp,model,mode,status,reason_codes,source_path` 순서의 TSV 헤더와 값이 출력되는 것을 확인했다.

## 다음 단계
다음에 바로 진행할 기능은 `/parent-stats`에 `--fields all` preset을 추가해 전체 record projection을 한 단어로 요청할 수 있게 만드는 것이다.
