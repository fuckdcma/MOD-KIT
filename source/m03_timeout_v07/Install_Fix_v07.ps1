param(
  [string]$ProjectRoot = 'D:\ModStudioAI\Milestone03'
)
$ErrorActionPreference = 'Stop'
$patchRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$manifestPath = Join-Path $patchRoot 'SHA256_MANIFEST.json'
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) { throw 'SHA256_MANIFEST.json missing' }
$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
$targets = @('src\modstudio_m03.py','Run_M03.ps1','tests\test_timeout_v07.py','Fixtures\guided_v06_timeout.json')
if (-not (Test-Path -LiteralPath $ProjectRoot -PathType Container)) { throw "Milestone03 does not exist: $ProjectRoot" }
if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot '.venv\Scripts\python.exe') -PathType Leaf)) { throw 'Missing local Python .venv' }
foreach ($t in $targets) {
  $src = Join-Path $patchRoot $t
  if (-not (Test-Path -LiteralPath $src -PathType Leaf)) { throw "Patch file missing: $t" }
  $key = $t.Replace('\','/')
  $entries = @($manifest.files | Where-Object { $_.path -eq $key })
  if ($entries.Count -ne 1) { throw "Manifest missing or duplicate: $t" }
  $sha = (Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($sha -ne $entries[0].sha256) { throw "SHA256 mismatch for patch file: $t" }
}
$backup = Join-Path $ProjectRoot ('Backups\M03_OllamaTimeout_v07_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
$installed=@()
try {
  foreach($t in $targets) {
    $src = Join-Path $patchRoot $t
    $dst = Join-Path $ProjectRoot $t
    if(Test-Path -LiteralPath $dst -PathType Leaf) {
      $bak = Join-Path $backup $t
      New-Item -ItemType Directory -Force -Path (Split-Path -Parent $bak) | Out-Null
      Copy-Item -LiteralPath $dst -Destination $bak -Force
    }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst) | Out-Null
    Copy-Item -LiteralPath $src -Destination $dst -Force
    $installed += $t
    Write-Host "Patched: $t"
  }
} catch {
  foreach ($t in $installed) {
    $dst = Join-Path $ProjectRoot $t
    $bak = Join-Path $backup $t
    if(Test-Path -LiteralPath $bak -PathType Leaf) { Copy-Item -LiteralPath $bak -Destination $dst -Force }
    elseif(Test-Path -LiteralPath $dst -PathType Leaf) { Remove-Item -LiteralPath $dst -Force }
  }
  throw
}
Write-Host "Backup directory: $backup"
Write-Host 'No .venv / REA / Unity build / AgentInput / ground truth / Outputs were modified.'
Write-Host 'First: -Mode tests, then -Mode probe, then -Mode agent -Strategy guided.'
