#!/usr/bin/env python3

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import shlex
import sys


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUNS_DIR = Path(os.environ.get("PARENTS_RUNS_DIR", ".parent/runs"))
VALID_STATUSES = {"ok", "failed", "dry-run"}
VALID_PROFILES = {"parent", "parent-no-opus"}


@dataclass
class StatsArgs:
    limit: int = 10
    date: str | None = None
    status: str | None = None
    profile: str | None = None


def detect_workspace_root() -> Path:
    override = os.environ.get("PARENTS_PROJECT_ROOT")
    if override:
        return Path(override).resolve()
    return PROJECT_ROOT


def parse_raw_args(raw_args: str) -> StatsArgs:
    tokens = shlex.split(raw_args)
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--date")
    parser.add_argument("--status")
    parser.add_argument("--profile")
    namespace = parser.parse_args(tokens)
    if namespace.limit <= 0:
        raise ValueError("--limit must be greater than zero")
    if namespace.date:
        try:
            datetime.strptime(namespace.date, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("--date must use YYYY-MM-DD") from exc
    if namespace.status and namespace.status not in VALID_STATUSES:
        raise ValueError("--status must be one of: dry-run, failed, ok")
    if namespace.profile and namespace.profile not in VALID_PROFILES:
        raise ValueError("--profile must be one of: parent, parent-no-opus")
    return StatsArgs(
        limit=namespace.limit,
        date=namespace.date,
        status=namespace.status,
        profile=namespace.profile,
    )


def load_stats_args(argv: list[str] | None = None) -> StatsArgs:
    argv = argv or sys.argv
    prompt = sys.stdin.read().strip()
    if prompt:
        return parse_raw_args(prompt)
    return parse_raw_args(" ".join(argv[1:]))


def iter_run_json_files(workspace_root: Path, args: StatsArgs) -> list[Path]:
    runs_root = workspace_root / RUNS_DIR
    if not runs_root.exists():
        return []
    if args.date:
        date_dir = runs_root / args.date
        if not date_dir.exists():
            return []
        return sorted(date_dir.glob("*.json"), reverse=True)
    return sorted(runs_root.glob("*/*.json"), reverse=True)


def execution_status(record: dict) -> str:
    return record.get("execution_status") or "dry-run"


def execution_profile(record: dict) -> str:
    return record.get("profile") or "(unknown)"


def load_run_records(paths: list[Path], args: StatsArgs) -> list[dict]:
    records: list[dict] = []
    for path in paths:
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if args.status and execution_status(record) != args.status:
            continue
        if args.profile and execution_profile(record) != args.profile:
            continue
        records.append(record)
        if len(records) >= args.limit:
            break
    return records


def summarize_request(text: str, limit: int = 72) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def format_counter(counter: Counter[str]) -> str:
    if not counter:
        return "(none)"
    return ", ".join(f"{key}={counter[key]}" for key in sorted(counter))


def format_report(records: list[dict], args: StatsArgs) -> str:
    header = ["Parent Run Stats"]
    if args.date:
        header.append(f"Date filter: {args.date}")
    if args.status:
        header.append(f"Status filter: {args.status}")
    if args.profile:
        header.append(f"Profile filter: {args.profile}")
    header.append(f"Runs analyzed: {len(records)}")
    if not records:
        return "\n".join(header + ["No run logs found."])

    status_counts: Counter[str] = Counter()
    profile_counts: Counter[str] = Counter()
    model_counts: Counter[str] = Counter()
    mode_counts: Counter[str] = Counter()
    confidence_counts: Counter[str] = Counter()
    reason_code_counts: Counter[str] = Counter()

    for record in records:
        status_counts[execution_status(record)] += 1
        profile_counts[execution_profile(record)] += 1
        model_counts[record.get("selected_model") or "(unknown)"] += 1
        mode_counts[record.get("selected_mode") or "(unknown)"] += 1
        confidence_counts[record.get("confidence") or "(unknown)"] += 1
        for reason_code in record.get("reason_codes") or []:
            reason_code_counts[reason_code] += 1

    lines = header + [
        f"Status: {format_counter(status_counts)}",
        f"Profiles: {format_counter(profile_counts)}",
        f"Models: {format_counter(model_counts)}",
        f"Modes: {format_counter(mode_counts)}",
        f"Confidence: {format_counter(confidence_counts)}",
        f"Reason codes: {format_counter(reason_code_counts)}",
        "Recent runs:",
    ]
    for record in records:
        lines.append(
            "- "
            + " | ".join(
                [
                    record.get("timestamp") or "(no timestamp)",
                    execution_profile(record),
                    f"{record.get('selected_model') or '?'}:{record.get('selected_mode') or '?'}",
                    execution_status(record),
                    summarize_request(record.get("request_text") or ""),
                ]
            )
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    try:
        args = load_stats_args(argv)
    except ValueError as exc:
        print(str(exc))
        return 2
    workspace_root = detect_workspace_root()
    paths = iter_run_json_files(workspace_root, args)
    records = load_run_records(paths, args)
    print(format_report(records, args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
