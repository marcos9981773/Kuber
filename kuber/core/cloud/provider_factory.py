"""
kuber/core/cloud/provider_factory.py
Unified cloud provider abstraction for AWS EKS, GCP GKE, and Azure AKS.
No PyQt5 imports.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CloudCluster:
    """Normalized cluster info from any cloud provider."""

    name: str
    region: str
    provider: str  # "eks" | "gke" | "aks"
    status: str
    version: str
    node_count: int = 0
    endpoint: str = ""


class CloudProvider(ABC):
    """Abstract interface for a cloud provider."""

    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider identifier (eks, gke, aks)."""

    @abstractmethod
    def list_clusters(self, region: str = "") -> list[CloudCluster]:
        """List Kubernetes clusters from this provider."""

    @abstractmethod
    def get_cluster(self, name: str, region: str = "") -> CloudCluster:
        """Get details for a single cluster."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider credentials / CLI is available."""


class EKSProvider(CloudProvider):
    """AWS EKS provider (requires boto3)."""

    def provider_name(self) -> str:
        return "eks"

    def is_available(self) -> bool:
        try:
            import boto3  # noqa: F401
            return True
        except ImportError:
            return False

    def list_clusters(self, region: str = "") -> list[CloudCluster]:
        try:
            import boto3
            client = boto3.client("eks", region_name=region or None)
            names = client.list_clusters().get("clusters", [])
            clusters: list[CloudCluster] = []
            for name in names:
                info = client.describe_cluster(name=name).get("cluster", {})
                clusters.append(CloudCluster(
                    name=name,
                    region=region,
                    provider="eks",
                    status=info.get("status", "UNKNOWN"),
                    version=info.get("version", ""),
                    endpoint=info.get("endpoint", ""),
                ))
            return clusters
        except Exception as exc:
            logger.warning(f"EKS list_clusters failed: {exc}")
            return []

    def get_cluster(self, name: str, region: str = "") -> CloudCluster:
        import boto3
        client = boto3.client("eks", region_name=region or None)
        info = client.describe_cluster(name=name).get("cluster", {})
        return CloudCluster(
            name=name,
            region=region,
            provider="eks",
            status=info.get("status", "UNKNOWN"),
            version=info.get("version", ""),
            endpoint=info.get("endpoint", ""),
        )


class GKEProvider(CloudProvider):
    """Google GKE provider (requires google-cloud-container)."""

    def provider_name(self) -> str:
        return "gke"

    def is_available(self) -> bool:
        try:
            from google.cloud import container_v1  # noqa: F401
            return True
        except ImportError:
            return False

    def list_clusters(self, region: str = "") -> list[CloudCluster]:
        try:
            from google.cloud import container_v1
            client = container_v1.ClusterManagerClient()
            parent = f"projects/-/locations/{region or '-'}"
            response = client.list_clusters(parent=parent)
            return [
                CloudCluster(
                    name=c.name,
                    region=c.location,
                    provider="gke",
                    status=c.status.name if c.status else "UNKNOWN",
                    version=c.current_master_version or "",
                    node_count=c.current_node_count or 0,
                    endpoint=c.endpoint or "",
                )
                for c in response.clusters
            ]
        except Exception as exc:
            logger.warning(f"GKE list_clusters failed: {exc}")
            return []

    def get_cluster(self, name: str, region: str = "") -> CloudCluster:
        from google.cloud import container_v1
        client = container_v1.ClusterManagerClient()
        full_name = f"projects/-/locations/{region or '-'}/clusters/{name}"
        c = client.get_cluster(name=full_name)
        return CloudCluster(
            name=c.name,
            region=c.location,
            provider="gke",
            status=c.status.name if c.status else "UNKNOWN",
            version=c.current_master_version or "",
            node_count=c.current_node_count or 0,
            endpoint=c.endpoint or "",
        )


class AKSProvider(CloudProvider):
    """Azure AKS provider (requires azure-mgmt-containerservice)."""

    def provider_name(self) -> str:
        return "aks"

    def is_available(self) -> bool:
        try:
            from azure.mgmt.containerservice import ContainerServiceClient  # noqa: F401
            return True
        except ImportError:
            return False

    def list_clusters(self, region: str = "") -> list[CloudCluster]:
        try:
            from azure.identity import DefaultAzureCredential
            from azure.mgmt.containerservice import ContainerServiceClient
            credential = DefaultAzureCredential()
            # subscription_id should be configured; placeholder
            sub_id = ""
            client = ContainerServiceClient(credential, sub_id)
            clusters: list[CloudCluster] = []
            for c in client.managed_clusters.list():
                clusters.append(CloudCluster(
                    name=c.name or "",
                    region=c.location or "",
                    provider="aks",
                    status=c.provisioning_state or "Unknown",
                    version=c.kubernetes_version or "",
                    endpoint=c.fqdn or "",
                ))
            return clusters
        except Exception as exc:
            logger.warning(f"AKS list_clusters failed: {exc}")
            return []

    def get_cluster(self, name: str, region: str = "") -> CloudCluster:
        raise NotImplementedError("AKS get_cluster requires resource group")


# ── Factory ──────────────────────────────────────────────────────────────────

_PROVIDERS: dict[str, type[CloudProvider]] = {
    "eks": EKSProvider,
    "gke": GKEProvider,
    "aks": AKSProvider,
}


def get_provider(name: str) -> CloudProvider:
    """
    Return a cloud provider instance by name.

    Args:
        name: One of ``"eks"``, ``"gke"``, ``"aks"``.

    Raises:
        ValueError: If the provider name is not recognized.
    """
    cls = _PROVIDERS.get(name.lower())
    if cls is None:
        raise ValueError(
            f"Unknown cloud provider '{name}'. "
            f"Supported: {', '.join(_PROVIDERS.keys())}"
        )
    return cls()


def list_available_providers() -> list[str]:
    """Return names of providers whose SDK is installed."""
    return [
        name for name, cls in _PROVIDERS.items()
        if cls().is_available()
    ]

