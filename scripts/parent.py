#!/usr/bin/env python3

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time
from typing import Iterable


CLAUDE_BIN = Path(
    os.environ.get("PARENTS_CLAUDE_BIN", str(Path.home() / ".local/bin/claude"))
)
CLAUDE_PROJECTS_DIR = Path(
    os.environ.get("PARENTS_PROJECTS_DIR", str(Path.home() / ".claude/projects"))
)
RUNS_DIR = Path(os.environ.get("PARENTS_RUNS_DIR", ".parent/runs"))
PROJECT_ROOT = Path(__file__).resolve().parent.parent
VISIBLE_TRANSCRIPT_MAX_MESSAGES = 24
VISIBLE_TRANSCRIPT_MAX_CHARS = 10000
OLDER_CONTEXT_SUMMARY_MAX_CHARS = 16000
OLDER_CONTEXT_SUMMARY_MAX_LINES = 10
SESSION_PROMPT_RETRY_COUNT = int(
    os.environ.get("PARENTS_SESSION_PROMPT_RETRY_COUNT", "120")
)
SESSION_PROMPT_RETRY_SLEEP_SECONDS = float(
    os.environ.get("PARENTS_SESSION_PROMPT_RETRY_SLEEP_SECONDS", "0.5")
)
CURRENT_PROMPT_LOOKBACK_SECONDS = 15
COMMAND_NAME_RE = re.compile(r"<command-name>(.*?)</command-name>", re.DOTALL)
COMMAND_ARGS_RE = re.compile(r"<command-args>(.*?)</command-args>", re.DOTALL)
NON_SOURCE_DIRS = {
    ".git",
    ".claude",
    ".parent",
    "__pycache__",
    "docs",
    "tests",
    "scripts",
}
EFFORT_ORDER = ("low", "medium", "high", "max")
VALID_MODELS = {"auto", "haiku", "sonnet", "opus"}
VALID_MODES = {"auto", "plan", "execute"}
VALID_EFFORTS = {"auto", *EFFORT_ORDER}


@dataclass(frozen=True)
class Profile:
    name: str
    command_name: str
    allowed_models: tuple[str, ...]


PROFILES = {
    "parent": Profile(
        name="parent",
        command_name="/parent",
        allowed_models=("haiku", "sonnet", "opus"),
    ),
    "parent-no-opus": Profile(
        name="parent-no-opus",
        command_name="/parent-no-opus",
        allowed_models=("haiku", "sonnet"),
    ),
}
COMMAND_TO_PROFILE = {profile.command_name: profile for profile in PROFILES.values()}


@dataclass
class ParsedCommand:
    model: str = "auto"
    mode: str = "auto"
    effort: str = "auto"
    why: bool = False
    dry_run: bool = False
    task: str = ""


@dataclass
class FeatureScores:
    scope: int
    ambiguity: int
    risk: int
    depth: int
    research: int
    action: int

    @property
    def total(self) -> int:
        return (
            self.scope
            + self.ambiguity
            + self.risk
            + self.depth
            + self.research
            + self.action
        )


@dataclass
class RouteDecision:
    profile: str
    request_text: str
    selected_model: str
    selected_mode: str
    selected_effort: str
    effective_effort: str
    confidence: str
    reason_codes: list[str]
    scores: FeatureScores
    explicit_model: str | None = None
    explicit_mode: str | None = None
    explicit_effort: str | None = None


@dataclass
class ExecutionResult:
    ok: bool
    stdout: str
    stderr: str
    exit_code: int
    argv: list[str] = field(default_factory=list)


def detect_workspace_root() -> Path:
    override = os.environ.get("PARENTS_PROJECT_ROOT")
    if override:
        return Path(override).resolve()
    return PROJECT_ROOT


def parse_started_at(raw_value: str) -> datetime | None:
    if not raw_value:
        return None
    try:
        return datetime.strptime(raw_value, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        return None


def parse_cli_args(argv: list[str]) -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--session-id")
    parser.add_argument("--command-name", default="/parent")
    parser.add_argument("--command-profile")
    parser.add_argument("--started-at")
    return parser.parse_known_args(argv[1:])


def locate_session_file(session_id: str) -> Path | None:
    if not session_id or not CLAUDE_PROJECTS_DIR.exists():
        return None
    matches = list(CLAUDE_PROJECTS_DIR.glob(f"*/{session_id}.jsonl"))
    return matches[0] if matches else None


def load_session_entries(session_id: str) -> list[dict]:
    session_file = locate_session_file(session_id)
    if session_file is None:
        return []
    entries: list[dict] = []
    try:
        for line in session_file.read_text(encoding="utf-8").splitlines():
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except OSError:
        return []
    return entries


def extract_command_args_from_user_entry(entry: dict, command_name: str) -> str:
    if entry.get("type") != "user":
        return ""
    message = entry.get("message") or {}
    content = message.get("content")
    if not isinstance(content, str):
        return ""
    name_match = COMMAND_NAME_RE.search(content)
    args_match = COMMAND_ARGS_RE.search(content)
    if name_match is None or args_match is None:
        return ""
    if name_match.group(1).strip() != command_name:
        return ""
    return args_match.group(1).strip()


def parse_entry_timestamp(entry: dict) -> datetime | None:
    raw_value = entry.get("timestamp")
    if not isinstance(raw_value, str) or not raw_value:
        return None
    normalized = raw_value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def is_recent_command_entry(entry: dict, invocation_started_at: datetime) -> bool:
    timestamp = parse_entry_timestamp(entry)
    if timestamp is None:
        return False
    return timestamp >= invocation_started_at - timedelta(
        seconds=CURRENT_PROMPT_LOOKBACK_SECONDS
    )


def find_current_command(
    entries: list[dict], command_name: str, invocation_started_at: datetime
) -> tuple[int, str]:
    recent_commands: list[tuple[int, str]] = []
    for idx, entry in enumerate(entries):
        prompt = extract_command_args_from_user_entry(entry, command_name)
        if not prompt or not is_recent_command_entry(entry, invocation_started_at):
            continue
        recent_commands.append((idx, prompt))
    return recent_commands[-1] if recent_commands else (-1, "")


def extract_prompt_from_session(
    session_id: str, command_name: str, invocation_started_at: datetime
) -> tuple[int, str]:
    for attempt in range(SESSION_PROMPT_RETRY_COUNT):
        entries = load_session_entries(session_id)
        anchor_index, prompt = find_current_command(
            entries, command_name, invocation_started_at
        )
        if prompt:
            return anchor_index, prompt
        if attempt + 1 < SESSION_PROMPT_RETRY_COUNT:
            time.sleep(SESSION_PROMPT_RETRY_SLEEP_SECONDS)
    return -1, ""


def find_anchor_index_from_session_once(
    session_id: str, command_name: str, invocation_started_at: datetime
) -> int:
    entries = load_session_entries(session_id)
    anchor_index, _ = find_current_command(entries, command_name, invocation_started_at)
    return anchor_index


def extract_visible_text_from_entry(entry: dict) -> str:
    message = entry.get("message") or {}
    content = message.get("content")
    entry_type = entry.get("type")
    if entry_type == "user":
        if not isinstance(content, str) or "<command-message>" in content:
            return ""
        return content.strip()
    if not isinstance(content, list):
        return ""
    texts: list[str] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text":
            text = block.get("text")
            if isinstance(text, str) and text.strip():
                texts.append(text.strip())
    return "\n".join(texts).strip()


def collect_visible_transcript_blocks(
    entries: list[dict], anchor_index: int
) -> list[str]:
    if not entries or anchor_index < 0:
        return []
    selected: list[str] = []
    for entry in reversed(entries[:anchor_index]):
        if entry.get("type") not in {"user", "assistant"}:
            continue
        if entry.get("isMeta") is True:
            continue
        text = extract_visible_text_from_entry(entry)
        if not text:
            continue
        label = "User" if entry.get("type") == "user" else "Assistant"
        selected.append(f"{label}: {text}")
    selected.reverse()
    return selected


def summarize_older_context(
    older_blocks: list[str],
    workspace_root: Path,
    claude_bin: Path = CLAUDE_BIN,
) -> str:
    if not older_blocks:
        return ""
    older_context = "\n\n".join(older_blocks)
    if len(older_context) > OLDER_CONTEXT_SUMMARY_MAX_CHARS:
        older_context = older_context[-OLDER_CONTEXT_SUMMARY_MAX_CHARS:]

    prompt = "\n\n".join(
        [
            "Summarize the older conversation context for a follow-up Claude Code request.",
            f"Keep it to at most {OLDER_CONTEXT_SUMMARY_MAX_LINES} short bullet lines.",
            "Preserve only durable context: user goal, constraints, decisions, repo facts, and unresolved questions.",
            "Omit greetings, filler, and temporary execution chatter.",
            "Return only the summary bullets.",
            f"Older conversation:\n{older_context}",
        ]
    )
    argv = [
        str(claude_bin),
        "-p",
        "--model",
        "haiku",
        "--effort",
        "low",
        "--disable-slash-commands",
        "--no-session-persistence",
        "--tools",
        "",
    ]
    env = os.environ.copy()
    env["TERM"] = "dumb"
    env["PARENTS_ACTIVE"] = "1"
    try:
        completed = run_command(argv, workspace_root, env, input_text=prompt)
    except OSError:
        return ""
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def build_recent_context(
    workspace_root: Path,
    session_id: str | None,
    anchor_index: int,
    claude_bin: Path = CLAUDE_BIN,
) -> str:
    if not session_id:
        return ""
    entries = load_session_entries(session_id)
    if not entries:
        return ""
    if anchor_index < 0:
        anchor_index = len(entries)
    blocks = collect_visible_transcript_blocks(entries, anchor_index)
    if not blocks:
        return ""

    summary = ""
    if len(blocks) > VISIBLE_TRANSCRIPT_MAX_MESSAGES:
        older_blocks = blocks[:-VISIBLE_TRANSCRIPT_MAX_MESSAGES]
        blocks = blocks[-VISIBLE_TRANSCRIPT_MAX_MESSAGES:]
        summary = summarize_older_context(
            older_blocks, workspace_root, claude_bin=claude_bin
        )

    context = "\n\n".join(blocks)
    if len(context) > VISIBLE_TRANSCRIPT_MAX_CHARS:
        context = context[-VISIBLE_TRANSCRIPT_MAX_CHARS:]
    if summary:
        context = f"Summary of earlier conversation:\n{summary}\n\nRecent conversation:\n{context}"
    return context


def parse_command_arguments(raw_args: str) -> ParsedCommand:
    try:
        tokens = shlex.split(raw_args)
    except ValueError:
        tokens = raw_args.split()
    parsed = ParsedCommand()
    idx = 0
    while idx < len(tokens):
        token = tokens[idx]
        if token == "--why":
            parsed.why = True
            idx += 1
            continue
        if token == "--dry-run":
            parsed.dry_run = True
            idx += 1
            continue
        if token in {"--model", "--mode", "--effort"}:
            if idx + 1 >= len(tokens):
                raise ValueError(f"Missing value for {token}")
            value = tokens[idx + 1].strip().lower()
            if token == "--model":
                parsed.model = value
            elif token == "--mode":
                parsed.mode = value
            else:
                parsed.effort = value
            idx += 2
            continue
        parsed.task = " ".join(tokens[idx:]).strip()
        break
    if not parsed.task:
        raise ValueError("No task provided. Use the command like `/parent <goal>`.")
    if parsed.model not in VALID_MODELS:
        raise ValueError(f"Invalid --model value: {parsed.model}")
    if parsed.mode not in VALID_MODES:
        raise ValueError(f"Invalid --mode value: {parsed.mode}")
    if parsed.effort not in VALID_EFFORTS:
        raise ValueError(f"Invalid --effort value: {parsed.effort}")
    return parsed


def clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))


def contains_any(text: str, phrases: Iterable[str]) -> bool:
    return any(phrase in text for phrase in phrases)


def count_meaningful_files(root: Path) -> int:
    count = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in NON_SOURCE_DIRS for part in path.parts):
            continue
        count += 1
        if count > 20:
            return count
    return count


def extract_scores(task: str, workspace_root: Path) -> tuple[FeatureScores, list[str]]:
    text = task.lower()
    reasons: list[str] = []
    plan_terms = (
        "plan",
        "planning",
        "design",
        "architecture",
        "strategy",
        "analyze",
        "analysis",
        "research",
        "review",
        "계획",
        "설계",
        "전략",
        "분석",
        "조사",
        "리뷰",
    )
    execute_terms = (
        "implement",
        "fix",
        "change",
        "modify",
        "create",
        "write",
        "build",
        "add",
        "refactor",
        "debug",
        "test",
        "구현",
        "수정",
        "생성",
        "작성",
        "추가",
        "리팩터링",
        "디버깅",
        "테스트",
    )
    high_risk_terms = (
        "migration",
        "production",
        "deploy",
        "auth",
        "authentication",
        "authorization",
        "security",
        "billing",
        "secret",
        "permission",
        "database",
        "public api",
        "breaking change",
        "rewrite history",
        "마이그레이션",
        "배포",
        "인증",
        "인가",
        "보안",
        "결제",
        "권한",
        "비밀",
        "데이터베이스",
    )
    multi_scope_terms = (
        "system",
        "platform",
        "framework",
        "workflow",
        "end-to-end",
        "whole",
        "entire",
        "across",
        "multi-file",
        "architecture",
        "시스템",
        "플랫폼",
        "프레임워크",
        "워크플로",
        "전체",
        "전부",
        "여러 파일",
        "아키텍처",
    )
    simple_terms = (
        "rename variable",
        "typo",
        "summarize",
        "translate",
        "rewrite this sentence",
        "format",
        "설명",
        "요약",
        "번역",
        "오타",
        "포맷",
    )
    vague_terms = (
        "improve",
        "better",
        "somehow",
        "something",
        "help me",
        "알아서",
        "개선",
        "좋게",
        "도와줘",
    )
    research_terms = (
        "latest",
        "recent",
        "current",
        "look up",
        "찾아봐",
        "최신",
        "요즘",
    )
    debugging_terms = ("debug", "investigate", "trace", "root cause", "디버그", "원인")
    greenfield_terms = (
        "from scratch",
        "greenfield",
        "new system",
        "새 시스템",
        "처음부터",
    )

    scope = 0
    ambiguity = 0
    risk = 0
    depth = 0
    research = 0
    action = 0

    if contains_any(text, simple_terms):
        reasons.append("SIMPLE_BOUNDED_TASK")
    if contains_any(text, multi_scope_terms):
        scope = max(scope, 2)
        reasons.append("MULTI_FILE_OR_MULTI_STEP")
    if contains_any(text, greenfield_terms):
        scope = 3
        depth = max(depth, 3)
        reasons.append("GREENFIELD_SYSTEM_REQUEST")
    if contains_any(text, high_risk_terms):
        risk = 3
        reasons.append("HIGH_RISK_CHANGE")
    elif contains_any(text, ("dependency", "config", "ci", "test", "테스트", "설정")):
        risk = 2
    elif contains_any(text, execute_terms):
        risk = 1

    if contains_any(
        text,
        ("architecture", "research", "strategy", "design", "아키텍처", "연구", "설계"),
    ):
        depth = max(depth, 3)
    elif contains_any(text, debugging_terms):
        depth = max(depth, 2)
    elif contains_any(text, execute_terms):
        depth = max(depth, 1)

    if contains_any(text, research_terms):
        research = 2
        reasons.append("EXTERNAL_RESEARCH_REQUIRED")
    elif "repo" in text or "repository" in text or "코드베이스" in text:
        research = 1

    if contains_any(text, execute_terms):
        action = 2
    elif contains_any(text, plan_terms):
        action = 0
    else:
        action = 1

    if contains_any(text, plan_terms) and contains_any(text, execute_terms):
        ambiguity = max(ambiguity, 1)
    if contains_any(text, vague_terms):
        ambiguity = max(ambiguity, 2)
        reasons.append("HIGH_AMBIGUITY")
    if not contains_any(text, execute_terms) and scope >= 2:
        ambiguity = max(ambiguity, 2)
    if "?" in task and action < 2:
        ambiguity = max(ambiguity, 1)

    meaningful_files = count_meaningful_files(workspace_root)
    if meaningful_files == 0 and contains_any(
        text, greenfield_terms + multi_scope_terms
    ):
        scope = 3
        depth = max(depth, 3)
        ambiguity = max(ambiguity, 2)
        reasons.append("GREENFIELD_SYSTEM_REQUEST")

    if scope == 0 and contains_any(text, execute_terms):
        scope = 1
    if len(task.split()) > 40:
        scope = clamp(scope + 1, 0, 3)

    scores = FeatureScores(
        scope=clamp(scope, 0, 3),
        ambiguity=clamp(ambiguity, 0, 3),
        risk=clamp(risk, 0, 3),
        depth=clamp(depth, 0, 3),
        research=clamp(research, 0, 2),
        action=clamp(action, 0, 2),
    )
    return scores, dedupe(reasons)


def dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def select_mode(
    parsed: ParsedCommand, scores: FeatureScores, task: str
) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if parsed.mode != "auto":
        reasons.append("USER_FORCED_MODE")
        return parsed.mode, reasons
    text = task.lower()
    if scores.risk >= 3 or scores.depth == 3 or scores.total >= 8:
        return "plan", reasons
    if scores.ambiguity >= 2 and scores.scope >= 2:
        return "plan", reasons
    if contains_any(
        text, ("plan", "design", "strategy", "계획", "설계", "전략", "분석")
    ):
        return "plan", reasons
    return "execute", reasons


def select_model(
    profile: Profile, parsed: ParsedCommand, scores: FeatureScores, mode: str
) -> tuple[str, list[str], bool]:
    reasons: list[str] = []
    would_have_used_opus = False
    if parsed.model != "auto":
        if parsed.model not in profile.allowed_models:
            raise ValueError(
                f"{profile.command_name} does not allow model `{parsed.model}`. "
                f"Use one of: {', '.join(profile.allowed_models)}."
            )
        reasons.append("USER_FORCED_MODEL")
        return parsed.model, reasons, False

    if (
        mode == "execute"
        and scores.total <= 3
        and scores.ambiguity == 0
        and scores.risk == 0
    ):
        return "haiku", reasons, False

    if scores.total >= 9 or scores.risk >= 3 or scores.depth == 3 or scores.scope == 3:
        would_have_used_opus = True
        if "opus" in profile.allowed_models:
            return "opus", reasons, would_have_used_opus
        reasons.append("PROFILE_NO_OPUS")
        return "sonnet", reasons, would_have_used_opus

    return "sonnet", reasons, False


def select_confidence(
    parsed: ParsedCommand,
    scores: FeatureScores,
    mode: str,
    model: str,
    would_have_used_opus: bool,
) -> str:
    if parsed.model != "auto" or parsed.mode != "auto" or parsed.effort != "auto":
        return "high"
    boundary = scores.total in {3, 4, 8, 9}
    conflicts = 0
    if mode == "execute" and scores.ambiguity >= 2:
        conflicts += 1
    if (
        mode == "plan"
        and parsed.mode == "auto"
        and scores.action >= 2
        and scores.total <= 6
    ):
        conflicts += 1
    if model == "haiku" and scores.depth >= 2:
        conflicts += 1
    if would_have_used_opus and mode != "plan":
        conflicts += 1
    if (
        scores.ambiguity >= 2
        and scores.scope >= 2
        and scores.depth < 3
        and scores.risk < 3
    ):
        conflicts += 2
    if conflicts >= 2:
        return "low"
    if boundary or conflicts == 1:
        return "medium"
    return "high"


def effort_rank(value: str) -> int:
    return EFFORT_ORDER.index(value)


def rank_to_effort(rank: int) -> str:
    return EFFORT_ORDER[clamp(rank, 0, len(EFFORT_ORDER) - 1)]


def select_effort(
    parsed: ParsedCommand, scores: FeatureScores, mode: str, model: str
) -> tuple[str, str, list[str]]:
    reasons: list[str] = []
    if parsed.effort != "auto":
        selected = parsed.effort
        reasons.append("USER_FORCED_EFFORT")
    else:
        if scores.total <= 2:
            selected = "low"
        elif scores.total <= 5:
            selected = "medium"
        elif scores.total <= 8:
            selected = "high"
        else:
            selected = "max"

    effective_rank = effort_rank(selected)
    if mode == "plan" and effective_rank < effort_rank("high"):
        effective_rank = effort_rank("high")
        reasons.append("EFFORT_CLAMPED_BY_MODE")
    if mode == "execute" and effective_rank > effort_rank("high"):
        effective_rank = effort_rank("high")
        reasons.append("EFFORT_CLAMPED_BY_MODE")

    model_cap = {"haiku": "medium", "sonnet": "max", "opus": "max"}[model]
    if effective_rank > effort_rank(model_cap):
        effective_rank = effort_rank(model_cap)
        reasons.append("EFFORT_CLAMPED_BY_MODEL")
    effective = rank_to_effort(effective_rank)
    return selected, effective, dedupe(reasons)


def choose_route(
    profile: Profile, parsed: ParsedCommand, workspace_root: Path
) -> RouteDecision:
    scores, reasons = extract_scores(parsed.task, workspace_root)
    mode, mode_reasons = select_mode(parsed, scores, parsed.task)
    reasons.extend(mode_reasons)
    model, model_reasons, would_have_used_opus = select_model(
        profile, parsed, scores, mode
    )
    reasons.extend(model_reasons)
    confidence = select_confidence(parsed, scores, mode, model, would_have_used_opus)
    if (
        confidence == "low"
        and parsed.model == "auto"
        and parsed.mode == "auto"
        and parsed.effort == "auto"
    ):
        model = "sonnet"
        mode = "plan"
        reasons.append("LOW_CONFIDENCE_SAFE_FALLBACK")
    if mode == "plan" and model == "haiku":
        raise ValueError(
            "`haiku` cannot be used in plan mode. Use `sonnet`, `opus`, or mode `execute`."
        )
    selected_effort, effective_effort, effort_reasons = select_effort(
        parsed, scores, mode, model
    )
    reasons.extend(effort_reasons)
    return RouteDecision(
        profile=profile.name,
        request_text=parsed.task,
        selected_model=model,
        selected_mode=mode,
        selected_effort=selected_effort,
        effective_effort=effective_effort,
        confidence=confidence,
        reason_codes=dedupe(reasons),
        scores=scores,
        explicit_model=None if parsed.model == "auto" else parsed.model,
        explicit_mode=None if parsed.mode == "auto" else parsed.mode,
        explicit_effort=None if parsed.effort == "auto" else parsed.effort,
    )


def build_child_prompt(decision: RouteDecision, recent_context: str) -> str:
    parts = [
        "You are continuing an existing Claude Code conversation after an internal router selected your model, mode, and effort.",
        "Respond directly to the user's request.",
        "Do not mention routing, internal tools, model choice, effort levels, or child-session execution.",
        "Do not invoke /parent or /parent-no-opus.",
    ]
    if decision.selected_mode == "plan":
        parts.append(
            "Produce a concrete implementation plan only. Do not claim that you already made changes."
        )
    else:
        parts.append(
            "Act as the assistant handling the request normally inside Claude Code."
        )
    if recent_context:
        parts.append(f"Visible conversation transcript so far:\n{recent_context}")
    parts.append(f"User request:\n{decision.request_text}")
    return "\n\n".join(parts)


def run_command(
    command: list[str],
    workspace_root: Path,
    env: dict[str, str],
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(workspace_root),
        text=True,
        capture_output=True,
        input=input_text,
        env=env,
        check=False,
    )


def execute_route(
    decision: RouteDecision,
    workspace_root: Path,
    recent_context: str,
    claude_bin: Path = CLAUDE_BIN,
) -> ExecutionResult:
    if os.environ.get("PARENTS_ACTIVE") == "1":
        return ExecutionResult(
            ok=False,
            stdout="",
            stderr="Recursive /parent invocation is blocked.",
            exit_code=2,
            argv=[],
        )

    argv = [
        str(claude_bin),
        "-p",
        "--model",
        decision.selected_model,
        "--effort",
        decision.effective_effort,
        "--disable-slash-commands",
        "--no-session-persistence",
    ]
    if decision.selected_mode == "plan":
        argv.extend(
            [
                "--permission-mode",
                "auto",
                "--tools",
                "Read,Grep,Glob",
                "--allowed-tools",
                "Read,Grep,Glob",
            ]
        )
    else:
        argv.extend(["--permission-mode", "auto"])
    child_prompt = build_child_prompt(decision, recent_context)
    env = os.environ.copy()
    env["TERM"] = "dumb"
    env["PARENTS_ACTIVE"] = "1"
    try:
        completed = run_command(argv, workspace_root, env, input_text=child_prompt)
    except OSError as exc:
        return ExecutionResult(
            ok=False, stdout="", stderr=str(exc), exit_code=127, argv=argv
        )
    return ExecutionResult(
        ok=completed.returncode == 0,
        stdout=completed.stdout.strip(),
        stderr=completed.stderr.strip(),
        exit_code=completed.returncode,
        argv=argv,
    )


def summarize_text(text: str, limit: int = 1000) -> str:
    compact = text.strip()
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def get_child_arg_value(argv: list[str], flag: str) -> str | None:
    try:
        index = argv.index(flag)
    except ValueError:
        return None
    next_index = index + 1
    if next_index >= len(argv):
        return None
    return argv[next_index]


def explain_decision(profile: Profile, decision: RouteDecision) -> str:
    model = decision.selected_model.capitalize()
    mode = decision.selected_mode
    effort = decision.effective_effort
    if profile.name == "parent-no-opus" and "PROFILE_NO_OPUS" in decision.reason_codes:
        return (
            f"I'll stay on {model} in {mode} mode with {effort} effort because this command excludes Opus "
            "and the request still looks broad or risky."
        )
    return f"I'll use {model} in {mode} mode with {effort} effort based on the request scope, risk, and ambiguity."


def fallback_transition_hint(decision: RouteDecision) -> str:
    if "LOW_CONFIDENCE_SAFE_FALLBACK" not in decision.reason_codes:
        return ""
    return (
        "I started with a plan because the request still looked broad or ambiguous enough "
        "that changing code directly would be risky."
    )


def profile_transition_hint(profile: Profile, decision: RouteDecision) -> str:
    if profile.name == "parent-no-opus" and "PROFILE_NO_OPUS" in decision.reason_codes:
        return (
            "I stayed on Sonnet and started with a plan because this command excludes Opus "
            "for broad or risky requests."
        )
    return ""


def clamp_transition_hint(decision: RouteDecision) -> str:
    if "USER_FORCED_EFFORT" not in decision.reason_codes:
        return ""
    if "EFFORT_CLAMPED_BY_MODEL" in decision.reason_codes:
        return (
            f"I adjusted the requested effort from {decision.selected_effort} to {decision.effective_effort} "
            f"because {decision.selected_model} cannot safely use a higher effort setting."
        )
    if "EFFORT_CLAMPED_BY_MODE" in decision.reason_codes:
        return (
            f"I adjusted the requested effort from {decision.selected_effort} to {decision.effective_effort} "
            f"because {decision.selected_mode} mode requires a different effort level."
        )
    return ""


def write_logs(
    workspace_root: Path,
    profile: Profile,
    command_name: str,
    parsed: ParsedCommand,
    decision: RouteDecision,
    result: ExecutionResult | None,
) -> None:
    timestamp = datetime.now(timezone.utc)
    date_dir = workspace_root / RUNS_DIR / timestamp.strftime("%Y-%m-%d")
    date_dir.mkdir(parents=True, exist_ok=True)
    stem = timestamp.strftime("%Y%m%dT%H%M%SZ")
    base = date_dir / f"{stem}-{profile.name}"
    record = {
        "timestamp": timestamp.isoformat(),
        "command_name": command_name,
        "profile": profile.name,
        "request_text": parsed.task,
        "requested_model": None if parsed.model == "auto" else parsed.model,
        "requested_mode": None if parsed.mode == "auto" else parsed.mode,
        "requested_effort": None if parsed.effort == "auto" else parsed.effort,
        "why_requested": parsed.why,
        "dry_run": parsed.dry_run,
        "scores": asdict(decision.scores),
        "selected_model": decision.selected_model,
        "selected_mode": decision.selected_mode,
        "selected_effort": decision.selected_effort,
        "effective_effort": decision.effective_effort,
        "confidence": decision.confidence,
        "reason_codes": decision.reason_codes,
        "execution_status": None
        if result is None
        else ("ok" if result.ok else "failed"),
        "exit_code": None if result is None else result.exit_code,
        "child_argv_summary": None if result is None else result.argv[:-1],
        "stdout_summary": None if result is None else summarize_text(result.stdout),
        "stderr_summary": None if result is None else summarize_text(result.stderr),
    }
    base.with_suffix(".json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    markdown = [
        "# Parent Run",
        "",
        "## Request",
        parsed.task,
        "",
        "## Route Decision",
        f"- Command: `{command_name}`",
        f"- Profile: `{profile.name}`",
        f"- Model: `{decision.selected_model}`",
        f"- Mode: `{decision.selected_mode}`",
        f"- Selected effort: `{decision.selected_effort}`",
        f"- Effective effort: `{decision.effective_effort}`",
        f"- Confidence: `{decision.confidence}`",
        f"- Reason codes: {', '.join(decision.reason_codes) if decision.reason_codes else '(none)'}",
        "",
        "## Execution Summary",
    ]
    if result is None:
        markdown.append("- Dry run: yes")
    else:
        markdown.extend(
            [
                f"- Status: `{'ok' if result.ok else 'failed'}`",
                f"- Exit code: `{result.exit_code}`",
                f"- Child permission mode: `{get_child_arg_value(result.argv, '--permission-mode') or '(none)'}`",
                f"- Child tools: `{get_child_arg_value(result.argv, '--tools') or '(none)'}`",
                f"- STDERR: {summarize_text(result.stderr) or '(empty)'}",
            ]
        )
    base.with_suffix(".md").write_text("\n".join(markdown) + "\n", encoding="utf-8")


def resolve_profile(cli_args: argparse.Namespace) -> Profile:
    if cli_args.command_profile:
        if cli_args.command_profile not in PROFILES:
            raise ValueError(f"Unknown command profile: {cli_args.command_profile}")
        return PROFILES[cli_args.command_profile]
    if cli_args.command_name in COMMAND_TO_PROFILE:
        return COMMAND_TO_PROFILE[cli_args.command_name]
    raise ValueError(f"Unknown command name: {cli_args.command_name}")


def load_request_text(
    cli_args: argparse.Namespace, remaining: list[str]
) -> tuple[int, str]:
    started_at = parse_started_at(cli_args.started_at) or datetime.now(timezone.utc)
    prompt = sys.stdin.read().strip()
    if prompt:
        if cli_args.session_id:
            anchor_index = find_anchor_index_from_session_once(
                cli_args.session_id,
                cli_args.command_name,
                started_at,
            )
            return anchor_index, prompt
        return -1, prompt
    if remaining:
        return -1, " ".join(remaining).strip()
    if cli_args.session_id:
        return extract_prompt_from_session(
            cli_args.session_id, cli_args.command_name, started_at
        )
    return -1, ""


def recovery_hint(decision: RouteDecision) -> str:
    if decision.selected_mode == "execute":
        return "Next step: retry with `--mode plan` if you want a safer plan before making changes."
    return "Next step: retry with `--dry-run --why` to inspect the route without running the child request."


def format_failure(decision: RouteDecision, result: ExecutionResult) -> str:
    stderr = summarize_text(result.stderr) or "(empty)"
    return (
        f"The routed Claude invocation failed with exit code {result.exit_code}.\n\n"
        f"Route: {decision.selected_model} in {decision.selected_mode} mode with {decision.effective_effort} effort.\n\n"
        f"{stderr}\n\n{recovery_hint(decision)}"
    )


def capture_failure_message(command_name: str) -> str:
    return (
        "Could not capture the current command arguments.\n\n"
        f"Retry like `{command_name} <goal>`, for example `{command_name} fix the flaky integration test`."
    )


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv
    workspace_root = detect_workspace_root()
    cli_args, remaining = parse_cli_args(argv)
    try:
        profile = resolve_profile(cli_args)
        anchor_index, raw_request = load_request_text(cli_args, remaining)
        if not raw_request:
            raise ValueError(capture_failure_message(cli_args.command_name))
        parsed = parse_command_arguments(raw_request)
        recent_context = build_recent_context(
            workspace_root, cli_args.session_id, anchor_index
        )
        decision = choose_route(profile, parsed, workspace_root)
    except ValueError as exc:
        print(str(exc))
        return 2

    if parsed.dry_run:
        write_logs(
            workspace_root, profile, cli_args.command_name, parsed, decision, None
        )
        message = explain_decision(profile, decision)
        print(message)
        return 0

    result = execute_route(decision, workspace_root, recent_context)
    write_logs(workspace_root, profile, cli_args.command_name, parsed, decision, result)
    if not result.ok:
        print(format_failure(decision, result))
        return result.exit_code or 1

    output = result.stdout or ""
    if parsed.why:
        output = explain_decision(profile, decision) + "\n\n" + output
    elif fallback_transition_hint(decision):
        output = fallback_transition_hint(decision) + "\n\n" + output
    elif profile_transition_hint(profile, decision):
        output = profile_transition_hint(profile, decision) + "\n\n" + output
    elif clamp_transition_hint(decision):
        output = clamp_transition_hint(decision) + "\n\n" + output
    print(output.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
