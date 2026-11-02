param(
  [string]$SourceRunsDir='D:\ModStudioAI\Milestone04\Runs_LOCAL',
  [string]$NewRunsDir='D:\ModStudioAI\Milestone04\Runs_AUTONOMOUS_BOUNDED_V09_LOCAL',
  [string]$M03Root='D:\ModStudioAI\Milestone03',
  [string]$Previous2560RunsDir='D:\ModStudioAI\Milestone04\Runs_AUTONOMOUS_2560_LOCAL',
  [string]$Server='http://127.0.0.1:11434',
  [string]$Model='qwen3.5:4b',
  [ValidateRange(1,5)][int]$Repeats=3,
  [ValidateRange(64,4096)][int]$NumPredict=2560,
  [ValidateRange(30,1800)][int]$TimeoutSeconds=900
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$root=Split-Path -Parent $PSScriptRoot
$agent=Join-Path $root 'src\modstudio_m03_v09.py'
$python=Join-Path $M03Root '.venv\Scripts\python.exe'
$frozen=Join-Path $M03Root 'src\modstudio_m03.py'
$srcIn=Join-Path $SourceRunsDir 'AgentInput'
$fp=Join-Path $SourceRunsDir 'evidence_fingerprint_public.json'
if (-not (Test-Path $python -PathType Leaf) -or -not (Test-Path $frozen -PathType Leaf)) {
  throw 'Frozen M03 v0.8 environment missing; do not install over it.'
}
if (-not (Test-Path $agent -PathType Leaf)) { throw 'M04 v0.9 source missing.' }
if (-not (Test-Path $fp -PathType Leaf)) { throw 'Original M04 evidence fingerprint missing.' }
if ($NewRunsDir -eq $SourceRunsDir -or $NewRunsDir -match 'MOD-KIT' -or $NewRunsDir -match 'PRIVATE_DO_NOT_UPLOAD') {
  throw 'NewRunsDir must be separate from baseline, public Git repository and private truth.'
}
if (Test-Path $NewRunsDir) { throw "Experiment directory already exists. Preserve it: $NewRunsDir" }
$meta=Get-Content -LiteralPath $fp -Raw | ConvertFrom-Json
$frozenSha=(Get-FileHash -LiteralPath $frozen -Algorithm SHA256).Hash.ToLowerInvariant()
if ($frozenSha -ne $meta.m03_source_sha256) { throw 'Frozen M03 source changed since evidence preparation. Stop.' }
$inputs=@('rea_evidence.jsonl','build_assets.json')
foreach ($name in $inputs) {
  if (-not (Test-Path (Join-Path $srcIn $name) -PathType Leaf)) { throw "Original source evidence missing: $name" }
}
$rootRun=New-Item -ItemType Directory -Path $NewRunsDir -ErrorAction Stop
$work=Join-Path $NewRunsDir 'AgentInput'
$out=Join-Path $NewRunsDir 'Outputs'
New-Item -ItemType Directory -Path $work,$out -Force | Out-Null
$hashes=@{}
foreach ($name in $inputs) {
  $src=Join-Path $srcIn $name
  $dst=Join-Path $work $name
  Copy-Item -LiteralPath $src -Destination $dst -ErrorAction Stop
  $sha=(Get-FileHash $src -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($sha -ne (Get-FileHash $dst -Algorithm SHA256).Hash.ToLowerInvariant()) { throw "Evidence copy SHA mismatch: $name" }
  $hashes[$name]=$sha
  Write-Host "MATCH SHA256: $name"
}
if ($hashes['rea_evidence.jsonl'] -ne $meta.rea_input_sha256 -or
    $hashes['build_assets.json'] -ne $meta.assets_input_sha256) {
  throw 'Original M04 evidence no longer matches sealed fingerprint. Stop.'
}
Copy-Item -LiteralPath $fp -Destination (Join-Path $NewRunsDir 'evidence_fingerprint_public.json')
$agentSha=(Get-FileHash -LiteralPath $agent -Algorithm SHA256).Hash.ToLowerInvariant()
$config=[ordered]@{
  schema='modstudio.m04.autonomous_bounded_v09.config.v1'
  label='EXPERIMENTAL RECOVERY - NOT ORIGINAL BASELINE'
  baseline_runs_dir=$SourceRunsDir
  new_runs_dir=$NewRunsDir
  baseline_m03_v08_sha256=$frozenSha
  experimental_agent_sha256=$agentSha
  rea_sha256=$hashes['rea_evidence.jsonl']
  assets_sha256=$hashes['build_assets.json']
  model=$Model
  server=$Server
  strategy='autonomous'
  num_predict=$NumPredict
  num_ctx=8192
  max_steps=16
  evidence_ledger_char_budget=5400
  timeout_seconds=$TimeoutSeconds
  repeats_requested=$Repeats
  original_failed_r01_sha256=''
  previous_2560_failed_r01_sha256=''
}
$first=Join-Path $SourceRunsDir 'Outputs\autonomous_r01.json'
if (Test-Path $first -PathType Leaf) {
  $config['original_failed_r01_sha256']=(Get-FileHash $first -Algorithm SHA256).Hash.ToLowerInvariant()
}
$second=Join-Path $Previous2560RunsDir 'Outputs\autonomous_r01.json'
if (Test-Path $second -PathType Leaf) {
  $config['previous_2560_failed_r01_sha256']=(Get-FileHash $second -Algorithm SHA256).Hash.ToLowerInvariant()
}
$utf8=New-Object System.Text.UTF8Encoding($false)
[IO.File]::WriteAllText((Join-Path $NewRunsDir 'experimental_config.json'),($config | ConvertTo-Json -Depth 5),$utf8)
for ($i=1; $i -le $Repeats; $i++) {
  $name=('autonomous_r{0:D2}.json' -f $i)
  $dest=Join-Path $out $name
  if (Test-Path $dest) { throw "Frozen result exists, refusing overwrite: $dest" }
  Write-Host "M04 v0.9 experimental research: $name"
  & $python $agent agent `
     --rea (Join-Path $work 'rea_evidence.jsonl') `
     --assets (Join-Path $work 'build_assets.json') `
     --out $dest --strategy autonomous --transport ollama `
     --server $Server --model $Model --steps 16 `
     --timeout "$TimeoutSeconds" --num-predict "$NumPredict"
  if ($LASTEXITCODE -ne 0) { throw 'Experimental agent process failed; preserve experiment directory.' }
  $result=Get-Content -LiteralPath $dest -Raw | ConvertFrom-Json
  $count=@($result.observations).Count
  Write-Host "completed=$($result.completed); observations=$count"
  if ($result.completed -ne $true) {
    Write-Warning "Incomplete $name. Preserve all outputs; do not score this run."
    break
  }
}
Write-Host "Original M03 v0.8 results and failure unchanged. Experimental output: $out"
