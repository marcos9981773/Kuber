---
mode: agent
description: Scaffold a new application service in kuber/services/ following the service pattern
---

Create a new application service: **${input:serviceName}Service**

## Target file
`kuber/services/${input:serviceName:snake}_service.py`

## Template

```python
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from kuber.core.exceptions import KuberError

logger = logging.getLogger(__name__)


@dataclass
class ${input:serviceName}Result:
    """Result DTO for ${input:serviceName}Service operations."""
    success: bool
    data: Any = None
    message: str = ""


class ${input:serviceName}Service:
    """
    Application service for ${input:serviceName} operations.

    This service coordinates between core modules and provides
    higher-level business operations. NO PyQt5 imports allowed.
    """

    def __init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)

    def execute(self, *args: Any, **kwargs: Any) -> ${input:serviceName}Result:
        """Main service operation."""
        try:
            ...
            return ${input:serviceName}Result(success=True)
        except KuberError as e:
            self._logger.error(f"Service error: {e}")
            return ${input:serviceName}Result(success=False, message=str(e))
```

## Requirements

1. **No PyQt5** — services must be pure Python, testable without a Qt app
2. **Return DTOs** — use `@dataclass` result objects, never raise to callers
3. **Logging** — use `logging` module, never `print()`
4. **Pathlib** — use `pathlib.Path` for file operations, never `os.path`
5. **Retry** — use exponential backoff (max 3 attempts) for external calls
6. **Timeouts** — all external calls must have explicit timeout values

## Also create
- Unit test: `tests/unit/test_${input:serviceName:snake}_service.py`
  - Test success case
  - Test failure returns result with success=False
  - Test retry behavior
  - Mock all external dependencies

