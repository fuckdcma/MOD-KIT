param(
  [string]$BaselineRunsDir='D:\ModStudioAI\Milestone04\Runs_LOCAL',
  [string]$EvidenceRunsDir='D:\ModStudioAI\Milestone04\Runs_EVIDENCE_GROUNDED_V10_LOCAL',
  [string]$PrivateDir='D:\ModStudioAI\Milestone04\PRIVATE_DO_NOT_UPLOAD',
  [string]$ScoreDir='D:\ModStudioAI\Milestone04\Runs_V10_REGRESSION_SCORE_V03_LOCAL',
  [string]$M03Root='D:\ModStudioAI\Milestone03'
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$root=Split-Path -Parent $PSScriptRoot
$scorer=Join-Path $root 'src\score_v10_regression.py'
$legacy=Join-Path $root 'vendor\m04_evaluate_v02.py'
$py=Join-Path $M03Root '.venv\Scripts\python.exe'
$frozen=Join-Path $M03Root 'src\modstudio_m03.py'
$truth=Join-Path $PrivateDir 'ground_truth_PRIVATE.json'
$fpPath=Join-Path $BaselineRunsDir 'evidence_fingerprint_public.json'
$cfgPath=Join-Path $EvidenceRunsDir 'experimental_config.json'
foreach ($p in @($scorer,$legacy,$py,$frozen,$truth,$fpPath,$cfgPath)) {
  if (-not (Test-Path -LiteralPath $p -PathType Leaf)) { throw "Missing expected input: $p" }
}
# Preserve old original, public MOD-KIT and private ground truth directories.
if (Test-Path -LiteralPath $ScoreDir) { throw "ScoreDir already exists. Do not overwrite: $ScoreDir" }
$scoreAbs=[IO.Path]::GetFullPath($ScoreDir).TrimEnd('\')
$baseAbs=[IO.Path]::GetFullPath($BaselineRunsDir).TrimEnd('\')
$runAbs=[IO.Path]::GetFullPath($EvidenceRunsDir).TrimEnd('\')
$privateAbs=[IO.Path]::GetFullPath($PrivateDir).TrimEnd('\')
if ($scoreAbs -ieq $baseAbs -or $scoreAbs -ieq $runAbs -or $scoreAbs -ieq $privateAbs -or
    $ScoreDir -match 'MOD-KIT|PRIVATE_DO_NOT_UPLOAD') { throw 'Choose an isolated private score directory.' }
$fp=Get-Content -LiteralPath $fpPath -Raw | ConvertFrom-Json
$cfg=Get-Content -LiteralPath $cfgPath -Raw | ConvertFrom-Json
if ($cfg.schema -ne 'modstudio.m04.evidence_grounded.v1.0-experimental.config') {
  throw 'Unexpected v1.0 experiment config schema.'
}
$frozenHash=(Get-FileHash -LiteralPath $frozen -Algorithm SHA256).Hash.ToLowerInvariant()
if ($frozenHash -ne $fp.m03_source_sha256 -or $frozenHash -ne $cfg.original_m03_sha256) {
  throw 'Frozen M03 code hash mismatch; do not score.'
}
foreach ($item in @(@('rea_evidence.jsonl','rea_input_sha256','rea_sha256'),
                     @('build_assets.json','assets_input_sha256','assets_sha256'))) {
  $base=Join-Path (Join-Path $BaselineRunsDir 'AgentInput') $item[0]
  $exp=Join-Path (Join-Path $EvidenceRunsDir 'AgentInput') $item[0]
  foreach ($p in @($base,$exp)) { if (-not (Test-Path -LiteralPath $p -PathType Leaf)) { throw "Missing input: $p" } }
  $one=(Get-FileHash $base -Algorithm SHA256).Hash.ToLowerInvariant()
  $two=(Get-FileHash $exp -Algorithm SHA256).Hash.ToLowerInvariant()
  $expected=if ($item[0] -eq 'rea_evidence.jsonl') { $fp.rea_input_sha256 } else { $fp.assets_input_sha256 }
  $fromCfg=if ($item[0] -eq 'rea_evidence.jsonl') { $cfg.rea_sha256 } else { $cfg.assets_sha256 }
  if ($one -ne $two -or $one -ne $expected -or $one -ne $fromCfg) { throw "Sealed input mismatched: $($item[0])" }
  Write-Host "SEALED INPUT SHA256 MATCH: $($item[0])"
}
# Check that all three reports really belong to the sealed M04 B experiment.
$reports=New-Object System.Collections.ArrayList
for ($i=1;$i -le 3;$i++) {
  $name='evidence_r{0:D2}.json' -f $i
  $path=Join-Path (Join-Path $EvidenceRunsDir 'Outputs') $name
  if (-not (Test-Path $path -PathType Leaf)) { throw "Missing report: $name" }
  $r=Get-Content -LiteralPath $path -Raw | ConvertFrom-Json
  if ($r.completed -ne $true -or $r.mode -ne 'agent' -or
      $r.strategy -ne 'evidence_grounded_v10_experimental' -or
      ([string]$r.assembly_sha256).ToLowerInvariant() -ne $fp.assembly_sha256) {
    throw "Invalid report mode, strategy, completion or build hash: $name"
  }
  [void]$reports.Add($path)
}
# The private answer file is read only after all preflight checks.
$stamp=[DateTime]::UtcNow.ToString('yyyyMMdd_HHmmss_fff')
$lock=Join-Path $PrivateDir ('locked_predictions_V10_REGRESSION_V03_'+$stamp)
$private=Join-Path $PrivateDir ('metrics_PRIVATE_V10_REGRESSION_V03_'+$stamp+'.json')
$aggregate=Join-Path $ScoreDir 'metrics_V10_REGRESSION_AGGREGATE_ONLY.json'
if ((Test-Path $lock) -or (Test-Path $private)) { throw 'Private output collision. Stop.' }
$cfgHash=(Get-FileHash $cfgPath -Algorithm SHA256).Hash.ToLowerInvariant()
$pyArgs=@($scorer,'--truth',$truth,'--fingerprint',$fpPath,
          '--lock-dir',$lock,'--out-private',$private,'--out-aggregate',$aggregate,
          '--v10-config-sha',$cfgHash,'--v10-agent-sha',([string]$cfg.v10_agent_sha256))
foreach ($path in $reports) { $pyArgs+=@('--report',$path) }
& $py @pyArgs
if ($LASTEXITCODE -ne 0) { throw 'Private regression scoring failed; do not publish. Preserve any created lock.' }
Write-Host "SAFE TO SHARE aggregate-only: $aggregate"
Write-Host "PRIVATE metrics (never upload): $private"
Write-Host "PRIVATE locked copies (never upload): $lock"
Write-Host 'B integration regression only. Not a new blind holdout or same-version M03 v0.8 benchmark.'
