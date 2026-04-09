"""
tests/unit/services/test_backup_service.py
Tests for kuber/services/backup_service.py using temporary file system.
"""
from __future__ import annotations

import tarfile
import pytest
from pathlib import Path

import yaml


class TestCreateBackup:
    def test_create_backup_produces_tar_gz(self, tmp_path, mocker) -> None:
        mocker.patch(
            "kuber.services.backup_service._fetch_all_namespaces",
            return_value=["default"],
        )
        mocker.patch(
            "kuber.services.backup_service._fetch_resources",
            return_value=[{
                "apiVersion": "v1",
                "kind": "ConfigMap",
                "metadata": {"name": "app-config", "namespace": "default"},
                "data": {"key": "value"},
            }],
        )

        from kuber.services.backup_service import create_backup
        manifest = create_backup(output_dir=tmp_path)

        assert manifest.filename.endswith(".tar.gz")
        assert manifest.resource_count > 0
        assert (tmp_path / manifest.filename).exists()

    def test_create_backup_contains_meta(self, tmp_path, mocker) -> None:
        mocker.patch(
            "kuber.services.backup_service._fetch_all_namespaces",
            return_value=["default"],
        )
        mocker.patch(
            "kuber.services.backup_service._fetch_resources",
            return_value=[],
        )

        from kuber.services.backup_service import create_backup
        manifest = create_backup(output_dir=tmp_path)

        with tarfile.open(tmp_path / manifest.filename, "r:gz") as tar:
            names = tar.getnames()
            assert "backup_meta.yaml" in names

    def test_create_backup_with_specific_namespaces(self, tmp_path, mocker) -> None:
        mocker.patch(
            "kuber.services.backup_service._fetch_resources",
            return_value=[],
        )

        from kuber.services.backup_service import create_backup
        manifest = create_backup(
            namespaces=["ns1", "ns2"],
            output_dir=tmp_path,
        )
        assert manifest.namespaces == ["ns1", "ns2"]


class TestListBackups:
    def test_list_backups_empty_dir(self, tmp_path) -> None:
        from kuber.services.backup_service import list_backups
        result = list_backups(backup_dir=tmp_path)
        assert result == []

    def test_list_backups_finds_archives(self, tmp_path, mocker) -> None:
        mocker.patch(
            "kuber.services.backup_service._fetch_all_namespaces",
            return_value=["default"],
        )
        mocker.patch(
            "kuber.services.backup_service._fetch_resources",
            return_value=[],
        )

        from kuber.services.backup_service import create_backup, list_backups
        create_backup(output_dir=tmp_path)
        result = list_backups(backup_dir=tmp_path)
        assert len(result) == 1

    def test_list_backups_nonexistent_dir(self, tmp_path) -> None:
        from kuber.services.backup_service import list_backups
        result = list_backups(backup_dir=tmp_path / "nonexistent")
        assert result == []


class TestRestoreBackup:
    def test_restore_dry_run_does_not_apply(self, tmp_path, mocker) -> None:
        mocker.patch(
            "kuber.services.backup_service._fetch_all_namespaces",
            return_value=["default"],
        )
        mocker.patch(
            "kuber.services.backup_service._fetch_resources",
            return_value=[{
                "apiVersion": "v1",
                "kind": "ConfigMap",
                "metadata": {"name": "cm-1", "namespace": "default"},
                "data": {"k": "v"},
            }],
        )
        mock_apply = mocker.patch(
            "kuber.services.backup_service._apply_resource",
        )

        from kuber.services.backup_service import create_backup, restore_backup
        manifest = create_backup(output_dir=tmp_path)
        count = restore_backup(
            manifest.filename, backup_dir=tmp_path, dry_run=True,
        )
        assert count > 0
        mock_apply.assert_not_called()

    def test_restore_nonexistent_file_raises(self, tmp_path) -> None:
        from kuber.services.backup_service import restore_backup
        from kuber.core.exceptions import KuberBackupError

        with pytest.raises(KuberBackupError):
            restore_backup("nonexistent.tar.gz", backup_dir=tmp_path)


class TestDeleteBackup:
    def test_delete_backup_removes_file(self, tmp_path, mocker) -> None:
        mocker.patch(
            "kuber.services.backup_service._fetch_all_namespaces",
            return_value=["default"],
        )
        mocker.patch(
            "kuber.services.backup_service._fetch_resources",
            return_value=[],
        )

        from kuber.services.backup_service import create_backup, delete_backup
        manifest = create_backup(output_dir=tmp_path)
        filepath = tmp_path / manifest.filename
        assert filepath.exists()

        delete_backup(manifest.filename, backup_dir=tmp_path)
        assert not filepath.exists()

