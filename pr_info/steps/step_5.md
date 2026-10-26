# Step 5 — SHA-pin the non-generated workflows

## LLM prompt
> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_5.md`. Replace every unpinned `uses:` in the listed workflows with the pin from the summary's "Resolved action pins" table. Change nothing else. Run pylint, pytest (`-n auto`, unit markers), mypy and `run_format_code`; all must pass. Produce one commit.

## WHERE
- `.github/workflows/ci.yml` (26 lines to pin; the `schneegans/dynamic-badges-action` line is already pinned)
- `.github/workflows/upstream-compat-check.yml` (3)
- `.github/workflows/publish.yml` (5)

## WHAT
Mapping (current → pinned):
| Current | Pinned |
|---|---|
| `actions/checkout@v7` | `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1` |
| `actions/setup-python@v7` | `actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0 # v7.1.0` |
| `astral-sh/setup-uv@v7` | `astral-sh/setup-uv@37802adc94f370d6bfd71619e3f0bf239e1f3b78 # v7.6.0` |
| `actions/upload-artifact@v7` | `actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9 # v7.0.2` |
| `actions/download-artifact@v8` | `actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333 # v8.0.2` |
| `pypa/gh-action-pypi-publish@release/v1` | `pypa/gh-action-pypi-publish@7245906fb61fa33a13554f9d5fb856fe61758086 # v1.14.3` |

## HOW
- Use `edit_file` with `replace_all=True` per file and per mapping row. Keep indentation and the `- ` list prefix.
- Plain `pip install` lines stay unpinned (decision).

## ALGORITHM (self-check after editing)
```
search_files(glob=".github/workflows/*.yml", pattern=r"^\s*(- )?uses:")
for each match:
    must match  uses: <owner>/<repo>[/<path>]@<40 hex> # v<digit>
```
Expected: 40 `uses:` lines in `.github/workflows/`, all pinned. That is 34 pinned in this step, 2 pinned by the generator in step 1, and 4 already pinned (the badge action plus 3 in `scorecard.yml`).

## Precondition
- If a `uses:` line is found that is not in the mapping table and is not already SHA-pinned, write one line to `pr_info/.blocked.txt` and stop.

## DATA
None.
