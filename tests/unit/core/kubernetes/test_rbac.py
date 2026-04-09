"""
tests/unit/core/kubernetes/test_rbac.py
Tests for kuber/core/kubernetes/rbac.py
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from kuber.core.kubernetes.rbac import (
    ClusterRoleInfo,
    PolicyRule,
    RoleBindingInfo,
    RoleInfo,
    ServiceAccountInfo,
)


class TestServiceAccountOperations:
    def test_list_service_accounts_returns_list(self, mocker) -> None:
        mock_api = MagicMock()
        meta = MagicMock(name="sa-1", namespace="default", creation_timestamp=None)
        meta.name = "sa-1"
        meta.namespace = "default"
        sa = MagicMock(metadata=meta, secrets=[MagicMock()])
        mock_api.list_namespaced_service_account.return_value = MagicMock(items=[sa])
        mocker.patch("kuber.core.kubernetes.rbac.core_v1", return_value=mock_api)
        mocker.patch("kuber.core.kubernetes.rbac.call_with_retry", side_effect=lambda fn: fn())

        from kuber.core.kubernetes.rbac import list_service_accounts
        result = list_service_accounts("default")
        assert len(result) == 1
        assert result[0].name == "sa-1"
        assert result[0].secrets == 1

    def test_create_service_account_calls_api(self, mocker) -> None:
        mock_api = MagicMock()
        mocker.patch("kuber.core.kubernetes.rbac.core_v1", return_value=mock_api)
        mocker.patch("kuber.core.kubernetes.rbac.call_with_retry", side_effect=lambda fn: fn())

        from kuber.core.kubernetes.rbac import create_service_account
        create_service_account("test-sa", "default")
        mock_api.create_namespaced_service_account.assert_called_once()

    def test_delete_service_account_calls_api(self, mocker) -> None:
        mock_api = MagicMock()
        mocker.patch("kuber.core.kubernetes.rbac.core_v1", return_value=mock_api)
        mocker.patch("kuber.core.kubernetes.rbac.call_with_retry", side_effect=lambda fn: fn())

        from kuber.core.kubernetes.rbac import delete_service_account
        delete_service_account("test-sa", "default")
        mock_api.delete_namespaced_service_account.assert_called_once()


class TestRoleOperations:
    def test_list_roles_returns_list(self, mocker) -> None:
        mock_api = MagicMock()
        meta = MagicMock(creation_timestamp=None)
        meta.name = "role-1"
        meta.namespace = "default"
        role = MagicMock(metadata=meta, rules=[MagicMock(), MagicMock()])
        mock_api.list_namespaced_role.return_value = MagicMock(items=[role])
        mocker.patch("kuber.core.kubernetes.rbac.rbac_v1", return_value=mock_api)
        mocker.patch("kuber.core.kubernetes.rbac.call_with_retry", side_effect=lambda fn: fn())

        from kuber.core.kubernetes.rbac import list_roles
        result = list_roles("default")
        assert len(result) == 1
        assert result[0].name == "role-1"
        assert result[0].rules_count == 2

    def test_create_role_calls_api(self, mocker) -> None:
        mock_api = MagicMock()
        mocker.patch("kuber.core.kubernetes.rbac.rbac_v1", return_value=mock_api)
        mocker.patch("kuber.core.kubernetes.rbac.call_with_retry", side_effect=lambda fn: fn())

        from kuber.core.kubernetes.rbac import create_role
        rules = [PolicyRule(api_groups=[""], resources=["pods"], verbs=["get", "list"])]
        create_role("pod-reader", "default", rules)
        mock_api.create_namespaced_role.assert_called_once()

    def test_delete_role_calls_api(self, mocker) -> None:
        mock_api = MagicMock()
        mocker.patch("kuber.core.kubernetes.rbac.rbac_v1", return_value=mock_api)
        mocker.patch("kuber.core.kubernetes.rbac.call_with_retry", side_effect=lambda fn: fn())

        from kuber.core.kubernetes.rbac import delete_role
        delete_role("pod-reader", "default")
        mock_api.delete_namespaced_role.assert_called_once()


class TestRoleBindingOperations:
    def test_list_role_bindings_returns_list(self, mocker) -> None:
        mock_api = MagicMock()
        meta = MagicMock(creation_timestamp=None)
        meta.name = "rb-1"
        meta.namespace = "default"
        role_ref = MagicMock()
        role_ref.kind = "Role"
        role_ref.name = "pod-reader"
        subject = MagicMock()
        subject.kind = "ServiceAccount"
        subject.name = "sa-1"
        rb = MagicMock(metadata=meta, role_ref=role_ref, subjects=[subject])
        mock_api.list_namespaced_role_binding.return_value = MagicMock(items=[rb])
        mocker.patch("kuber.core.kubernetes.rbac.rbac_v1", return_value=mock_api)
        mocker.patch("kuber.core.kubernetes.rbac.call_with_retry", side_effect=lambda fn: fn())

        from kuber.core.kubernetes.rbac import list_role_bindings
        result = list_role_bindings("default")
        assert len(result) == 1
        assert result[0].role_name == "pod-reader"
        assert "ServiceAccount/sa-1" in result[0].subjects

    def test_create_role_binding_calls_api(self, mocker) -> None:
        mock_api = MagicMock()
        mocker.patch("kuber.core.kubernetes.rbac.rbac_v1", return_value=mock_api)
        mocker.patch("kuber.core.kubernetes.rbac.call_with_retry", side_effect=lambda fn: fn())

        from kuber.core.kubernetes.rbac import create_role_binding
        create_role_binding(
            name="rb-1", namespace="default",
            role_name="pod-reader", role_kind="Role",
            subject_name="sa-1", subject_kind="ServiceAccount",
        )
        mock_api.create_namespaced_role_binding.assert_called_once()

    def test_delete_role_binding_calls_api(self, mocker) -> None:
        mock_api = MagicMock()
        mocker.patch("kuber.core.kubernetes.rbac.rbac_v1", return_value=mock_api)
        mocker.patch("kuber.core.kubernetes.rbac.call_with_retry", side_effect=lambda fn: fn())

        from kuber.core.kubernetes.rbac import delete_role_binding
        delete_role_binding("rb-1", "default")
        mock_api.delete_namespaced_role_binding.assert_called_once()


class TestClusterRoleOperations:
    def test_list_cluster_roles_returns_list(self, mocker) -> None:
        mock_api = MagicMock()
        meta = MagicMock(creation_timestamp=None)
        meta.name = "cluster-admin"
        cr = MagicMock(metadata=meta, rules=[MagicMock()])
        mock_api.list_cluster_role.return_value = MagicMock(items=[cr])
        mocker.patch("kuber.core.kubernetes.rbac.rbac_v1", return_value=mock_api)
        mocker.patch("kuber.core.kubernetes.rbac.call_with_retry", side_effect=lambda fn: fn())

        from kuber.core.kubernetes.rbac import list_cluster_roles
        result = list_cluster_roles()
        assert len(result) == 1
        assert result[0].name == "cluster-admin"

