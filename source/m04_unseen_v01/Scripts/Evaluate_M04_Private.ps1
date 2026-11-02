param(
  [string]$PrivateDir='D:\ModStudioAI\Milestone04\PRIVATE_DO_NOT_UPLOAD',
  [string]$RunsDir='D:\ModStudioAI\Milestone04\Runs_LOCAL',
  [string]$Python='D:\ModStudioAI\Milestone03\.venv\Scripts\python.exe',
  [switch]$AllowPartial
)
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$source=Join-Path $root 'src\m04_evaluate.py'
$truth=Join-Path $PrivateDir 'ground_truth_PRIVATE.json'
$lock=Join-Path $PrivateDir ('locked_predictions_'+(Get-Date -Format 'yyyyMMdd_HHmmss'))
$privateOut=Join-Path $PrivateDir ('metrics_PRIVATE_'+(Get-Date -Format 'yyyyMMdd_HHmmss')+'.json')
$publicOut=Join-Path $RunsDir 'metrics_public_AGGREGATE_ONLY.json'
if (Test-Path $publicOut) { throw 'Public metrics already exist. Do not replace a prior benchmark; use a new RunsDir.' }
if (-not (Test-Path $truth)) { throw "Missing PRIVATE truth file: $truth" }
$evalArgs=@($source,'--truth',$truth,'--lock-dir',$lock,'--out-private',$privateOut,'--out-public',$publicOut)
$names=New-Object System.Collections.Generic.List[string]
foreach ($strategy in @('baseline','autonomous','guided')) {
  foreach ($f in @(Get-ChildItem (Join-Path $RunsDir 'Outputs') -Filter ($strategy+'_r??.json') -ErrorAction SilentlyContinue | Sort-Object Name)) {
    $name=$f.BaseName
    $names.Add($name)
    $evalArgs+=@('--run',($name+'='+$f.FullName))
  }
}
if (-not $AllowPartial) {
  foreach ($s in @('guided','autonomous')) {
    $n=@($names | Where-Object { $_ -like ($s+'_r??') }).Count
    if ($n -lt 3) { throw "Need 3 completed $s runs before scoring, found $n. Use -AllowPartial only for diagnostics." }
  }
}
if ($names.Count -eq 0) { throw 'No M04 reports to evaluate.' }
& $Python @evalArgs
if ($LASTEXITCODE -ne 0) { throw 'Private scoring rejected one or more runs. No scores should be published.' }
Write-Host "SAFE-TO-SHARE aggregate-only summary: $publicOut"
Write-Host "PRIVATE per-case evaluation (DO NOT UPLOAD): $privateOut"
