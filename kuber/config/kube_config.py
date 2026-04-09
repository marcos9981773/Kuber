"""
kuber/config/kube_config.py
Kubernetes configuration loader and context management.
No PyQt5 imports.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from kubernetes import client as k8s_client
from kubernetes import config as k8s_config
from kubernetes.client.exceptions import ApiException
from kubernetes.config.config_exception import ConfigException

from kuber.constants import K8S_API_TIMEOUT_SECONDS, KUBE_CONFIG_DEFAULT
from kuber.core.exceptions import (
    KuberApiError,
    KuberConfigError,
    KuberConnectionError,
    KuberPermissionError,
)

logger = logging.getLogger(__name__)


@dataclass
class KubeContext:
    """Represents a single Kubernetes context from kubeconfig."""

    name: str
    cluster: str
    user: str
    namespace: str = "default"
    is_active: bool = False
    server: str = ""


@dataclass
class KubeConfigInfo:
    """Parsed kubeconfig state."""

    contexts: list[KubeContext] = field(default_factory=list)
    active_context_name: str = ""
    config_path: Path = KUBE_CONFIG_DEFAULT


def load_kube_config(config_path: Path = KUBE_CONFIG_DEFAULT) -> KubeConfigInfo:
    """
    Load kubeconfig from disk and return parsed context information.

    Args:
        config_path: Path to the kubeconfig file.

    Returns:
        :class:`KubeConfigInfo` with all available contexts.

    Raises:
        KuberConfigError: If the file is missing or malformed.
    """
    if not config_path.exists():
        raise KuberConfigError(
            f"Kubeconfig file not found at '{config_path}'.",
            details="Create a kubeconfig file or set the KUBECONFIG environment variable.",
        )

    try:
        k8s_config.load_kube_config(config_file=str(config_path))
        raw_contexts, raw_active = k8s_config.list_kube_config_contexts(
            config_file=str(config_path)
        )
    except ConfigException as exc:
        raise KuberConfigError(
            f"Kubeconfig file at '{config_path}' is invalid.",
            details=str(exc),
        ) from exc

    active_name = raw_active.get("name", "") if raw_active else ""

    contexts: list[KubeContext] = []
    for ctx in raw_contexts:
        name = ctx.get("name", "")
        ctx_info: dict[str, Any] = ctx.get("context", {})
        contexts.append(
            KubeContext(
                name=name,
                cluster=ctx_info.get("cluster", ""),
                user=ctx_info.get("user", ""),
                namespace=ctx_info.get("namespace", "default"),
                is_active=(name == active_name),
                server=_get_server_for_context(ctx_info.get("cluster", ""), config_path),
            )
        )

    logger.info(f"Loaded {len(contexts)} context(s) from {config_path}; active='{active_name}'")
    return KubeConfigInfo(
        contexts=contexts,
        active_context_name=active_name,
        config_path=config_path,
    )


def switch_context(context_name: str, config_path: Path = KUBE_CONFIG_DEFAULT) -> None:
    """
    Switch the active Kubernetes context.

    Args:
        context_name: Name of the context to activate.
        config_path:  Path to the kubeconfig file.

    Raises:
        KuberConfigError: If the context name is not found.
    """
    try:
        k8s_config.load_kube_config(
            config_file=str(config_path),
            context=context_name,
        )
        logger.info(f"Switched active context to '{context_name}'")
    except ConfigException as exc:
        raise KuberConfigError(
            f"Cannot switch to context '{context_name}'.",
            details=str(exc),
        ) from exc


def validate_cluster_access(timeout: int = K8S_API_TIMEOUT_SECONDS) -> None:
    """
    Verify that the current kubeconfig grants API access.

    Calls the Kubernetes version endpoint as a lightweight connectivity check
    and validates basic RBAC permissions by listing namespaces.

    Args:
        timeout: Request timeout in seconds.

    Raises:
        KuberConnectionError: If the API server is unreachable.
        KuberPermissionError: If the user lacks required permissions.
        KuberApiError:        For any other API error.
    """
    version_api = k8s_client.VersionApi()
    try:
        version_api.get_code(_request_timeout=timeout)
        logger.debug("Kubernetes API version endpoint reachable.")
    except ApiException as exc:
        if exc.status == 403:
            raise KuberPermissionError(
                "Cannot access the Kubernetes API.",
                details=f"Insufficient permissions: {exc.reason}",
            ) from exc
        raise KuberApiError(
            "Kubernetes API returned an error.",
            status_code=exc.status,
            details=exc.reason,
        ) from exc
    except Exception as exc:
        raise KuberConnectionError(
            "Cannot reach the Kubernetes API server.",
            details=str(exc),
        ) from exc


# ── Private helpers ─────────────────────────────────────────────────────────

def _get_server_for_context(cluster_name: str, config_path: Path) -> str:
    """Extract the API server URL for a given cluster name from the kubeconfig."""
    try:
        import yaml

        with config_path.open(encoding="utf-8") as fh:
            raw: dict[str, Any] = yaml.safe_load(fh)

        for cluster_entry in raw.get("clusters", []):
            if cluster_entry.get("name") == cluster_name:
                return cluster_entry.get("cluster", {}).get("server", "")
    except Exception:
        pass
    return ""

