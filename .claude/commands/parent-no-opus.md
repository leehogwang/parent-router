---
description: Route a request without ever using Opus, while still selecting mode and effort automatically
argument-hint: <goal>
allowed-tools: Bash
disable-model-invocation: true
---
You are handling a user-invoked `/parent-no-opus` command.

Do this:
1. Use Bash exactly once with a timeout of `900000` milliseconds and `run_in_background` set to `false`.
2. Find the nearest ancestor directory that contains `scripts/parent.py`.
3. Run:
   `ROOT="$PWD"; while [ ! -f "$ROOT/scripts/parent.py" ] && [ "$ROOT" != "/" ]; do ROOT="$(dirname "$ROOT")"; done; python3 "$ROOT/scripts/parent.py" --session-id "${CLAUDE_SESSION_ID}" --command-name "/parent-no-opus"`
4. Wait for it to finish.
5. If it succeeds, reply with exactly the script output and nothing else.
6. If it fails, reply with exactly the script output and nothing else.

Rules:
- Do not ask follow-up questions.
- Do not summarize the result.
- Do not add commentary before or after the result.
- Do not pass the user's prompt on the command line.
- Do not use Bash more than once.
