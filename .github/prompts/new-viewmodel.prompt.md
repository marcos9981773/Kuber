---
mode: agent
description: Scaffold a new ViewModel for a Kuber feature following MVVM pattern
---

Create a new ViewModel for the feature: **${input:featureName}**

## Target file
`kuber/viewmodels/${input:featureName:snake}_vm.py`

## Template

```python
from __future__ import annotations

from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from kuber.views.common.base_worker import BaseWorker
from kuber.core.${input:coreModule} import ${input:coreClass}


class ${input:featureName}ViewModel(QObject):
    """ViewModel for ${input:featureName} feature."""

    # --- Signals ---
    data_loaded = pyqtSignal(list)          # Emits when data is refreshed
    loading_changed = pyqtSignal(bool)      # True = loading, False = idle
    error_occurred = pyqtSignal(str)        # User-friendly error message
    item_selected = pyqtSignal(object)      # Emits selected item

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._core = ${input:coreClass}()
        self._worker: BaseWorker | None = None
        self._connect_signals()

    def _connect_signals(self) -> None:
        """Wire internal signals and slots."""
        pass

    def load(self) -> None:
        """Trigger async data load."""
        ...

    def refresh(self) -> None:
        """Force data refresh."""
        self.load()
```

## Requirements

1. **Signals** — declare all as class-level `pyqtSignal` attributes
2. **Workers** — all async operations use `BaseWorker` subclasses defined in the same file
3. **Error handling** — catch exceptions from core, emit user-friendly messages via `error_occurred`
4. **No UI imports** — ViewModels must only import from `PyQt5.QtCore`, not `PyQt5.QtWidgets`
5. **State management** — track loading state and emit `loading_changed` signal
6. **Thread safety** — never call `core` methods directly on the main thread for long ops

## Workers pattern
```python
class _Load${input:featureName}Worker(BaseWorker):
    def run_task(self) -> list:
        return ${input:coreClass}().list_all()
```

## Also create
- Unit test: `tests/unit/viewmodels/test_${input:featureName:snake}_vm.py`
  - Mock the core module
  - Test: load emits data_loaded, error handling emits error_occurred, loading state changes

