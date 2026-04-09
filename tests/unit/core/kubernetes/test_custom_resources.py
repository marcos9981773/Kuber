"""
tests/unit/core/kubernetes/test_custom_resources.py
Tests for kuber/core/kubernetes/custom_resources.py
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from kuber.core.kubernetes.custom_resources import CRDInfo, CustomResourceInstance


class TestListCRDs:
    def test_list_crds_returns_list(self, mocker) -> None:
        names = MagicMock()
        names.kind = "Widget"
        names.plural = "widgets"
        ver = MagicMock()
        ver.name = "v1alpha1"
        spec = MagicMock()
        spec.group = "example.com"
        spec.names = names
        spec.scope = "Namespaced"
        spec.versions = [ver]
        meta = MagicMock()
        meta.name = "widgets.example.com"
        crd = MagicMock()
        crd.metadata = meta
        crd.spec = spec

        mock_api = MagicMock()
        mock_api.list_custom_resource_definition.return_value = MagicMock(items=[crd])

        mocker.patch(
            "kuber.core.kubernetes.custom_resources.call_with_retry",
            side_effect=lambda fn: fn(),
        )
        mocker.patch(
            "kuber.core.kubernetes.custom_resources.k8s_client.ApiextensionsV1Api",
            return_value=mock_api,
        )

        from kuber.core.kubernetes.custom_resources import list_crds
        result = list_crds()
        assert len(result) == 1
        assert result[0].kind == "Widget"
        assert result[0].group == "example.com"


class TestListCustomResources:
    def test_list_returns_instances(self, mocker) -> None:
        mock_api = MagicMock()
        mock_api.list_namespaced_custom_object.return_value = {
            "items": [
                {
                    "apiVersion": "example.com/v1",
                    "kind": "Widget",
                    "metadata": {"name": "w-1", "namespace": "default"},
                },
            ],
        }
        mocker.patch("kuber.core.kubernetes.custom_resources.custom_objects", return_value=mock_api)
        mocker.patch(
            "kuber.core.kubernetes.custom_resources.call_with_retry",
            side_effect=lambda fn: fn(),
        )

        from kuber.core.kubernetes.custom_resources import list_custom_resources
        result = list_custom_resources("example.com", "v1", "widgets", "default")
        assert len(result) == 1
        assert result[0].name == "w-1"
        assert result[0].kind == "Widget"


class TestDeleteCustomResource:
    def test_delete_calls_api(self, mocker) -> None:
        mock_api = MagicMock()
        mocker.patch("kuber.core.kubernetes.custom_resources.custom_objects", return_value=mock_api)
        mocker.patch(
            "kuber.core.kubernetes.custom_resources.call_with_retry",
            side_effect=lambda fn: fn(),
        )

        from kuber.core.kubernetes.custom_resources import delete_custom_resource
        delete_custom_resource("example.com", "v1", "widgets", "w-1", "default")
        mock_api.delete_namespaced_custom_object.assert_called_once()

