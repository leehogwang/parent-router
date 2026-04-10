# 작업 기록 2026-04-10-1605-parent-stats-confidence-filter

## 유형
feature expansion

## 요약
`/parent-stats`와 `scripts/parent_stats.py`에 `--confidence high|medium|low` 필터를 추가했다. 이제 경계 상황 라우팅이나 저신뢰 라우팅만 따로 분리해서 확인할 수 있다.

## 배경
status, profile, mode, model 필터가 추가된 뒤에도 low-confidence 결정만 따로 보려면 출력 전체를 다시 읽어야 했다. confidence 필터는 라우팅 품질과 경계 상황 분석을 직접 지원하는 관측 기능 확장이다.

## 변경 사항
- `scripts/parent_stats.py`
  - `--confidence high|medium|low` 인자를 추가했다.
  - confidence 정규화 helper를 추가하고, 조건에 맞는 로그만 집계하도록 확장했다.
  - 최근 실행 목록에도 confidence 값을 명시적으로 포함했다.
- `tests/test_parent_stats.py`
  - stdin 파싱에 confidence가 반영되는지 검증을 추가했다.
  - 잘못된 confidence 값을 거부하는 검증을 추가했다.
  - confidence 필터가 다른 confidence 수준의 실행을 제외하는지 검증하는 테스트를 추가했다.
- `.claude/commands/parent-stats.md`, `scripts/install_global_commands.py`
  - 새 confidence 필터가 argument hint에 드러나도록 갱신했다.
- `README.md`, `docs/parent-routing.md`
  - 새 옵션과 사용 예시를 문서에 반영했다.

## 검증
- `python3 -m unittest discover -s tests -p 'test_parent_stats.py' -v`
  - 결과: confidence 필터를 포함한 stats 테스트 통과.
- `python3 -m py_compile scripts/parent_stats.py tests/test_parent_stats.py scripts/install_global_commands.py`
  - 결과: 성공.
- `python3 - <<'PY' ... parent_stats.py --date 2026-04-10 --confidence medium --limit 5 ... PY`
  - 결과: 샘플 로그 2개 중 `medium` confidence 실행 1개만 남고 다른 confidence 출력이 제외되는 것을 확인했다.

## 다음 단계
다음에 바로 진행할 기능은 `/parent-stats`에 TSV/CSV 스타일의 machine-friendly 출력 모드를 추가해 외부 분석이나 복사-붙여넣기 워크플로를 더 쉽게 만드는 것이다.
