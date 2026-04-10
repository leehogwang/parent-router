#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "parent.py"
STATS_SCRIPT_PATH = ROOT / "scripts" / "parent_stats.py"
TARGET_DIR = Path.home() / ".claude" / "commands"


def command_body(
    command_name: str,
    description: str,
    script_path: Path = SCRIPT_PATH,
    argument_hint: str = "<goal>",
    script_args: str = '--session-id "${CLAUDE_SESSION_ID}" --command-name "{command_name}"',
) -> str:
    rendered_script_args = script_args.replace("{command_name}", command_name)
    return f"""---
description: {description}
argument-hint: {argument_hint}
allowed-tools: Bash
disable-model-invocation: true
---
You are handling a user-invoked `{command_name}` command.

Do this:
1. Use Bash exactly once with a timeout of `900000` milliseconds and `run_in_background` set to `false`.
2. Run:
   `PARENTS_PROJECT_ROOT="$PWD" python3 "{script_path}" {rendered_script_args} <<'__PARENTS_ARGS__'
$ARGUMENTS
__PARENTS_ARGS__`
3. Wait for it to finish.
4. Claude UI already shows the Bash tool stdout and stderr. Do not repeat that content in an assistant message.
5. Your final assistant response must be completely empty after the Bash tool finishes, including on failure.

Rules:
- Do not ask follow-up questions.
- Do not summarize the result.
- Do not add commentary before or after the Bash tool output.
- Do not emit any assistant text after the Bash tool call.
- Do not pass the user's prompt on the command line.
- Do not use Bash more than once.
"""


def main() -> int:
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    targets = {
        "parent.md": command_body(
            "/parent",
            "Route a request to the appropriate Claude model, mode, and effort automatically",
        ),
        "parent-no-opus.md": command_body(
            "/parent-no-opus",
            "Route a request without ever using Opus, while still selecting mode and effort automatically",
        ),
        "parent-stats.md": command_body(
            "/parent-stats",
            "Inspect recent /parent routing logs with aggregated stats",
            script_path=STATS_SCRIPT_PATH,
            argument_hint="[--limit N|0] [--date YYYY-MM-DD] [--since YYYY-MM-DD] [--until YYYY-MM-DD] [--window Nd] [--status ok|failed|dry-run] [--profile parent|parent-no-opus] [--mode plan|execute] [--model haiku|sonnet|opus] [--confidence high|medium|low] [--format text|tsv|json] [--fields a,b,c|core|debug] [--reasons-only] [--fail-if-empty] [--summary-only] [--show-paths] [--sort newest|oldest] [--count-only]",
            script_args="",
        ),
    }
    for name, content in targets.items():
        (TARGET_DIR / name).write_text(content, encoding="utf-8")
        print(f"Wrote {TARGET_DIR / name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
