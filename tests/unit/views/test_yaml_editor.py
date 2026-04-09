"""
tests/unit/views/test_yaml_editor.py
Tests for kuber/views/common/yaml_editor.py
"""
from __future__ import annotations

import pytest


class TestYamlHighlighter:
    def test_highlighter_attached_to_document(self, qtbot) -> None:
        from kuber.views.common.yaml_editor import YamlEditor
        editor = YamlEditor()
        qtbot.addWidget(editor)
        assert editor._highlighter is not None
        assert editor._highlighter.document() is editor._editor.document()

    def test_highlighter_rules_not_empty(self, qtbot) -> None:
        from kuber.views.common.yaml_editor import YamlEditor
        editor = YamlEditor()
        qtbot.addWidget(editor)
        assert len(editor._highlighter._rules) > 0


class TestYamlEditor:
    def test_set_and_get_text(self, qtbot) -> None:
        from kuber.views.common.yaml_editor import YamlEditor
        editor = YamlEditor()
        qtbot.addWidget(editor)
        editor.set_text("apiVersion: v1\nkind: Pod")
        assert editor.get_text() == "apiVersion: v1\nkind: Pod"

    def test_clear_empties_text(self, qtbot) -> None:
        from kuber.views.common.yaml_editor import YamlEditor
        editor = YamlEditor()
        qtbot.addWidget(editor)
        editor.set_text("some: yaml")
        editor.clear()
        assert editor.get_text() == ""

    def test_read_only_mode(self, qtbot) -> None:
        from kuber.views.common.yaml_editor import YamlEditor
        editor = YamlEditor(read_only=True)
        qtbot.addWidget(editor)
        assert editor.is_read_only() is True

    def test_editable_mode_default(self, qtbot) -> None:
        from kuber.views.common.yaml_editor import YamlEditor
        editor = YamlEditor()
        qtbot.addWidget(editor)
        assert editor.is_read_only() is False

    def test_toggle_read_only(self, qtbot) -> None:
        from kuber.views.common.yaml_editor import YamlEditor
        editor = YamlEditor()
        qtbot.addWidget(editor)
        editor.set_read_only(True)
        assert editor.is_read_only() is True
        editor.set_read_only(False)
        assert editor.is_read_only() is False

    def test_accessible_name_set(self, qtbot) -> None:
        from kuber.views.common.yaml_editor import YamlEditor
        editor = YamlEditor()
        qtbot.addWidget(editor)
        assert editor._editor.accessibleName() != ""

    def test_monospace_font_applied(self, qtbot) -> None:
        from PyQt5.QtGui import QFont
        from kuber.views.common.yaml_editor import YamlEditor
        editor = YamlEditor()
        qtbot.addWidget(editor)
        assert editor._editor.font().styleHint() == QFont.Monospace

    def test_plain_text_edit_property(self, qtbot) -> None:
        from PyQt5.QtWidgets import QPlainTextEdit
        from kuber.views.common.yaml_editor import YamlEditor
        editor = YamlEditor()
        qtbot.addWidget(editor)
        assert isinstance(editor.plain_text_edit, QPlainTextEdit)

