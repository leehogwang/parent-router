# 작업 기록 2026-04-10-1545-parent-stats-mode-filter

## 유형
feature expansion

## 요약
`/parent-stats`와 `scripts/parent_stats.py`에 `--mode plan|execute` 필터를 추가했다. 이제 계획형 라우팅과 실행형 라우팅의 실제 사용 분포를 바로 분리해서 볼 수 있다.

## 배경
profile 필터까지 추가된 상태에서도 `plan`과 `execute` 결과는 여전히 같은 출력 안에 섞여 있었다. mode 필터를 추가하면 라우팅 정책의 의도와 실제 사용 패턴을 훨씬 더 직접적으로 비교할 수 있다.

## 변경 사항
- `scripts/parent_stats.py`
  - `--mode plan|execute` 인자를 추가했다.
  - mode 정규화 helper를 추가하고, 조건에 맞는 로그만 집계하도록 확장했다.
- `tests/test_parent_stats.py`
  - stdin 파싱에 mode가 반영되는지 검증을 추가했다.
  - 잘못된 mode 값을 거부하는 검증을 추가했다.
  - mode 필터가 다른 mode의 실행을 제외하는지 검증하는 테스트를 추가했다.
- `.claude/commands/parent-stats.md`, `scripts/install_global_commands.py`
  - 새 mode 필터가 argument hint에 드러나도록 갱신했다.
- `README.md`, `docs/parent-routing.md`
  - 새 옵션과 사용 예시를 문서에 반영했다.

## 검증
- `python3 -m unittest discover -s tests -p 'test_parent_stats.py' -v`
  - 결과: mode 필터를 포함한 stats 테스트 통과.
- `python3 -m py_compile scripts/parent_stats.py tests/test_parent_stats.py scripts/install_global_commands.py`
  - 결과: 성공.
- `python3 - <<'PY' ... parent_stats.py --date 2026-04-10 --mode execute --limit 5 ... PY`
  - 결과: 샘플 로그 2개 중 `execute` 모드 실행 1개만 남고 `plan` 모드 출력이 제외되는 것을 확인했다.

## 다음 단계
다음에 바로 진행할 기능은 `/parent-stats`에 `--model haiku|sonnet|opus` 필터를 추가해 모델별 라우팅 패턴을 직접 분리해서 보는 것이다.
