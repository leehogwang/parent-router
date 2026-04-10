# 작업 기록 2026-04-10-1845-parent-stats-fields-all-preset

## 유형
feature expansion

## 요약
`/parent-stats`의 `--fields`에 `all` preset을 추가했다. 이제 전체 record projection을 한 단어로 요청할 수 있다.

## 배경
기본 TSV/JSON projection은 암묵적으로 전체 필드를 내보내지만, 명시적인 preset이 없어서 호출 시점에 의도가 드러나지 않았다. `all` preset은 `core`, `debug`와 같은 방식으로 전체 projection도 안정적인 별칭으로 제공한다.

## 변경 사항
- `scripts/parent_stats.py`
  - `FIELD_PRESETS`에 `all`을 추가했다.
  - `--fields all`이 전체 record field 집합으로 확장되도록 parser를 확장했다.
- `tests/test_parent_stats.py`
  - stdin 파싱에 `all` preset이 반영되는지 검증을 추가했다.
  - preset parser가 전체 필드 묶음으로 확장되는지 검증을 추가했다.
- `.claude/commands/parent-stats.md`, `scripts/install_global_commands.py`
  - argument hint에 `all` preset을 반영했다.
- `README.md`, `docs/parent-routing.md`
  - all preset 사용 예시와 설명을 문서에 반영했다.

## 검증
- `python3 -m unittest discover -s tests -p 'test_parent_stats.py' -v`
  - 결과: fields all preset을 포함한 stats 테스트 통과.
- `python3 -m py_compile scripts/parent_stats.py tests/test_parent_stats.py scripts/install_global_commands.py`
  - 결과: 성공.
- `python3 - <<'PY' ... parent_stats.py --window 7d --format tsv --fields all --limit 0 ... PY`
  - 결과: 전체 TSV 헤더와 전체 값이 preset alias로 동일하게 출력되는 것을 확인했다.

## 다음 단계
다음에 바로 진행할 기능은 `/parent-stats`에 `--group-by model|mode|profile` 같은 집계 축 제어를 추가하는 것이다.
