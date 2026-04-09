"""
kuber/core/kubernetes/services.py
Kubernetes Service read and basic operations.
No PyQt5 imports.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from kuber.constants import K8S_API_TIMEOUT_SECONDS
from kuber.core.kubernetes.client import call_with_retry, core_v1
from kuber.core.kubernetes.pods import _compute_age

logger = logging.getLogger(__name__)


@dataclass
class ServicePort:
    port: int
    target_port: str
    protocol: str
    node_port: int | None = None


@dataclass
class ServiceInfo:
    """Lightweight representation of a Kubernetes Service."""

    name: str
    namespace: str
    type: str            # ClusterIP | NodePort | LoadBalancer | ExternalName
    cluster_ip: str
    external_ip: str
    ports: list[ServicePort] = field(default_factory=list)
    age: str = ""


def list_services(
    namespace: str = "default",
    timeout: int = K8S_API_TIMEOUT_SECONDS,
) -> list[ServiceInfo]:
    """List services in a namespace."""
    def _call() -> list[ServiceInfo]:
        api = core_v1()
        if namespace == "all":
            response = api.list_service_for_all_namespaces(_request_timeout=timeout)
        else:
            response = api.list_namespaced_service(namespace, _request_timeout=timeout)

        items: list[ServiceInfo] = []
        for svc in response.items:
            meta = svc.metadata
            spec = svc.spec
            status = svc.status

            ext_ips: list[str] = []
            if status and status.load_balancer and status.load_balancer.ingress:
                ext_ips = [
                    ing.ip or ing.hostname or ""
                    for ing in status.load_balancer.ingress
                ]

            ports: list[ServicePort] = []
            for p in (spec.ports or [] if spec else []):
                ports.append(ServicePort(
                    port=p.port,
                    target_port=str(p.target_port),
                    protocol=p.protocol or "TCP",
                    node_port=p.node_port,
                ))

            items.append(ServiceInfo(
                name=meta.name or "" if meta else "",
                namespace=meta.namespace or "" if meta else "",
                type=spec.type or "ClusterIP" if spec else "ClusterIP",
                cluster_ip=spec.cluster_ip or "" if spec else "",
                external_ip=", ".join(ext_ips) or "<none>",
                ports=ports,
                age=_compute_age(meta.creation_timestamp) if meta else "",
            ))
        return items

    return call_with_retry(_call)


def delete_service(
    name: str,
    namespace: str,
    timeout: int = K8S_API_TIMEOUT_SECONDS,
) -> None:
    """Delete a service by name."""
    def _call() -> None:
        core_v1().delete_namespaced_service(name, namespace, _request_timeout=timeout)
        logger.info(f"Deleted service '{name}' in '{namespace}'.")

    call_with_retry(_call)

