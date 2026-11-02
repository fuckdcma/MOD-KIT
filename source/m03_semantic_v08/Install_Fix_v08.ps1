param(
  [string]$ProjectRoot = 'D:\ModStudioAI\Milestone03'
)
$ErrorActionPreference='Stop'
$patchRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$manifest = Get-Content -LiteralPath (Join-Path $patchRoot 'SHA256_MANIFEST.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$targets = @('src\modstudio_m03.py','tests\test_semantics_v08.py')
if(-not (Test-Path -LiteralPath $ProjectRoot -PathType Container)) { throw "Milestone03 not found: $ProjectRoot" }
if(-not (Test-Path -LiteralPath (Join-Path $ProjectRoot '.venv\Scripts\python.exe') -PathType Leaf)) { throw 'Missing project-local Python .venv' }
foreach($item in $targets) {
  $src = Join-Path $patchRoot $item
  if(-not (Test-Path -LiteralPath $src -PathType Leaf)) { throw "Missing patch: $item" }
  $match = @($manifest.files | Where-Object { $_.path -eq $item.Replace('\','/') })
  if($match.Count -ne 1) { throw "Manifest record missing/duplicate for: $item" }
  $actual = (Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash.ToLowerInvariant()
  if($actual -ne $match[0].sha256) { throw "SHA256 mismatch: $item" }
}
$backup = Join-Path $ProjectRoot ('Backups\M03_Semantic_v08_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
$updated = @()
try {
  foreach($item in $targets) {
    $src = Join-Path $patchRoot $item
    $dst = Join-Path $ProjectRoot $item
    if(Test-Path -LiteralPath $dst -PathType Leaf) {
      $bak = Join-Path $backup $item
      New-Item -ItemType Directory -Force -Path (Split-Path -Parent $bak) | Out-Null
      Copy-Item -LiteralPath $dst -Destination $bak -Force
    }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst) | Out-Null
    Copy-Item -LiteralPath $src -Destination $dst -Force
    $updated += $item
    Write-Host "Patched: $item"
  }
} catch {
  foreach($item in $updated) {
    $dst=Join-Path $ProjectRoot $item
    $bak=Join-Path $backup $item
    if(Test-Path -LiteralPath $bak -PathType Leaf) { Copy-Item -LiteralPath $bak -Destination $dst -Force }
    elseif(Test-Path -LiteralPath $dst) { Remove-Item -LiteralPath $dst -Force }
  }
  throw
}
Write-Host "Backup: $backup"
Write-Host 'Python .venv, original Unity build, REA, private evaluation and Outputs unchanged.'
Write-Host 'Next: run tests, back up old guided reports, run guided AI and evaluate only when completed=True.'
