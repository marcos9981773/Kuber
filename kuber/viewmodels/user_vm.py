"""
kuber/viewmodels/user_vm.py
ViewModel for User Management (RBAC) views.
"""
from __future__ import annotations

import logging
from typing import Any

from PyQt5.QtCore import QObject, pyqtSignal

from kuber.core.kubernetes.events import EventInfo, list_events
from kuber.core.kubernetes.rbac import (
    PolicyRule,
    RoleBindingInfo,
    RoleInfo,
    ServiceAccountInfo,
    create_role,
    create_role_binding,
    create_service_account,
    delete_role,
    delete_role_binding,
    delete_service_account,
    list_role_bindings,
    list_roles,
    list_service_accounts,
)
from kuber.viewmodels.resource_vm import ResourceViewModel
from kuber.views.common.base_worker import BaseWorker

logger = logging.getLogger(__name__)


class _RolesWorker(BaseWorker):
    def __init__(self, namespace: str) -> None:
        super().__init__()
        self._ns = namespace

    def run_task(self) -> list[RoleInfo]:
        return list_roles(namespace=self._ns)


class _BindingsWorker(BaseWorker):
    def __init__(self, namespace: str) -> None:
        super().__init__()
        self._ns = namespace

    def run_task(self) -> list[RoleBindingInfo]:
        return list_role_bindings(namespace=self._ns)


class _AuditWorker(BaseWorker):
    def __init__(self, namespace: str) -> None:
        super().__init__()
        self._ns = namespace

    def run_task(self) -> list[EventInfo]:
        events = list_events(namespace=self._ns)
        return [
            e for e in events
            if e.type == "Warning"
            or "rbac" in (e.reason or "").lower()
            or "forbidden" in (e.message or "").lower()
            or "unauthorized" in (e.message or "").lower()
        ]


class UserViewModel(ResourceViewModel):
    """
    ViewModel for RBAC management — ServiceAccounts, Roles, RoleBindings.

    Extra signals beyond ResourceViewModel:
        roles_loaded (list):        list[RoleInfo]
        bindings_loaded (list):     list[RoleBindingInfo]
        audit_events_loaded (list): list[EventInfo] (filtered)
    """

    roles_loaded: pyqtSignal = pyqtSignal(list)
    bindings_loaded: pyqtSignal = pyqtSignal(list)
    audit_events_loaded: pyqtSignal = pyqtSignal(list)

    # ── ResourceViewModel overrides ──────────────────────────────────────────

    def _fetch_items(self, namespace: str) -> list[ServiceAccountInfo]:
        return list_service_accounts(namespace=namespace)

    def _delete_item(self, name: str, namespace: str) -> None:
        delete_service_account(name=name, namespace=namespace)

    # ── Extra actions ────────────────────────────────────────────────────────

    def create_sa(self, name: str, namespace: str | None = None) -> None:
        """Create a new ServiceAccount."""
        ns = namespace or self._namespace
        self._run_action(
            create_service_account,
            description=f"Create ServiceAccount {name}",
            name=name,
            namespace=ns,
        )

    def load_roles(self) -> None:
        """Fetch Roles for the current namespace."""
        w = _RolesWorker(self._namespace)
        self._start(w, self._on_roles_loaded)

    def load_bindings(self) -> None:
        """Fetch RoleBindings for the current namespace."""
        w = _BindingsWorker(self._namespace)
        self._start(w, self._on_bindings_loaded)

    def load_audit_events(self) -> None:
        """Fetch RBAC-related audit events."""
        w = _AuditWorker(self._namespace)
        self._start(w, self._on_audit_loaded)

    def create_new_role(
        self, name: str, namespace: str, rules: list[PolicyRule],
    ) -> None:
        """Create a namespaced Role."""
        self._run_action(
            create_role,
            description=f"Create Role {name}",
            name=name,
            namespace=namespace,
            rules=rules,
        )

    def create_new_binding(
        self,
        name: str,
        namespace: str,
        role_name: str,
        role_kind: str,
        subject_name: str,
        subject_kind: str,
    ) -> None:
        """Create a RoleBinding."""
        self._run_action(
            create_role_binding,
            description=f"Create RoleBinding {name}",
            name=name,
            namespace=namespace,
            role_name=role_name,
            role_kind=role_kind,
            subject_name=subject_name,
            subject_kind=subject_kind,
        )

    def delete_role_item(self, name: str, namespace: str | None = None) -> None:
        """Delete a Role."""
        ns = namespace or self._namespace
        self._run_action(
            delete_role,
            description=f"Delete Role {name}",
            name=name,
            namespace=ns,
        )

    def delete_binding_item(self, name: str, namespace: str | None = None) -> None:
        """Delete a RoleBinding."""
        ns = namespace or self._namespace
        self._run_action(
            delete_role_binding,
            description=f"Delete RoleBinding {name}",
            name=name,
            namespace=ns,
        )

    # ── Slots ────────────────────────────────────────────────────────────────

    def _on_roles_loaded(self, result: Any) -> None:
        self.loading_changed.emit(False)
        self.roles_loaded.emit(result)

    def _on_bindings_loaded(self, result: Any) -> None:
        self.loading_changed.emit(False)
        self.bindings_loaded.emit(result)

    def _on_audit_loaded(self, result: Any) -> None:
        self.loading_changed.emit(False)
        self.audit_events_loaded.emit(result)

