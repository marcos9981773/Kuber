"""
kuber/views/users/role_editor_dialog.py
Dialog for creating or editing a Kubernetes Role with policy rules.
"""
from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from kuber.core.kubernetes.rbac import PolicyRule

_COMMON_VERBS = ["get", "list", "watch", "create", "update", "patch", "delete"]
_COMMON_RESOURCES = [
    "pods", "services", "deployments", "configmaps", "secrets",
    "serviceaccounts", "roles", "rolebindings",
]


class RoleEditorDialog(QDialog):
    """Dialog for creating a Role with multiple policy rules."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Create Role"))
        self.setMinimumWidth(600)
        self._rules: list[PolicyRule] = []
        self._setup_ui()
        self._setup_accessibility()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Name field
        form = QFormLayout()
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText(self.tr("e.g. pod-reader"))
        form.addRow(self.tr("Role Name:"), self._name_edit)
        layout.addLayout(form)

        # Rule builder
        rule_group = QGroupBox(self.tr("Add Rule"))
        rule_layout = QVBoxLayout(rule_group)

        # API Groups
        api_row = QFormLayout()
        self._api_groups_edit = QLineEdit()
        self._api_groups_edit.setPlaceholderText(
            self.tr("Comma-separated, e.g.: '', apps, batch")
        )
        self._api_groups_edit.setText("")
        api_row.addRow(self.tr("API Groups:"), self._api_groups_edit)
        rule_layout.addLayout(api_row)

        # Resources — checkboxes
        res_label = QLabel(self.tr("Resources:"))
        rule_layout.addWidget(res_label)
        res_row = QHBoxLayout()
        self._resource_checks: dict[str, QCheckBox] = {}
        for res in _COMMON_RESOURCES:
            cb = QCheckBox(res)
            self._resource_checks[res] = cb
            res_row.addWidget(cb)
        rule_layout.addLayout(res_row)

        # Verbs — checkboxes
        verb_label = QLabel(self.tr("Verbs:"))
        rule_layout.addWidget(verb_label)
        verb_row = QHBoxLayout()
        self._verb_checks: dict[str, QCheckBox] = {}
        for verb in _COMMON_VERBS:
            cb = QCheckBox(verb)
            self._verb_checks[verb] = cb
            verb_row.addWidget(cb)
        rule_layout.addLayout(verb_row)

        btn_add_rule = QPushButton(self.tr("+ Add Rule"))
        btn_add_rule.setObjectName("btnPrimary")
        btn_add_rule.clicked.connect(self._add_rule)
        rule_layout.addWidget(btn_add_rule)

        layout.addWidget(rule_group)

        # Rules table
        self._rules_table = QTableWidget(0, 3)
        self._rules_table.setHorizontalHeaderLabels([
            self.tr("API Groups"), self.tr("Resources"), self.tr("Verbs"),
        ])
        self._rules_table.horizontalHeader().setStretchLastSection(True)
        self._rules_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch,
        )
        self._rules_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self._rules_table, stretch=1)

        # Dialog buttons
        self._buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
        )
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)
        layout.addWidget(self._buttons)

    def _setup_accessibility(self) -> None:
        self._name_edit.setAccessibleName(self.tr("Role name"))
        self._name_edit.setAccessibleDescription(
            self.tr("Enter the name for the new Kubernetes Role"),
        )
        self._rules_table.setAccessibleName(self.tr("Policy rules table"))
        self._api_groups_edit.setAccessibleName(self.tr("API groups"))

    # ── Actions ──────────────────────────────────────────────────────────────

    def _add_rule(self) -> None:
        resources = [
            r for r, cb in self._resource_checks.items() if cb.isChecked()
        ]
        verbs = [v for v, cb in self._verb_checks.items() if cb.isChecked()]
        if not resources or not verbs:
            return

        raw_groups = self._api_groups_edit.text().strip()
        api_groups = [g.strip() for g in raw_groups.split(",")]

        rule = PolicyRule(api_groups=api_groups, resources=resources, verbs=verbs)
        self._rules.append(rule)

        row = self._rules_table.rowCount()
        self._rules_table.insertRow(row)
        self._rules_table.setItem(row, 0, QTableWidgetItem(", ".join(api_groups)))
        self._rules_table.setItem(row, 1, QTableWidgetItem(", ".join(resources)))
        self._rules_table.setItem(row, 2, QTableWidgetItem(", ".join(verbs)))

        # Reset checkboxes
        for cb in self._resource_checks.values():
            cb.setChecked(False)
        for cb in self._verb_checks.values():
            cb.setChecked(False)

    # ── Public API ───────────────────────────────────────────────────────────

    def get_role_name(self) -> str:
        """Return the role name entered by the user."""
        return self._name_edit.text().strip()

    def get_rules(self) -> list[PolicyRule]:
        """Return the list of policy rules configured."""
        return list(self._rules)

