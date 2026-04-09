"""
kuber/core/kubernetes/rbac.py
RBAC operations: ServiceAccounts, Roles, ClusterRoles, RoleBindings.
No PyQt5 imports.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from kubernetes import client as k8s_client

from kuber.constants import K8S_API_TIMEOUT_SECONDS
from kuber.core.kubernetes.client import call_with_retry, core_v1, rbac_v1
from kuber.core.kubernetes.pods import _compute_age

logger = logging.getLogger(__name__)


# ── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class ServiceAccountInfo:
    """Lightweight representation of a Kubernetes ServiceAccount."""

    name: str
    namespace: str
    secrets: int
    age: str = ""


@dataclass
class PolicyRule:
    """A single RBAC policy rule."""

    api_groups: list[str] = field(default_factory=lambda: [""])
    resources: list[str] = field(default_factory=list)
    verbs: list[str] = field(default_factory=list)


@dataclass
class RoleInfo:
    """Lightweight representation of a namespaced Role."""

    name: str
    namespace: str
    rules_count: int
    age: str = ""


@dataclass
class ClusterRoleInfo:
    """Lightweight representation of a ClusterRole."""

    name: str
    rules_count: int
    age: str = ""


@dataclass
class RoleBindingInfo:
    """Lightweight representation of a RoleBinding."""

    name: str
    namespace: str
    role_kind: str   # Role | ClusterRole
    role_name: str
    subjects: str    # comma-separated subject names
    age: str = ""


# ── ServiceAccount operations ────────────────────────────────────────────────

def list_service_accounts(
    namespace: str = "default",
    timeout: int = K8S_API_TIMEOUT_SECONDS,
) -> list[ServiceAccountInfo]:
    """List ServiceAccounts in a namespace."""

    def _call() -> list[ServiceAccountInfo]:
        api = core_v1()
        if namespace == "all":
            response = api.list_service_account_for_all_namespaces(
                _request_timeout=timeout,
            )
        else:
            response = api.list_namespaced_service_account(
                namespace, _request_timeout=timeout,
            )

        items: list[ServiceAccountInfo] = []
        for sa in response.items:
            meta = sa.metadata
            secrets = sa.secrets or []
            items.append(ServiceAccountInfo(
                name=meta.name or "" if meta else "",
                namespace=meta.namespace or "" if meta else "",
                secrets=len(secrets),
                age=_compute_age(meta.creation_timestamp) if meta else "",
            ))
        return items

    return call_with_retry(_call)


def create_service_account(
    name: str,
    namespace: str = "default",
    timeout: int = K8S_API_TIMEOUT_SECONDS,
) -> None:
    """Create a ServiceAccount."""

    def _call() -> None:
        body = k8s_client.V1ServiceAccount(
            metadata=k8s_client.V1ObjectMeta(name=name),
        )
        core_v1().create_namespaced_service_account(
            namespace, body, _request_timeout=timeout,
        )
        logger.info(f"Created ServiceAccount '{name}' in '{namespace}'.")

    call_with_retry(_call)


def delete_service_account(
    name: str,
    namespace: str = "default",
    timeout: int = K8S_API_TIMEOUT_SECONDS,
) -> None:
    """Delete a ServiceAccount by name."""

    def _call() -> None:
        core_v1().delete_namespaced_service_account(
            name, namespace, _request_timeout=timeout,
        )
        logger.info(f"Deleted ServiceAccount '{name}' in '{namespace}'.")

    call_with_retry(_call)


# ── Role operations ──────────────────────────────────────────────────────────

def list_roles(
    namespace: str = "default",
    timeout: int = K8S_API_TIMEOUT_SECONDS,
) -> list[RoleInfo]:
    """List namespaced Roles."""

    def _call() -> list[RoleInfo]:
        api = rbac_v1()
        if namespace == "all":
            response = api.list_role_for_all_namespaces(_request_timeout=timeout)
        else:
            response = api.list_namespaced_role(namespace, _request_timeout=timeout)

        items: list[RoleInfo] = []
        for role in response.items:
            meta = role.metadata
            items.append(RoleInfo(
                name=meta.name or "" if meta else "",
                namespace=meta.namespace or "" if meta else "",
                rules_count=len(role.rules or []),
                age=_compute_age(meta.creation_timestamp) if meta else "",
            ))
        return items

    return call_with_retry(_call)


def create_role(
    name: str,
    namespace: str,
    rules: list[PolicyRule],
    timeout: int = K8S_API_TIMEOUT_SECONDS,
) -> None:
    """Create a namespaced Role with the given rules."""

    def _call() -> None:
        k8s_rules = [
            k8s_client.V1PolicyRule(
                api_groups=r.api_groups,
                resources=r.resources,
                verbs=r.verbs,
            )
            for r in rules
        ]
        body = k8s_client.V1Role(
            metadata=k8s_client.V1ObjectMeta(name=name),
            rules=k8s_rules,
        )
        rbac_v1().create_namespaced_role(namespace, body, _request_timeout=timeout)
        logger.info(f"Created Role '{name}' in '{namespace}'.")

    call_with_retry(_call)


def delete_role(
    name: str,
    namespace: str = "default",
    timeout: int = K8S_API_TIMEOUT_SECONDS,
) -> None:
    """Delete a namespaced Role."""

    def _call() -> None:
        rbac_v1().delete_namespaced_role(name, namespace, _request_timeout=timeout)
        logger.info(f"Deleted Role '{name}' in '{namespace}'.")

    call_with_retry(_call)


# ── ClusterRole operations ───────────────────────────────────────────────────

def list_cluster_roles(
    timeout: int = K8S_API_TIMEOUT_SECONDS,
) -> list[ClusterRoleInfo]:
    """List ClusterRoles."""

    def _call() -> list[ClusterRoleInfo]:
        response = rbac_v1().list_cluster_role(_request_timeout=timeout)
        items: list[ClusterRoleInfo] = []
        for cr in response.items:
            meta = cr.metadata
            items.append(ClusterRoleInfo(
                name=meta.name or "" if meta else "",
                rules_count=len(cr.rules or []),
                age=_compute_age(meta.creation_timestamp) if meta else "",
            ))
        return items

    return call_with_retry(_call)


# ── RoleBinding operations ───────────────────────────────────────────────────

def list_role_bindings(
    namespace: str = "default",
    timeout: int = K8S_API_TIMEOUT_SECONDS,
) -> list[RoleBindingInfo]:
    """List RoleBindings in a namespace."""

    def _call() -> list[RoleBindingInfo]:
        api = rbac_v1()
        if namespace == "all":
            response = api.list_role_binding_for_all_namespaces(
                _request_timeout=timeout,
            )
        else:
            response = api.list_namespaced_role_binding(
                namespace, _request_timeout=timeout,
            )

        items: list[RoleBindingInfo] = []
        for rb in response.items:
            meta = rb.metadata
            role_ref = rb.role_ref
            subjects = rb.subjects or []
            subject_names = ", ".join(
                f"{s.kind}/{s.name}" for s in subjects
            )
            items.append(RoleBindingInfo(
                name=meta.name or "" if meta else "",
                namespace=meta.namespace or "" if meta else "",
                role_kind=role_ref.kind if role_ref else "",
                role_name=role_ref.name if role_ref else "",
                subjects=subject_names or "<none>",
                age=_compute_age(meta.creation_timestamp) if meta else "",
            ))
        return items

    return call_with_retry(_call)


def create_role_binding(
    name: str,
    namespace: str,
    role_name: str,
    role_kind: str = "Role",
    subject_name: str = "",
    subject_kind: str = "ServiceAccount",
    subject_namespace: str = "",
    timeout: int = K8S_API_TIMEOUT_SECONDS,
) -> None:
    """Create a RoleBinding linking a subject to a role."""

    def _call() -> None:
        body = k8s_client.V1RoleBinding(
            metadata=k8s_client.V1ObjectMeta(name=name),
            role_ref=k8s_client.V1RoleRef(
                api_group="rbac.authorization.k8s.io",
                kind=role_kind,
                name=role_name,
            ),
            subjects=[
                k8s_client.RbacV1Subject(
                    kind=subject_kind,
                    name=subject_name,
                    namespace=subject_namespace or namespace,
                ),
            ],
        )
        rbac_v1().create_namespaced_role_binding(
            namespace, body, _request_timeout=timeout,
        )
        logger.info(f"Created RoleBinding '{name}' in '{namespace}'.")

    call_with_retry(_call)


def delete_role_binding(
    name: str,
    namespace: str = "default",
    timeout: int = K8S_API_TIMEOUT_SECONDS,
) -> None:
    """Delete a RoleBinding by name."""

    def _call() -> None:
        rbac_v1().delete_namespaced_role_binding(
            name, namespace, _request_timeout=timeout,
        )
        logger.info(f"Deleted RoleBinding '{name}' in '{namespace}'.")

    call_with_retry(_call)

