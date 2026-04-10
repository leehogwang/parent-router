# 작업 기록 2026-04-10-1805-parent-stats-count-only

## 유형
feature expansion

## 요약
`/parent-stats`와 `scripts/parent_stats.py`에 `--count-only` 플래그를 추가했다. 이제 aggregate count 라인만 빠르게 보고 싶을 때 헤더나 상세 블록 없이 더 짧은 출력을 얻을 수 있다.

## 배경
`--summary-only`는 recent runs를 숨겨주지만 여전히 header와 filter 문구까지 포함한다. 반복적으로 count 값만 확인하는 워크플로에서는 더 압축된 출력이 유용하므로 `--count-only`를 별도 경로로 추가했다.

## 변경 사항
- `scripts/parent_stats.py`
  - `--count-only` boolean 플래그를 추가했다.
  - text 모드에서 이 플래그가 켜지면 aggregate counter 라인만 출력하고 header, filter 문구, recent-run detail은 모두 생략하도록 확장했다.
  - JSON filter 메타데이터에 `count_only` 값을 포함했다.
- `tests/test_parent_stats.py`
  - stdin 파싱에 `--count-only`가 반영되는지 검증을 추가했다.
  - count-only 출력이 aggregate counts만 남기는지 검증하는 테스트를 추가했다.
- `.claude/commands/parent-stats.md`, `scripts/install_global_commands.py`
  - 새 플래그가 argument hint에 드러나도록 갱신했다.
- `README.md`, `docs/parent-routing.md`
  - 새 옵션과 compact count-only 사용 예시를 문서에 반영했다.

## 검증
- `python3 -m unittest discover -s tests -p 'test_parent_stats.py' -v`
  - 결과: count-only를 포함한 stats 테스트 통과.
- `python3 -m py_compile scripts/parent_stats.py tests/test_parent_stats.py scripts/install_global_commands.py`
  - 결과: 성공.
- `python3 - <<'PY' ... parent_stats.py --window 7d --count-only --limit 0 ... PY`
  - 결과: Status/Profiles/Models/Modes/Confidence/Reason codes 라인만 출력되고 header나 상세 블록은 생략되는 것을 확인했다.

## 다음 단계
다음에 바로 진행할 기능은 `/parent-stats`에 `--fields ...`를 추가해 TSV/JSON 출력에서 필요한 컬럼만 선택하는 것이다.
