param(
  [string]$BaselineRunsDir='D:\ModStudioAI\Milestone04\Runs_LOCAL',
  [string]$Auto09RunsDir='D:\ModStudioAI\Milestone04\Runs_AUTONOMOUS_BOUNDED_V09_LOCAL',
  [string]$PrivateDir='D:\ModStudioAI\Milestone04\PRIVATE_DO_NOT_UPLOAD',
  [string]$ScoreDir='D:\ModStudioAI\Milestone04\Runs_MIXED_SCORE_V02_LOCAL',
  [string]$M03Root='D:\ModStudioAI\Milestone03'
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$root=Split-Path -Parent $PSScriptRoot
$scorer=Join-Path $root 'src\m04_evaluate_v02.py'
$py=Join-Path $M03Root '.venv\Scripts\python.exe'
$frozen=Join-Path $M03Root 'src\modstudio_m03.py'
$truth=Join-Path $PrivateDir 'ground_truth_PRIVATE.json'
$fingerprint=Join-Path $BaselineRunsDir 'evidence_fingerprint_public.json'
$autoConfig=Join-Path $Auto09RunsDir 'experimental_config.json'

foreach ($file in @($scorer,$py,$frozen,$truth,$fingerprint,$autoConfig)) {
  if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "Missing required input: $file" }
}
$cmp1=[IO.Path]::GetFullPath($ScoreDir).TrimEnd('\')
$cmp2=[IO.Path]::GetFullPath($BaselineRunsDir).TrimEnd('\')
$cmp3=[IO.Path]::GetFullPath($Auto09RunsDir).TrimEnd('\')
$cmp4=[IO.Path]::GetFullPath($PrivateDir).TrimEnd('\')
if ($cmp1 -ieq $cmp2 -or $cmp1 -ieq $cmp3 -or $cmp1 -ieq $cmp4 -or
    $ScoreDir -match 'MOD-KIT|PRIVATE_DO_NOT_UPLOAD') {
  throw 'ScoreDir must be separate from original runs, public GitHub and private answers.'
}
if (Test-Path -LiteralPath $ScoreDir) { throw "Score folder exists. Do not overwrite: $ScoreDir" }
$fp=Get-Content -LiteralPath $fingerprint -Raw | ConvertFrom-Json
$cfg=Get-Content -LiteralPath $autoConfig -Raw | ConvertFrom-Json
$sha=(Get-FileHash -LiteralPath $frozen -Algorithm SHA256).Hash.ToLowerInvariant()
if ($sha -ne $fp.m03_source_sha256 -or $sha -ne $cfg.baseline_m03_v08_sha256) {
  throw 'Frozen M03 v0.8 code SHA mismatch; stop before scoring.'
}
foreach ($item in @(@('rea_evidence.jsonl','rea_input_sha256','rea_sha256'),
                     @('build_assets.json','assets_input_sha256','assets_sha256'))) {
  $base=Join-Path (Join-Path $BaselineRunsDir 'AgentInput') $item[0]
  $trial=Join-Path (Join-Path $Auto09RunsDir 'AgentInput') $item[0]
  foreach ($p in @($base,$trial)) {
    if (-not (Test-Path -LiteralPath $p -PathType Leaf)) { throw "Missing evidence: $p" }
  }
  $baseHash=(Get-FileHash -LiteralPath $base -Algorithm SHA256).Hash.ToLowerInvariant()
  $trialHash=(Get-FileHash -LiteralPath $trial -Algorithm SHA256).Hash.ToLowerInvariant()
  $fpHash = if ($item[0] -eq 'rea_evidence.jsonl') { $fp.rea_input_sha256 } else { $fp.assets_input_sha256 }
  $cfgHash = if ($item[0] -eq 'rea_evidence.jsonl') { $cfg.rea_sha256 } else { $cfg.assets_sha256 }
  if ($baseHash -ne $fpHash -or $trialHash -ne $cfgHash -or $baseHash -ne $trialHash) {
    throw "Cross-version evidence hash mismatch: $($item[0])"
  }
  Write-Host "INPUT MATCH: $($item[0])"
}

# Avoid opening the private ground truth until every report is prevalidated.
$reports=New-Object System.Collections.ArrayList
[void]$reports.Add(@{ Name='baseline_r01'; Path=(Join-Path $BaselineRunsDir 'Outputs\baseline_r01.json'); Mode='baseline'; Strategy='static_baseline' })
for ($i=1;$i -le 3;$i++) {
  $name='guided_r{0:D2}' -f $i
  [void]$reports.Add(@{ Name=$name; Path=(Join-Path $BaselineRunsDir ('Outputs\'+$name+'.json')); Mode='agent'; Strategy='guided' })
}
for ($i=1;$i -le 3;$i++) {
  $name='autonomous_r{0:D2}' -f $i
  [void]$reports.Add(@{ Name=$name; Path=(Join-Path $Auto09RunsDir ('Outputs\'+$name+'.json')); Mode='agent'; Strategy='autonomous' })
}
foreach ($report in $reports) {
  if (-not (Test-Path -LiteralPath $report.Path -PathType Leaf)) { throw "Missing completed run: $($report.Name)" }
  $data=Get-Content -LiteralPath $report.Path -Raw | ConvertFrom-Json
  if ($data.completed -ne $true -or $data.mode -ne $report.Mode -or $data.strategy -ne $report.Strategy) {
    throw "Incomplete/mismatched report. No scoring: $($report.Name)"
  }
  if (([string]$data.assembly_sha256).ToLowerInvariant() -ne $fp.assembly_sha256) {
    throw "Assembly hash mismatch in $($report.Name)"
  }
}

$stamp=[DateTime]::UtcNow.ToString('yyyyMMdd_HHmmss_fff')
$lock=Join-Path $PrivateDir ('locked_predictions_MIXED_V02_'+$stamp)
$private=Join-Path $PrivateDir ('metrics_PRIVATE_MIXED_V02_'+$stamp+'.json')
$public=Join-Path $ScoreDir 'metrics_MIXED_V08_GUIDED_V09_AUTO_AGGREGATE_ONLY.json'
if ((Test-Path -LiteralPath $lock) -or (Test-Path -LiteralPath $private)) { throw 'Private lock/output exists. Stop.' }
New-Item -ItemType Directory -Path $ScoreDir -ErrorAction Stop | Out-Null
$argsList=@($scorer,'--truth',$truth,'--lock-dir',$lock,'--out-private',$private,'--out-public',$public)
foreach ($report in $reports) { $argsList+=@('--run',($report.Name+'='+$report.Path)) }
& $py @argsList
if ($LASTEXITCODE -ne 0) { throw 'Scoring failed. Keep any created paths; do not publish.' }
Write-Host ('M04 mixed-version EXPERIMENTAL aggregate: '+$public)
Write-Host ('PRIVATE results (never upload): '+$private)
Write-Host ('PRIVATE SHA-locked prediction copies: '+$lock)
Write-Host 'Original failed v0.8 Autonomous and 2560 retry remain excluded; never report this as original v0.8 3/3 benchmark.'
