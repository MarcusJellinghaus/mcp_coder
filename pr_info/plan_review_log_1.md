# review-plan review log 1

## Round 1 — 2026-11-25
**Findings**:
Now the source code.Reviewing plan vs. code; checking the vscodeclaude and verify test fixtures next.Checking `load_toolkit` and the `setup` built-in path to confirm the plan's assumptions.pr_info/steps/step_3.md:40 — low — `InstallConfig.from_args` (`src/mcp_coder/install/_env.py:83-88`) lists every cause of its `ValueError` under `Raises`. After this change a non-table `tool`, `mcp-coder` or `install` also raises, but the plan doesn't add that case to the docstring, so the docstring will be incomplete.
pr_info/steps/step_3.md:89 — low — The `TestNonTablePolicy` check "warning contains the key name" can't fail for the `install = 1` case. The fixed text of the warning already contains "`mcp-coder install`". Assert the quoted key `'install'` / `'install-from-github'` (from the `ValueError` text) instead.
**Decisions**:
Verdict(decision='tasks', tasks=['In pr_info/steps/step_3.md (around line 40), have the plan update the `Raises` section of the `InstallConfig.from_args` docstring (src/mcp_coder/install/_env.py:83-88) to say that a `ValueError` is also raised when `tool`, `mcp-coder` or `install` in pyproject.toml is not a table.', 'In pr_info/steps/step_3.md (around line 89), change the `TestNonTablePolicy` assertion so it can actually fail. Instead of checking that the warning contains the key name, assert that it contains the quoted key from the `ValueError` text (`\'install\'` / `\'install-from-github\'`). The fixed warning text already contains "mcp-coder install", so the current check passes even when the key name is missing.'], escalate_reason=None)
**Changes**:
applied

## Round 2 — 2026-11-25
**Findings**:
Reviewing plan against source — checking the verify end-to-end test helpers and the vscodeclaude/setup paths.Nearly done — checking existing verify_project_keys tests for conflicts with step 4's behaviour change.`pr_info/steps/step_3.md:70` — low — Step 3 parametrizes `test_invalid_target_pyproject_returns_one` but keeps its docstring, which says "the failure comes from `phase_overrides`' config read". After the change, the `tool = 1`, `mcp-coder = 1` and `install = 1` cases fail earlier, in `InstallConfig.from_args` (`get_install_extras(strict=True)`). Only the `packages` and `install-from-github` cases still reach `phase_overrides`, so the plan should also have the docstring updated to name both failure points.
**Decisions**:
Verdict(decision='tasks', tasks=["In pr_info/steps/step_3.md (around line 70), add a task to update the docstring of the parametrized `test_invalid_target_pyproject_returns_one`. It should name both failure points: the `tool = 1`, `mcp-coder = 1` and `install = 1` cases now fail in `InstallConfig.from_args` (`get_install_extras(strict=True)`), while the `packages` and `install-from-github` cases still fail in `phase_overrides`' config read."], escalate_reason=None)
**Changes**:
applied
