param(
  [string]$ProjectRoot = 'D:\ModStudioAI\Milestone03'
)
$ErrorActionPreference = 'Stop'
$srcRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$required = @(
  @{ Relative = 'src\modstudio_m03.py'; ContentType='code' },
  @{ Relative = 'Run_M03.ps1'; ContentType='script' },
  @{ Relative = 'tests\test_pointer_v04.py'; ContentType='test' },
  @{ Relative = 'Fixtures\build_assets_v03.json'; ContentType='fixture' }
)
if (-not (Test-Path -LiteralPath $ProjectRoot -PathType Container)) {
  throw "Milestone03 project directory missing: $ProjectRoot"
}
$backup = Join-Path $ProjectRoot ('Backups\M03_PointerResolver_v04_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
foreach ($file in $required) {
  $src = Join-Path $srcRoot $file.Relative
  if (-not (Test-Path -LiteralPath $src -PathType Leaf)) { throw "Patch file missing: $src" }
}
foreach ($file in $required) {
  $target = Join-Path $ProjectRoot $file.Relative
  $source = Join-Path $srcRoot $file.Relative
  if (Test-Path -LiteralPath $target -PathType Leaf) {
    $saved = Join-Path $backup $file.Relative
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $saved) | Out-Null
    Copy-Item -LiteralPath $target -Destination $saved -Force
  }
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null
  Copy-Item -LiteralPath $source -Destination $target -Force
  Write-Host "Updated: $target"
}
Write-Host "Backup location (if existing files): $backup"
Write-Host 'Keep your .venv, AgentInput, PrivateEvaluation and existing Outputs unchanged.'
Write-Host 'Next: -Mode tests, -Mode scan-assets, -Mode provenance, -Mode baseline, -Mode evaluate.'
