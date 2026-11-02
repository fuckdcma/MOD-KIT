param(
  [string]$ProjectRoot = 'D:\ModStudioAI\Milestone03'
)
$ErrorActionPreference = 'Stop'
$patchRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$manifestFile = Join-Path $patchRoot 'SHA256_MANIFEST.json'
if (-not (Test-Path -LiteralPath $manifestFile -PathType Leaf)) { throw 'Missing SHA256_MANIFEST.json' }
$manifest = Get-Content -LiteralPath $manifestFile -Raw -Encoding UTF8 | ConvertFrom-Json
$targets = @('src\modstudio_m03.py','Run_M03.ps1','tests\test_guided_v06.py')
if (-not (Test-Path -LiteralPath $ProjectRoot -PathType Container)) { throw "Milestone03 not found: $ProjectRoot" }
if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot '.venv\Scripts\python.exe') -PathType Leaf)) { throw 'Local Python .venv is required' }
foreach ($t in $targets) {
  $s = Join-Path $patchRoot $t
  if (-not (Test-Path -LiteralPath $s -PathType Leaf)) { throw "Missing patch file: $s" }
  $m = @($manifest.files | Where-Object { $_.path -eq ($t.Replace('\','/')) })
  if ($m.Count -ne 1) { throw "Manifest entry missing or duplicated: $t" }
  $hash = (Get-FileHash -LiteralPath $s -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($hash -ne $m[0].sha256) { throw "SHA256 mismatch: $t" }
}
$backup = Join-Path $ProjectRoot ('Backups\M03_GuidedAgent_v06_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
$updated = @()
try {
  foreach ($t in $targets) {
    $src = Join-Path $patchRoot $t
    $dst = Join-Path $ProjectRoot $t
    if (Test-Path -LiteralPath $dst -PathType Leaf) {
      $bak = Join-Path $backup $t
      New-Item -ItemType Directory -Force -Path (Split-Path -Parent $bak) | Out-Null
      Copy-Item -LiteralPath $dst -Destination $bak -Force
    }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst) | Out-Null
    Copy-Item -LiteralPath $src -Destination $dst -Force
    $updated += $t
    Write-Host "Patched: $t"
  }
} catch {
  foreach ($t in $updated) {
    $dst = Join-Path $ProjectRoot $t
    $bak = Join-Path $backup $t
    if (Test-Path -LiteralPath $bak -PathType Leaf) { Copy-Item -LiteralPath $bak -Destination $dst -Force }
    elseif (Test-Path -LiteralPath $dst -PathType Leaf) { Remove-Item -LiteralPath $dst -Force }
  }
  throw
}
Write-Host "Backup directory: $backup"
Write-Host 'No changes to .venv, Unity build, REA, agent inputs, private ground truth or existing Outputs.'
Write-Host 'Run tests with powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode tests'
Write-Host 'Run guided Agent with -Mode agent -Strategy guided -Transport ollama -Server http://127.0.0.1:11434 -Model qwen3.5:4b'
