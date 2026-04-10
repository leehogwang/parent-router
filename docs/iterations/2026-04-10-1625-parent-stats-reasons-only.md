# 작업 기록 2026-04-10-1625-parent-stats-reasons-only

## 유형
feature expansion

## 요약
`/parent-stats`와 `scripts/parent_stats.py`에 `--reasons-only` 요약 모드를 추가했다. 이제 전체 최근 실행 목록을 보지 않아도 필터된 reason code 집계만 빠르게 확인할 수 있다.

## 배경
status/profile/mode/model/confidence 필터와 TSV 출력까지 추가된 상태에서도, 라우팅 규칙이 왜 발동했는지만 빠르게 보고 싶을 때는 여전히 전체 요약을 훑어야 했다. `--reasons-only`는 정책 분석 중심의 짧은 확인 경로를 제공한다.

## 변경 사항
- `scripts/parent_stats.py`
  - `--reasons-only` boolean 플래그를 추가했다.
  - text 모드에서 이 플래그가 켜지면 필터 정보, 실행 수, reason code 집계만 출력하도록 분기했다.
- `tests/test_parent_stats.py`
  - stdin 파싱에 `--reasons-only`가 반영되는지 검증을 추가했다.
  - reasons-only 출력이 recent runs 없이 reason code 집계만 남기는지 검증하는 테스트를 추가했다.
- `.claude/commands/parent-stats.md`, `scripts/install_global_commands.py`
  - 새 플래그가 argument hint에 드러나도록 갱신했다.
- `README.md`, `docs/parent-routing.md`
  - 새 옵션과 사용 예시를 문서에 반영했다.

## 검증
- `python3 -m unittest discover -s tests -p 'test_parent_stats.py' -v`
  - 결과: reasons-only 모드를 포함한 stats 테스트 통과.
- `python3 -m py_compile scripts/parent_stats.py tests/test_parent_stats.py scripts/install_global_commands.py`
  - 결과: 성공.
- `python3 - <<'PY' ... parent_stats.py --date 2026-04-10 --model opus --reasons-only --limit 5 ... PY`
  - 결과: 필터 정보와 `Reason codes:` 집계만 출력되고 최근 실행 목록은 생략되는 것을 확인했다.

## 다음 단계
다음에 바로 진행할 기능은 `/parent-stats`에 `--json` 출력 모드를 추가해 외부 자동화가 더 쉽게 결과를 파싱할 수 있게 만드는 것이다.
