---
mode: agent
description: Scaffold a new PyQt5 View widget with accessibility, theming, and i18n support
---

Create a new PyQt5 View for the feature: **${input:featureName}**

## Target files
- View: `kuber/views/${input:viewFolder}/${input:featureName:snake}_view.py`
- Test: `tests/unit/views/test_${input:featureName:snake}_view.py`

## Requirements for the View

### Structure
```python
class ${input:featureName}View(QWidget):
    def __init__(self, view_model: ${input:featureName}ViewModel, parent=None):
        super().__init__(parent)
        self._vm = view_model
        self._setup_ui()
        self._setup_accessibility()
        self._setup_tab_order()
        self._connect_signals()
```

### UI Setup (`_setup_ui`)
- Use `QVBoxLayout` / `QHBoxLayout` — NO absolute positioning
- All text strings wrapped in `self.tr("...")`
- No hardcoded colors or fonts — use QSS classes only
- Use `QSizePolicy` for responsive behavior

### Accessibility (`_setup_accessibility`)
- `setAccessibleName()` on ALL interactive widgets
- `setAccessibleDescription()` on widgets that need explanation
- `setWhatsThis()` for complex controls
- Keyboard shortcuts with `QShortcut` where applicable

### Tab Order (`_setup_tab_order`)
- Explicitly define tab order using `QWidget.setTabOrder(a, b)`
- Document the intended tab flow in a comment

### Signal Connections (`_connect_signals`)
- Connect ViewModel signals to UI update slots
- Connect UI actions to ViewModel methods
- NEVER connect signals outside this method

### Theming
- Apply object names: `self.btn_save.setObjectName("btnPrimary")`
- Use CSS classes from `kuber/resources/themes/` QSS files

## Test Requirements
- Use `pytest-qt` (`qtbot` fixture)
- Test that all widgets are created
- Test signal/slot connections
- Test accessibility names are set
- Mock the ViewModel

## Rules
- Inherit from `QWidget` (or `QDialog`, `QWizardPage` if appropriate)
- Long operations MUST use ViewModel + BaseWorker — never block UI thread
- Follow `.github/copilot-instructions.md` strictly

