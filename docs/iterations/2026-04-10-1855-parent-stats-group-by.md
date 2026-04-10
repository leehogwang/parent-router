# 작업 기록 2026-04-10-1855-parent-stats-group-by

## 유형
feature expansion

## 요약
`/parent-stats`에 `--group-by model|mode|profile|status`를 추가했다. 이제 text 요약을 하나의 집계 축으로 바로 축약해서 볼 수 있다.

## 배경
기존 text 요약은 항상 status/profile/model/mode/confidence/reason_codes를 모두 함께 출력했다. 빠르게 특정 축 하나만 비교하고 싶을 때는 정보가 과했다. `--group-by`는 가장 작은 집계 축 제어 기능이다.

## 변경 사항
- `scripts/parent_stats.py`
  - `--group-by model|mode|profile|status` 인자를 추가했다.
  - text 요약에서 선택된 한 축만 출력하도록 count 라인 생성을 분기했다.
  - `--group-by`는 text 출력에서만 허용하도록 제한했다.
- `tests/test_parent_stats.py`
  - stdin 파싱에 group-by가 반영되는지 검증을 추가했다.
  - 잘못된 group-by 값과 non-text format 조합을 거부하는 검증을 추가했다.
  - group-by 출력이 한 축만 남기고 다른 집계 라인을 제거하는지 검증하는 테스트를 추가했다.
- `.claude/commands/parent-stats.md`, `scripts/install_global_commands.py`
  - 새 옵션이 argument hint에 드러나도록 갱신했다.
- `README.md`, `docs/parent-routing.md`
  - group-by 사용 예시와 설명을 문서에 반영했다.

## 검증
- `python3 -m unittest discover -s tests -p 'test_parent_stats.py' -v`
  - 결과: group-by를 포함한 stats 테스트 통과.
- `python3 -m py_compile scripts/parent_stats.py tests/test_parent_stats.py scripts/install_global_commands.py`
  - 결과: 성공.
- `python3 - <<'PY' ... parent_stats.py --window 7d --group-by model --limit 0 ... PY`
  - 결과: `Models: ...` 라인만 출력되고 다른 집계 라인은 생략되는 것을 확인했다.

## 다음 단계
다음에 바로 진행할 기능은 `/parent-stats`에 `--group-by reason_codes`를 추가해 라우팅 근거 집계도 같은 방식으로 단독 축으로 볼 수 있게 만드는 것이다.
