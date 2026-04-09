"""
tests/unit/core/cloud/test_provider_factory.py
Tests for kuber/core/cloud/provider_factory.py
"""
from __future__ import annotations

import pytest


class TestProviderFactory:
    def test_get_provider_eks(self) -> None:
        from kuber.core.cloud.provider_factory import get_provider, EKSProvider
        provider = get_provider("eks")
        assert isinstance(provider, EKSProvider)
        assert provider.provider_name() == "eks"

    def test_get_provider_gke(self) -> None:
        from kuber.core.cloud.provider_factory import get_provider, GKEProvider
        provider = get_provider("gke")
        assert isinstance(provider, GKEProvider)

    def test_get_provider_aks(self) -> None:
        from kuber.core.cloud.provider_factory import get_provider, AKSProvider
        provider = get_provider("aks")
        assert isinstance(provider, AKSProvider)

    def test_get_provider_unknown_raises(self) -> None:
        from kuber.core.cloud.provider_factory import get_provider
        with pytest.raises(ValueError, match="Unknown cloud provider"):
            get_provider("unknown")

    def test_get_provider_case_insensitive(self) -> None:
        from kuber.core.cloud.provider_factory import get_provider, EKSProvider
        provider = get_provider("EKS")
        assert isinstance(provider, EKSProvider)


class TestCloudCluster:
    def test_cloud_cluster_dataclass(self) -> None:
        from kuber.core.cloud.provider_factory import CloudCluster
        cluster = CloudCluster(
            name="prod", region="us-east-1", provider="eks",
            status="ACTIVE", version="1.29",
        )
        assert cluster.name == "prod"
        assert cluster.provider == "eks"


class TestEKSProvider:
    def test_is_available_returns_bool(self) -> None:
        from kuber.core.cloud.provider_factory import EKSProvider
        result = EKSProvider().is_available()
        assert isinstance(result, bool)

    def test_list_clusters_without_sdk_returns_empty(self, mocker) -> None:
        mocker.patch.dict("sys.modules", {"boto3": None})
        from kuber.core.cloud.provider_factory import EKSProvider
        provider = EKSProvider()
        result = provider.list_clusters("us-east-1")
        assert result == []


class TestOpenShiftClient:
    def test_is_openshift_cluster_returns_false_on_error(self, mocker) -> None:
        mocker.patch(
            "kubernetes.client.ApisApi",
            side_effect=Exception("no cluster"),
        )
        from kuber.core.openshift.client import is_openshift_cluster
        assert is_openshift_cluster() is False


class TestCustomResourceView:
    def test_view_creates(self, qtbot) -> None:
        from kuber.views.resources.custom_resource_view import CustomResourceView
        view = CustomResourceView()
        qtbot.addWidget(view)
        assert view._table is not None
        assert view._crd_combo is not None

    def test_set_crds_populates_combo(self, qtbot) -> None:
        from kuber.core.kubernetes.custom_resources import CRDInfo
        from kuber.views.resources.custom_resource_view import CustomResourceView
        view = CustomResourceView()
        qtbot.addWidget(view)
        crds = [
            CRDInfo("widgets.example.com", "example.com", "v1", "Widget", "Namespaced", "widgets"),
        ]
        view.set_crds(crds)
        assert view._crd_combo.count() == 1
        assert view.selected_crd() is not None
        assert view.selected_crd().kind == "Widget"

    def test_set_instances_populates_model(self, qtbot) -> None:
        from kuber.core.kubernetes.custom_resources import CustomResourceInstance
        from kuber.views.resources.custom_resource_view import CustomResourceView
        view = CustomResourceView()
        qtbot.addWidget(view)
        instances = [
            CustomResourceInstance("w-1", "default", "Widget", "example.com/v1"),
        ]
        view.set_instances(instances)
        assert view._model.rowCount() == 1


class TestCloudSettingsView:
    def test_view_creates(self, qtbot) -> None:
        from kuber.views.settings.cloud_settings_view import CloudSettingsView
        view = CloudSettingsView()
        qtbot.addWidget(view)
        assert view._eks_region is not None
        assert view._gke_project is not None
        assert view._aks_subscription is not None

    def test_get_eks_config(self, qtbot) -> None:
        from kuber.views.settings.cloud_settings_view import CloudSettingsView
        view = CloudSettingsView()
        qtbot.addWidget(view)
        view._eks_region.setText("us-west-2")
        view._eks_profile.setText("production")
        config = view.get_eks_config()
        assert config["region"] == "us-west-2"
        assert config["profile"] == "production"

    def test_get_gke_config(self, qtbot) -> None:
        from kuber.views.settings.cloud_settings_view import CloudSettingsView
        view = CloudSettingsView()
        qtbot.addWidget(view)
        view._gke_project.setText("my-project")
        config = view.get_gke_config()
        assert config["project"] == "my-project"

    def test_accessible_names_set(self, qtbot) -> None:
        from kuber.views.settings.cloud_settings_view import CloudSettingsView
        view = CloudSettingsView()
        qtbot.addWidget(view)
        assert view._eks_region.accessibleName() != ""
        assert view._btn_save.accessibleName() != ""

