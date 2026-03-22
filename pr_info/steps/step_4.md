# Step 4: src/ W0707 + W0719 — raise-missing-from + broad-exception-raised (8 occurrences)

## Goal
Add proper exception chaining (`from e`) and replace `raise Exception` with `raise RuntimeError`.
These two warnings are tightly coupled — the W0719 occurrence also needs W0707 fix.

## WHERE — Files Modified

**W0707 — Add `from e` to raise statements (7 total):**
- `src/mcp_coder/prompt_manager.py`
  - line 582: `raise FileNotFoundError(...)` to `raise FileNotFoundError(...) from e`
  - line 600: `raise FileNotFoundError(...)` to `raise FileNotFoundError(...) from e`
  - line 612: `except FileNotFoundError:` to `except FileNotFoundError as exc:` + `raise ... from exc`
  - line 614: `raise FileNotFoundError(...)` to `raise FileNotFoundError(...) from e`
- `src/mcp_coder/cli/parsers.py`
  - line 481: `except ValueError:` to `except ValueError as exc:` + `raise argparse.ArgumentTypeError(...) from exc`
- `src/mcp_coder/utils/timezone_utils.py`
  - line 66: `raise ValueError(...)` to `raise ValueError(...) from e`
- `src/mcp_coder/workflows/implement/task_processing.py`
  - line 217: `raise Exception(...)` to `raise RuntimeError(...) from e` (also fixes W0719)

**W0719 — Replace broad exception raised (1 total):**
- `src/mcp_coder/workflows/implement/task_processing.py` line 217 — handled above

## WHAT

```python
# W0707 pattern:
except SomeError:
    raise NewError("message")
# becomes:
except SomeError as exc:
    raise NewError("message") from exc

# W0719 pattern:
raise Exception(...)
# becomes:
raise RuntimeError(...)
```

## DATA

Pylint count reduced by: **8 warnings** (7 W0707 + 1 W0719).

## TDD Note

Run existing tests after changes to confirm nothing broken.

---

## LLM Prompt

```
Please implement Step 4: fix W0707 (raise-missing-from) and W0719 (broad-exception-raised) in src/.
See pr_info/steps/step_4.md for exact locations.
Rules: add `from e`/`from exc` to raises inside except blocks. Change `raise Exception` to `raise RuntimeError`.
No other logic changes. Run pylint, pytest (fast unit tests), and mypy to verify.
```
