"""
tests/conftest.py — Shared pytest fixtures for all tests.
"""
from __future__ import annotations

import pytest


@pytest.fixture(scope="session")
def qapp_args() -> list[str]:
    """Provide minimal Qt app arguments for pytest-qt."""
    return ["--no-sandbox"]


@pytest.fixture(autouse=True)
def _reset_namespace_store() -> None:
    """Reset the global NamespaceStore singleton between tests."""
    from kuber.views.common.namespace_store import NamespaceStore
    NamespaceStore.reset()


