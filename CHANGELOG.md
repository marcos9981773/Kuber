# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.0.0] — 2026-04-06

### Added

#### Core Infrastructure (Phases 0–1)
- Project scaffolding with MVVM + Clean Architecture structure
- CI pipeline with ruff, mypy, and pytest
- GitHub Copilot custom instructions and prompt files
- Structured JSON logging with file rotation (`kuber/utils/logger.py`)
- Network connectivity checker (`kuber/utils/network.py`)
- Kubeconfig loader with context listing and RBAC validation
- Kubernetes API client wrapper with retry + exponential backoff
- Full CRUD for Pods, Deployments, Services, ConfigMaps
- Docker client: version check, daemon status, image pull
- Helm client: install, list, remove charts
- Git client: config validation, repo access check
- App requirement validators (Docker, Git, k8s, Helm, connectivity)

#### Application Shell (Phase 2)
- Main window with sidebar navigation and `QStackedWidget`
- Three QSS themes: dark, light, high contrast
- Theme manager with dynamic switching
- Error dialog with expandable details
- Loading overlay for async operations
- Splash screen with startup validation feedback
- `BaseWorker` QThread abstraction for async tasks
- i18n support with English and Portuguese (Brazil) translations

#### Cluster Management (Phase 3)
- Cluster list view with status, context, and actions
- Cluster detail view (nodes, version, reachability)
- Cluster context switcher in toolbar
- Async status polling via QTimer

#### Resource Management (Phase 4)
- Generic `ResourceTableModel` and `ResourceFilterProxy`
- Pods view with namespace filter and status
- Deployments view with scale and rolling update actions
- Services view with type, ClusterIP, and ports
- ConfigMaps view with YAML editor dialog
- YAML editor widget with syntax highlighting (`QSyntaxHighlighter`)
- Resource detail panel (properties + YAML tabs)
- Reusable namespace selector and search bar

#### Application Deployment (Phase 5)
- Deploy wizard with Docker image, Helm chart, and manifest modes
- Docker deploy page (image, tag, namespace, replicas)
- Helm deploy page (chart, release, YAML values editor)
- Manifest deploy page (upload or inline YAML editor)
- Review page with dry-run option
- Deploy progress dialog with real-time log output

#### Monitoring & Logging (Phase 6)
- Monitoring service with metrics caching and summary
- Pod metrics and node metrics via metrics-server API
- Pod log fetching with tail lines support
- Cluster events listing with filtering
- Metrics view with CPU/memory summary
- Logs view with pod input, auto-scroll, and search
- Events view with type filter (Warning/Normal) and loading overlay
- Monitoring ViewModel with polling support

#### User Management — RBAC (Phase 7)
- CRUD for ServiceAccounts, Roles, ClusterRoles, RoleBindings
- Users view with create/delete actions and namespace filter
- Role editor dialog with policy rule builder
- Audit log view for RBAC-related cluster events

#### Backup & Restore (Phase 8)
- Backup service: export resources to compressed `.tar.gz` archives
- Selective restore by namespace and resource type with dry-run
- Backup listing with create, restore, and delete actions
- Restore wizard with namespace/type selection and dry-run option
- Backup deletion

#### Advanced Features (Phase 9)
- Custom Resource Definition (CRD) listing and CRUD operations
- Dynamic custom resource view with CRD selector
- OpenShift cluster detection and Route operations
- Cloud provider factory for AWS EKS, GCP GKE, Azure AKS
- Cloud settings view for provider credentials

#### Quality & Packaging (Phase 10)
- Settings view (theme, language, backup schedule)
- 200+ unit tests with pytest, pytest-qt, pytest-mock
- Comprehensive test coverage across all layers

