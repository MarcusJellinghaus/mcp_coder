# Step 2: Refactor jenkins_operations/client.py

## LLM Prompt
```
Read pr_info/steps/summary.md for context, then implement Step 2.
Replace structlog with standard logging in client.py.
This is a simple mechanical change - 1 import, 1 logger definition, 1 log call.
```

## WHERE
- **File**: `src/mcp_coder/utils/jenkins_operations/client.py`

## WHAT

### Changes Required

| Line | Before | After |
|------|--------|-------|
| 31 | `import structlog` | `import logging` |
| 39 | `logger = structlog.get_logger(__name__)` | `logger = logging.getLogger(__name__)` |
| ~147 | `logger.debug("Job started successfully", job_path=job_path, queue_id=queue_id)` | `logger.debug("Job started successfully", extra={"job_path": job_path, "queue_id": queue_id})` |

## HOW

### Before (lines 31-39)
```python
import structlog
from jenkins import Jenkins

from ..log_utils import log_function_call
from ..user_config import get_config_value
from .models import JobStatus, QueueSummary

# Setup logger
logger = structlog.get_logger(__name__)
```

### After (lines 31-39)
```python
import logging

from jenkins import Jenkins

from ..log_utils import log_function_call
from ..user_config import get_config_value
from .models import JobStatus, QueueSummary

# Setup logger
logger = logging.getLogger(__name__)
```

### Before (in start_job method)
```python
logger.debug(
    "Job started successfully", job_path=job_path, queue_id=queue_id
)
```

### After (in start_job method)
```python
logger.debug(
    "Job started successfully", extra={"job_path": job_path, "queue_id": queue_id}
)
```

## ALGORITHM

N/A - This is a mechanical search-and-replace change with no algorithmic complexity.

## DATA

No data structure changes. The log output format changes from structlog's JSON-style to standard logging with extra fields.

## TEST VERIFICATION

Existing tests in `tests/utils/jenkins_operations/test_client.py` should continue to pass. These tests mock the Jenkins client and don't test logging behavior directly.

```bash
pytest tests/utils/jenkins_operations/test_client.py -v
```

## IMPLEMENTATION CHECKLIST

- [ ] Change `import structlog` to `import logging`
- [ ] Change `logger = structlog.get_logger(__name__)` to `logger = logging.getLogger(__name__)`
- [ ] Update the one `logger.debug()` call to use `extra={}`
- [ ] Run tests: `pytest tests/utils/jenkins_operations/test_client.py -v`
