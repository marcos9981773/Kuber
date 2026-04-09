"""
kuber/views/common/resource_detail_panel.py
Reusable side panel that displays details of any selected Kubernetes resource.
"""
from __future__ import annotations

from dataclasses import fields as dc_fields
from typing import Any

import yaml

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFormLayout,
    QLabel,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from kuber.views.common.yaml_editor import YamlEditor


class ResourceDetailPanel(QWidget):
    """
    Collapsible/embeddable panel that renders a dataclass resource in two tabs:

    1. **Properties** — key/value form derived from dataclass fields.
    2. **YAML** — read-only YAML representation.

    Usage::

        panel = ResourceDetailPanel()
        panel.set_resource(pod_info)   # any dataclass instance
        panel.clear()
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("resourceDetailPanel")
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Title
        self._title = QLabel(self.tr("Resource Details"))
        self._title.setObjectName("detailPanelTitle")
        self._title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._title.setAccessibleName(self.tr("Resource detail panel title"))
        layout.addWidget(self._title)

        # Tabs: Properties | YAML
        self._tabs = QTabWidget()
        self._tabs.setObjectName("detailTabs")
        self._tabs.setAccessibleName(self.tr("Resource detail tabs"))

        # -- Properties tab --
        self._props_scroll = QScrollArea()
        self._props_scroll.setWidgetResizable(True)
        self._props_scroll.setAccessibleName(self.tr("Resource properties"))

        self._props_container = QWidget()
        self._props_layout = QFormLayout(self._props_container)
        self._props_layout.setContentsMargins(12, 12, 12, 12)
        self._props_layout.setSpacing(8)
        self._props_scroll.setWidget(self._props_container)
        self._tabs.addTab(self._props_scroll, self.tr("Properties"))

        # -- YAML tab --
        self._yaml_editor = YamlEditor(read_only=True)
        self._yaml_editor.setAccessibleName(self.tr("Resource YAML view"))
        self._tabs.addTab(self._yaml_editor, self.tr("YAML"))

        layout.addWidget(self._tabs, stretch=1)

        # Empty state
        self._empty_label = QLabel(self.tr("Select a resource to view details."))
        self._empty_label.setAlignment(Qt.AlignCenter)
        self._empty_label.setObjectName("detailEmpty")
        self._empty_label.setAccessibleName(self.tr("No resource selected"))
        layout.addWidget(self._empty_label)

        self._tabs.hide()

    # ── Public API ────────────────────────────────────────────────────────────

    def set_resource(self, item: Any) -> None:
        """
        Populate the panel from a dataclass instance.

        Args:
            item: Any dataclass object (PodInfo, DeploymentInfo, etc.).
        """
        if item is None:
            self.clear()
            return

        self._empty_label.hide()
        self._tabs.show()

        # Title
        name = getattr(item, "name", str(item))
        self._title.setText(f"<b>{name}</b>")

        # Properties tab
        self._clear_props()
        try:
            for field in dc_fields(item):
                value = getattr(item, field.name, "")
                label_key = QLabel(f"<b>{field.name.replace('_', ' ').title()}</b>")
                label_key.setTextFormat(Qt.RichText)

                if isinstance(value, list):
                    display = ", ".join(str(v) for v in value) if value else "—"
                elif isinstance(value, dict):
                    display = yaml.dump(value, default_flow_style=False).strip()
                else:
                    display = str(value) if value not in (None, "") else "—"

                label_val = QLabel(display)
                label_val.setWordWrap(True)
                label_val.setTextInteractionFlags(Qt.TextSelectableByMouse)
                self._props_layout.addRow(label_key, label_val)
        except TypeError:
            # Not a dataclass — show raw string
            label = QLabel(str(item))
            label.setWordWrap(True)
            self._props_layout.addRow(label)

        # YAML tab
        try:
            from dataclasses import asdict
            data = asdict(item)
            self._yaml_editor.set_text(yaml.dump(data, default_flow_style=False))
        except TypeError:
            self._yaml_editor.set_text(str(item))

    def clear(self) -> None:
        """Reset the panel to its empty state."""
        self._title.setText(self.tr("Resource Details"))
        self._clear_props()
        self._yaml_editor.clear()
        self._tabs.hide()
        self._empty_label.show()

    # ── Private helpers ───────────────────────────────────────────────────────

    def _clear_props(self) -> None:
        """Remove all rows from the properties form layout."""
        while self._props_layout.count():
            child = self._props_layout.takeAt(0)
            widget = child.widget()
            if widget:
                widget.deleteLater()

