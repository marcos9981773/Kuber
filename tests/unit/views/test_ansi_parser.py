"""
tests/unit/views/test_ansi_parser.py
Tests for kuber/views/common/ansi_parser.py
"""
from __future__ import annotations

import pytest
from PyQt5.QtGui import QColor, QFont

from kuber.views.common.ansi_parser import (
    AnsiSegment,
    parse_ansi,
    render_ansi,
    strip_ansi,
)


class TestStripAnsi:
    """Tests for strip_ansi()."""

    def test_strip_removes_basic_codes(self) -> None:
        assert strip_ansi("\x1b[31mERROR\x1b[0m ok") == "ERROR ok"

    def test_strip_no_codes_returns_same(self) -> None:
        assert strip_ansi("plain text") == "plain text"

    def test_strip_multiple_codes(self) -> None:
        text = "\x1b[1;32mGREEN\x1b[0m \x1b[33mYELLOW\x1b[0m end"
        assert strip_ansi(text) == "GREEN YELLOW end"

    def test_strip_256_color(self) -> None:
        text = "\x1b[38;5;196mred256\x1b[0m"
        assert strip_ansi(text) == "red256"

    def test_strip_truecolor(self) -> None:
        text = "\x1b[38;2;255;128;0morange\x1b[0m"
        assert strip_ansi(text) == "orange"

    def test_strip_empty_string(self) -> None:
        assert strip_ansi("") == ""

    def test_strip_only_escape(self) -> None:
        assert strip_ansi("\x1b[0m") == ""


class TestParseAnsi:
    """Tests for parse_ansi()."""

    def test_plain_text_single_segment(self) -> None:
        segments = parse_ansi("hello world")
        assert len(segments) == 1
        assert segments[0].text == "hello world"

    def test_red_text_has_foreground(self) -> None:
        segments = parse_ansi("\x1b[31mERROR\x1b[0m")
        # First segment should be "ERROR" with red foreground
        assert len(segments) >= 1
        red_seg = segments[0]
        assert red_seg.text == "ERROR"
        fg = red_seg.fmt.foreground().color()
        assert fg == QColor("#cc0000")

    def test_reset_clears_format(self) -> None:
        segments = parse_ansi("\x1b[31mred\x1b[0m plain")
        assert len(segments) == 2
        # Second segment ("plain") should have no special foreground
        plain_seg = segments[1]
        assert plain_seg.text == " plain"
        assert not plain_seg.fmt.foreground().color().isValid() or \
            plain_seg.fmt.foreground().style() == 0

    def test_bold_sets_font_weight(self) -> None:
        segments = parse_ansi("\x1b[1mbold text\x1b[0m")
        assert segments[0].text == "bold text"
        assert segments[0].fmt.fontWeight() == QFont.Bold

    def test_italic_sets_font_italic(self) -> None:
        segments = parse_ansi("\x1b[3mitalic\x1b[0m")
        assert segments[0].text == "italic"
        assert segments[0].fmt.fontItalic() is True

    def test_underline_sets_font_underline(self) -> None:
        segments = parse_ansi("\x1b[4munderlined\x1b[0m")
        assert segments[0].text == "underlined"
        assert segments[0].fmt.fontUnderline() is True

    def test_combined_bold_and_color(self) -> None:
        segments = parse_ansi("\x1b[1;32mOK\x1b[0m")
        seg = segments[0]
        assert seg.text == "OK"
        assert seg.fmt.fontWeight() == QFont.Bold
        fg = seg.fmt.foreground().color()
        assert fg == QColor("#4e9a06")  # green

    def test_bright_color(self) -> None:
        segments = parse_ansi("\x1b[91mbright red\x1b[0m")
        seg = segments[0]
        assert seg.text == "bright red"
        fg = seg.fmt.foreground().color()
        assert fg == QColor("#ef2929")

    def test_background_color(self) -> None:
        segments = parse_ansi("\x1b[41mred bg\x1b[0m")
        seg = segments[0]
        assert seg.text == "red bg"
        bg = seg.fmt.background().color()
        assert bg == QColor("#cc0000")

    def test_256_color_foreground(self) -> None:
        segments = parse_ansi("\x1b[38;5;196mred256\x1b[0m")
        seg = segments[0]
        assert seg.text == "red256"
        # Color 196 = bright red in the 6x6x6 cube
        fg = seg.fmt.foreground().color()
        assert fg.isValid()

    def test_truecolor_foreground(self) -> None:
        segments = parse_ansi("\x1b[38;2;255;128;0morange\x1b[0m")
        seg = segments[0]
        assert seg.text == "orange"
        fg = seg.fmt.foreground().color()
        assert fg == QColor(255, 128, 0)

    def test_multiple_lines_preserved(self) -> None:
        text = "\x1b[32mline1\x1b[0m\nline2"
        segments = parse_ansi(text)
        full_text = "".join(s.text for s in segments)
        assert "line1" in full_text
        assert "line2" in full_text
        assert "\n" in full_text

    def test_empty_input(self) -> None:
        assert parse_ansi("") == []

    def test_only_escape_no_text(self) -> None:
        segments = parse_ansi("\x1b[31m\x1b[0m")
        # No visible text segments expected
        texts = [s.text for s in segments]
        assert all(t == "" for t in texts) or len(segments) == 0


class TestRenderAnsi:
    """Tests for render_ansi() into a QTextEdit."""

    def test_render_plain_text(self, qtbot) -> None:
        from PyQt5.QtWidgets import QTextEdit
        edit = QTextEdit()
        qtbot.addWidget(edit)
        render_ansi(edit, "hello world")
        assert edit.toPlainText() == "hello world"

    def test_render_strips_ansi_from_plain(self, qtbot) -> None:
        from PyQt5.QtWidgets import QTextEdit
        edit = QTextEdit()
        qtbot.addWidget(edit)
        render_ansi(edit, "\x1b[31mERROR\x1b[0m ok")
        plain = edit.toPlainText()
        assert "\x1b[" not in plain
        assert "ERROR" in plain
        assert "ok" in plain

    def test_render_multiline(self, qtbot) -> None:
        from PyQt5.QtWidgets import QTextEdit
        edit = QTextEdit()
        qtbot.addWidget(edit)
        render_ansi(edit, "line1\n\x1b[33mline2\x1b[0m\nline3")
        plain = edit.toPlainText()
        assert "line1" in plain
        assert "line2" in plain
        assert "line3" in plain

    def test_render_clears_previous_content(self, qtbot) -> None:
        from PyQt5.QtWidgets import QTextEdit
        edit = QTextEdit()
        qtbot.addWidget(edit)
        edit.setPlainText("old content")
        render_ansi(edit, "new content")
        assert edit.toPlainText() == "new content"
        assert "old" not in edit.toPlainText()

    def test_render_complex_kubernetes_log(self, qtbot) -> None:
        from PyQt5.QtWidgets import QTextEdit
        edit = QTextEdit()
        qtbot.addWidget(edit)
        # Simulated k8s log with timestamp + level coloring
        log = (
            "\x1b[2m2024-01-15T10:30:00Z\x1b[0m "
            "\x1b[1;31mERROR\x1b[0m "
            "Failed to pull image \x1b[36m\"nginx:latest\"\x1b[0m: "
            "rpc error: code = NotFound\n"
            "\x1b[2m2024-01-15T10:30:01Z\x1b[0m "
            "\x1b[32mINFO\x1b[0m "
            "Back-off restarting failed container"
        )
        render_ansi(edit, log)
        plain = edit.toPlainText()
        assert "\x1b[" not in plain
        assert "ERROR" in plain
        assert "INFO" in plain
        assert "nginx:latest" in plain
        assert "2024-01-15T10:30:00Z" in plain

