# branch-cleanup

Find and delete local git branches that are already merged (including
GitHub squash-merges, which `git branch --merged` cannot detect on its own).

## Usage

Run from the root of any clone of the repo:

```powershell
./tools/branch-cleanup/prune-branches.ps1          # dry run: classify only
./tools/branch-cleanup/prune-branches.ps1 -Delete  # delete the merged branches
./tools/branch-cleanup/prune-branches.ps1 -Main master   # different base branch
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
- **Active:** everything else — kept.

Deletion uses `git branch -D` because squash-merged branches are not
"merged" from git's point of view (their commits never land in `main`).

## Requirements

- PowerShell (`pwsh` or Windows PowerShell 5.1).
- [`gh`](https://cli.github.com/) installed and authenticated (`gh auth status`).
  Without it the script still runs but warns and can only detect true
  fast-forward / merge-commit branches, missing squash-merges.
