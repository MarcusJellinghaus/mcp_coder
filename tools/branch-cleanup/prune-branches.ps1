<#
.SYNOPSIS
  Classify local git branches as merged (obsolete) or active, and optionally delete the merged ones.

.DESCRIPTION
  A branch is considered MERGED if either:
    - its tip is reachable from the main branch (git branch --merged), OR
    - GitHub reports a merged PR for it (catches squash-merges, which --merged misses).

  The current branch and the main branch are always protected.

  Reused-name guard: a squash-merge is matched by branch name, so a new local
  branch that reuses a merged branch's name would look merged. If such a
  branch's tip commit is NEWER than the PR merge time, it is treated as
  NEEDS REVIEW and kept unless -Force is given.

.PARAMETER Delete
  Actually delete the merged branches (git branch -D). Without this flag, the script only reports.

.PARAMETER Force
  Also delete NEEDS REVIEW branches (tip newer than the merge). Off by default.

.PARAMETER Main
  Name of the main/base branch. Defaults to 'main'.

.PARAMETER Path
  Path to the repo to operate on. Defaults to the current directory.

.EXAMPLE
  ./tools/branch-cleanup/prune-branches.ps1                 # dry run in the current repo
  ./tools/branch-cleanup/prune-branches.ps1 -Delete         # delete the merged branches
  ./tools/branch-cleanup/prune-branches.ps1 -Delete -Force  # also delete NEEDS REVIEW branches
  ./tools/branch-cleanup/prune-branches.ps1 -Path C:\code\other-clone   # target another clone
#>
[CmdletBinding()]
param(
    [switch]$Delete,
    [string]$Main = 'main',
    [string]$Path = '.',
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path (Join-Path $Path '.git'))) {
    throw "Not a git repository: $Path"
}
Push-Location $Path
try {

# Refresh remote state and prune stale remote-tracking refs.
Write-Host "Fetching + pruning remotes..." -ForegroundColor Cyan
git fetch --all --prune | Out-Null

$current = (git rev-parse --abbrev-ref HEAD).Trim()
$hasGh   = [bool](Get-Command gh -ErrorAction SilentlyContinue)
if (-not $hasGh) {
    Write-Warning "gh CLI not found - squash-merged branches will NOT be detected."
}

# Branches whose tip is an ancestor of main (classic merge detection).
$mergedByGit = @(git branch --merged $Main --format '%(refname:short)') |
    Where-Object { $_ -and $_ -ne $Main }

# Merged-PR head names + latest merge time, one call (catches squash-merges).
$prMergedAt = @{}
if ($hasGh) {
    $prs = gh pr list --state merged --limit 1000 --json headRefName,mergedAt | ConvertFrom-Json
    foreach ($pr in $prs) {
        $h    = $pr.headRefName
        $when = [datetimeoffset]$pr.mergedAt
        if (-not $prMergedAt.ContainsKey($h) -or $when -gt $prMergedAt[$h]) {
            $prMergedAt[$h] = $when
        }
    }
}

$branches = @(git branch --format '%(refname:short)') |
    Where-Object { $_ -and $_ -ne $Main -and $_ -ne $current }

$merged     = [System.Collections.Generic.List[object]]::new()
$suspicious = [System.Collections.Generic.List[object]]::new()
$active     = [System.Collections.Generic.List[string]]::new()

foreach ($b in $branches) {
    if ($mergedByGit -contains $b) {
        $merged.Add([pscustomobject]@{ Branch = $b; Reason = 'merged into main' })
    }
    elseif ($prMergedAt.ContainsKey($b)) {
        # Squash-merge match by name. Guard the reused-name case: if the tip
        # commit post-dates the merge, the branch holds new work, not the
        # merged work - flag it instead of deleting.
        $tip = [datetimeoffset](git log -1 --format=%cI $b)
        if ($tip -gt $prMergedAt[$b]) {
            $suspicious.Add([pscustomobject]@{ Branch = $b; Reason = 'PR merged, but tip commit is NEWER - possible reused name' })
        }
        else {
            $merged.Add([pscustomobject]@{ Branch = $b; Reason = 'merged via PR (squash)' })
        }
    }
    else {
        $active.Add($b)
    }
}

Write-Host ""
Write-Host "ACTIVE (keep): $($active.Count)" -ForegroundColor Green
$active | ForEach-Object { Write-Host "  $_" }
Write-Host "  * $current  (current, protected)" -ForegroundColor DarkGray

Write-Host ""
Write-Host "MERGED / obsolete: $($merged.Count)" -ForegroundColor Yellow
$merged | ForEach-Object { Write-Host ("  {0,-55} {1}" -f $_.Branch, $_.Reason) }

if ($suspicious.Count -gt 0) {
    Write-Host ""
    Write-Host "NEEDS REVIEW - kept unless -Force: $($suspicious.Count)" -ForegroundColor Red
    $suspicious | ForEach-Object { Write-Host ("  {0,-55} {1}" -f $_.Branch, $_.Reason) }
}

if (-not $Delete) {
    Write-Host ""
    Write-Host "Dry run. Re-run with -Delete to remove the $($merged.Count) merged branch(es)." -ForegroundColor Cyan
    return
}

$toDelete = [System.Collections.Generic.List[object]]::new()
$toDelete.AddRange($merged)
if ($Force) { $toDelete.AddRange($suspicious) }

if ($toDelete.Count -eq 0) { Write-Host "`nNothing to delete." -ForegroundColor Green; return }

Write-Host ""
foreach ($m in $toDelete) {
    git branch -D $m.Branch
}
Write-Host "Deleted $($toDelete.Count) branch(es)." -ForegroundColor Green
if ($suspicious.Count -gt 0 -and -not $Force) {
    Write-Host "Kept $($suspicious.Count) needing review; re-run with -Force to delete those too." -ForegroundColor Yellow
}

}
finally {
    Pop-Location
}
