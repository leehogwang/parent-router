# 작업 기록 2026-04-10-1555-parent-stats-model-filter

## 유형
feature expansion

## 요약
`/parent-stats`와 `scripts/parent_stats.py`에 `--model haiku|sonnet|opus` 필터를 추가했다. 이제 모델별 라우팅 패턴과 실패/드라이런 분포를 직접 분리해서 볼 수 있다.

## 배경
status, profile, mode 필터까지 갖춘 뒤에도 특정 모델의 사용 결과를 좁혀보려면 전체 출력에서 다시 눈으로 걸러야 했다. model 필터를 추가하면 라우팅 정책의 실제 모델 선택 패턴을 더 빠르게 분석할 수 있다.

## 변경 사항
- `scripts/parent_stats.py`
  - `--model haiku|sonnet|opus` 인자를 추가했다.
  - model 정규화 helper를 추가하고, 조건에 맞는 로그만 집계하도록 확장했다.
- `tests/test_parent_stats.py`
  - stdin 파싱에 model이 반영되는지 검증을 추가했다.
  - 잘못된 model 값을 거부하는 검증을 추가했다.
  - model 필터가 다른 모델의 실행을 제외하는지 검증하는 테스트를 추가했다.
- `.claude/commands/parent-stats.md`, `scripts/install_global_commands.py`
  - 새 model 필터가 argument hint에 드러나도록 갱신했다.
- `README.md`, `docs/parent-routing.md`
  - 새 옵션과 사용 예시를 문서에 반영했다.

## 검증
- `python3 -m unittest discover -s tests -p 'test_parent_stats.py' -v`
  - 결과: model 필터를 포함한 stats 테스트 통과.
- `python3 -m py_compile scripts/parent_stats.py tests/test_parent_stats.py scripts/install_global_commands.py`
  - 결과: 성공.
- `python3 - <<'PY' ... parent_stats.py --date 2026-04-10 --model sonnet --limit 5 ... PY`
  - 결과: 샘플 로그 2개 중 `sonnet` 모델 실행 1개만 남고 다른 모델 출력이 제외되는 것을 확인했다.

## 다음 단계
다음에 바로 진행할 기능은 `/parent-stats`에 `--confidence high|medium|low` 필터를 추가해 경계 상황 라우팅만 따로 분리해서 보는 것이다.
