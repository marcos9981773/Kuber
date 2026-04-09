"""
kuber/views/settings/cloud_settings_view.py
Configuration panel for cloud provider credentials.
"""
from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class CloudSettingsView(QWidget):
    """
    Settings view for configuring cloud provider access.

    Provides credential/region inputs for AWS EKS, GCP GKE, and Azure AKS.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()
        self._setup_accessibility()
        self._setup_tab_order()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        title = QLabel(self.tr("Cloud Provider Settings"))
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        info = QLabel(self.tr(
            "Configure credentials and regions for cloud-managed Kubernetes clusters. "
            "Install the required SDK for each provider (boto3, google-cloud-container, "
            "azure-mgmt-containerservice)."
        ))
        info.setWordWrap(True)
        info.setObjectName("infoLabel")
        layout.addWidget(info)

        # AWS EKS
        self._eks_group = QGroupBox(self.tr("AWS EKS"))
        eks_form = QFormLayout(self._eks_group)
        self._eks_region = QLineEdit()
        self._eks_region.setPlaceholderText("us-east-1")
        eks_form.addRow(self.tr("Region:"), self._eks_region)
        self._eks_profile = QLineEdit()
        self._eks_profile.setPlaceholderText("default")
        eks_form.addRow(self.tr("AWS Profile:"), self._eks_profile)
        layout.addWidget(self._eks_group)

        # GCP GKE
        self._gke_group = QGroupBox(self.tr("Google GKE"))
        gke_form = QFormLayout(self._gke_group)
        self._gke_project = QLineEdit()
        self._gke_project.setPlaceholderText("my-project-id")
        gke_form.addRow(self.tr("Project ID:"), self._gke_project)
        self._gke_region = QLineEdit()
        self._gke_region.setPlaceholderText("us-central1")
        gke_form.addRow(self.tr("Region:"), self._gke_region)
        layout.addWidget(self._gke_group)

        # Azure AKS
        self._aks_group = QGroupBox(self.tr("Azure AKS"))
        aks_form = QFormLayout(self._aks_group)
        self._aks_subscription = QLineEdit()
        self._aks_subscription.setPlaceholderText("xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
        aks_form.addRow(self.tr("Subscription ID:"), self._aks_subscription)
        self._aks_resource_group = QLineEdit()
        self._aks_resource_group.setPlaceholderText("my-resource-group")
        aks_form.addRow(self.tr("Resource Group:"), self._aks_resource_group)
        layout.addWidget(self._aks_group)

        # Actions
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self._btn_detect = QPushButton(self.tr("🔍 Detect Available Providers"))
        self._btn_detect.setObjectName("btnPrimary")
        btn_row.addWidget(self._btn_detect)

        self._btn_save = QPushButton(self.tr("💾 Save"))
        self._btn_save.setObjectName("btnPrimary")
        btn_row.addWidget(self._btn_save)

        layout.addLayout(btn_row)

        # Status
        self._status = QLabel("")
        self._status.setObjectName("resourceStatus")
        layout.addWidget(self._status)

        layout.addStretch()

    def _setup_accessibility(self) -> None:
        self._eks_region.setAccessibleName(self.tr("AWS EKS region"))
        self._eks_profile.setAccessibleName(self.tr("AWS CLI profile name"))
        self._gke_project.setAccessibleName(self.tr("GCP project ID"))
        self._gke_region.setAccessibleName(self.tr("GKE region"))
        self._aks_subscription.setAccessibleName(self.tr("Azure subscription ID"))
        self._aks_resource_group.setAccessibleName(self.tr("Azure resource group"))
        self._btn_detect.setAccessibleName(self.tr("Detect available cloud providers"))
        self._btn_save.setAccessibleName(self.tr("Save cloud settings"))

    def _setup_tab_order(self) -> None:
        QWidget.setTabOrder(self._eks_region, self._eks_profile)
        QWidget.setTabOrder(self._eks_profile, self._gke_project)
        QWidget.setTabOrder(self._gke_project, self._gke_region)
        QWidget.setTabOrder(self._gke_region, self._aks_subscription)
        QWidget.setTabOrder(self._aks_subscription, self._aks_resource_group)
        QWidget.setTabOrder(self._aks_resource_group, self._btn_detect)
        QWidget.setTabOrder(self._btn_detect, self._btn_save)

    # ── Public API ───────────────────────────────────────────────────────────

    def set_status(self, text: str) -> None:
        """Update the status label."""
        self._status.setText(text)

    def get_eks_config(self) -> dict[str, str]:
        """Return AWS EKS configuration."""
        return {
            "region": self._eks_region.text().strip(),
            "profile": self._eks_profile.text().strip(),
        }

    def get_gke_config(self) -> dict[str, str]:
        """Return GCP GKE configuration."""
        return {
            "project": self._gke_project.text().strip(),
            "region": self._gke_region.text().strip(),
        }

    def get_aks_config(self) -> dict[str, str]:
        """Return Azure AKS configuration."""
        return {
            "subscription_id": self._aks_subscription.text().strip(),
            "resource_group": self._aks_resource_group.text().strip(),
        }

