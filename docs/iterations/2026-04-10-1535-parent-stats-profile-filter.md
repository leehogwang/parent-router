# 작업 기록 2026-04-10-1535-parent-stats-profile-filter

## 유형
feature expansion

## 요약
`/parent-stats`와 `scripts/parent_stats.py`에 `--profile parent|parent-no-opus` 필터를 추가했다. 이제 두 라우팅 프로필의 사용 패턴을 섞어 보지 않고 바로 분리해서 확인할 수 있다.

## 배경
이미 status 필터와 reason code 집계는 추가됐지만, `/parent`와 `/parent-no-opus`의 사용 결과를 비교하려면 출력 전체를 다시 눈으로 나눠 봐야 했다. profile 필터는 기존 로그 메타데이터를 활용해 실제 운영/디버깅 분석 경로를 더 직접적으로 만든다.

## 변경 사항
- `scripts/parent_stats.py`
  - `--profile parent|parent-no-opus` 인자를 추가했다.
  - profile 정규화 helper를 추가하고, 조건에 맞는 로그만 집계하도록 확장했다.
- `tests/test_parent_stats.py`
  - stdin 파싱에 profile이 반영되는지 검증을 추가했다.
  - 잘못된 profile 값을 거부하는 검증을 추가했다.
  - profile 필터가 다른 프로필의 실행을 제외하는지 검증하는 테스트를 추가했다.
- `.claude/commands/parent-stats.md`, `scripts/install_global_commands.py`
  - 새 profile 필터가 명령 argument hint에 드러나도록 갱신했다.
- `README.md`, `docs/parent-routing.md`
  - 새 옵션과 사용 예시를 문서에 반영했다.

## 검증
- `python3 -m unittest discover -s tests -p 'test_parent_stats.py' -v`
  - 결과: profile 필터를 포함한 stats 테스트 통과.
- `python3 -m py_compile scripts/parent_stats.py tests/test_parent_stats.py scripts/install_global_commands.py`
  - 결과: 성공.
- `python3 - <<'PY' ... parent_stats.py --date 2026-04-10 --profile parent-no-opus --limit 5 ... PY`
  - 결과: 샘플 로그 2개 중 `parent-no-opus` 프로필 실행 1개만 남고 다른 프로필 출력이 제외되는 것을 확인했다.

## 다음 단계
다음에 바로 진행할 기능은 `/parent-stats`에 `--mode plan|execute` 필터를 추가해 계획형/실행형 라우팅 분포를 직접 분리해서 보는 것이다.
