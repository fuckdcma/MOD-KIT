param(
  [string]$ModStudioRoot = 'D:\ModStudioAI',
  [switch]$Push
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
if (-not (Test-Path (Join-Path $repo '.git'))) { throw 'Script must run inside a cloned MOD-KIT Git repository.' }
$remote = (& git -C $repo remote get-url origin 2>$null)
if ($LASTEXITCODE -ne 0 -or $remote -notmatch '(^|[:/])fuckdcma/MOD-KIT(\.git)?$') { throw "Unexpected git remote: $remote" }
$dst = Join-Path $repo 'local_snapshot'
New-Item -ItemType Directory -Force -Path $dst | Out-Null
$maps = @(
  @{ Source = (Join-Path $ModStudioRoot 'Milestone03'); Dest='milestone03'; Filter='code' },
  @{ Source = (Join-Path $ModStudioRoot 'Research\REA'); Dest='rea'; Filter='code' },
  @{ Source = (Join-Path $ModStudioRoot 'UnityLab\UnityTextLab\Assets\Scripts'); Dest='unitylab/Assets/Scripts'; Filter='code' },
  @{ Source = (Join-Path $ModStudioRoot 'UnityLab\UnityTextLab\Assets\Editor'); Dest='unitylab/Assets/Editor'; Filter='code' },
  @{ Source = (Join-Path $ModStudioRoot 'UnityLab\UnityTextLab\Assets\Resources'); Dest='unitylab/Assets/Resources'; Filter='code' }
)
$extensions = @('.py','.ps1','.cs','.json','.jsonl','.csv','.txt','.md','.yaml','.yml','.meta')
foreach ($map in $maps) {
  if (-not (Test-Path $map.Source)) { Write-Warning "Not found: $($map.Source)"; continue }
  Get-ChildItem -LiteralPath $map.Source -Recurse -File | ForEach-Object {
    $srcFile = $_
    if ($srcFile.FullName -match '[\\/](\.venv|venv|Library|Temp|Obj|Logs|UserSettings|node_modules|__pycache__|\.git)[\\/]') { return }
    if ($extensions -notcontains $srcFile.Extension.ToLowerInvariant()) { return }
    if ($srcFile.Length -gt 100MB) { Write-Warning "Skip large: $($srcFile.FullName)"; return }
    $rel = $srcFile.FullName.Substring($map.Source.TrimEnd('\').Length).TrimStart('\')
    $target = Join-Path (Join-Path $dst $map.Dest) $rel
    New-Item -ItemType Directory -Force -Path (Split-Path $target) | Out-Null
    Copy-Item -LiteralPath $srcFile.FullName -Destination $target -Force
  }
}
Write-Host "Local artifact source staged under: $dst"
Write-Host 'Inspect changes, especially any passwords or proprietary game assets:'
& git -C $repo status --short
if (-not $Push) { Write-Host 'Preview only. Re-run with -Push to explicitly approve commit and push.'; exit 0 }
Write-Host 'Repository is PUBLIC; all staged files will be visible to everyone.'
$confirmation = Read-Host 'Type PUBLISH to commit and push'
if ($confirmation -cne 'PUBLISH') { Write-Host 'Cancelled.'; exit 1 }
& git -C $repo add local_snapshot
& git -C $repo diff --cached --stat
& git -C $repo commit -m 'chore: sync local Mod Studio AI source artifacts'
if ($LASTEXITCODE -ne 0) { throw 'Git commit failed.' }
& git -C $repo push origin main
if ($LASTEXITCODE -ne 0) { throw 'Git push failed; local commit remains available.' }
Write-Host 'Pushed local snapshot.'
