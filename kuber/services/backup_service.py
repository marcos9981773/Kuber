"""
kuber/services/backup_service.py
Backup and restore Kubernetes resources as compressed YAML archives.
No PyQt5 imports.
"""
from __future__ import annotations

import logging
import tarfile
import tempfile
import time
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import Any

import yaml

from kuber.constants import BACKUPS_DIR, K8S_API_TIMEOUT_SECONDS
from kuber.core.exceptions import KuberBackupError, KuberValidationError
from kuber.core.kubernetes.client import call_with_retry, core_v1, apps_v1, rbac_v1

logger = logging.getLogger(__name__)

# Resource types available for backup
BACKUP_RESOURCE_TYPES = [
    "configmaps", "secrets", "services", "deployments",
    "serviceaccounts", "roles", "rolebindings",
]


@dataclass
class BackupManifest:
    """Metadata about a completed backup."""

    filename: str
    timestamp: str
    namespaces: list[str] = field(default_factory=list)
    resource_types: list[str] = field(default_factory=list)
    resource_count: int = 0
    size_bytes: int = 0


def create_backup(
    namespaces: list[str] | None = None,
    resource_types: list[str] | None = None,
    output_dir: Path | None = None,
    timeout: int = K8S_API_TIMEOUT_SECONDS,
) -> BackupManifest:
    """
    Export Kubernetes resources to a compressed ``.tar.gz`` archive.

    Args:
        namespaces:     Namespaces to back up (None = all).
        resource_types: Resource types to include (None = all supported).
        output_dir:     Target directory (default: ``BACKUPS_DIR``).
        timeout:        API timeout per request.

    Returns:
        A :class:`BackupManifest` describing the created backup.
    """
    output_dir = output_dir or BACKUPS_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    types = resource_types or list(BACKUP_RESOURCE_TYPES)
    ts = time.strftime("%Y%m%d_%H%M%S")
    filename = f"kuber_backup_{ts}.tar.gz"
    filepath = output_dir / filename

    ns_list = namespaces or _fetch_all_namespaces(timeout)
    resource_count = 0

    try:
        with tarfile.open(filepath, "w:gz") as tar:
            # Write manifest.yaml first
            for ns in ns_list:
                for rtype in types:
                    items = _fetch_resources(rtype, ns, timeout)
                    for item in items:
                        name = item.get("metadata", {}).get("name", "unknown")
                        yaml_bytes = yaml.dump(
                            item, default_flow_style=False,
                        ).encode("utf-8")
                        member_path = f"{ns}/{rtype}/{name}.yaml"
                        info = tarfile.TarInfo(name=member_path)
                        info.size = len(yaml_bytes)
                        tar.addfile(info, BytesIO(yaml_bytes))
                        resource_count += 1

            # Add backup metadata
            meta = {
                "timestamp": ts,
                "namespaces": ns_list,
                "resource_types": types,
                "resource_count": resource_count,
            }
            meta_bytes = yaml.dump(meta, default_flow_style=False).encode("utf-8")
            info = tarfile.TarInfo(name="backup_meta.yaml")
            info.size = len(meta_bytes)
            tar.addfile(info, BytesIO(meta_bytes))

    except Exception as exc:
        logger.error(f"Backup failed: {exc}")
        if filepath.exists():
            filepath.unlink()
        raise KuberBackupError(
            "Backup creation failed.",
            details=str(exc),
        ) from exc

    size = filepath.stat().st_size
    logger.info(
        f"Backup created: {filename} ({resource_count} resources, "
        f"{size / 1024:.1f} KB)"
    )

    return BackupManifest(
        filename=filename,
        timestamp=ts,
        namespaces=ns_list,
        resource_types=types,
        resource_count=resource_count,
        size_bytes=size,
    )


def list_backups(backup_dir: Path | None = None) -> list[BackupManifest]:
    """List all backup archives in the backup directory."""
    backup_dir = backup_dir or BACKUPS_DIR
    if not backup_dir.exists():
        return []

    manifests: list[BackupManifest] = []
    for path in sorted(backup_dir.glob("kuber_backup_*.tar.gz"), reverse=True):
        try:
            meta = _read_backup_meta(path)
            meta["size_bytes"] = path.stat().st_size
            meta["filename"] = path.name
            manifests.append(BackupManifest(**meta))
        except Exception:
            # Corrupted backup — include with minimal info
            manifests.append(BackupManifest(
                filename=path.name,
                timestamp="unknown",
                size_bytes=path.stat().st_size,
            ))
    return manifests


def restore_backup(
    filename: str,
    backup_dir: Path | None = None,
    namespaces: list[str] | None = None,
    resource_types: list[str] | None = None,
    dry_run: bool = False,
    timeout: int = K8S_API_TIMEOUT_SECONDS,
) -> int:
    """
    Restore resources from a backup archive.

    Args:
        filename:       Backup archive filename.
        backup_dir:     Directory containing backups.
        namespaces:     Only restore these namespaces (None = all).
        resource_types: Only restore these types (None = all).
        dry_run:        If True, validate without applying.
        timeout:        API timeout.

    Returns:
        Number of resources restored.
    """
    backup_dir = backup_dir or BACKUPS_DIR
    filepath = backup_dir / filename
    if not filepath.exists():
        raise KuberBackupError(f"Backup file not found: {filename}")

    restored = 0
    try:
        with tarfile.open(filepath, "r:gz") as tar:
            for member in tar.getmembers():
                if member.name == "backup_meta.yaml":
                    continue
                parts = member.name.split("/")
                if len(parts) != 3:
                    continue

                ns, rtype, _ = parts

                if namespaces and ns not in namespaces:
                    continue
                if resource_types and rtype not in resource_types:
                    continue

                f = tar.extractfile(member)
                if f is None:
                    continue
                manifest = yaml.safe_load(f.read().decode("utf-8"))

                if not dry_run:
                    _apply_resource(manifest, ns, timeout)
                restored += 1

    except KuberBackupError:
        raise
    except Exception as exc:
        raise KuberBackupError(
            "Restore failed.",
            details=str(exc),
        ) from exc

    action = "validated" if dry_run else "restored"
    logger.info(f"Backup restore: {restored} resources {action} from {filename}.")
    return restored


def delete_backup(filename: str, backup_dir: Path | None = None) -> None:
    """Delete a backup archive."""
    backup_dir = backup_dir or BACKUPS_DIR
    filepath = backup_dir / filename
    if filepath.exists():
        filepath.unlink()
        logger.info(f"Deleted backup: {filename}")


# ── Private helpers ──────────────────────────────────────────────────────────

def _fetch_all_namespaces(timeout: int) -> list[str]:
    def _call() -> list[str]:
        resp = core_v1().list_namespace(_request_timeout=timeout)
        return [ns.metadata.name for ns in resp.items if ns.metadata]
    return call_with_retry(_call)


def _fetch_resources(
    resource_type: str, namespace: str, timeout: int,
) -> list[dict[str, Any]]:
    """Fetch raw resource dicts for a given type and namespace."""
    fetchers = {
        "configmaps": lambda: core_v1().list_namespaced_config_map(
            namespace, _request_timeout=timeout,
        ),
        "secrets": lambda: core_v1().list_namespaced_secret(
            namespace, _request_timeout=timeout,
        ),
        "services": lambda: core_v1().list_namespaced_service(
            namespace, _request_timeout=timeout,
        ),
        "serviceaccounts": lambda: core_v1().list_namespaced_service_account(
            namespace, _request_timeout=timeout,
        ),
        "deployments": lambda: apps_v1().list_namespaced_deployment(
            namespace, _request_timeout=timeout,
        ),
        "roles": lambda: rbac_v1().list_namespaced_role(
            namespace, _request_timeout=timeout,
        ),
        "rolebindings": lambda: rbac_v1().list_namespaced_role_binding(
            namespace, _request_timeout=timeout,
        ),
    }
    fetcher = fetchers.get(resource_type)
    if not fetcher:
        return []

    def _call() -> list[dict[str, Any]]:
        response = fetcher()
        from kubernetes.client import ApiClient
        api_client = ApiClient()
        items = []
        for item in response.items:
            raw = api_client.sanitize_for_serialization(item)
            # Strip cluster-specific metadata for portability
            meta = raw.get("metadata", {})
            for key in ["uid", "resourceVersion", "creationTimestamp", "managedFields"]:
                meta.pop(key, None)
            items.append(raw)
        return items

    try:
        return call_with_retry(_call)
    except Exception as exc:
        logger.warning(f"Could not fetch {resource_type} in {namespace}: {exc}")
        return []


def _read_backup_meta(filepath: Path) -> dict[str, Any]:
    """Read backup_meta.yaml from inside a tar.gz archive."""
    with tarfile.open(filepath, "r:gz") as tar:
        f = tar.extractfile("backup_meta.yaml")
        if f is None:
            return {"timestamp": "unknown"}
        return yaml.safe_load(f.read().decode("utf-8"))


def _apply_resource(
    manifest: dict[str, Any], namespace: str, timeout: int,
) -> None:
    """Apply a single resource manifest to the cluster (create or update)."""
    from kubernetes import client as k8s_client
    from kubernetes.client.exceptions import ApiException
    from kubernetes.utils import create_from_dict

    api_client = k8s_client.ApiClient()
    try:
        create_from_dict(api_client, manifest, namespace=namespace)
    except ApiException as exc:
        if exc.status == 409:
            # Resource exists — skip (could add patch logic here)
            logger.debug(f"Resource already exists, skipping: {manifest.get('metadata', {}).get('name')}")
        else:
            raise

