# Step 7 — Docs and agent setup

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement **Step 7** exactly as described in `pr_info/steps/step_7.md`.
> This step changes only docs and config. Check that `.claude/settings.local.json` is still valid JSON by reading it back. Run pylint, the fast pytest set and mypy (they must still pass), then make one commit.

## WHERE

- `docs/repository-setup/internal.md` — "Other Internal Scripts" table.
- `.claude/CLAUDE.md` — new `## Jenkins` section, placed directly before `## Shared Libraries`.
- `.claude/settings.local.json` — `permissions.allow`.

## WHAT

`internal.md`, two rows added after the `tools/safe_delete_folder.py` row:

```
| `tools/jenkins_builds.py` (+ `.bat` / `.sh`) | List recent Jenkins builds with time, status, folder, job and build number |
| `tools/jenkins_download_logs.py` (+ `.bat` / `.sh`) | Download console logs of recent Jenkins builds (default: failure, aborted, unstable) |
```

`.claude/CLAUDE.md`:

```
## Jenkins

- Recent builds: `tools/jenkins_builds.sh [--limit N] [--folder PATH] [--status failure,...]`
- Download console logs: `tools/jenkins_download_logs.sh [--status ...] [--outdir .scratch/jenkins_logs]` — read them with `read_file`, delete `.scratch/` when done.
```

Use exactly the `tools/<name>.sh` form so the permission prefix rules match.

`.claude/settings.local.json` — four entries inserted after `"Bash(start docs/architecture/dependency_graph.html)",`:

```json
"Bash(tools/jenkins_builds.bat:*)",
"Bash(tools/jenkins_builds.sh:*)",
"Bash(tools/jenkins_download_logs.bat:*)",
"Bash(tools/jenkins_download_logs.sh:*)",
```

## HOW / ALGORITHM / DATA

Not applicable: no code changes.

## Precondition

If `docs/repository-setup/internal.md` has no "Other Internal Scripts" table, write one line to `pr_info/.blocked.txt` and stop.
