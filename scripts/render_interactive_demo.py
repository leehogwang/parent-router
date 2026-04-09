#!/usr/bin/env python3

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable

import cv2
import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import pyte


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets" / "demo"
SOURCE_DIR = ASSETS / "source"
INPUT_LOG = SOURCE_DIR / "parent-interactive.in"
OUTPUT_LOG = SOURCE_DIR / "parent-interactive.out"
TIMING_LOG = SOURCE_DIR / "parent-interactive.time"
GIF_PATH = ASSETS / "parent-interactive.gif"
MP4_PATH = ASSETS / "parent-interactive.mp4"
TEXT_PATH = ASSETS / "parent-interactive.txt"

WIDTH = 1680
HEIGHT = 980
FPS = 12
GIF_SAMPLE_EVERY = 2
GIF_SCALE = 0.72
CANVAS_BG_TOP = np.array([13, 17, 26], dtype=np.float32)
CANVAS_BG_BOTTOM = np.array([24, 31, 46], dtype=np.float32)
WINDOW_BG = (10, 14, 22)
WINDOW_BORDER = (54, 66, 86)
HEADER_BG = (19, 25, 37)
TEXT_COLOR = (234, 239, 247)
MUTED_TEXT = (140, 153, 173)
COMMAND_TEXT = TEXT_COLOR
ACCENT = (255, 141, 84)
SUCCESS = (121, 214, 145)
KEYWORD_BG = (37, 52, 84)
COMMAND_BG = None
KEYWORDS = ("haiku", "sonnet", "opus", "plan", "execute", "effort")
ANSI_RE = re.compile(
    r"\x1b\[[0-?]*[ -/]*[@-~]|\x1b\][^\x07]*\x07|\x1b[@-_]",
    re.DOTALL,
)
SCRIPT_BOOKEND_RE = re.compile(
    rb"^Script started on .*?\n|\nScript done on .*?$",
    re.DOTALL,
)
BASE_FRAME: Image.Image | None = None
VIEWPORT_ROWS = 18


@dataclass(frozen=True)
class Event:
    kind: str
    delay: float
    size: int


@dataclass(frozen=True)
class Snapshot:
    delay: float
    rows: tuple[str, ...]


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/dejavu/DejaVuSansMono.ttf",
    )
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


TITLE_FONT = load_font(32)
SUBTITLE_FONT = load_font(20)
BODY_FONT = load_font(18)
CAPTION_FONT = load_font(17)


def parse_timing_log(path: Path) -> tuple[dict[str, str], list[Event]]:
    headers: dict[str, str] = {}
    events: list[Event] = []
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not raw_line:
            continue
        parts = raw_line.split(" ", 3)
        if len(parts) < 3:
            continue
        kind = parts[0]
        delay = float(parts[1])
        if kind == "H":
            if len(parts) == 4:
                headers[parts[2]] = parts[3]
            continue
        events.append(Event(kind=kind, delay=delay, size=int(parts[2])))
    return headers, events


def clamp_delay(delay: float) -> float:
    if delay <= 0.03:
        return 0.04
    if delay <= 0.20:
        return 0.07 + (delay * 0.25)
    return min(0.55, 0.14 + (delay * 0.06))


def build_snapshots(headers: dict[str, str], events: Iterable[Event]) -> list[Snapshot]:
    columns = int(headers.get("COLUMNS", "80"))
    lines = int(headers.get("LINES", "24"))
    screen = pyte.Screen(columns, lines)
    stream = pyte.Stream(screen)
    output_bytes = strip_script_bookends(OUTPUT_LOG.read_bytes())
    offset = 0
    previous_rows: tuple[str, ...] | None = None
    snapshots: list[Snapshot] = []
    for event in events:
        if event.kind != "O":
            continue
        chunk = output_bytes[offset : offset + event.size]
        offset += event.size
        if not chunk:
            continue
        stream.feed(chunk.decode("utf-8", errors="ignore"))
        rows = tuple(row.rstrip() for row in screen.display)
        if rows == previous_rows:
            continue
        snapshots.append(Snapshot(delay=clamp_delay(event.delay), rows=rows))
        previous_rows = rows
    return snapshots


def gradient_background() -> Image.Image:
    y = np.linspace(0.0, 1.0, HEIGHT, dtype=np.float32)[:, None]
    row = CANVAS_BG_TOP * (1.0 - y) + CANVAS_BG_BOTTOM * y
    image = np.repeat(row[:, None, :], WIDTH, axis=1)
    return Image.fromarray(np.uint8(image))


def strip_script_bookends(payload: bytes) -> bytes:
    return SCRIPT_BOOKEND_RE.sub(b"", payload).strip(b"\n") + (b"\n" if payload else b"")


def base_frame() -> Image.Image:
    global BASE_FRAME
    if BASE_FRAME is not None:
        return BASE_FRAME.copy()
    base = gradient_background()
    draw = ImageDraw.Draw(base)

    panel_x0 = 96
    panel_y0 = 84
    panel_x1 = WIDTH - 96
    panel_y1 = HEIGHT - 72

    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle(
        (panel_x0 + 12, panel_y0 + 18, panel_x1 + 12, panel_y1 + 18),
        radius=28,
        fill=(0, 0, 0, 140),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(14))
    base = Image.alpha_composite(base.convert("RGBA"), shadow).convert("RGB")
    draw = ImageDraw.Draw(base)

    draw.rounded_rectangle((panel_x0, panel_y0, panel_x1, panel_y1), radius=28, fill=WINDOW_BG, outline=WINDOW_BORDER, width=2)
    draw.rounded_rectangle((panel_x0, panel_y0, panel_x1, panel_y0 + 64), radius=28, fill=HEADER_BG)
    draw.rectangle((panel_x0, panel_y0 + 38, panel_x1, panel_y0 + 64), fill=HEADER_BG)

    for idx, color in enumerate(((255, 95, 86), (255, 189, 46), (39, 201, 63))):
        cx = panel_x0 + 34 + (idx * 22)
        cy = panel_y0 + 32
        draw.ellipse((cx - 7, cy - 7, cx + 7, cy + 7), fill=color)

    draw.text((panel_x0 + 96, panel_y0 + 18), "parents interactive demo", font=TITLE_FONT, fill=TEXT_COLOR)
    draw.text(
        (panel_x0 + 96, panel_y0 + 64),
        "Real Claude Code session with /parent routing",
        font=SUBTITLE_FONT,
        fill=MUTED_TEXT,
    )
    draw.text((panel_x0, 48), "cropped to terminal focus, paced and highlighted for readability", font=CAPTION_FONT, fill=MUTED_TEXT)
    BASE_FRAME = base
    return BASE_FRAME.copy()


def line_style(text: str) -> tuple[tuple[int, int, int], tuple[int, int, int] | None]:
    lowered = text.lower()
    if "/parent" in lowered or "/parent-no-opus" in lowered or "/help" in lowered:
        return COMMAND_TEXT, COMMAND_BG
    if any(keyword in lowered for keyword in KEYWORDS):
        return TEXT_COLOR, KEYWORD_BG
    if text.strip().startswith("❯"):
        return SUCCESS, None
    return TEXT_COLOR, None


def visible_focus_rows(rows: tuple[str, ...]) -> list[int]:
    focused: list[int] = []
    for index, row in enumerate(rows):
        lowered = row.lower()
        if "/parent" in lowered or "/parent-no-opus" in lowered or any(keyword in lowered for keyword in KEYWORDS):
            focused.append(index)
    return focused


def select_viewport_rows(rows: tuple[str, ...]) -> tuple[str, ...]:
    prompt_indices = [idx for idx, row in enumerate(rows) if "❯" in row or "/parent" in row.lower()]
    if prompt_indices:
        start = max(0, prompt_indices[0] - 2)
        end = min(len(rows), start + VIEWPORT_ROWS)
        return rows[start:end]
    non_empty = [idx for idx, row in enumerate(rows) if row.strip()]
    if not non_empty:
        return rows[:VIEWPORT_ROWS]
    end = min(len(rows), non_empty[-1] + 1)
    start = max(0, end - VIEWPORT_ROWS)
    return rows[start:end]


def draw_terminal(snapshot: Snapshot) -> Image.Image:
    base = base_frame()
    draw = ImageDraw.Draw(base)

    panel_x0 = 96
    panel_y0 = 84
    panel_x1 = WIDTH - 96
    panel_y1 = HEIGHT - 72

    viewport_rows = select_viewport_rows(snapshot.rows)
    focus_rows = visible_focus_rows(viewport_rows)
    pane_x = panel_x0 + 34
    pane_y = panel_y0 + 108
    line_height = 24
    line_box_height = 20
    pane_width = panel_x1 - panel_x0 - 68

    if focus_rows:
        top = pane_y + (min(focus_rows) * line_height) - 12
        bottom = pane_y + (max(focus_rows) * line_height) + 22
        draw.rounded_rectangle(
            (pane_x - 18, top, pane_x + pane_width + 18, bottom),
            radius=18,
            outline=ACCENT,
            width=2,
        )

    for row_index, row in enumerate(viewport_rows):
        text = row.rstrip()
        color, background = line_style(text)
        y = pane_y + (row_index * line_height)
        if background is not None and text:
            draw.rounded_rectangle(
                (pane_x - 8, y - 2, pane_x + pane_width - 6, y + line_box_height),
                radius=10,
                fill=background,
            )
        draw.text((pane_x, y), text or " ", font=BODY_FONT, fill=color)
    return base


def frame_stream(snapshots: list[Snapshot]):
    if not snapshots:
        raise RuntimeError("No terminal snapshots were generated from the capture.")
    for snapshot in snapshots:
        frame = np.array(draw_terminal(snapshot))
        frame_count = max(1, round(snapshot.delay * FPS))
        for _ in range(frame_count):
            yield frame
    for _ in range(int(FPS * 1.5)):
        yield frame


def write_video(snapshots: list[Snapshot]) -> None:
    writer = cv2.VideoWriter(
        str(MP4_PATH),
        cv2.VideoWriter_fourcc(*"mp4v"),
        FPS,
        (WIDTH, HEIGHT),
    )
    if not writer.isOpened():
        raise RuntimeError("Failed to open MP4 writer.")
    gif_frames: list[np.ndarray] = []
    frame_index = 0
    try:
        for frame in frame_stream(snapshots):
            frame_index += 1
            writer.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            if frame_index % GIF_SAMPLE_EVERY == 0:
                gif_frame = Image.fromarray(frame).resize(
                    (int(WIDTH * GIF_SCALE), int(HEIGHT * GIF_SCALE)),
                    Image.Resampling.LANCZOS,
                )
                gif_frames.append(np.array(gif_frame))
    finally:
        writer.release()
    imageio.mimsave(GIF_PATH, gif_frames, fps=max(1, FPS // GIF_SAMPLE_EVERY), loop=0)


def build_clean_transcript() -> str:
    input_text = strip_script_bookends(INPUT_LOG.read_bytes()).decode("utf-8", errors="ignore")
    commands = [line.strip() for line in input_text.splitlines() if line.strip().startswith("/")]

    output_text = strip_script_bookends(OUTPUT_LOG.read_bytes()).decode("utf-8", errors="ignore")
    clean = ANSI_RE.sub("", output_text).replace("\r", " ")
    clean = re.sub(r"\s+", " ", clean)

    summaries: list[str] = []
    for pattern in (
        r"I'll use .*?ambiguity\.",
        r"I'll stay .*?risky\.",
    ):
        match = re.search(pattern, clean)
        if match:
            summary = match.group(0)
            summary = summary.replace(
                "effortbasedontherequestscope,risk,andambiguity.",
                "effort based on the request scope, risk, and ambiguity.",
            )
            summary = summary.replace(
                "maxeffortbecausethiscommandexcludesOpusandtherequeststilllooksbroadorrisky.",
                "max effort because this command excludes Opus and the request still looks broad or risky.",
            )
            summaries.append(summary)

    lines = [
        "Interactive Claude Code session in ~/parents",
        "Rendered from a real terminal capture with crop and highlight effects.",
        "",
    ]
    for command in commands:
        lines.append(f"$ {command}")
    if summaries:
        lines.append("")
        lines.extend(summaries)
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    headers, events = parse_timing_log(TIMING_LOG)
    snapshots = build_snapshots(headers, events)
    write_video(snapshots)
    TEXT_PATH.write_text(build_clean_transcript(), encoding="utf-8")
    print(f"Wrote {GIF_PATH}")
    print(f"Wrote {MP4_PATH}")
    print(f"Wrote {TEXT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
