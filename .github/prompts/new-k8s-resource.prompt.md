---
mode: agent
description: Scaffold a new Kubernetes resource module (pods, services, deployments, etc.) with full MVVM stack
---

Create a complete MVVM stack for the Kubernetes resource: **${input:resourceName}**
(e.g., "Pod", "Service", "Deployment", "ConfigMap", "StatefulSet")

## Files to create

### 1. Core module — `kuber/core/kubernetes/${input:resourceName:lower}s.py`
- Pure Python, NO PyQt5 imports
- Use `kubernetes` client (`CoreV1Api` or `AppsV1Api` as appropriate)
- Implement: `list_all(namespace)`, `get(name, namespace)`, `create(manifest)`, `update(name, namespace, manifest)`, `delete(name, namespace)`
- Handle `ApiException` and raise custom exceptions from `kuber/core/exceptions.py`
- Add timeout=30 to all API calls
- Add docstrings and type hints on all public methods

### 2. Qt Model — `kuber/models/${input:resourceName:lower}_model.py`
- Subclass `QAbstractTableModel`
- Implement `rowCount`, `columnCount`, `data`, `headerData`
- Include relevant columns for the resource type
- Support `Qt.UserRole` to return the raw resource object

### 3. ViewModel — `kuber/viewmodels/${input:resourceName:lower}_vm.py`
- Subclass `QObject`
- Declare signals: `resources_loaded = pyqtSignal(list)`, `error_occurred = pyqtSignal(str)`, `loading_changed = pyqtSignal(bool)`
- Use `BaseWorker` for async loading
- Methods: `load(namespace)`, `delete(name, namespace)`, `refresh()`

### 4. View — `kuber/views/resources/${input:resourceName:lower}s_view.py`
- Subclass `QWidget`
- Include: namespace selector, search/filter bar, `QTableView` bound to the Qt Model, detail panel
- All strings wrapped in `self.tr()`
- Set `setAccessibleName()` on all interactive widgets
- Connect to ViewModel signals

### 5. Tests — `tests/unit/core/kubernetes/test_${input:resourceName:lower}s.py`
- Use `pytest` + `pytest-mock`
- Mock `kubernetes` API client
- Test: list, get, create, update, delete, ApiException handling (403, 404, 500)

## Rules
- Follow `.github/copilot-instructions.md` strictly
- No hardcoded colors — use theme system
- No blocking calls on main thread

