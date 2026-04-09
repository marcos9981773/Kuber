"""
kuber/views/common/yaml_editor.py
YAML editor widget with syntax highlighting via QSyntaxHighlighter.
"""
from __future__ import annotations

import re

from PyQt5.QtCore import Qt
from PyQt5.QtGui import (
    QColor,
    QFont,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextDocument,
)
from PyQt5.QtWidgets import QPlainTextEdit, QVBoxLayout, QWidget


class YamlHighlighter(QSyntaxHighlighter):
    """
    QSyntaxHighlighter subclass that colorizes YAML syntax.

    Highlights:
    - Keys (before the colon)
    - String values (quoted)
    - Numbers and booleans
    - Comments (``# …``)
    - Anchors and aliases (``&anchor``, ``*alias``)
    - List dashes (``-``)
    """

    def __init__(self, document: QTextDocument) -> None:
        super().__init__(document)
        self._rules: list[tuple[re.Pattern[str], QTextCharFormat]] = []
        self._build_rules()

    def _build_rules(self) -> None:
        # ── Comment: # until end of line ─────────────────────────────────────
        fmt_comment = QTextCharFormat()
        fmt_comment.setForeground(QColor("#6a9955"))
        fmt_comment.setFontItalic(True)
        self._rules.append((re.compile(r"#[^\n]*"), fmt_comment))

        # ── Key: word(s) followed by a colon ─────────────────────────────────
        fmt_key = QTextCharFormat()
        fmt_key.setForeground(QColor("#569cd6"))
        fmt_key.setFontWeight(QFont.Bold)
        self._rules.append((re.compile(r"^\s*[\w.\-/]+\s*(?=:)", re.MULTILINE), fmt_key))

        # ── Quoted strings (single and double) ──────────────────────────────
        fmt_string = QTextCharFormat()
        fmt_string.setForeground(QColor("#ce9178"))
        self._rules.append((re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), fmt_string))
        self._rules.append((re.compile(r"'[^'\\]*(\\.[^'\\]*)*'"), fmt_string))

        # ── Numbers ──────────────────────────────────────────────────────────
        fmt_number = QTextCharFormat()
        fmt_number.setForeground(QColor("#b5cea8"))
        self._rules.append((re.compile(r"\b\d+(\.\d+)?\b"), fmt_number))

        # ── Boolean / null ───────────────────────────────────────────────────
        fmt_bool = QTextCharFormat()
        fmt_bool.setForeground(QColor("#d16969"))
        fmt_bool.setFontWeight(QFont.Bold)
        self._rules.append(
            (re.compile(r"\b(true|false|yes|no|null|True|False|None)\b"), fmt_bool)
        )

        # ── Anchors & aliases ────────────────────────────────────────────────
        fmt_anchor = QTextCharFormat()
        fmt_anchor.setForeground(QColor("#dcdcaa"))
        self._rules.append((re.compile(r"[&*]\w+"), fmt_anchor))

        # ── List dash ────────────────────────────────────────────────────────
        fmt_dash = QTextCharFormat()
        fmt_dash.setForeground(QColor("#d4d4d4"))
        fmt_dash.setFontWeight(QFont.Bold)
        self._rules.append((re.compile(r"^\s*-\s", re.MULTILINE), fmt_dash))

    def highlightBlock(self, text: str) -> None:  # noqa: N802
        for pattern, fmt in self._rules:
            for match in pattern.finditer(text):
                start = match.start()
                length = match.end() - start
                self.setFormat(start, length, fmt)


class YamlEditor(QWidget):
    """
    Reusable YAML editor widget with syntax highlighting.

    Wraps a ``QPlainTextEdit`` and applies :class:`YamlHighlighter`.

    Usage::

        editor = YamlEditor(read_only=False)
        editor.set_text("apiVersion: v1\\nkind: ConfigMap")
        yaml_str = editor.get_text()
    """

    def __init__(
        self,
        read_only: bool = False,
        placeholder: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._setup_ui(read_only, placeholder)

    def _setup_ui(self, read_only: bool, placeholder: str) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._editor = QPlainTextEdit()
        self._editor.setObjectName("yamlEditor")
        self._editor.setReadOnly(read_only)
        self._editor.setTabStopDistance(20.0)
        self._editor.setLineWrapMode(QPlainTextEdit.NoWrap)
        self._editor.setAccessibleName(self.tr("YAML editor"))
        self._editor.setAccessibleDescription(
            self.tr("Edit YAML content with syntax highlighting.")
        )

        if placeholder:
            self._editor.setPlaceholderText(placeholder)

        # Monospace font
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.Monospace)
        self._editor.setFont(font)

        # Apply syntax highlighter
        self._highlighter = YamlHighlighter(self._editor.document())

        layout.addWidget(self._editor)

    # ── Public API ────────────────────────────────────────────────────────────

    def get_text(self) -> str:
        """Return the current YAML text."""
        return self._editor.toPlainText()

    def set_text(self, text: str) -> None:
        """Replace the editor content."""
        self._editor.setPlainText(text)

    def set_read_only(self, read_only: bool) -> None:
        """Toggle read-only mode."""
        self._editor.setReadOnly(read_only)

    def is_read_only(self) -> bool:
        """Return whether the editor is read-only."""
        return self._editor.isReadOnly()

    def clear(self) -> None:
        """Clear all text."""
        self._editor.clear()

    @property
    def plain_text_edit(self) -> QPlainTextEdit:
        """Direct access to the underlying QPlainTextEdit (for advanced use)."""
        return self._editor

