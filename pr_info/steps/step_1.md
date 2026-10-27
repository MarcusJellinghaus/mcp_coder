# Step 1 — `BuildInfo` and pure build functions (`builds.py`)

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement **Step 1** exactly as described in `pr_info/steps/step_1.md`.
> Use TDD: write `tests/utils/jenkins_operations/test_builds.py` first, then `BuildInfo` and `builds.py`.
> These tests use no mocks. Run pylint, the fast pytest set and mypy; all must pass. Then run the formatter and make one commit.

## WHERE

- `src/mcp_coder/utils/jenkins_operations/models.py` — add `BuildInfo`; mention it in the module docstring.
- `src/mcp_coder/utils/jenkins_operations/__init__.py` — import and export `BuildInfo` (`__all__`, docstring "Main Components").
- `src/mcp_coder/utils/jenkins_operations/builds.py` — **new**.
- `tests/utils/jenkins_operations/test_builds.py` — **new**.

## WHAT

```python
# models.py
@dataclass(frozen=True)
class BuildInfo:
    job_path: str            # Jenkins fullName, e.g. "Windows-Agents/CD/Rebuild-mcp-coder-dev"
    folder: str              # full folder path from the root, "" at top level
    job_name: str            # last path segment (multibranch: still URL-encoded)
    number: int
    status: str              # one of builds.VALID_STATUSES
    timestamp: datetime      # timezone-aware UTC
    duration_ms: int | None  # None while running or unknown
    url: str
```

```python
# builds.py
VALID_STATUSES: tuple[str, ...] = (
    "running", "success", "unstable", "failure", "aborted", "not_built", "unknown",
)
MAX_DEPTH = 4
BUILDS_CAP = 100  # Jenkins returns at most the newest 100 builds per job via `builds`

def map_status(build: dict[str, Any]) -> str: ...
def split_job_path(job_path: str) -> tuple[str, str]: ...
def build_tree_query(limit: int) -> str: ...
def flatten_builds(tree: dict[str, Any]) -> list[BuildInfo]: ...
def validate_statuses(statuses: Iterable[str] | None) -> None: ...
def select_builds(
    builds: list[BuildInfo], limit: int, statuses: Collection[str] | None
) -> list[BuildInfo]: ...
def log_filename(job_path: str, number: int) -> str: ...
```

The module docstring states that the `tree=` query is spelled out to `MAX_DEPTH` (Jenkins has no recursive tree syntax) and that jobs nested deeper are not reported.

## HOW

- `builds.py` imports only the standard library and `.models.BuildInfo`. It does no I/O and no logging.
- `__init__.py` exports only `BuildInfo`. `builds.py` is imported by module path (`from .builds import ...`) by the client in step 2 and the tools in steps 5–6.

## ALGORITHM

```
map_status(b):    "running" if b.get("building") else (b.get("result") or "unknown").lower()
split_job_path(p): folder, _, name = p.rpartition("/"); return folder, name
build_tree_query(limit):
    field = "builds" if limit <= BUILDS_CAP else "allBuilds"
    level = f"fullName,url,{field}[number,building,result,timestamp,duration,url]{{0,{limit}}}"
    inner = level; repeat MAX_DEPTH-1 times: inner = f"{level},jobs[{inner}]"
    return f"?tree=jobs[{inner}]"
flatten_builds(tree): for job in tree.get("jobs") or []:
    for b in job.get("builds") or job.get("allBuilds") or []: append BuildInfo(...)
    extend with flatten_builds(job)          # recurse into folders / multibranch
select_builds(builds, limit, statuses):
    newest = sorted(builds, key=timestamp, reverse=True)[:limit]
    return newest if not statuses else [b for b in newest if b.status in statuses]
validate_statuses: any s not in VALID_STATUSES → ValueError(f"Unknown status '{s}'. Valid values: {', '.join(VALID_STATUSES)}")
log_filename(p, n): re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", p) + f"_{n}.txt"
```

`flatten_builds` details:
- `timestamp = datetime.fromtimestamp(b["timestamp"] / 1000, tz=timezone.utc)`
- `duration_ms = None if status in ("running", "unknown") else b.get("duration")`
- `job_path = job["fullName"]`; `folder, job_name = split_job_path(job_path)`; `url = b["url"]`
- Folders have no build list and jobs without builds have an empty one; both contribute nothing. A response for a single job (no `jobs` key) gives `[]`.

## DATA

- `build_tree_query(100)` → `"?tree=jobs[fullName,url,builds[...]{0,100},jobs[...]]"` with exactly `MAX_DEPTH` occurrences of `jobs[`.
- `build_tree_query(101)` uses `allBuilds[...]{0,101}`.
- `flatten_builds` returns builds in tree order, unsorted. `select_builds` returns a new list.

## Tests (`test_builds.py`, no mocks, plain dicts)

- `map_status`: `building=True` → `running` (even with a result set); `building=False, result=None` → `unknown`; parametrised `SUCCESS/UNSTABLE/FAILURE/ABORTED/NOT_BUILT` → lowercase.
- `split_job_path`: `"job"` → `("", "job")`; `"A/B/job"` → `("A/B", "job")`; `"A/mb/feature%2Fx"` → `("A/mb", "feature%2Fx")`.
- `build_tree_query`: `builds` at 100, `allBuilds` at 101, `{0,N}` present, `jobs[` count == `MAX_DEPTH`.
- `flatten_builds`:
  - a top-level job
  - a folder containing a job
  - a multibranch project with branch jobs (`fullName` keeps `%2F`)
  - a job with no builds
  - an empty tree
  - a tree that uses `allBuilds`
  - check that the UTC timestamp is timezone-aware
  - check `duration_ms` is `None` for running and unknown builds
- `select_builds`:
  - merges across jobs newest first
  - truncates to `limit`
  - filters *after* truncation: a `failure` build older than the newest `limit` is excluded
  - `statuses=None` keeps everything
- `validate_statuses`: `None` and valid lists pass; `["failed"]` → `ValueError` whose message lists the valid values.
- `log_filename`: `"A/B/job", 5` → `"A_B_job_5.txt"`; `<>:"\|?*` replaced; `%2F` kept.
