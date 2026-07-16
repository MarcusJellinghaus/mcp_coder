<#
.SYNOPSIS
  Classify local git branches as merged (obsolete) or active, and optionally delete the merged ones.

.DESCRIPTION
  A branch is considered MERGED if either:
    - its tip is reachable from the main branch (git branch --merged), OR
    - GitHub reports a merged PR for it (catches squash-merges, which --merged misses).

  The current branch and the main branch are always protected.

.PARAMETER Delete
  Actually delete the merged branches (git branch -D). Without this flag, the script only reports.

.PARAMETER Main
  Name of the main/base branch. Defaults to 'main'.

.PARAMETER Path
  Path to the repo to operate on. Defaults to the current directory.

.EXAMPLE
  ./tools/branch-cleanup/prune-branches.ps1            # dry run in the current repo
  ./tools/branch-cleanup/prune-branches.ps1 -Delete    # delete the merged branches
  ./tools/branch-cleanup/prune-branches.ps1 -Path C:\code\other-clone   # target another clone
#>
[CmdletBinding()]
param(
    [switch]$Delete,
    [string]$Main = 'main',
    [string]$Path = '.'
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

# Head-branch names of merged PRs, fetched in one call (catches squash-merges).
$mergedPrHeads = @()
if ($hasGh) {
    $mergedPrHeads = @(gh pr list --state merged --limit 500 --json headRefName --jq '.[].headRefName')
}

$branches = @(git branch --format '%(refname:short)') |
    Where-Object { $_ -and $_ -ne $Main -and $_ -ne $current }

$merged = [System.Collections.Generic.List[object]]::new()
$active = [System.Collections.Generic.List[string]]::new()

foreach ($b in $branches) {
    $reason = $null
    if ($mergedByGit -contains $b) {
        $reason = 'merged into main'
    }
    elseif ($mergedPrHeads -contains $b) {
        $reason = 'merged via PR (squash)'
    }

    if ($reason) { $merged.Add([pscustomobject]@{ Branch = $b; Reason = $reason }) }
    else         { $active.Add($b) }
}

Write-Host ""
Write-Host "ACTIVE (keep): $($active.Count)" -ForegroundColor Green
$active | ForEach-Object { Write-Host "  $_" }
Write-Host "  * $current  (current, protected)" -ForegroundColor DarkGray

Write-Host ""
Write-Host "MERGED / obsolete: $($merged.Count)" -ForegroundColor Yellow
$merged | ForEach-Object { Write-Host ("  {0,-55} {1}" -f $_.Branch, $_.Reason) }

if (-not $Delete) {
    Write-Host ""
    Write-Host "Dry run. Re-run with -Delete to remove the $($merged.Count) merged branch(es)." -ForegroundColor Cyan
    return
}

if ($merged.Count -eq 0) { Write-Host "`nNothing to delete." -ForegroundColor Green; return }

Write-Host ""
foreach ($m in $merged) {
    git branch -D $m.Branch
}
Write-Host "Deleted $($merged.Count) branch(es)." -ForegroundColor Green

}
finally {
    Pop-Location
}
