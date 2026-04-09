# ☸ Kuber

A **PyQt5 desktop application** for managing Kubernetes clusters. Kuber provides a
unified interface to deploy, monitor, and manage applications across multiple
Kubernetes clusters and cloud providers (AWS EKS, GCP GKE, Azure AKS, OpenShift).

![Python 3.13+](https://img.shields.io/badge/Python-3.13%2B-blue)
![PyQt5 5.15+](https://img.shields.io/badge/PyQt5-5.15%2B-green)
![License MIT](https://img.shields.io/badge/License-MIT-yellow)
![Tests 261 passing](https://img.shields.io/badge/Tests-261%20passing-brightgreen)

---

## ✨ Features

| Feature | Description |
|---|---|
| **Cluster Management** | List, switch, and inspect Kubernetes contexts with live status polling |
| **Resource Browser** | View and manage Pods, Deployments, Services, and ConfigMaps with namespace filtering |
| **Application Deployment** | Wizard-driven deploy via Docker image, Helm chart, or raw YAML manifest |
| **Monitoring & Logging** | Real-time CPU/memory metrics, pod log viewer with ANSI color support, cluster events |
| **RBAC / User Management** | CRUD for ServiceAccounts, Roles, ClusterRoles, RoleBindings, and audit log |
| **Backup & Restore** | Export cluster resources to `.tar.gz` archives with selective restore and dry-run |
| **Custom Resources** | Browse and manage any CRD dynamically |
| **Multi-Cloud** | Provider support for AWS EKS, GCP GKE, Azure AKS, and OpenShift |
| **Themes** | Dark, Light, and High Contrast themes — switchable at runtime |
| **i18n** | English and Brazilian Portuguese translations |

---

## 📸 Architecture

Kuber follows **MVVM + Clean Architecture**:

```
┌─────────────────────────────────────────────┐
│              Views (UI)                      │  PyQt5 Widgets — no business logic
├─────────────────────────────────────────────┤
│           ViewModels (Glue)                  │  Qt signals/slots — async via QThread
├─────────────────────────────────────────────┤
│         Models (Qt Data Models)              │  QAbstractItemModel subclasses
├─────────────────────────────────────────────┤
│          Core (Business Logic)               │  Pure Python — zero PyQt5 imports
├─────────────────────────────────────────────┤
│       Services / Config / Utils              │  App-level services, settings, validators
└─────────────────────────────────────────────┘
```

> See [`docs/architecture.md`](docs/architecture.md) for the full Architecture Decision Record.

---

## 📋 Prerequisites

Before running Kuber, make sure you have the following installed on your system:

| Requirement | Minimum Version | Purpose |
|---|---|---|
| **Python** | 3.13+ | Runtime |
| **pip** | latest | Package management |
| **kubectl** | 1.27+ | Kubernetes CLI (must be on `PATH`) |
| **Docker** | 20.10+ | Container operations (daemon must be running) |
| **Git** | 2.39+ | Git operations |
| **Helm** *(optional)* | 3.x | Helm chart deployments |
| **kubeconfig** | — | A valid `~/.kube/config` file with at least one cluster context |

### Platform-Specific Notes

<details>
<summary><strong>🪟 Windows</strong></summary>

- Install Python 3.13+ from [python.org](https://www.python.org/downloads/) or via `winget`:
  ```powershell
  winget install Python.Python.3.13
  ```
- Docker Desktop: [Install Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
- Git: [Install Git for Windows](https://git-scm.com/download/win)
- kubectl: 
  ```powershell
  winget install Kubernetes.kubectl
  ```

</details>

<details>
<summary><strong>🍎 macOS</strong></summary>

```bash
brew install python@3.13 kubectl docker git helm
```

</details>

<details>
<summary><strong>🐧 Linux (Debian/Ubuntu)</strong></summary>

```bash
sudo apt update
sudo apt install python3.13 python3.13-venv python3-pip git docker.io
# Install kubectl: https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/
```

</details>

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/your-org/Kuber.git
cd Kuber
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it:

| OS | Command |
|---|---|
| **Windows (PowerShell)** | `.\.venv\Scripts\Activate.ps1` |
| **Windows (cmd)** | `.\.venv\Scripts\activate.bat` |
| **macOS / Linux** | `source .venv/bin/activate` |

### 3. Install dependencies

**Runtime only:**

```bash
pip install -r requirements.txt
```

**With development tools** (testing, linting, type checking):

```bash
pip install -r requirements-dev.txt
```

Or via `pyproject.toml`:

```bash
pip install -e ".[dev]"
```

### 4. Verify your environment

Make sure Docker is running and you have a valid kubeconfig:

```bash
kubectl cluster-info
docker info
```

### 5. Run the application

```bash
python main.py
```

Kuber will show a splash screen that validates your environment (kubeconfig, Docker,
Git, internet connectivity) before launching the main window.

---

## 🧪 Running Tests

Kuber uses **pytest** with **pytest-qt** for widget tests and **pytest-mock** for mocking.

```bash
# Run the full test suite
python -m pytest

# Run with verbose output
python -m pytest -xvs

# Run a specific test file
python -m pytest tests/unit/views/test_monitoring_views.py

# Run with coverage report
python -m pytest --cov=kuber --cov-report=term-missing
```

---

## 🔍 Linting & Type Checking

```bash
# Lint with ruff
ruff check kuber/

# Auto-fix lint issues
ruff check kuber/ --fix

# Format with black
black kuber/

# Type check with mypy
mypy kuber/
```

---

## 📦 Building a Standalone Executable

Kuber can be packaged into a single executable using [PyInstaller](https://pyinstaller.org/):

```bash
pip install pyinstaller
pyinstaller main.spec
```

The output binary will be placed in the `dist/` directory.

---

## 🎨 Themes

Kuber ships with three themes. Switch at any time via the **🌗 Theme** button in the toolbar
or under **Settings**.

| Theme | Description |
|---|---|
| **Dark** *(default)* | Dark navy backgrounds with cyan accents |
| **Light** | White/grey backgrounds with blue accents |
| **High Contrast** | WCAG 2.1 AA compliant, yellow-on-black |

Theme files are located at `kuber/resources/themes/*.qss`.

---

## 🌐 Internationalization

Kuber supports multiple languages. The current languages are:

- 🇺🇸 **English** (default)
- 🇧🇷 **Brazilian Portuguese**

Change the language under **Settings → Language**. To add a new translation, see the
[Qt Linguist workflow](https://doc.qt.io/qt-5/qtlinguist-index.html).

---

## 📁 Project Structure

```
Kuber/
├── main.py                          # Application entry point
├── pyproject.toml                   # Project metadata & tool config
├── requirements.txt                 # Runtime dependencies
├── requirements-dev.txt             # Development dependencies
├── kuber/
│   ├── app.py                       # QApplication bootstrap
│   ├── constants.py                 # Global constants
│   ├── config/                      # Settings & kubeconfig loader
│   ├── core/                        # Business logic (no PyQt5)
│   │   ├── kubernetes/              # k8s API operations
│   │   ├── docker/                  # Docker SDK wrapper
│   │   ├── helm/                    # Helm chart operations
│   │   ├── git/                     # Git operations
│   │   ├── openshift/               # OpenShift support
│   │   ├── cloud/                   # Multi-cloud provider factory
│   │   └── exceptions.py            # Custom exception hierarchy
│   ├── models/                      # Qt data models
│   ├── viewmodels/                  # MVVM ViewModels
│   ├── views/                       # PyQt5 UI widgets
│   │   ├── common/                  # Reusable widgets & BaseWorker
│   │   ├── cluster/                 # Cluster management views
│   │   ├── resources/               # Resource browser views
│   │   ├── deployment/              # Deploy wizard
│   │   ├── monitoring/              # Metrics, logs, events
│   │   ├── users/                   # RBAC management
│   │   ├── backup/                  # Backup & restore
│   │   └── settings/                # App settings
│   ├── services/                    # Application-level services
│   ├── utils/                       # Logging, validators, network
│   ├── i18n/                        # Translation files (.ts/.qm)
│   └── resources/                   # Icons & QSS themes
├── tests/
│   ├── unit/                        # Unit tests (mirrors kuber/)
│   └── integration/                 # Integration tests
└── docs/
    └── architecture.md              # Architecture Decision Record
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Follow the coding standards in [`.github/copilot-instructions.md`](.github/copilot-instructions.md)
4. Write tests for your changes (target ≥ 80% coverage)
5. Run linting and tests before pushing:
   ```bash
   ruff check kuber/
   mypy kuber/
   python -m pytest
   ```
6. Open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License**. See [`pyproject.toml`](pyproject.toml) for details.

