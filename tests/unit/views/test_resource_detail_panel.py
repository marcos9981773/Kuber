"""
tests/unit/views/test_resource_detail_panel.py
Tests for kuber/views/common/resource_detail_panel.py
"""
from __future__ import annotations

import pytest
from dataclasses import dataclass


@dataclass
class _FakeResource:
    name: str
    namespace: str
    status: str
    replicas: int


class TestResourceDetailPanel:
    def test_panel_starts_in_empty_state(self, qtbot) -> None:
        from kuber.views.common.resource_detail_panel import ResourceDetailPanel
        panel = ResourceDetailPanel()
        qtbot.addWidget(panel)
        panel.show()
        assert panel._tabs.isHidden()
        assert panel._empty_label.isVisible()

    def test_set_resource_shows_tabs(self, qtbot) -> None:
        from kuber.views.common.resource_detail_panel import ResourceDetailPanel
        panel = ResourceDetailPanel()
        qtbot.addWidget(panel)
        panel.show()
        item = _FakeResource(name="pod-x", namespace="default", status="Running", replicas=3)
        panel.set_resource(item)
        assert panel._tabs.isVisible()
        assert panel._empty_label.isHidden()

    def test_set_resource_populates_title(self, qtbot) -> None:
        from kuber.views.common.resource_detail_panel import ResourceDetailPanel
        panel = ResourceDetailPanel()
        qtbot.addWidget(panel)
        item = _FakeResource(name="my-deploy", namespace="ns", status="Running", replicas=1)
        panel.set_resource(item)
        assert "my-deploy" in panel._title.text()

    def test_set_resource_populates_yaml_tab(self, qtbot) -> None:
        from kuber.views.common.resource_detail_panel import ResourceDetailPanel
        panel = ResourceDetailPanel()
        qtbot.addWidget(panel)
        item = _FakeResource(name="web", namespace="default", status="Running", replicas=2)
        panel.set_resource(item)
        yaml_text = panel._yaml_editor.get_text()
        assert "name: web" in yaml_text
        assert "replicas: 2" in yaml_text

    def test_set_resource_populates_properties(self, qtbot) -> None:
        from kuber.views.common.resource_detail_panel import ResourceDetailPanel
        panel = ResourceDetailPanel()
        qtbot.addWidget(panel)
        item = _FakeResource(name="svc-a", namespace="prod", status="Active", replicas=5)
        panel.set_resource(item)
        # Properties form should have rows (at least 4 fields)
        assert panel._props_layout.count() >= 4

    def test_clear_resets_to_empty_state(self, qtbot) -> None:
        from kuber.views.common.resource_detail_panel import ResourceDetailPanel
        panel = ResourceDetailPanel()
        qtbot.addWidget(panel)
        panel.show()
        item = _FakeResource(name="x", namespace="y", status="z", replicas=1)
        panel.set_resource(item)
        panel.clear()
        assert panel._tabs.isHidden()
        assert panel._empty_label.isVisible()

    def test_set_none_calls_clear(self, qtbot) -> None:
        from kuber.views.common.resource_detail_panel import ResourceDetailPanel
        panel = ResourceDetailPanel()
        qtbot.addWidget(panel)
        panel.show()
        item = _FakeResource(name="x", namespace="y", status="z", replicas=1)
        panel.set_resource(item)
        panel.set_resource(None)
        assert panel._tabs.isHidden()

    def test_set_resource_with_list_field(self, qtbot) -> None:
        from dataclasses import dataclass, field
        from kuber.views.common.resource_detail_panel import ResourceDetailPanel

        @dataclass
        class _WithList:
            name: str
            tags: list[str] = field(default_factory=list)

        panel = ResourceDetailPanel()
        qtbot.addWidget(panel)
        panel.show()
        panel.set_resource(_WithList(name="a", tags=["t1", "t2"]))
        assert panel._tabs.isVisible()

    def test_set_resource_with_dict_field(self, qtbot) -> None:
        from dataclasses import dataclass, field
        from kuber.views.common.resource_detail_panel import ResourceDetailPanel

        @dataclass
        class _WithDict:
            name: str
            data: dict[str, str] = field(default_factory=dict)

        panel = ResourceDetailPanel()
        qtbot.addWidget(panel)
        panel.show()
        panel.set_resource(_WithDict(name="b", data={"k": "v"}))
        assert panel._tabs.isVisible()

