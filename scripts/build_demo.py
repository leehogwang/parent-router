#!/usr/bin/env python3

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
MIN_EVENT_SECONDS = 0.04
MAX_HOLD_SECONDS = 0.55
SCRIPT_BOOKEND_RE = re.compile(
    rb"^Script started on .*?\n|\nScript done on .*?$",
    re.DOTALL,
)
ANSI_RE = re.compile(
    r"\x1b\[[0-?]*[ -/]*[@-~]|\x1b\][^\x07]*\x07|\x1b[@-_]",
    re.DOTALL,
)


@dataclass(frozen=True)
class TimingEntry:
    stream: str
    delay: float
    size: int


def run_step(args: list[str]) -> None:
    completed = subprocess.run(args, cwd=str(ROOT), check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def strip_script_bookends(payload: bytes) -> bytes:
    return SCRIPT_BOOKEND_RE.sub(b"", payload).strip(b"\n") + (b"\n" if payload else b"")


def parse_timing_entries(path: Path) -> list[TimingEntry]:
    entries: list[TimingEntry] = []
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        parts = raw_line.split(" ", 3)
        if len(parts) < 3 or parts[0] == "H":
            continue
        entries.append(TimingEntry(stream=parts[0], delay=float(parts[1]), size=int(parts[2])))
    return entries


def compress_delay(delay: float) -> float:
    if delay <= 0:
        return 0.0
    if delay < MIN_EVENT_SECONDS:
        return MIN_EVENT_SECONDS
    return min(MAX_HOLD_SECONDS, delay)


def clean_terminal_output(payload: bytes) -> str:
    stripped = strip_script_bookends(payload).decode("utf-8", errors="ignore")
    clean = ANSI_RE.sub("", stripped)
    clean = clean.replace("\r", "")
    clean = re.sub(r"\n{3,}", "\n\n", clean)
    return clean.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the interactive README demo assets.")
    parser.add_argument("--skip-capture", action="store_true", help="Reuse the existing source capture.")
    args = parser.parse_args()
    if not args.skip_capture:
        run_step([sys.executable, "scripts/capture_interactive_demo.py"])
    run_step([sys.executable, "scripts/render_interactive_demo.py"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
