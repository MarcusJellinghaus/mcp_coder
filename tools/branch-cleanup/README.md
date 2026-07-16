# branch-cleanup

Find and delete local git branches that are already merged (including
GitHub squash-merges, which `git branch --merged` cannot detect on its own).

## Usage

Run from the root of a clone (operates on the current directory)...

```powershell
./tools/branch-cleanup/prune-branches.ps1                 # dry run: classify only
./tools/branch-cleanup/prune-branches.ps1 -Delete         # delete the merged branches
./tools/branch-cleanup/prune-branches.ps1 -Delete -Force  # also delete "needs review" branches
./tools/branch-cleanup/prune-branches.ps1 -Main master    # different base branch
```

...or run it from anywhere and point it at a clone with `-Path`:

```powershell
./tools/branch-cleanup/prune-branches.ps1 -Path C:\code\other-clone
./tools/branch-cleanup/prune-branches.ps1 -Path C:\code\other-clone -Delete
```

Or double-click / call the `.bat` launcher, which forwards the same flags
and picks whichever PowerShell is installed:

```bat
tools\branch-cleanup\prune-branches.bat
tools\branch-cleanup\prune-branches.bat -Delete
```

## How it classifies

- **Protected:** the current branch and `main` are never touched.
- **Merged / obsolete:** the branch tip is reachable from `main`
  (`git branch --merged`) **or** GitHub reports a merged PR for it.
  The PR check is what catches squash-merges.
- **Needs review:** a squash-merge is matched by branch *name*, so a new local
  branch that reuses a merged branch's name would look merged. If such a
  branch's tip commit is **newer** than the PR merge time, it is flagged and
  **kept** — deleted only with `-Force`. This protects unpushed work on a
  reused branch name.
- **Active:** everything else — kept.

Deletion uses `git branch -D` because squash-merged branches are not
"merged" from git's point of view (their commits never land in `main`).
Deleted refs remain recoverable via `git reflog` for ~30 days.

## Requirements

- **git** and **PowerShell** (`pwsh` or Windows PowerShell 5.1).
- **[`gh`](https://cli.github.com/) installed and authenticated** (`gh auth status`).
  Effectively **required** if you squash-merge: a squash collapses the branch
  into one new commit on `main`, so the branch's own commits never land there
  and `git branch --merged` cannot see it. The `gh` merged-PR lookup is the
  only path that detects squash-merged branches — without it the tool warns
  and detects almost nothing on a squash workflow.

The `gh` lookup covers the 1000 most recently merged PRs. If a merged branch
is older than that, it is classified **active** and kept (never wrongly
deleted) — clean those few up by hand.
