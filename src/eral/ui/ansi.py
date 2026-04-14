"""ANSI terminal rendering utilities for erAL TUI.

Provides 256-color output, CJK-aware text alignment, and progress-bar
rendering.  Pure standard library — no external dependencies.
"""

from __future__ import annotations

import os
import unicodedata

# ── Color constants (256-color palette) ────────────────────────────

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

# Foreground shortcuts — 256-color via \033[38;5;Xm
FG_WHITE = 255
FG_GRAY = 245
FG_DARK_GRAY = 240
FG_BLUE = 69       # eraTW header blue
FG_CYAN = 80       # 気力 bar
FG_GREEN = 34       # 体力 bar (healthy)
FG_YELLOW = 220     # warning / palam
FG_RED = 196        # critical
FG_MAGENTA = 170    # relationship / affection
FG_ORANGE = 208     # marks / tags

# Background shortcuts
BG_BAR_EMPTY = 236  # dark gray track


def fg(color_code: int) -> str:
    """Return ANSI escape for a 256-color foreground."""
    return f"\033[38;5;{color_code}m"


def bg(color_code: int) -> str:
    """Return ANSI escape for a 256-color background."""
    return f"\033[48;5;{color_code}m"


def colorize(
    text: str,
    fg_color: int | None = None,
    bg_color: int | None = None,
    bold: bool = False,
) -> str:
    """Wrap *text* in ANSI color escapes."""
    parts: list[str] = []
    if bold:
        parts.append(BOLD)
    if fg_color is not None:
        parts.append(fg(fg_color))
    if bg_color is not None:
        parts.append(bg(bg_color))
    parts.append(text)
    parts.append(RESET)
    return "".join(parts)


# ── CJK width helpers ──────────────────────────────────────────────

def cjk_width(text: str) -> int:
    """Return the display width of *text*, counting wide chars as 2."""
    width = 0
    for ch in text:
        eaw = unicodedata.east_asian_width(ch)
        width += 2 if eaw in ("W", "F") else 1
    return width


def cjk_ljust(text: str, width: int, fillchar: str = " ") -> str:
    """Left-justify *text* to *width* display columns, CJK-aware."""
    pad = width - cjk_width(text)
    return text + fillchar * max(0, pad)


def cjk_rjust(text: str, width: int, fillchar: str = " ") -> str:
    """Right-justify *text* to *width* display columns, CJK-aware."""
    pad = width - cjk_width(text)
    return fillchar * max(0, pad) + text


def cjk_center(text: str, width: int, fillchar: str = " ") -> str:
    """Center *text* to *width* display columns, CJK-aware."""
    pad = width - cjk_width(text)
    left = pad // 2
    right = pad - left
    return fillchar * max(0, left) + text + fillchar * max(0, right)


# ── Progress bar ───────────────────────────────────────────────────

def bar(
    current: int,
    max_val: int,
    width: int = 20,
    fg_color: int = FG_GREEN,
    empty_color: int = BG_BAR_EMPTY,
    show_numbers: bool = True,
) -> str:
    """Render a colored progress bar like ``████████░░░░ 1500/2000``."""
    if max_val <= 0:
        ratio = 0.0
    else:
        ratio = max(0.0, min(1.0, current / max_val))

    filled = int(ratio * width)
    empty = width - filled

    bar_str = (
        fg(fg_color) + "█" * filled
        + fg(FG_DARK_GRAY) + "░" * empty
        + RESET
    )
    if show_numbers:
        num = f" {current}/{max_val}"
        bar_str += fg(FG_GRAY) + num + RESET
    return bar_str


def hp_color(current: int, max_val: int) -> int:
    """Pick a bar color based on health ratio."""
    if max_val <= 0:
        return FG_GRAY
    ratio = current / max_val
    if ratio > 0.6:
        return FG_GREEN
    if ratio > 0.3:
        return FG_YELLOW
    return FG_RED


# ── Terminal helpers ───────────────────────────────────────────────

def terminal_width() -> int:
    """Get current terminal column count."""
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 80


def clear_screen() -> None:
    """Clear the terminal screen."""
    print("\033[2J\033[H", end="", flush=True)


def separator(char: str = "─", width: int | None = None,
              color: int = FG_DARK_GRAY) -> str:
    """Return a full-width separator line."""
    w = width or terminal_width()
    return fg(color) + char * w + RESET


def header_separator(char: str = "═", width: int | None = None,
                     color: int = FG_BLUE) -> str:
    """Return a full-width header separator line."""
    w = width or terminal_width()
    return fg(color) + char * w + RESET
