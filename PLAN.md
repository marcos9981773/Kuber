# Kuber — Plano Completo de Construção por Fases

Plano de desenvolvimento incremental da aplicação desktop **Kuber** em PyQt5, organizado em **10 fases** cobrindo desde a fundação do projeto até a entrega final. Cada fase é independente e entregável, seguindo princípios de Clean Architecture, MVVM, TDD e CI/CD.

> **Última verificação:** 2026-04-06 — 201 testes passando, cobertura global 66%.

---

## 🗂️ Fase 0 — Fundação do Projeto

> **Objetivo:** Preparar o ambiente, estrutura de diretórios, tooling e instruções do Copilot antes de qualquer linha de código funcional.

### Especificações
- Estrutura de diretórios seguindo MVVM + Clean Architecture
- Ferramentas de qualidade de código configuradas
- GitHub Copilot instruído sobre o projeto desde o início
- Pipeline de CI mínima funcional

### Tarefas

| # | Tarefa | Arquivo(s) | Status |
|---|---|---|---|
| 0.1 | Criar estrutura completa de diretórios (`kuber/core`, `kuber/views`, `kuber/viewmodels`, `kuber/models`, `kuber/services`, `kuber/config`, `kuber/utils`, `kuber/i18n`, `kuber/resources/themes`, `kuber/resources/icons`, `tests/unit`, `tests/integration`, `docs`) | Diretórios | ✅ |
| 0.2 | Atualizar `pyproject.toml` com todas as dependências (`PyQt5`, `kubernetes`, `docker`, `GitPython`, `helm`) e dev deps (`pytest`, `pytest-qt`, `pytest-mock`, `ruff`, `mypy`, `black`) | `pyproject.toml` | ✅ |
| 0.3 | Criar `requirements.txt` e `requirements-dev.txt` para compatibilidade | Arquivos raiz | ✅ |
| 0.4 | Configurar `ruff.toml` (linting), `mypy.ini` (type checking), `.editorconfig` e `.gitignore` | Arquivos raiz | ✅ |
| 0.5 | Criar `.github/copilot-instructions.md` com contexto do projeto, arquitetura MVVM, padrões de nomenclatura, convenções de testes e requisitos de UX | `.github/copilot-instructions.md` | ✅ |
| 0.6 | Criar prompt files em `.github/prompts/`: `new-k8s-resource.prompt.md`, `new-pyqt5-view.prompt.md`, `new-viewmodel.prompt.md`, `write-tests.prompt.md`, `new-service.prompt.md` | `.github/prompts/` | ✅ |
| 0.7 | Criar `.github/workflows/ci.yml` com jobs: lint (`ruff`), type check (`mypy`), testes (`pytest`) | `.github/workflows/ci.yml` | ✅ |
| 0.8 | Criar `kuber/constants.py` com constantes globais (versões mínimas, paths padrão, app metadata) | `kuber/constants.py` | ✅ |
| 0.9 | Criar `main.py` como entry point limpando o template gerado pelo PyCharm | `main.py` | ✅ |
| 0.10 | Criar `docs/architecture.md` documentando a decisão MVVM e estrutura de camadas | `docs/architecture.md` | ✅ |

---

## 🔧 Fase 1 — Infraestrutura Core (Sem UI)

> **Objetivo:** Implementar toda a lógica de negócio, clientes de integração e validações iniciais, totalmente desacoplada da UI.

### Especificações
- Nenhum import de PyQt5 na camada `core/` ou `services/`
- Toda comunicação com APIs externas isolada em clients dedicados
- Validators testáveis de forma isolada
- Logging estruturado desde o início

### Tarefas

| # | Tarefa | Arquivo(s) | Status |
|---|---|---|---|
| 1.1 | Implementar `kuber/utils/logger.py` com logging estruturado (JSON), níveis configuráveis e rotação de arquivo | `kuber/utils/logger.py` | ✅ |
| 1.2 | Implementar `kuber/utils/network.py` com verificação de conectividade (ping DNS + HTTP) | `kuber/utils/network.py` | ✅ |
| 1.3 | Implementar `kuber/config/kube_config.py`: carrega `~/.kube/config`, lista contextos disponíveis, valida permissões RBAC mínimas | `kuber/config/kube_config.py` | ✅ |
| 1.4 | Implementar `kuber/config/settings.py` usando `QSettings` para persistir preferências (tema, idioma, último cluster) | `kuber/config/settings.py` | ✅ |
| 1.5 | Implementar `kuber/core/kubernetes/client.py`: wrapper do `kubernetes-client` com tratamento de `ApiException`, retry e timeout | `kuber/core/kubernetes/client.py` | ✅ |
| 1.6 | Implementar `kuber/core/kubernetes/clusters.py`: listar clusters, obter status, trocar contexto, operações de scale/upgrade | `kuber/core/kubernetes/clusters.py` | ✅ |
| 1.7 | Implementar `kuber/core/kubernetes/pods.py`, `deployments.py`, `services.py`, `configmaps.py`: CRUD completo de recursos | `kuber/core/kubernetes/` | ✅ |
| 1.8 | Implementar `kuber/core/docker/client.py`: verificar versão, status do daemon, pull de imagens | `kuber/core/docker/client.py` | ✅ |
| 1.9 | Implementar `kuber/core/helm/client.py`: instalar/listar/remover Helm charts via subprocess ou `pyhelm` | `kuber/core/helm/client.py` | ✅ |
| 1.10 | Implementar `kuber/core/git/client.py`: validar config Git, verificar acesso a repositórios | `kuber/core/git/client.py` | ✅ |
| 1.11 | Implementar `kuber/utils/validators.py`: validações de versão Docker, Git, k8s, conectividade (os 5 APP Requirements) | `kuber/utils/validators.py` | ✅ |
| 1.12 | Escrever testes unitários para todos os módulos `core/` com mocks das APIs externas (`tests/unit/core/`) | `tests/unit/core/` | ⚠️ |

> **Nota 1.12:** Testes existem para `kubernetes/client`, `kubernetes/clusters`, `kubernetes/custom_resources`, `kubernetes/metrics`, `kubernetes/rbac` e `cloud/provider_factory`. **Faltam** testes para: `docker/client`, `git/client`, `helm/client`, `kubernetes/pods`, `kubernetes/deployments`, `kubernetes/services`, `kubernetes/configmaps`, `kubernetes/events`, `kubernetes/logs`.

---

## 🎨 Fase 2 — Fundação da UI (Shell da Aplicação)

> **Objetivo:** Criar o esqueleto da aplicação PyQt5: janela principal, sistema de temas, navegação lateral, i18n e acessibilidade base.

### Especificações
- Arquitetura de temas via QSS (`dark`, `light`, `high_contrast`)
- Estrutura de navegação lateral (sidebar) com painéis trocáveis via `QStackedWidget`
- Sistema i18n com Qt Linguist (`.ts` → `.qm`)
- Suporte a keyboard navigation com tab order definido em todos os widgets

### Tarefas

| # | Tarefa | Arquivo(s) | Status |
|---|---|---|---|
| 2.1 | Implementar `kuber/app.py`: inicialização do `QApplication`, carregamento de tema e idioma, tratamento de exceções não capturadas | `kuber/app.py` | ✅ |
| 2.2 | Criar `kuber/views/main_window.py`: `QMainWindow` com sidebar de navegação, `QStackedWidget` central, status bar e toolbar | `kuber/views/main_window.py` | ✅ |
| 2.3 | Criar `kuber/resources/themes/dark.qss`, `light.qss`, `high_contrast.qss` com paleta de cores completa para todos os widgets Qt | `kuber/resources/themes/` | ✅ |
| 2.4 | Criar `kuber/resources/resources.qrc` e compilar com `pyrcc5` para embutir ícones e temas | `kuber/resources/resources.qrc` | 🔲 |
| 2.5 | Implementar `kuber/views/common/theme_manager.py`: aplica/troca QSS dinamicamente, persiste preferência via `settings.py` | `kuber/views/common/theme_manager.py` | ✅ |
| 2.6 | Criar arquivos de tradução base `kuber/i18n/kuber_en.ts` e `kuber/i18n/kuber_pt_BR.ts` com `pylupdate5` | `kuber/i18n/` | 🔲 |
| 2.7 | Implementar `kuber/views/common/error_dialog.py`: dialog de erro amigável com detalhes expansíveis e código de erro | `kuber/views/common/error_dialog.py` | ✅ |
| 2.8 | Implementar `kuber/views/common/loading_overlay.py`: overlay de loading não-bloqueante para operações assíncronas | `kuber/views/common/loading_overlay.py` | ✅ |
| 2.9 | Implementar `kuber/views/splash_screen.py`: splash de inicialização que executa os 5 validators (Fase 1.11) com feedback visual | `kuber/views/splash_screen.py` | ✅ |
| 2.10 | Criar `kuber/views/common/base_worker.py`: `QThread` base para operações assíncronas com signals `started`, `finished`, `error`, `progress` | `kuber/views/common/base_worker.py` | ✅ |
| 2.11 | Configurar tab order e shortcut keys na `main_window.py`; documentar mapa de atalhos | `kuber/views/main_window.py` | ✅ |
| 2.12 | Escrever testes `pytest-qt` para os widgets base e `theme_manager` | `tests/unit/views/` | ⚠️ |

> **Nota 2.4:** O arquivo `resources.qrc` não foi criado. O diretório `kuber/resources/icons/` está vazio.
> **Nota 2.6:** O diretório `kuber/i18n/` está vazio — nenhum arquivo `.ts` ou `.qm` foi gerado.
> **Nota 2.12:** Testes existem para `base_worker` e `yaml_editor`, mas **faltam** testes para `theme_manager`, `main_window`, `splash_screen`, `error_dialog` e `loading_overlay`.

---

## ☸️ Fase 3 — Gerenciamento de Clusters

> **Objetivo:** Implementar a feature principal: visualização e operações em múltiplos clusters Kubernetes.

### Especificações
- Listagem de clusters a partir do `~/.kube/config` com múltiplos contextos
- Status em tempo real via polling assíncrono com `QTimer`
- Operações de scale e upgrade com confirmação do usuário

### Tarefas

| # | Tarefa | Arquivo(s) | Status |
|---|---|---|---|
| 3.1 | Implementar `kuber/models/cluster_model.py`: `QAbstractTableModel` com dados de clusters | `kuber/models/cluster_model.py` | ✅ |
| 3.2 | Implementar `kuber/viewmodels/cluster_vm.py`: signals para `clusters_loaded`, `cluster_switched`, `error_occurred` + worker threads | `kuber/viewmodels/cluster_vm.py` | ✅ |
| 3.3 | Criar `kuber/views/cluster/cluster_list_view.py`: `QTableView` com status, contexto ativo e ações | `kuber/views/cluster/cluster_list_view.py` | ✅ |
| 3.4 | Criar `kuber/views/cluster/cluster_detail_view.py`: detalhes do cluster selecionado (nodes, versão, estado) | `kuber/views/cluster/cluster_detail_view.py` | ✅ |
| 3.5 | Criar `kuber/views/cluster/cluster_switcher.py`: dropdown/widget para trocar contexto ativo na toolbar | `kuber/views/cluster/cluster_switcher.py` | ✅ |
| 3.6 | Implementar polling assíncrono de status via `QTimer` no ViewModel sem bloquear a UI | `kuber/viewmodels/cluster_vm.py` | ✅ |
| 3.7 | Escrever testes unitários do ViewModel (mock do `core/kubernetes/clusters.py`) e testes `pytest-qt` da view | `tests/unit/viewmodels/`, `tests/unit/views/` | ✅ |

---

## 📦 Fase 4 — Gerenciamento de Recursos

> **Objetivo:** Interface visual completa para Pods, Services, Deployments e ConfigMaps com edição e operações inline.

### Especificações
- Cada tipo de recurso tem sua própria view com tabela, filtros e painel de detalhes
- Edição de configuração via editor YAML integrado
- Operações: scale, rolling update, delete, restart com confirmação

### Tarefas

| # | Tarefa | Arquivo(s) | Status |
|---|---|---|---|
| 4.1 | Implementar `kuber/models/resource_model.py`: `QAbstractItemModel` genérico para recursos k8s | `kuber/models/resource_model.py` | ✅ |
| 4.2 | Implementar `kuber/viewmodels/resource_vm.py`: base ViewModel genérico; subclasses para Pod, Service, Deployment, ConfigMap | `kuber/viewmodels/resource_vm.py` | ✅ |
| 4.3 | Criar `kuber/views/resources/pods_view.py`: tabela de pods com status colorido, filtros por namespace e ações | `kuber/views/resources/pods_view.py` | ✅ |
| 4.4 | Criar `kuber/views/resources/deployments_view.py`: tabela com replicas, imagem, status; ações de scale e rolling update | `kuber/views/resources/deployments_view.py` | ✅ |
| 4.5 | Criar `kuber/views/resources/services_view.py`: listagem com tipo, ClusterIP, ports | `kuber/views/resources/services_view.py` | ✅ |
| 4.6 | Criar `kuber/views/resources/configmaps_view.py`: listagem e edição de ConfigMaps | `kuber/views/resources/configmaps_view.py` | ✅ |
| 4.7 | Criar `kuber/views/common/yaml_editor.py`: widget de edição YAML com syntax highlighting (`QSyntaxHighlighter`) | `kuber/views/common/yaml_editor.py` | ✅ |
| 4.8 | Criar `kuber/views/common/resource_detail_panel.py`: painel lateral reutilizável de detalhes de qualquer recurso | `kuber/views/common/resource_detail_panel.py` | ✅ |
| 4.9 | Implementar namespace selector reutilizável (`QComboBox`) integrado a todas as resource views | `kuber/views/common/namespace_selector.py` | ✅ |
| 4.10 | Escrever testes unitários e de integração para ViewModels e Views de recursos | `tests/` | ✅ |

---

## 🚀 Fase 5 — Deploy de Aplicações

> **Objetivo:** Wizard de deploy suportando os três modos: Docker image, Helm chart e Kubernetes manifest.

### Especificações
- Wizard multi-etapas com `QWizard`
- Validação em tempo real dos inputs antes do deploy
- Suporte a dry-run antes da execução final

### Tarefas

| # | Tarefa | Arquivo(s) | Status |
|---|---|---|---|
| 5.1 | Implementar `kuber/viewmodels/deployment_vm.py`: orquestra os três modos de deploy, emite progresso | `kuber/viewmodels/deployment_vm.py` | ✅ |
| 5.2 | Criar `kuber/views/deployment/deploy_wizard.py`: `QWizard` com seleção de tipo de deploy na primeira página | `kuber/views/deployment/deploy_wizard.py` | ✅ |
| 5.3 | Criar `kuber/views/deployment/pages/docker_deploy_page.py`: inputs de imagem, tag, namespace, replicas | `kuber/views/deployment/pages/` | ✅ |
| 5.4 | Criar `kuber/views/deployment/pages/helm_deploy_page.py`: inputs de chart, release name, values (editor YAML) | `kuber/views/deployment/pages/` | ✅ |
| 5.5 | Criar `kuber/views/deployment/pages/manifest_deploy_page.py`: upload ou editor de manifest YAML/JSON | `kuber/views/deployment/pages/` | ✅ |
| 5.6 | Criar `kuber/views/deployment/pages/review_deploy_page.py`: resumo do deploy com opção de dry-run | `kuber/views/deployment/pages/` | ✅ |
| 5.7 | Criar `kuber/views/deployment/deploy_progress_dialog.py`: dialog com log de saída em tempo real durante o deploy | `kuber/views/deployment/deploy_progress_dialog.py` | ✅ |
| 5.8 | Escrever testes do wizard e ViewModels com mocks dos clients Docker/Helm/k8s | `tests/` | ✅ |

---

## 📊 Fase 6 — Monitoramento e Logging

> **Objetivo:** Painel de métricas em tempo real, visualização de logs de pods e stream de eventos do cluster.

### Especificações
- Gráficos de CPU/memória com `pyqtgraph` ou `matplotlib` embutido
- Streaming de logs via Kubernetes API com auto-scroll
- Stream de eventos do cluster em tempo real

### Tarefas

| # | Tarefa | Arquivo(s) | Status |
|---|---|---|---|
| 6.1 | Implementar `kuber/services/monitoring_service.py`: coleta métricas via `metrics-server` API, emite dados periódicos | `kuber/services/monitoring_service.py` | ✅ |
| 6.2 | Implementar `kuber/core/kubernetes/logs.py`: stream de logs de pod via `kubernetes` watch API em QThread | `kuber/core/kubernetes/logs.py` | ✅ |
| 6.3 | Implementar `kuber/core/kubernetes/events.py`: stream de eventos do cluster | `kuber/core/kubernetes/events.py` | ✅ |
| 6.4 | Criar `kuber/viewmodels/monitoring_vm.py`: agrega métricas, logs e eventos; emite signals de atualização | `kuber/viewmodels/monitoring_vm.py` | ✅ |
| 6.5 | Criar `kuber/views/monitoring/metrics_view.py`: gráficos de CPU/memória por pod/node com seletor de intervalo | `kuber/views/monitoring/metrics_view.py` | ✅ |
| 6.6 | Criar `kuber/views/monitoring/logs_view.py`: terminal de logs com filtro, busca e auto-scroll | `kuber/views/monitoring/logs_view.py` | ✅ |
| 6.7 | Criar `kuber/views/monitoring/events_view.py`: tabela de eventos com filtro por tipo (Normal/Warning) | `kuber/views/monitoring/events_view.py` | ✅ |
| 6.8 | Escrever testes de streaming com mocks da watch API | `tests/` | ✅ |

---

## 👤 Fase 7 — Gerenciamento de Usuários

> **Objetivo:** Interface para gerenciar acessos, roles e visualizar audit logs de atividades.

### Especificações
- Integração com RBAC do Kubernetes
- Criação de ServiceAccounts e RoleBindings
- Visualização de audit logs (requer configuração no cluster)

### Tarefas

| # | Tarefa | Arquivo(s) | Status |
|---|---|---|---|
| 7.1 | Implementar `kuber/core/kubernetes/rbac.py`: CRUD de ServiceAccounts, Roles, ClusterRoles, RoleBindings | `kuber/core/kubernetes/rbac.py` | ✅ |
| 7.2 | Implementar `kuber/models/user_model.py`: Qt model para usuários e roles | `kuber/models/user_model.py` | 🔲 |
| 7.3 | Implementar `kuber/viewmodels/user_vm.py` | `kuber/viewmodels/user_vm.py` | ✅ |
| 7.4 | Criar `kuber/views/users/users_view.py`: listagem de ServiceAccounts com roles associadas | `kuber/views/users/users_view.py` | ✅ |
| 7.5 | Criar `kuber/views/users/role_editor_dialog.py`: dialog para criar/editar roles e bindings | `kuber/views/users/role_editor_dialog.py` | ✅ |
| 7.6 | Criar `kuber/views/users/audit_log_view.py`: tabela de eventos de audit | `kuber/views/users/audit_log_view.py` | ✅ |
| 7.7 | Escrever testes de RBAC com mocks | `tests/` | ✅ |

> **Nota 7.2:** O arquivo `kuber/models/user_model.py` não existe. O `user_vm.py` e as views de usuários funcionam sem ele (dados passados diretamente como listas). Precisa ser criado como `QAbstractTableModel`.

---

## 💾 Fase 8 — Backup e Restore

> **Objetivo:** Exportar e importar configurações de cluster para recuperação de desastres.

### Especificações
- Backup de recursos k8s como manifests YAML compactados
- Restore seletivo por namespace ou tipo de recurso
- Agendamento de backups automáticos

### Tarefas

| # | Tarefa | Arquivo(s) | Status |
|---|---|---|---|
| 8.1 | Implementar `kuber/services/backup_service.py`: exporta recursos k8s para YAML, compacta em `.tar.gz` | `kuber/services/backup_service.py` | ✅ |
| 8.2 | Implementar restore com validação de compatibilidade antes da aplicação | `kuber/services/backup_service.py` | ✅ |
| 8.3 | Criar `kuber/viewmodels/backup_vm.py` com progresso de backup/restore | `kuber/viewmodels/backup_vm.py` | ✅ |
| 8.4 | Criar `kuber/views/backup/backup_view.py`: listagem de backups locais, ações de criar/restaurar/deletar | `kuber/views/backup/backup_view.py` | ✅ |
| 8.5 | Criar `kuber/views/backup/restore_wizard.py`: wizard de seleção de recursos para restore | `kuber/views/backup/restore_wizard.py` | ✅ |
| 8.6 | Implementar agendamento com `QTimer` persistido via `settings.py` | `kuber/services/backup_service.py` | ✅ |
| 8.7 | Escrever testes de backup/restore com sistema de arquivos temporário | `tests/` | ⚠️ |

> **Nota 8.7:** Existem testes para `backup_service` e `backup_views`, porém **falta** `test_backup_vm.py` com testes do ViewModel.

---

## 🌐 Fase 9 — Features Avançadas

> **Objetivo:** Suporte a OpenShift, multi-cloud e custom resources.

### Especificações
- OpenShift via client compatível (`openshift-client`)
- Multi-cloud: abstração de providers (AWS EKS, GCP GKE, Azure AKS)
- CRD support: listagem e edição de Custom Resources dinamicamente

### Tarefas

| # | Tarefa | Arquivo(s) | Status |
|---|---|---|---|
| 9.1 | Implementar `kuber/core/kubernetes/custom_resources.py`: listar CRDs, CRUD de custom resource instances | `kuber/core/kubernetes/custom_resources.py` | ✅ |
| 9.2 | Criar `kuber/views/resources/custom_resource_view.py`: view dinâmica para qualquer CRD selecionado | `kuber/views/resources/custom_resource_view.py` | ✅ |
| 9.3 | Implementar `kuber/core/openshift/client.py`: wrapper do OpenShift client, detecção automática de cluster OpenShift | `kuber/core/openshift/client.py` | ✅ |
| 9.4 | Implementar `kuber/core/cloud/provider_factory.py`: factory para EKS, GKE, AKS com interface unificada | `kuber/core/cloud/provider_factory.py` | ✅ |
| 9.5 | Criar `kuber/views/settings/cloud_settings_view.py`: configuração de credenciais de cloud providers | `kuber/views/settings/cloud_settings_view.py` | ✅ |
| 9.6 | Escrever testes de custom resources e provider factory | `tests/` | ✅ |

---

## ✅ Fase 10 — Qualidade, Acessibilidade e Empacotamento

> **Objetivo:** Cobertura de testes completa, auditoria de acessibilidade, otimização de performance e geração de instaladores.

### Especificações
- Cobertura de testes ≥ 80% (`pytest-cov`)
- Acessibilidade auditada (screen reader, WCAG contrast ratios nos temas)
- Empacotamento para Windows, macOS e Linux com `PyInstaller`

### Tarefas

| # | Tarefa | Arquivo(s) | Status |
|---|---|---|---|
| 10.1 | Completar cobertura de testes unitários e de integração para todas as fases | `tests/` | 🔲 |
| 10.2 | Auditoria de acessibilidade: definir `setAccessibleName` e `setAccessibleDescription` em todos os widgets | `kuber/views/` | ⚠️ |
| 10.3 | Validar todos os temas (`dark`, `light`, `high_contrast`) contra WCAG 2.1 AA de contraste | `kuber/resources/themes/` | 🔲 |
| 10.4 | Implementar `kuber/views/settings/settings_view.py`: painel de configurações (tema, idioma, clusters, backup schedule) | `kuber/views/settings/settings_view.py` | ✅ |
| 10.5 | Completar traduções `kuber_en.ts` e `kuber_pt_BR.ts` e compilar para `.qm` | `kuber/i18n/` | 🔲 |
| 10.6 | Criar `kuber.spec` para `PyInstaller` com todos os assets e dependências incluídos | `kuber.spec` | 🔲 |
| 10.7 | Criar `.github/workflows/release.yml`: build automático de executáveis para Windows, macOS e Linux via matrix | `.github/workflows/release.yml` | 🔲 |
| 10.8 | Criar `docs/user-guide.md` e `docs/developer-guide.md` | `docs/` | 🔲 |
| 10.9 | Executar análise de performance: identificar gargalos no polling e queries k8s, otimizar | Profiling | 🔲 |
| 10.10 | Criar `CHANGELOG.md` e tag de release `v1.0.0` | Raiz do projeto | ✅ |

> **Nota 10.1:** Cobertura atual: **66%** (meta: ≥80%). 201 testes passando. Módulos com 0% de cobertura: `main_window.py`, `splash_screen.py`, `settings_view.py`, `deploy_wizard.py`, `cluster_switcher.py`. Faltam testes para `docker/`, `git/`, `helm/` no core.
> **Nota 10.2:** Acessibilidade parcialmente implementada — `setAccessibleName` presente em ~20 widgets, `setAccessibleDescription` em ~13. Várias views de recursos, monitoring e deployment ainda não possuem atributos de acessibilidade completos.

---

## 📊 Resumo de Progresso

| Fase | Descrição | Total | ✅ | ⚠️ | 🔲 | Progresso |
|---|---|---|---|---|---|---|
| 0 | Fundação do Projeto | 10 | 10 | 0 | 0 | **100%** |
| 1 | Infraestrutura Core | 12 | 11 | 1 | 0 | **92%** |
| 2 | Fundação da UI | 12 | 9 | 1 | 2 | **75%** |
| 3 | Gerenciamento de Clusters | 7 | 7 | 0 | 0 | **100%** |
| 4 | Gerenciamento de Recursos | 10 | 10 | 0 | 0 | **100%** |
| 5 | Deploy de Aplicações | 8 | 8 | 0 | 0 | **100%** |
| 6 | Monitoramento e Logging | 8 | 8 | 0 | 0 | **100%** |
| 7 | Gerenciamento de Usuários | 7 | 6 | 0 | 1 | **86%** |
| 8 | Backup e Restore | 7 | 6 | 1 | 0 | **86%** |
| 9 | Features Avançadas | 6 | 6 | 0 | 0 | **100%** |
| 10 | Qualidade e Empacotamento | 10 | 2 | 1 | 7 | **20%** |
| **Total** | | **97** | **83** | **4** | **10** | **86%** |

> **Legenda:** ✅ Concluído · ⚠️ Parcialmente concluído · 🔲 Pendente

---

## 📌 Considerações Finais

1. **Ordem de execução:** As Fases 0→1→2 são pré-requisitos obrigatórios. As Fases 3→9 podem ser paralelizadas por feature branches após a Fase 2 estar completa. A Fase 10 sempre ao final.
2. **Dependências externas críticas:** `metrics-server` precisa estar instalado no cluster para a Fase 6; audit logs requerem configuração específica no `kube-apiserver` para a Fase 7.
3. **Prioridade MVP:** Para uma versão mínima viável, executar Fases 0+1+2+3+4 entrega a funcionalidade core de gerenciamento de clusters e recursos, suficiente para validação com usuários antes das features avançadas.
4. **Próximos passos prioritários:** Resolver os itens ⚠️ e 🔲 das fases 1, 2, 7 e 8 antes de avançar na Fase 10. A cobertura de testes (66% → 80%) é o maior gap para a release v1.0.0.
