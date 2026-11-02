param([string]$Target = 'D:\ModStudioAI\Milestone03')
$ErrorActionPreference = 'Stop'
$sourceDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$srcNew = Join-Path $sourceDir 'src\modstudio_m03.py'
$psNew = Join-Path $sourceDir 'Run_M03.ps1'
$testNew = Join-Path $sourceDir 'tests\test_scanner_v02.py'
foreach ($f in @($srcNew,$psNew,$testNew)) { if (-not (Test-Path -LiteralPath $f -PathType Leaf)) { throw "Missing patch source: $f" } }
$srcOld = Join-Path $Target 'src\modstudio_m03.py'
$psOld = Join-Path $Target 'Run_M03.ps1'
if (-not (Test-Path -LiteralPath $srcOld -PathType Leaf) -or -not (Test-Path -LiteralPath $psOld -PathType Leaf)) {
  throw "Not a Milestone03 installation: $Target"
}
$backup = Join-Path $Target ('Backups\M03_AssetFix_v02_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Force -Path $backup | Out-Null
Copy-Item -LiteralPath $srcOld -Destination (Join-Path $backup 'modstudio_m03.py')
Copy-Item -LiteralPath $psOld -Destination (Join-Path $backup 'Run_M03.ps1')
Copy-Item -LiteralPath $srcNew -Destination $srcOld -Force
Copy-Item -LiteralPath $psNew -Destination $psOld -Force
New-Item -ItemType Directory -Force -Path (Join-Path $Target 'tests') | Out-Null
Copy-Item -LiteralPath $testNew -Destination (Join-Path $Target 'tests\test_scanner_v02.py') -Force
Write-Host "Patch v0.2 installed into $Target" -ForegroundColor Green
Write-Host "Backups: $backup"
Write-Host 'Recommended: .\.venv\Scripts\python.exe -m pip install TypeTreeGeneratorAPI==0.0.10'
Write-Host 'Then run: tests -> scan-assets -> baseline -> evaluate.'