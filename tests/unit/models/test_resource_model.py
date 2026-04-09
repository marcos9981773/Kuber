"""
tests/unit/models/test_resource_model.py
Tests for kuber/models/resource_model.py
"""
from __future__ import annotations

import pytest
from dataclasses import dataclass

from kuber.models.resource_model import ResourceFilterProxy, ResourceTableModel


@dataclass
class _FakeItem:
    name: str
    namespace: str
    status: str


class TestResourceTableModel:
    """Tests for the generic ResourceTableModel."""

    def test_set_items_populates_rows(self) -> None:
        model = ResourceTableModel()
        items = [
            _FakeItem(name="pod-a", namespace="default", status="Running"),
            _FakeItem(name="pod-b", namespace="kube-system", status="Pending"),
        ]
        model.set_items(items)
        assert model.rowCount() == 2

    def test_columns_auto_derived_from_dataclass(self) -> None:
        model = ResourceTableModel()
        model.set_items([_FakeItem(name="x", namespace="y", status="z")])
        assert model.columnCount() == 3

    def test_columns_explicit_override(self) -> None:
        model = ResourceTableModel(columns=["name", "status"])
        model.set_items([_FakeItem(name="x", namespace="y", status="z")])
        assert model.columnCount() == 2

    def test_data_display_role_returns_string(self) -> None:
        from PyQt5.QtCore import Qt
        model = ResourceTableModel(columns=["name", "namespace", "status"])
        model.set_items([_FakeItem(name="pod-a", namespace="ns", status="Running")])
        idx = model.index(0, 0)
        assert model.data(idx, Qt.DisplayRole) == "pod-a"

    def test_header_data_titlecases_underscored_names(self) -> None:
        from PyQt5.QtCore import Qt
        model = ResourceTableModel(columns=["ready_replicas"])
        model.set_items([])
        header = model.headerData(0, Qt.Horizontal, Qt.DisplayRole)
        assert header == "Ready Replicas"

    def test_item_at_returns_correct_object(self) -> None:
        model = ResourceTableModel()
        item = _FakeItem(name="pod-x", namespace="ns", status="Running")
        model.set_items([item])
        assert model.item_at(0) is item

    def test_item_at_out_of_range_returns_none(self) -> None:
        model = ResourceTableModel()
        assert model.item_at(99) is None

    def test_clear_removes_all_items(self) -> None:
        model = ResourceTableModel()
        model.set_items([_FakeItem(name="a", namespace="b", status="c")])
        model.clear()
        assert model.rowCount() == 0


class TestResourceFilterProxy:
    """Tests for the filter proxy model."""

    def test_filter_accepts_matching_row(self) -> None:
        from PyQt5.QtCore import Qt
        model = ResourceTableModel(columns=["name", "status"])
        model.set_items([
            _FakeItem(name="nginx-abc", namespace="default", status="Running"),
            _FakeItem(name="redis-xyz", namespace="default", status="Pending"),
        ])
        proxy = ResourceFilterProxy()
        proxy.setSourceModel(model)
        proxy.set_filter_text("nginx")
        assert proxy.rowCount() == 1

    def test_filter_empty_shows_all(self) -> None:
        model = ResourceTableModel(columns=["name", "status"])
        model.set_items([
            _FakeItem(name="a", namespace="ns", status="Running"),
            _FakeItem(name="b", namespace="ns", status="Pending"),
        ])
        proxy = ResourceFilterProxy()
        proxy.setSourceModel(model)
        proxy.set_filter_text("")
        assert proxy.rowCount() == 2

    def test_filter_case_insensitive(self) -> None:
        model = ResourceTableModel(columns=["name", "status"])
        model.set_items([
            _FakeItem(name="MyPod", namespace="ns", status="Running"),
        ])
        proxy = ResourceFilterProxy()
        proxy.setSourceModel(model)
        proxy.set_filter_text("mypod")
        assert proxy.rowCount() == 1

