"""
kuber/core/kubernetes/events.py
Kubernetes cluster event operations.
No PyQt5 imports.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from kuber.constants import K8S_API_TIMEOUT_SECONDS
from kuber.core.kubernetes.client import call_with_retry, core_v1
from kuber.core.kubernetes.pods import _compute_age

logger = logging.getLogger(__name__)


@dataclass
class EventInfo:
    """Lightweight representation of a Kubernetes Event."""

    namespace: str
    name: str
    type: str            # Normal | Warning
    reason: str
    message: str
    source: str
    involved_object: str
    count: int
    age: str


def list_events(
    namespace: str = "default",
    timeout: int = K8S_API_TIMEOUT_SECONDS,
) -> list[EventInfo]:
    """List events in a namespace (or all namespaces)."""
    def _call() -> list[EventInfo]:
        api = core_v1()
        if namespace == "all":
            response = api.list_event_for_all_namespaces(_request_timeout=timeout)
        else:
            response = api.list_namespaced_event(namespace, _request_timeout=timeout)

        items: list[EventInfo] = []
        for ev in response.items:
            meta = ev.metadata
            obj = ev.involved_object
            items.append(EventInfo(
                namespace=meta.namespace or "" if meta else "",
                name=meta.name or "" if meta else "",
                type=ev.type or "Normal",
                reason=ev.reason or "",
                message=ev.message or "",
                source=(ev.source.component or "") if ev.source else "",
                involved_object=f"{obj.kind}/{obj.name}" if obj else "",
                count=ev.count or 1,
                age=_compute_age(meta.creation_timestamp) if meta else "",
            ))
        return items

    return call_with_retry(_call)

