# 작업 기록 2026-04-10-1815-parent-stats-fields-selector

## 유형
feature expansion

## 요약
`/parent-stats`에 `--fields ...` 선택자를 추가했다. 이제 TSV/JSON 출력에서 필요한 컬럼만 골라 내보낼 수 있다.

## 배경
기존 TSV/JSON export는 항상 전체 record shape를 반환해서, downstream 도구에서 불필요한 열을 다시 제거해야 했다. `--fields`는 projection을 호출 시점에 해결해 더 가벼운 export 경로를 제공한다.

## 변경 사항
- `scripts/parent_stats.py`
  - `--fields a,b,c` 인자를 추가했다.
  - 허용 가능한 field 이름을 검증하는 parser를 추가했다.
  - TSV/JSON 출력이 선택된 fields만 포함하도록 projection 로직을 확장했다.
  - `--fields`는 `--format json|tsv`에서만 허용하도록 제한했다.
- `tests/test_parent_stats.py`
  - stdin 파싱에 fields가 반영되는지 검증을 추가했다.
  - 잘못된 field 이름과 format 없는 사용을 거부하는 검증을 추가했다.
  - TSV/JSON output이 선택된 컬럼만 포함하는지 검증하는 테스트를 추가했다.
- `.claude/commands/parent-stats.md`, `scripts/install_global_commands.py`
  - 새 옵션이 argument hint에 드러나도록 갱신했다.
- `README.md`, `docs/parent-routing.md`
  - fields 선택자와 사용 예시를 문서에 반영했다.

## 검증
- `python3 -m unittest discover -s tests -p 'test_parent_stats.py' -v`
  - 결과: fields 선택자를 포함한 stats 테스트 통과.
- `python3 -m py_compile scripts/parent_stats.py tests/test_parent_stats.py scripts/install_global_commands.py`
  - 결과: 성공.
- `python3 - <<'PY' ... parent_stats.py --window 7d --format tsv --fields timestamp,model,status --limit 0 ... PY`
  - 결과: TSV 헤더와 행이 선택된 세 컬럼만 포함하는 것을 확인했다.

## 다음 단계
다음에 바로 진행할 기능은 `/parent-stats`에 preset projection(`--fields core`) 같은 축약 별칭을 추가하는 것이다.
