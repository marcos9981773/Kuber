# Kuber — Architecture Decision Record

## Overview

Kuber is a PyQt5 desktop application for managing Kubernetes clusters. This document describes
the architectural decisions, patterns, and conventions that govern the codebase.

---

## Architecture: MVVM + Clean Architecture

Kuber uses a layered architecture combining **MVVM (Model-View-ViewModel)** with principles from
**Clean Architecture**. This combination provides:

- **Testability:** Business logic in `core/` is 100% testable without a Qt application.
- **Separation of concerns:** UI logic, business logic, and data access are clearly separated.
- **Maintainability:** Each layer can evolve independently.
- **Scalability:** New features follow established patterns, reducing decision fatigue.

```
┌─────────────────────────────────────────────────────────────┐
│                         Views (UI)                           │
│  kuber/views/**                                              │
│  • PyQt5 Widgets only                                        │
│  • No business logic                                         │
│  • All strings use self.tr() for i18n                        │
│  • Themes via QSS files — no hardcoded colors                │
├─────────────────────────────────────────────────────────────┤
│                      ViewModels (Glue)                       │
│  kuber/viewmodels/**                                         │
│  • Inherits QObject to support Qt signals                    │
│  • Bridges Core ↔ Views via signals/slots                    │
│  • Runs async operations via BaseWorker (QThread)            │
│  • Only imports from PyQt5.QtCore (no QWidget)               │
├─────────────────────────────────────────────────────────────┤
│                    Models (Qt Data Models)                    │
│  kuber/models/**                                             │
│  • QAbstractItemModel subclasses                             │
│  • Feeds data from Core to Views via ViewModels              │
├─────────────────────────────────────────────────────────────┤
│                   Core (Business Logic)                      │
│  kuber/core/**                                               │
│  • Pure Python — ZERO PyQt5 imports                          │
│  • All k8s, Docker, Git, Helm operations                     │
│  • Raises custom exceptions (never raw ApiException)         │
├─────────────────────────────────────────────────────────────┤
│              Services / Config / Utils                        │
│  kuber/services|config|utils/**                              │
│  • App-level orchestration services                          │
│  • Settings management (QSettings)                           │
│  • Shared utilities (logging, network, validators)           │
│  • No UI dependencies                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Layer Responsibilities

### Views (`kuber/views/`)
- **What:** PyQt5 widget classes only
- **Responsibility:** Render data, capture user input, display feedback
- **Rules:**
  - Inherit from `QWidget` or `QMainWindow`
  - All user-facing strings use `self.tr()` for i18n
  - Never call core/service modules directly — always via ViewModel
  - Long operations via ViewModel + BaseWorker (never block main thread)
  - Themes via QSS classes — never hardcode colors or fonts

### ViewModels (`kuber/viewmodels/`)
- **What:** `QObject` subclasses with `pyqtSignal` declarations
- **Responsibility:** Bridge Core ↔ Views, manage UI state, run async tasks
- **Rules:**
  - Suffix: `*ViewModel` (e.g., `ClusterViewModel`)
  - Signals declared as class-level attributes
  - `_connect_signals()` private method for all signal wiring
  - Only import from `PyQt5.QtCore` — never from `PyQt5.QtWidgets`

### Models (`kuber/models/`)
- **What:** `QAbstractItemModel` / `QAbstractTableModel` subclasses
- **Responsibility:** Provide data to Qt views (QTableView, QListView, etc.)
- **Rules:**
  - Implement `rowCount`, `columnCount`, `data`, `headerData`
  - `Qt.UserRole` returns the underlying Python object

### Core (`kuber/core/`)
- **What:** Pure Python business logic, no framework dependencies
- **Responsibility:** All operations with Kubernetes, Docker, Helm, Git
- **Rules:**
  - **ZERO PyQt5 imports** — must be runnable without Qt
  - Raise only custom exceptions from `kuber/core/exceptions.py`
  - All API calls have explicit timeout parameters
  - Retry logic (max 3 attempts, exponential backoff) for transient failures

### Services (`kuber/services/`)
- **What:** Application-level orchestration, higher-level operations
- **Responsibility:** Coordinate multiple core modules for complex workflows
- **Rules:**
  - No PyQt5 imports
  - Return result DTOs (dataclasses), never raise to callers

---

## Async Pattern

All operations that may block (network, filesystem, API calls) must run in a `QThread` via
the `BaseWorker` base class:

```
kuber/views/common/base_worker.py

BaseWorker (QThread)
  ├── signals: started, finished(result), error(str), progress(int)
  └── abstract method: run_task() -> Any
```

**Usage in ViewModels:**
```python
class _LoadClustersWorker(BaseWorker):
    def run_task(self) -> list:
        return clusters_core.list_all()   # pure Python, no PyQt5

# In ViewModel.load():
self._worker = _LoadClustersWorker()
self._worker.finished.connect(self._on_clusters_loaded)
self._worker.error.connect(self._on_error)
self._worker.start()
```

---

## Error Handling Strategy

```
kubernetes ApiException
    └── core layer catches and raises:
            ├── KuberPermissionError (403)
            ├── KuberNotFoundError   (404)
            ├── KuberApiError        (other)
            └── KuberConnectionError (network)

ViewModel catches custom exceptions
    └── emits: error_occurred = pyqtSignal(str)  ← user-friendly message

View connects to error_occurred
    └── shows: ErrorDialog with [What happened. Why. What to do next.]
```

**Error message format:**
> `"[What happened]. [Why it happened]. [What to do next]."`

Example: `"Could not connect to cluster 'prod-us'. The API server is unreachable. Check your VPN connection and try again."`

---

## Theme System

Themes are implemented as QSS (Qt Style Sheet) files loaded at runtime.

```
kuber/resources/themes/
  ├── dark.qss
  ├── light.qss
  └── high_contrast.qss
```

**Rules:**
- Never hardcode colors, fonts, or spacing values in Python code
- Apply object names to widgets for QSS targeting: `btn.setObjectName("btnPrimary")`
- Theme switching is live (no restart required)
- Theme preference persisted via `QSettings`

---

## Internationalization (i18n)

All user-facing strings use Qt's tr() mechanism:

```python
# In any QWidget subclass:
self.btn = QPushButton(self.tr("Connect to Cluster"))
self.label = QLabel(self.tr("Status: {0}").format(status))
```

Translation files:
```
kuber/i18n/
  ├── kuber_en.ts      ← source language (English)
  └── kuber_pt_BR.ts   ← Brazilian Portuguese
```

Workflow:
1. `pylupdate5` extracts strings from source → `.ts` files
2. Qt Linguist used to translate `.ts` files
3. `lrelease` compiles `.ts` → `.qm` (binary, shipped with the app)

---

## Directory Structure

```
Kuber/
├── .github/
│   ├── copilot-instructions.md     ← Copilot context
│   ├── prompts/                    ← Reusable prompt files
│   └── workflows/
│       ├── ci.yml                  ← Lint + typecheck + tests
│       └── release.yml             ← Build installers
├── kuber/
│   ├── app.py                      ← QApplication setup
│   ├── constants.py                ← Global constants
│   ├── config/                     ← Settings + kube config loader
│   ├── core/                       ← Business logic (no UI)
│   │   ├── kubernetes/             ← k8s operations
│   │   ├── docker/                 ← Docker SDK wrapper
│   │   ├── helm/                   ← Helm chart operations
│   │   ├── git/                    ← Git operations
│   │   ├── openshift/              ← OpenShift support
│   │   ├── cloud/                  ← Multi-cloud provider factory
│   │   └── exceptions.py           ← Custom exception hierarchy
│   ├── models/                     ← Qt data models
│   ├── viewmodels/                 ← MVVM ViewModels
│   ├── views/                      ← PyQt5 widgets
│   │   ├── cluster/
│   │   ├── resources/
│   │   ├── deployment/
│   │   ├── monitoring/
│   │   ├── users/
│   │   ├── backup/
│   │   ├── settings/
│   │   └── common/                 ← Reusable widgets + BaseWorker
│   ├── services/                   ← Application services
│   ├── utils/                      ← Logging, validators, network
│   ├── i18n/                       ← Translation files
│   └── resources/                  ← Icons, themes, QRC
├── tests/
│   ├── unit/                       ← Mirrors kuber/ structure
│   └── integration/
├── docs/
│   ├── architecture.md             ← This file
│   ├── user-guide.md
│   └── developer-guide.md
├── main.py                         ← Entry point
├── pyproject.toml
├── requirements.txt
└── PLAN.md                         ← Development roadmap
```

---

## Key ADRs (Architecture Decision Records)

### ADR-001: PyQt5 over PyQt6 / PySide6
**Decision:** Use PyQt5 5.15.x  
**Rationale:** Wider ecosystem compatibility, stable bindings, mature documentation.
**Trade-off:** PyQt6 has a cleaner API but ecosystem is less mature as of 2026.

### ADR-002: MVVM over MVC
**Decision:** MVVM with Qt signals  
**Rationale:** Qt's signal/slot mechanism maps naturally to ViewModel data binding.
The ViewModel acts as an observable state container without needing a controller.

### ADR-003: QThread Worker over asyncio
**Decision:** `QThread`-based workers via `BaseWorker`  
**Rationale:** Asyncio requires a running event loop incompatible with Qt's event loop.
`QThread` integrates natively with Qt's signal/slot mechanism.

### ADR-004: Custom exceptions over raw ApiException
**Decision:** Catch `ApiException` in core layer, re-raise as domain exceptions  
**Rationale:** Core modules should not leak `kubernetes` SDK types into ViewModels.
Domain exceptions carry semantic meaning (Permission, NotFound, etc.).

