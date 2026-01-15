# Step 4: Refactor All Callers to Use Batch Config Function

## LLM Prompt

```
Implement Step 4 of Issue #228 (see pr_info/steps/summary.md for context).

Refactor all 8 callers of `get_config_value()` to use the new `get_config_values()` 
batch function. This is a mechanical refactoring - no new tests needed, existing 
tests should continue to pass.

Requirements:
- Replace individual get_config_value() calls with single get_config_values() call
- Group related config reads together
- Maintain same behavior (env var priority, None for missing values)
```

## WHERE: File Paths (8 Locations)

1. `src/mcp_coder/utils/github_operations/base_manager.py`
2. `src/mcp_coder/utils/jenkins_operations/client.py`
3. `src/mcp_coder/cli/commands/coordinator/core.py` (3 functions)
4. `tests/conftest.py`
5. `tests/utils/jenkins_operations/test_integration.py`

## WHAT: Refactoring Pattern

### Before (Individual Calls)
```python
from mcp_coder.utils.user_config import get_config_value

server_url = get_config_value("jenkins", "server_url")
username = get_config_value("jenkins", "username")
api_token = get_config_value("jenkins", "api_token")
```

### After (Batch Call)
```python
from mcp_coder.utils.user_config import get_config_values

config = get_config_values([
    ("jenkins", "server_url", None),
    ("jenkins", "username", None),
    ("jenkins", "api_token", None),
])
server_url = config[("jenkins", "server_url")]
username = config[("jenkins", "username")]
api_token = config[("jenkins", "api_token")]
```

---

## Refactoring Details by File

### 1. `base_manager.py` - BaseGitHubManager.__init__()

**Current:**
```python
github_token = user_config.get_config_value("github", "token")
```

**After:**
```python
config = user_config.get_config_values([("github", "token", None)])
github_token = config[("github", "token")]
```

---

### 2. `client.py` - _get_jenkins_config()

**Current:**
```python
def _get_jenkins_config() -> dict[str, Optional[str]]:
    server_url = get_config_value("jenkins", "server_url")
    username = get_config_value("jenkins", "username")
    api_token = get_config_value("jenkins", "api_token")
    return {"server_url": server_url, "username": username, "api_token": api_token}
```

**After:**
```python
def _get_jenkins_config() -> dict[str, Optional[str]]:
    config = get_config_values([
        ("jenkins", "server_url", None),
        ("jenkins", "username", None),
        ("jenkins", "api_token", None),
    ])
    return {
        "server_url": config[("jenkins", "server_url")],
        "username": config[("jenkins", "username")],
        "api_token": config[("jenkins", "api_token")],
    }
```

---

### 3. `core.py` - load_repo_config()

**Current:**
```python
def load_repo_config(repo_name: str) -> dict[str, Optional[str]]:
    coordinator = _get_coordinator()
    section = f"coordinator.repos.{repo_name}"
    
    repo_url = coordinator.get_config_value(section, "repo_url")
    executor_job_path = coordinator.get_config_value(section, "executor_job_path")
    github_credentials_id = coordinator.get_config_value(section, "github_credentials_id")
    executor_os = coordinator.get_config_value(section, "executor_os")
    # ... normalize executor_os
```

**After:**
```python
def load_repo_config(repo_name: str) -> dict[str, Optional[str]]:
    coordinator = _get_coordinator()
    section = f"coordinator.repos.{repo_name}"
    
    config = coordinator.get_config_values([
        (section, "repo_url", None),
        (section, "executor_job_path", None),
        (section, "github_credentials_id", None),
        (section, "executor_os", None),
    ])
    
    repo_url = config[(section, "repo_url")]
    executor_job_path = config[(section, "executor_job_path")]
    github_credentials_id = config[(section, "github_credentials_id")]
    executor_os = config[(section, "executor_os")]
    # ... normalize executor_os
```

---

### 4. `core.py` - get_cache_refresh_minutes()

**Current:**
```python
def get_cache_refresh_minutes() -> int:
    coordinator = _get_coordinator()
    value = coordinator.get_config_value("coordinator", "cache_refresh_minutes")
    # ...
```

**After:**
```python
def get_cache_refresh_minutes() -> int:
    coordinator = _get_coordinator()
    config = coordinator.get_config_values([("coordinator", "cache_refresh_minutes", None)])
    value = config[("coordinator", "cache_refresh_minutes")]
    # ...
```

---

### 5. `core.py` - get_jenkins_credentials()

**Current:**
```python
def get_jenkins_credentials() -> tuple[str, str, str]:
    coordinator = _get_coordinator()
    server_url = coordinator.get_config_value("jenkins", "server_url")
    username = coordinator.get_config_value("jenkins", "username")
    api_token = coordinator.get_config_value("jenkins", "api_token")
    # ...
```

**After:**
```python
def get_jenkins_credentials() -> tuple[str, str, str]:
    coordinator = _get_coordinator()
    config = coordinator.get_config_values([
        ("jenkins", "server_url", None),
        ("jenkins", "username", None),
        ("jenkins", "api_token", None),
    ])
    server_url = config[("jenkins", "server_url")]
    username = config[("jenkins", "username")]
    api_token = config[("jenkins", "api_token")]
    # ...
```

---

### 6. `tests/conftest.py` - github_test_setup fixture

**Current:**
```python
if not github_token:
    github_token = get_config_value("github", "token")
if not test_repo_url:
    test_repo_url = get_config_value("github", "test_repo_url")
```

**After:**
```python
if not github_token or not test_repo_url:
    config = get_config_values([
        ("github", "token", None),
        ("github", "test_repo_url", None),
    ])
    if not github_token:
        github_token = config[("github", "token")]
    if not test_repo_url:
        test_repo_url = config[("github", "test_repo_url")]
```

---

### 7. `tests/utils/jenkins_operations/test_integration.py` - jenkins_test_setup fixture

**Current:**
```python
if not server_url:
    server_url = get_config_value("jenkins", "server_url")
if not username:
    username = get_config_value("jenkins", "username")
if not api_token:
    api_token = get_config_value("jenkins", "api_token")
if not test_job:
    test_job = get_config_value("jenkins", "test_job")
```

**After:**
```python
# Get any missing values from config file in one batch
missing_keys = []
if not server_url:
    missing_keys.append(("jenkins", "server_url", None))
if not username:
    missing_keys.append(("jenkins", "username", None))
if not api_token:
    missing_keys.append(("jenkins", "api_token", None))
if not test_job:
    missing_keys.append(("jenkins", "test_job", None))

if missing_keys:
    config = get_config_values(missing_keys)
    if not server_url:
        server_url = config[("jenkins", "server_url")]
    if not username:
        username = config[("jenkins", "username")]
    if not api_token:
        api_token = config[("jenkins", "api_token")]
    if not test_job:
        test_job = config[("jenkins", "test_job")]
```

---

## HOW: Update Imports

Each file needs import update:

**Before:**
```python
from mcp_coder.utils.user_config import get_config_value
```

**After:**
```python
from mcp_coder.utils.user_config import get_config_values
```

---

## Implementation Checklist

- [ ] Update `base_manager.py` - 1 call site
- [ ] Update `client.py` - 3 calls → 1 batch
- [ ] Update `core.py` load_repo_config() - 4 calls → 1 batch
- [ ] Update `core.py` get_cache_refresh_minutes() - 1 call
- [ ] Update `core.py` get_jenkins_credentials() - 3 calls → 1 batch
- [ ] Update `tests/conftest.py` - 2 calls → 1 batch
- [ ] Update `tests/utils/jenkins_operations/test_integration.py` - 4 calls → 1 batch
- [ ] Run all existing tests to verify refactoring correctness
- [ ] Verify no references to `get_config_value` remain (grep codebase)
