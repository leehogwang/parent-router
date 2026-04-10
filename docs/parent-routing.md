# Parent Routing

`parents` adds two Claude Code commands:

- `/parent`
- `/parent-no-opus`
- `/parent-stats`

Both commands are thin skill entrypoints that call the shared router at [`scripts/parent.py`](/home/students/cs/202421012/parents/scripts/parent.py). The router first reads the current command arguments from stdin when the wrapper passes them through, falls back to the Claude session transcript when needed, chooses `model`, `mode`, and `effort`, and then launches a child `claude -p` session exactly once.

## Behavior

- `/parent` may choose `haiku`, `sonnet`, or `opus`.
- `/parent-no-opus` may choose only `haiku` or `sonnet`.
- Both commands may auto-select:
  - `mode`: `plan` or `execute`
  - `effort`: `low`, `medium`, `high`, or `max`
- The default user-facing output is just the child Claude response, so the command feels like normal Claude usage.
- `--why` adds a short natural-language explanation before the response.
- `--dry-run` prints only the chosen route in natural language and does not launch a child session.

## Supported Flags

- `--model auto|haiku|sonnet|opus`
- `--mode auto|plan|execute`
- `--effort auto|low|medium|high|max`
- `--why`
- `--dry-run`

`/parent-no-opus` rejects `--model opus`.

## Routing Notes

- High-risk, high-ambiguity, migration, security, architecture, and greenfield requests are pushed into `plan`.
- Small bounded low-risk requests may use `haiku`.
- Normal coding work defaults to `sonnet`.
- `/parent-no-opus` handles `opus`-class tasks by staying on `sonnet` and preferring `plan`.
- There is no runtime fallback or automatic retry. One route is selected, one child session is launched, and any failure is returned directly.

## Logging

Each run writes:

- JSON metadata to `.parent/runs/YYYY-MM-DD/*.json`
- A Markdown summary to `.parent/runs/YYYY-MM-DD/*.md`

The logs include:

- original request
- explicit overrides
- feature scores
- selected model, mode, and effort
- effective effort after clamping
- confidence and reason codes
- child permission mode and tool restrictions used for the routed Claude invocation
- child exit status and stderr summary

This keeps the interactive UX clean while preserving the full decision trail for later inspection.

## Stats Inspection

Use `/parent-stats` or `python3 scripts/parent_stats.py` to inspect recent `.parent/runs` JSON logs without opening individual files. The inspector supports `--limit N|0`, `--date YYYY-MM-DD`, `--since YYYY-MM-DD`, `--until YYYY-MM-DD`, `--window Nd`, `--status ok|failed|dry-run`, `--profile parent|parent-no-opus`, `--mode plan|execute`, `--model haiku|sonnet|opus`, `--confidence high|medium|low`, `--format text|tsv|json`, `--reasons-only`, `--fail-if-empty`, `--summary-only`, `--show-paths`, `--sort newest|oldest`, and `--count-only`. The default text mode prints aggregated counts plus a compact recent-run list, `--summary-only` keeps only the aggregate counters, `--count-only` reduces the output further to just the aggregate count lines, `--show-paths` reveals which log files were included, `--sort oldest` flips the query to prefer older matching logs, `--since YYYY-MM-DD` sets a lower date bound across day-directories, `--window Nd` creates a recent rolling lower bound from the current day, `--limit 0` keeps the full filtered result set, TSV mode emits machine-friendly tab-separated rows, JSON mode emits structured records or reason-code summaries for automation, `--reasons-only` collapses the output to the filtered reason-code summary, and `--fail-if-empty` turns an empty filtered result into a non-zero exit for scripts.
