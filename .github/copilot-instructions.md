# Kuber — GitHub Copilot Instructions

## Project Overview

**Kuber** is a PyQt5 desktop application for managing Kubernetes clusters. It provides a unified
interface to deploy, monitor and manage applications across multiple Kubernetes clusters and cloud
providers (AWS EKS, GCP GKE, Azure AKS, OpenShift).

- **Python:** 3.13+
- **UI Framework:** PyQt5 5.15+
- **Architecture:** MVVM (Model-View-ViewModel)
- **Target OS:** Windows, macOS, Linux

---

## Architecture: MVVM + Clean Architecture

```
┌─────────────────────────────────────────────┐
│                  Views (UI)                  │  PyQt5 Widgets only. No business logic.
│     kuber/views/**                           │  Use self.tr() for ALL user-facing strings.
├─────────────────────────────────────────────┤
│              ViewModels (Glue)               │  Qt signals/slots. Bridges Core ↔ Views.
│     kuber/viewmodels/**                      │  Runs async ops via QThread workers.
├─────────────────────────────────────────────┤
│          Models (Qt Data Models)             │  QAbstractItemModel subclasses only.
│     kuber/models/**                          │  Feed data from Core to Views.
├─────────────────────────────────────────────┤
│            Core (Business Logic)             │  Pure Python. ZERO PyQt5 imports.
│     kuber/core/**                            │  All k8s/docker/git/helm operations here.
├─────────────────────────────────────────────┤
│        Services / Config / Utils             │  App-level services, settings, validators.
│     kuber/services|config|utils/**           │  No UI dependencies.
└─────────────────────────────────────────────┘
```

### The Golden Rule
> **`kuber/core/`**, **`kuber/services/`**, and **`kuber/utils/`** must NEVER import PyQt5.
> If you need to communicate results to the UI, do it via a ViewModel signal.

---

## Tech Stack & Libraries

| Library | Version | Purpose |
|---|---|---|
| `PyQt5` | ≥5.15.11 | UI framework |
| `kubernetes` | ≥29.0 | Official k8s Python client |
| `docker` | ≥7.1 | Docker SDK for Python |
| `GitPython` | ≥3.1 | Git operations |
| `PyYAML` | ≥6.0 | YAML parsing for manifests |
| `pyqtgraph` | ≥0.13 | Real-time charts (metrics) |
| `requests` | ≥2.32 | HTTP connectivity checks |

---

## Coding Standards

### Python
- Use **type hints** on ALL public functions, methods, and class attributes
- Follow **PEP 8** with max line length of **100 characters**
- Use **f-strings** for string formatting
- Use **dataclasses** or **Pydantic** models for data transfer objects
- Use **`pathlib.Path`** instead of `os.path` for file system operations
- Prefer **`contextlib.suppress`** over bare `except: pass`

### PyQt5 / Views
- All Views must inherit from `QWidget` or `QMainWindow`
- **All user-facing strings MUST use `self.tr("string")`** for i18n support
- Set `setAccessibleName()` and `setAccessibleDescription()` on every interactive widget
- Define tab order explicitly using `QWidget.setTabOrder()`
- Themes are applied via QSS files in `kuber/resources/themes/` — never hardcode colors
- Connect signals to slots only in the ViewModel constructor or `_connect_signals()` method
- Long operations MUST run in a `QThread` worker — never block the main thread

### ViewModels
- Suffix: `*ViewModel` (e.g., `ClusterViewModel`)
- Inherit from `QObject` to support signals
- Declare all signals as class-level attributes: `my_signal = pyqtSignal(list)`
- Have a `_connect_signals()` private method for internal wiring
- Use `BaseWorker` from `kuber/views/common/base_worker.py` for async operations

### Core / Services
- NO PyQt5 imports — these modules must be testable without a Qt application
- Raise custom exceptions from `kuber/core/exceptions.py` instead of raw exceptions
- Handle `kubernetes.client.exceptions.ApiException` explicitly with status codes
- All external API calls must have **timeout** parameters
- Use **retry logic** (max 3 attempts with exponential backoff) for transient failures

### Tests
- Mirror the source structure: `tests/unit/core/kubernetes/` mirrors `kuber/core/kubernetes/`
- Use `pytest-mock` (`mocker` fixture) to mock all external API calls
- Use `pytest-qt` (`qtbot` fixture) for all PyQt5 widget tests
- Minimum coverage target: **80%**
- Test naming: `test_<unit>_<scenario>_<expected_result>`

---

## File & Directory Naming Conventions

| Layer | Location | Suffix/Pattern |
|---|---|---|
| Views | `kuber/views/**/` | `*_view.py`, `*_dialog.py`, `*_wizard.py` |
| ViewModels | `kuber/viewmodels/` | `*_vm.py` |
| Qt Models | `kuber/models/` | `*_model.py` |
| Core modules | `kuber/core/**/` | descriptive nouns (`client.py`, `clusters.py`) |
| Services | `kuber/services/` | `*_service.py` |
| Workers | inline or `kuber/views/common/` | `*_worker.py` |
| Tests | `tests/unit/` or `tests/integration/` | `test_*.py` |

---

## Error Handling & UX

- NEVER show raw Python exceptions to users
- Use `kuber/views/common/error_dialog.py` for all error presentations
- Error messages must be: **clear, actionable, and in the user's language**
- Format: `"[What happened]. [Why it happened]. [What to do next]."`
- Example: `"Could not connect to cluster 'prod-us'. The API server is unreachable. Check your VPN connection and try again."`

---

## Kubernetes Specifics

```python
# Always load config this way:
from kubernetes import config as k8s_config
k8s_config.load_kube_config()  # loads from ~/.kube/config

# List available contexts:
contexts, active_context = k8s_config.list_kube_config_contexts()

# Always handle ApiException:
from kubernetes.client.exceptions import ApiException
try:
    result = api.some_operation()
except ApiException as e:
    if e.status == 403:
        raise KuberPermissionError(f"Insufficient permissions: {e.reason}")
    elif e.status == 404:
        raise KuberNotFoundError(f"Resource not found: {e.reason}")
    else:
        raise KuberApiError(f"API error {e.status}: {e.reason}")
```

---

## Theme System

```python
# Loading a theme (never hardcode colors):
from kuber.views.common.theme_manager import ThemeManager
ThemeManager.apply(app, theme="dark")  # "dark" | "light" | "high_contrast"

# QSS files location:
# kuber/resources/themes/dark.qss
# kuber/resources/themes/light.qss
# kuber/resources/themes/high_contrast.qss
```

---

## Async Pattern (QThread Worker)

```python
# Always use BaseWorker for async operations — never use raw QThread
from kuber.views.common.base_worker import BaseWorker

class LoadClustersWorker(BaseWorker):
    def run_task(self) -> list:
        return clusters_core.list_all()  # pure Python, no PyQt5

# In ViewModel:
self._worker = LoadClustersWorker()
self._worker.finished.connect(self._on_clusters_loaded)
self._worker.error.connect(self._on_error)
self._worker.start()
```

---

## i18n Pattern

```python
# In any QWidget subclass — always wrap user strings:
self.btn_connect = QPushButton(self.tr("Connect"))
self.lbl_status = QLabel(self.tr("Status: {0}").format(status))

# Plural forms:
msg = self.tr("%n cluster(s) found", "", count)
```

