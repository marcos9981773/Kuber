"""
kuber/core/kubernetes/deployments.py
Deployment CRUD, scale, and rolling-update operations.
No PyQt5 imports.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from kubernetes import client as k8s_client

from kuber.constants import K8S_API_TIMEOUT_SECONDS
from kuber.core.exceptions import KuberNotFoundError, KuberValidationError
from kuber.core.kubernetes.client import apps_v1, call_with_retry
from kuber.core.kubernetes.pods import _compute_age

logger = logging.getLogger(__name__)


@dataclass
class DeploymentInfo:
    """Lightweight representation of a Kubernetes Deployment."""

    name: str
    namespace: str
    replicas: int
    ready_replicas: int
    image: str
    age: str
    strategy: str


def list_deployments(
    namespace: str = "default",
    timeout: int = K8S_API_TIMEOUT_SECONDS,
) -> list[DeploymentInfo]:
    """List deployments in a namespace."""
    def _call() -> list[DeploymentInfo]:
        api = apps_v1()
        if namespace == "all":
            response = api.list_deployment_for_all_namespaces(_request_timeout=timeout)
        else:
            response = api.list_namespaced_deployment(namespace, _request_timeout=timeout)

        items: list[DeploymentInfo] = []
        for dep in response.items:
            meta = dep.metadata
            spec = dep.spec
            status = dep.status
            containers = spec.template.spec.containers if spec and spec.template.spec else []
            image = containers[0].image or "" if containers else ""
            strategy = spec.strategy.type if spec and spec.strategy else ""

            items.append(DeploymentInfo(
                name=meta.name or "" if meta else "",
                namespace=meta.namespace or "" if meta else "",
                replicas=spec.replicas or 0 if spec else 0,
                ready_replicas=status.ready_replicas or 0 if status else 0,
                image=image,
                age=_compute_age(meta.creation_timestamp) if meta else "",
                strategy=strategy,
            ))
        return items

    return call_with_retry(_call)


def scale_deployment(
    name: str,
    namespace: str,
    replicas: int,
    timeout: int = K8S_API_TIMEOUT_SECONDS,
) -> None:
    """
    Scale a deployment to the specified number of replicas.

    Raises:
        KuberValidationError: If replicas < 0.
        KuberNotFoundError:   If the deployment does not exist.
    """
    if replicas < 0:
        raise KuberValidationError("Replica count cannot be negative.")

    def _call() -> None:
        body = {"spec": {"replicas": replicas}}
        apps_v1().patch_namespaced_deployment_scale(
            name, namespace, body, _request_timeout=timeout
        )
        logger.info(f"Scaled deployment '{name}' in '{namespace}' to {replicas} replicas.")

    call_with_retry(_call)


def update_deployment_image(
    name: str,
    namespace: str,
    container_name: str,
    image: str,
    timeout: int = K8S_API_TIMEOUT_SECONDS,
) -> None:
    """
    Trigger a rolling update by setting a new container image.

    Args:
        name:           Deployment name.
        namespace:      Target namespace.
        container_name: Name of the container to update.
        image:          New image reference (e.g., ``"nginx:1.25"``).
    """
    def _call() -> None:
        body = {
            "spec": {
                "template": {
                    "spec": {
                        "containers": [{"name": container_name, "image": image}]
                    }
                }
            }
        }
        apps_v1().patch_namespaced_deployment(name, namespace, body, _request_timeout=timeout)
        logger.info(f"Updated image of '{container_name}' in deployment '{name}' to '{image}'.")

    call_with_retry(_call)


def delete_deployment(
    name: str,
    namespace: str,
    timeout: int = K8S_API_TIMEOUT_SECONDS,
) -> None:
    """Delete a deployment by name."""
    def _call() -> None:
        apps_v1().delete_namespaced_deployment(name, namespace, _request_timeout=timeout)
        logger.info(f"Deleted deployment '{name}' in '{namespace}'.")

    call_with_retry(_call)


def apply_manifest(
    manifest: dict,  # type: ignore[type-arg]
    namespace: str,
    timeout: int = K8S_API_TIMEOUT_SECONDS,
) -> None:
    """
    Apply a Deployment manifest (create or replace).

    Args:
        manifest:  Parsed YAML/JSON dict of the Deployment resource.
        namespace: Target namespace.

    Raises:
        KuberValidationError: If the manifest is not a Deployment kind.
    """
    kind = manifest.get("kind", "")
    if kind != "Deployment":
        raise KuberValidationError(f"Expected kind 'Deployment', got '{kind}'.")

    name: str = manifest.get("metadata", {}).get("name", "")

    def _call() -> None:
        try:
            apps_v1().replace_namespaced_deployment(
                name, namespace, manifest, _request_timeout=timeout
            )
            logger.info(f"Replaced deployment '{name}' in '{namespace}'.")
        except Exception:
            apps_v1().create_namespaced_deployment(
                namespace, manifest, _request_timeout=timeout
            )
            logger.info(f"Created deployment '{name}' in '{namespace}'.")

    call_with_retry(_call)

