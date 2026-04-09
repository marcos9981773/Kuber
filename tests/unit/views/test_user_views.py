"""
tests/unit/views/test_user_views.py
Tests for kuber/views/users/ (UsersView, RoleEditorDialog, AuditLogView).
"""
from __future__ import annotations

import pytest
from PyQt5.QtCore import QObject, pyqtSignal

from kuber.core.kubernetes.events import EventInfo
from kuber.core.kubernetes.rbac import ServiceAccountInfo


@pytest.fixture
def mock_user_vm():
    """Fake UserViewModel with all required signals."""

    class _FakeVM(QObject):
        items_loaded = pyqtSignal(list)
        item_deleted = pyqtSignal(str)
        action_completed = pyqtSignal(str)
        loading_changed = pyqtSignal(bool)
        error_occurred = pyqtSignal(str)
        namespaces_loaded = pyqtSignal(list)
        roles_loaded = pyqtSignal(list)
        bindings_loaded = pyqtSignal(list)
        audit_events_loaded = pyqtSignal(list)

        _namespace = "default"

        def load_items(self) -> None: pass
        def load_namespaces(self) -> None: pass
        def delete_item(self, name, ns=None) -> None: pass
        def set_namespace(self, ns) -> None: self._namespace = ns
        def create_sa(self, name) -> None: pass
        def load_roles(self) -> None: pass
        def load_bindings(self) -> None: pass
        def load_audit_events(self) -> None: pass

    return _FakeVM()


class TestUsersView:
    def test_users_view_creates(self, qtbot, mock_user_vm) -> None:
        from kuber.views.users.users_view import UsersView
        view = UsersView(view_model=mock_user_vm)
        qtbot.addWidget(view)
        assert view._table is not None

    def test_users_view_items_loaded_populates_model(self, qtbot, mock_user_vm) -> None:
        from kuber.views.users.users_view import UsersView
        view = UsersView(view_model=mock_user_vm)
        qtbot.addWidget(view)

        sas = [
            ServiceAccountInfo("default", "default", 1, "5d"),
            ServiceAccountInfo("deployer", "default", 0, "1d"),
        ]
        mock_user_vm.items_loaded.emit(sas)
        assert view._model.rowCount() == 2

    def test_users_view_has_create_button(self, qtbot, mock_user_vm) -> None:
        from kuber.views.users.users_view import UsersView
        view = UsersView(view_model=mock_user_vm)
        qtbot.addWidget(view)
        assert hasattr(view, "_btn_create")
        assert view._btn_create.accessibleName() != ""

    def test_users_view_has_delete_button(self, qtbot, mock_user_vm) -> None:
        from kuber.views.users.users_view import UsersView
        view = UsersView(view_model=mock_user_vm)
        qtbot.addWidget(view)
        assert not view._btn_delete.isEnabled()


class TestRoleEditorDialog:
    def test_dialog_creates(self, qtbot) -> None:
        from kuber.views.users.role_editor_dialog import RoleEditorDialog
        dialog = RoleEditorDialog()
        qtbot.addWidget(dialog)
        assert dialog._name_edit is not None
        assert dialog._rules_table is not None

    def test_get_role_name_returns_text(self, qtbot) -> None:
        from kuber.views.users.role_editor_dialog import RoleEditorDialog
        dialog = RoleEditorDialog()
        qtbot.addWidget(dialog)
        dialog._name_edit.setText("pod-reader")
        assert dialog.get_role_name() == "pod-reader"

    def test_get_rules_initially_empty(self, qtbot) -> None:
        from kuber.views.users.role_editor_dialog import RoleEditorDialog
        dialog = RoleEditorDialog()
        qtbot.addWidget(dialog)
        assert dialog.get_rules() == []

    def test_add_rule_populates_table(self, qtbot) -> None:
        from kuber.views.users.role_editor_dialog import RoleEditorDialog
        dialog = RoleEditorDialog()
        qtbot.addWidget(dialog)
        dialog._resource_checks["pods"].setChecked(True)
        dialog._verb_checks["get"].setChecked(True)
        dialog._verb_checks["list"].setChecked(True)
        dialog._add_rule()
        assert dialog._rules_table.rowCount() == 1
        assert len(dialog.get_rules()) == 1
        assert "pods" in dialog.get_rules()[0].resources

    def test_add_rule_resets_checkboxes(self, qtbot) -> None:
        from kuber.views.users.role_editor_dialog import RoleEditorDialog
        dialog = RoleEditorDialog()
        qtbot.addWidget(dialog)
        dialog._resource_checks["pods"].setChecked(True)
        dialog._verb_checks["get"].setChecked(True)
        dialog._add_rule()
        assert not dialog._resource_checks["pods"].isChecked()
        assert not dialog._verb_checks["get"].isChecked()

    def test_add_rule_ignored_when_no_selection(self, qtbot) -> None:
        from kuber.views.users.role_editor_dialog import RoleEditorDialog
        dialog = RoleEditorDialog()
        qtbot.addWidget(dialog)
        dialog._add_rule()
        assert dialog._rules_table.rowCount() == 0


class TestAuditLogView:
    def test_audit_view_creates(self, qtbot, mock_user_vm) -> None:
        from kuber.views.users.audit_log_view import AuditLogView
        view = AuditLogView(view_model=mock_user_vm)
        qtbot.addWidget(view)
        assert view._table is not None

    def test_audit_events_loaded_populates_model(self, qtbot, mock_user_vm) -> None:
        from kuber.views.users.audit_log_view import AuditLogView
        view = AuditLogView(view_model=mock_user_vm)
        qtbot.addWidget(view)

        events = [
            EventInfo(
                namespace="default", name="ev-1", type="Warning",
                reason="Forbidden", message="User cannot list pods",
                source="apiserver", involved_object="Pod/test",
                count=1, age="5m",
            ),
        ]
        mock_user_vm.audit_events_loaded.emit(events)
        assert view._model.rowCount() == 1
        assert "1 event(s)" in view._status.text()

    def test_audit_view_accessible_names(self, qtbot, mock_user_vm) -> None:
        from kuber.views.users.audit_log_view import AuditLogView
        view = AuditLogView(view_model=mock_user_vm)
        qtbot.addWidget(view)
        assert view._table.accessibleName() != ""
        assert view._type_combo.accessibleName() != ""

