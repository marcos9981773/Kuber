"""
kuber/views/common/ansi_parser.py
Parses ANSI escape codes and renders colored text into a QTextEdit.

Supports:
- Standard foreground colors (30–37, 90–97)
- Standard background colors (40–47, 100–107)
- 256-color mode (38;5;N / 48;5;N)
- 24-bit true-color mode (38;2;R;G;B / 48;2;R;G;B)
- Bold (1), dim (2), italic (3), underline (4), reset (0)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Sequence

from PyQt5.QtGui import QColor, QFont, QTextCharFormat, QTextCursor
from PyQt5.QtWidgets import QTextEdit

# Regex that matches a single CSI SGR sequence: ESC[ ... m
_ANSI_RE = re.compile(r"\x1b\[([0-9;]*)m")

# ── Standard 4-bit color palette ────────────────────────────────────────────

_STANDARD_COLORS: dict[int, str] = {
    0: "#000000",   # Black
    1: "#cc0000",   # Red
    2: "#4e9a06",   # Green
    3: "#c4a000",   # Yellow
    4: "#3465a4",   # Blue
    5: "#75507b",   # Magenta
    6: "#06989a",   # Cyan
    7: "#d3d7cf",   # White
}

_BRIGHT_COLORS: dict[int, str] = {
    0: "#555753",   # Bright Black (Gray)
    1: "#ef2929",   # Bright Red
    2: "#8ae234",   # Bright Green
    3: "#fce94f",   # Bright Yellow
    4: "#729fcf",   # Bright Blue
    5: "#ad7fa8",   # Bright Magenta
    6: "#34e2e2",   # Bright Cyan
    7: "#eeeeec",   # Bright White
}


def _color_256(n: int) -> QColor:
    """Convert a 256-color index to a QColor."""
    if 0 <= n <= 7:
        return QColor(_STANDARD_COLORS[n])
    if 8 <= n <= 15:
        return QColor(_BRIGHT_COLORS[n - 8])
    if 16 <= n <= 231:
        # 6×6×6 color cube
        n -= 16
        b = n % 6
        n //= 6
        g = n % 6
        r = n // 6
        return QColor(r * 51, g * 51, b * 51)
    if 232 <= n <= 255:
        # Grayscale ramp
        v = 8 + (n - 232) * 10
        return QColor(v, v, v)
    return QColor()


@dataclass
class _AnsiState:
    """Tracks the current SGR attribute state."""

    fg: QColor | None = None
    bg: QColor | None = None
    bold: bool = False
    dim: bool = False
    italic: bool = False
    underline: bool = False

    def to_format(self) -> QTextCharFormat:
        """Build a QTextCharFormat from the current state."""
        fmt = QTextCharFormat()
        if self.fg is not None:
            fmt.setForeground(self.fg)
        if self.bg is not None:
            fmt.setBackground(self.bg)
        if self.bold:
            fmt.setFontWeight(QFont.Bold)
        if self.italic:
            fmt.setFontItalic(True)
        if self.underline:
            fmt.setFontUnderline(True)
        return fmt

    def reset(self) -> None:
        """Reset all attributes to defaults."""
        self.fg = None
        self.bg = None
        self.bold = False
        self.dim = False
        self.italic = False
        self.underline = False


def _parse_sgr(params: Sequence[int], state: _AnsiState) -> None:
    """Apply a list of SGR parameter codes to *state*."""
    it = iter(params)
    for code in it:
        if code == 0:
            state.reset()
        elif code == 1:
            state.bold = True
        elif code == 2:
            state.dim = True
        elif code == 3:
            state.italic = True
        elif code == 4:
            state.underline = True
        elif code == 22:
            state.bold = False
            state.dim = False
        elif code == 23:
            state.italic = False
        elif code == 24:
            state.underline = False
        elif 30 <= code <= 37:
            state.fg = QColor(_STANDARD_COLORS[code - 30])
        elif code == 38:
            # Extended foreground: 38;5;N or 38;2;R;G;B
            try:
                mode = next(it)
                if mode == 5:
                    state.fg = _color_256(next(it))
                elif mode == 2:
                    r, g, b = next(it), next(it), next(it)
                    state.fg = QColor(r, g, b)
            except StopIteration:
                pass
        elif code == 39:
            state.fg = None
        elif 40 <= code <= 47:
            state.bg = QColor(_STANDARD_COLORS[code - 40])
        elif code == 48:
            # Extended background: 48;5;N or 48;2;R;G;B
            try:
                mode = next(it)
                if mode == 5:
                    state.bg = _color_256(next(it))
                elif mode == 2:
                    r, g, b = next(it), next(it), next(it)
                    state.bg = QColor(r, g, b)
            except StopIteration:
                pass
        elif code == 49:
            state.bg = None
        elif 90 <= code <= 97:
            state.fg = QColor(_BRIGHT_COLORS[code - 90])
        elif 100 <= code <= 107:
            state.bg = QColor(_BRIGHT_COLORS[code - 100])


@dataclass
class AnsiSegment:
    """One chunk of text with its resolved formatting."""

    text: str
    fmt: QTextCharFormat = field(default_factory=QTextCharFormat)


def parse_ansi(text: str) -> list[AnsiSegment]:
    """
    Parse *text* containing ANSI SGR escape sequences.

    Returns:
        Ordered list of :class:`AnsiSegment` objects, each carrying the plain
        text and the ``QTextCharFormat`` that should be applied when inserting
        it into a ``QTextEdit``.
    """
    segments: list[AnsiSegment] = []
    state = _AnsiState()
    last_end = 0

    for match in _ANSI_RE.finditer(text):
        # Text before this escape
        if match.start() > last_end:
            plain = text[last_end:match.start()]
            segments.append(AnsiSegment(text=plain, fmt=state.to_format()))

        # Parse the SGR codes
        raw = match.group(1)
        codes = [int(c) for c in raw.split(";") if c] if raw else [0]
        _parse_sgr(codes, state)
        last_end = match.end()

    # Remaining text after last escape
    if last_end < len(text):
        segments.append(AnsiSegment(text=text[last_end:], fmt=state.to_format()))

    return segments


def render_ansi(target: QTextEdit, text: str) -> None:
    """
    Clear *target* and insert *text* with ANSI colors rendered.

    This replaces a simple ``target.setPlainText(text)`` call and properly
    renders any ANSI SGR escape sequences as colored / styled text.
    """
    target.clear()
    cursor: QTextCursor = target.textCursor()
    cursor.beginEditBlock()
    for segment in parse_ansi(text):
        cursor.insertText(segment.text, segment.fmt)
    cursor.endEditBlock()
    target.setTextCursor(cursor)


def strip_ansi(text: str) -> str:
    """Remove all ANSI escape sequences, returning plain text."""
    return _ANSI_RE.sub("", text)

