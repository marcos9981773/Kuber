---
mode: agent
description: Generate comprehensive pytest unit tests for a given Kuber module
---

Generate `pytest` unit tests for the module: **${input:modulePath}**
(e.g., `kuber/core/kubernetes/clusters.py`)

## Target test file
Mirror the source path under `tests/unit/`:
- Source: `kuber/core/kubernetes/clusters.py`
- Tests:  `tests/unit/core/kubernetes/test_clusters.py`

## Test structure required

### For Core modules (no PyQt5)
```python
import pytest
from unittest.mock import MagicMock, patch
from kuber.core.exceptions import KuberApiError, KuberNotFoundError, KuberPermissionError

class TestClassName:
    """Tests for ClassName in ${input:modulePath}."""

    def test_method_happy_path_returns_expected(self, mocker): ...
    def test_method_api_403_raises_permission_error(self, mocker): ...
    def test_method_api_404_raises_not_found_error(self, mocker): ...
    def test_method_api_500_raises_api_error(self, mocker): ...
    def test_method_timeout_raises_error(self, mocker): ...
    def test_method_empty_response_returns_empty_list(self, mocker): ...
```

### For ViewModels (PyQt5, use qtbot)
```python
import pytest
from PyQt5.QtCore import QCoreApplication
from unittest.mock import MagicMock

@pytest.fixture
def vm(qtbot, mocker):
    mocker.patch("kuber.core.xxx.CoreClass")
    from kuber.viewmodels.xxx_vm import XxxViewModel
    return XxxViewModel()

class TestXxxViewModel:
    def test_load_emits_data_loaded_signal(self, vm, qtbot): ...
    def test_load_error_emits_error_occurred(self, vm, qtbot): ...
    def test_loading_changed_emitted_during_load(self, vm, qtbot): ...
```

### For Views (use qtbot)
```python
@pytest.fixture
def view(qtbot, mocker):
    mock_vm = mocker.MagicMock()
    widget = XxxView(view_model=mock_vm)
    qtbot.addWidget(widget)
    return widget

class TestXxxView:
    def test_view_creates_all_widgets(self, view): ...
    def test_accessible_names_are_set(self, view): ...
    def test_tab_order_is_defined(self, view): ...
```

## Coverage requirements
- Happy path ✅
- All error paths (403, 404, 500, timeout, network error) ✅
- Edge cases: empty data, None values, invalid inputs ✅
- State transitions for ViewModels ✅

## Rules
- Mock ALL external calls (kubernetes API, docker, git, network)
- Use `mocker.patch` for patching — do NOT use `unittest.mock.patch` decorator
- Test names: `test_<unit>_<scenario>_<expected_result>`
- Each test must have a single assertion focus
- Add docstrings explaining what each test verifies

