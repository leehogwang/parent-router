#!/usr/bin/env python3

from __future__ import annotations

import os
from pathlib import Path
import shutil
import time

import pexpect


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "assets" / "demo" / "source"
INPUT_LOG = SOURCE_DIR / "parent-interactive.in"
OUTPUT_LOG = SOURCE_DIR / "parent-interactive.out"
TIMING_LOG = SOURCE_DIR / "parent-interactive.time"


DEMO_STEPS = (
    "/parent --dry-run rename one variable",
)
QUIET_STARTUP_SECONDS = 2.0
QUIET_AFTER_COMMAND_SECONDS = 3.0
QUIET_EXIT_SECONDS = 1.0
MAX_STARTUP_SECONDS = 30.0
MAX_COMMAND_SECONDS = 90.0
MAX_EXIT_SECONDS = 10.0
CHAR_DELAY_SECONDS = 0.02


def clean_previous_capture() -> None:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    for path in SOURCE_DIR.iterdir():
        if path.is_file():
            path.unlink()


def build_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("PARENTS_SESSION_PROMPT_RETRY_COUNT", "16")
    env.setdefault("PARENTS_SESSION_PROMPT_RETRY_SLEEP_SECONDS", "0.2")
    return env


def spawn_capture() -> pexpect.spawn:
    command = [
        "script",
        "-q",
        "-f",
        "-m",
        "advanced",
        "-I",
        str(INPUT_LOG),
        "-O",
        str(OUTPUT_LOG),
        "-T",
        str(TIMING_LOG),
        "-c",
        "claude",
    ]
    child = pexpect.spawn(
        command[0],
        command[1:],
        cwd=str(ROOT),
        env=build_env(),
        encoding="utf-8",
        timeout=20,
    )
    child.setwinsize(32, 96)
    return child


def drive_session(child: pexpect.spawn) -> None:
    read_until_quiet(
        child,
        quiet_seconds=QUIET_STARTUP_SECONDS,
        max_seconds=MAX_STARTUP_SECONDS,
    )
    for command in DEMO_STEPS:
        type_command(child, command)
        read_until_quiet(
            child,
            quiet_seconds=QUIET_AFTER_COMMAND_SECONDS,
            max_seconds=MAX_COMMAND_SECONDS,
        )


def read_until_quiet(
    child: pexpect.spawn,
    *,
    quiet_seconds: float,
    max_seconds: float,
) -> None:
    start = time.monotonic()
    last_output = start
    while time.monotonic() - start < max_seconds:
        try:
            child.read_nonblocking(size=4096, timeout=0.2)
        except pexpect.TIMEOUT:
            if time.monotonic() - last_output >= quiet_seconds:
                return
            continue
        except pexpect.EOF:
            return
        else:
            last_output = time.monotonic()


def type_command(child: pexpect.spawn, command: str) -> None:
    for char in command:
        child.send(char)
        time.sleep(CHAR_DELAY_SECONDS)
    child.send("\r")


def stop_session(child: pexpect.spawn) -> None:
    if not child.isalive():
        return
    child.sendcontrol("d")
    read_until_quiet(
        child,
        quiet_seconds=QUIET_EXIT_SECONDS,
        max_seconds=MAX_EXIT_SECONDS,
    )
    if child.isalive():
        child.terminate(force=True)
        time.sleep(0.5)


def ensure_capture_exists() -> None:
    missing = [path.name for path in (INPUT_LOG, OUTPUT_LOG, TIMING_LOG) if not path.exists()]
    if missing:
        raise RuntimeError(f"Missing capture files: {', '.join(missing)}")


def main() -> int:
    if shutil.which("script") is None:
        raise RuntimeError("The `script` command is required to capture the interactive demo.")
    clean_previous_capture()
    child = spawn_capture()
    try:
        drive_session(child)
    finally:
        stop_session(child)
    ensure_capture_exists()
    print(f"Wrote {INPUT_LOG}")
    print(f"Wrote {OUTPUT_LOG}")
    print(f"Wrote {TIMING_LOG}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
