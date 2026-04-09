"""
tests/unit/viewmodels/test_user_vm.py
Tests for kuber/viewmodels/user_vm.py
"""
from __future__ import annotations

import pytest

from kuber.core.kubernetes.rbac import (
    PolicyRule,
    RoleBindingInfo,
    RoleInfo,
    ServiceAccountInfo,
)
from kuber.core.kubernetes.events import EventInfo


_FAKE_SAS = [
    ServiceAccountInfo(name="default", namespace="default", secrets=1, age="5d"),
    ServiceAccountInfo(name="deployer", namespace="default", secrets=0, age="1d"),
]

_FAKE_ROLES = [
    RoleInfo(name="pod-reader", namespace="default", rules_count=2, age="3d"),
]

_FAKE_BINDINGS = [
    RoleBindingInfo(
        name="rb-1", namespace="default", role_kind="Role",
        role_name="pod-reader", subjects="ServiceAccount/deployer", age="2d",
    ),
]

_FAKE_AUDIT_EVENTS = [
    EventInfo(
        namespace="default", name="ev-1", type="Warning",
        reason="Forbidden", message="forbidden: User cannot list pods",
        source="apiserver", involved_object="Pod/test",
        count=1, age="5m",
    ),
]


class TestUserVMServiceAccounts:
    def test_load_items_emits_items_loaded(self, qtbot, mocker) -> None:
        mocker.patch(
            "kuber.viewmodels.user_vm.list_service_accounts",
            return_value=_FAKE_SAS,
        )
        mocker.patch(
            "kuber.viewmodels.resource_vm.list_namespaces",
            return_value=["default"],
        )
        from kuber.viewmodels.user_vm import UserViewModel
        vm = UserViewModel()

        with qtbot.waitSignal(vm.items_loaded, timeout=3000) as blocker:
            vm.load_items()

        assert len(blocker.args[0]) == 2
        assert blocker.args[0][0].name == "default"

    def test_delete_item_emits_item_deleted(self, qtbot, mocker) -> None:
        mocker.patch("kuber.viewmodels.user_vm.delete_service_account")
        mocker.patch(
            "kuber.viewmodels.user_vm.list_service_accounts",
            return_value=[],
        )
        from kuber.viewmodels.user_vm import UserViewModel
        vm = UserViewModel()

        with qtbot.waitSignal(vm.item_deleted, timeout=3000) as blocker:
            vm.delete_item("deployer", "default")

        assert blocker.args[0] == "deployer"

    def test_create_sa_emits_action_completed(self, qtbot, mocker) -> None:
        mocker.patch("kuber.viewmodels.user_vm.create_service_account")
        mocker.patch(
            "kuber.viewmodels.user_vm.list_service_accounts",
            return_value=[],
        )
        from kuber.viewmodels.user_vm import UserViewModel
        vm = UserViewModel()

        with qtbot.waitSignal(vm.action_completed, timeout=3000):
            vm.create_sa("new-sa")


class TestUserVMRoles:
    def test_load_roles_emits_roles_loaded(self, qtbot, mocker) -> None:
        mocker.patch(
            "kuber.viewmodels.user_vm.list_roles",
            return_value=_FAKE_ROLES,
        )
        from kuber.viewmodels.user_vm import UserViewModel
        vm = UserViewModel()

        with qtbot.waitSignal(vm.roles_loaded, timeout=3000) as blocker:
            vm.load_roles()

        assert len(blocker.args[0]) == 1
        assert blocker.args[0][0].name == "pod-reader"

    def test_load_bindings_emits_bindings_loaded(self, qtbot, mocker) -> None:
        mocker.patch(
            "kuber.viewmodels.user_vm.list_role_bindings",
            return_value=_FAKE_BINDINGS,
        )
        from kuber.viewmodels.user_vm import UserViewModel
        vm = UserViewModel()

        with qtbot.waitSignal(vm.bindings_loaded, timeout=3000) as blocker:
            vm.load_bindings()

        assert blocker.args[0][0].role_name == "pod-reader"


class TestUserVMAudit:
    def test_load_audit_events_emits_signal(self, qtbot, mocker) -> None:
        mocker.patch(
            "kuber.viewmodels.user_vm.list_events",
            return_value=_FAKE_AUDIT_EVENTS,
        )
        from kuber.viewmodels.user_vm import UserViewModel
        vm = UserViewModel()

        with qtbot.waitSignal(vm.audit_events_loaded, timeout=3000) as blocker:
            vm.load_audit_events()

        assert len(blocker.args[0]) == 1
        assert "Forbidden" in blocker.args[0][0].reason

