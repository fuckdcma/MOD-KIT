param(
  [string]$EvidenceRunsDir = 'D:\ModStudioAI\Milestone04\Runs_LOCAL',
  [string]$NewRunsDir = 'D:\ModStudioAI\Milestone04\Runs_EVIDENCE_GROUNDED_V10_LOCAL',
  [string]$M03Root = 'D:\ModStudioAI\Milestone03',
  [string]$Server = 'http://127.0.0.1:11434',
  [string]$Model = 'qwen3.5:4b',
  [ValidateRange(1,5)][int]$Repeats = 3,
  [ValidateRange(30,1800)][int]$TimeoutSeconds = 900,
  [ValidateRange(64,4096)][int]$NumPredict = 512,
  [ValidateRange(1,20)][int]$BatchSize = 10,
  [switch]$PreflightOnly
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$root = Split-Path -Parent $PSScriptRoot
$agent = Join-Path $root 'src\m04_evidence_agent_v10.py'
$python = Join-Path $M03Root '.venv\Scripts\python.exe'
$frozen = Join-Path $M03Root 'src\modstudio_m03.py'
$fp = Join-Path $EvidenceRunsDir 'evidence_fingerprint_public.json'
$original = Join-Path $EvidenceRunsDir 'AgentInput'
if (-not (Test-Path $python -PathType Leaf) -or -not (Test-Path $frozen -PathType Leaf)) {
  throw 'Frozen M03 Python or source not found. Do NOT reinstall over M03.'
}
if (-not (Test-Path $agent -PathType Leaf) -or -not (Test-Path $fp -PathType Leaf)) {
  throw 'v1.0 agent or sealed M04 evidence fingerprint is missing.'
}
if ($Server -ne 'http://127.0.0.1:11434' -and $Server -ne 'http://localhost:11434') {
  throw 'Only the local Ollama endpoint is allowed.'
}
$seal = Get-Content $fp -Raw | ConvertFrom-Json
$frozenHash = (Get-FileHash $frozen -Algorithm SHA256).Hash.ToLowerInvariant()
if ($frozenHash -ne $seal.m03_source_sha256) { throw 'M03 frozen code fingerprint mismatch.' }
$sourceNames = @('rea_evidence.jsonl','build_assets.json')
$sourceHashes = @{}
foreach ($name in $sourceNames) {
  $f = Join-Path $original $name
  if (-not (Test-Path $f -PathType Leaf)) { throw "Missing original evidence: $name" }
  $sourceHashes[$name] = (Get-FileHash $f -Algorithm SHA256).Hash.ToLowerInvariant()
}
if (($sourceHashes['rea_evidence.jsonl'] -ne $seal.rea_input_sha256) -or
    ($sourceHashes['build_assets.json'] -ne $seal.assets_input_sha256)) {
  throw 'Original REA/UnityPy evidence changed since M04 seal. Stop.'
}
Write-Host 'FROZEN M03 SHA256 MATCH'
Write-Host 'SEALED REA/ASSET SHA256 MATCH'
$inputs = @('--m03',$frozen,'--rea',(Join-Path $original 'rea_evidence.jsonl'),
            '--assets',(Join-Path $original 'build_assets.json'))
Write-Host '=== Candidate inventory (no model, no private truth) ==='
& $python $agent inventory @inputs
if ($LASTEXITCODE -ne 0) { throw 'Evidence catalog inventory failed; nothing was run.' }
if ($PreflightOnly) { Write-Host 'Preflight-only success; no experimental outputs created.'; exit 0 }
if ($NewRunsDir -eq $EvidenceRunsDir -or $NewRunsDir -match 'MOD-KIT|PRIVATE_DO_NOT_UPLOAD') {
  throw 'NewRunsDir must be new/private and separate from baseline.'
}
if (Test-Path $NewRunsDir) { throw "Experiment folder exists; preserve it: $NewRunsDir" }
$work = Join-Path $NewRunsDir 'AgentInput'
$out = Join-Path $NewRunsDir 'Outputs'
New-Item -ItemType Directory -Path $work,$out -ErrorAction Stop | Out-Null
foreach ($name in $sourceNames) {
  $dst = Join-Path $work $name
  Copy-Item (Join-Path $original $name) $dst -ErrorAction Stop
  if ((Get-FileHash $dst -Algorithm SHA256).Hash.ToLowerInvariant() -ne $sourceHashes[$name]) {
    throw "Copied evidence hash mismatch: $name"
  }
  Write-Host "COPY SHA256 MATCH: $name"
}
Copy-Item $fp (Join-Path $NewRunsDir 'evidence_fingerprint_public.json')
$agentHash = (Get-FileHash $agent -Algorithm SHA256).Hash.ToLowerInvariant()
$config = [ordered]@{
  schema='modstudio.m04.evidence_grounded.v1.0-experimental.config'
  label='M04 B REGRESSION ONLY - NOT A NEW BLIND HOLDOUT'
  original_evidence_dir=$EvidenceRunsDir
  experiment_dir=$NewRunsDir
  original_m03_sha256=$frozenHash
  v10_agent_sha256=$agentHash
  rea_sha256=$sourceHashes['rea_evidence.jsonl']
  assets_sha256=$sourceHashes['build_assets.json']
  server=$Server
  model=$Model
  num_ctx=8192
  num_predict=$NumPredict
  batch_size=$BatchSize
  timeout_seconds=$TimeoutSeconds
  repeats=$Repeats
  run_label='Evidence-ID-gated selection, no answer key, static only'
}
$utf8 = New-Object System.Text.UTF8Encoding($false)
[IO.File]::WriteAllText((Join-Path $NewRunsDir 'experimental_config.json'),($config | ConvertTo-Json -Depth 5),$utf8)
for ($i = 1; $i -le $Repeats; $i++) {
  $name = ('evidence_r{0:D2}.json' -f $i)
  $dest = Join-Path $out $name
  if (Test-Path $dest) { throw "Frozen prediction exists: $dest" }
  Write-Host "M04 v1.0 experimental model selection: $name"
  & $python $agent agent --m03 $frozen `
    --rea (Join-Path $work 'rea_evidence.jsonl') `
    --assets (Join-Path $work 'build_assets.json') `
    --out $dest --server $Server --model $Model `
    --num-predict $NumPredict --num-ctx 8192 `
    --timeout $TimeoutSeconds --batch-size $BatchSize
  if ($LASTEXITCODE -ne 0) { throw 'Agent process failed; preserve experiment.' }
  $r = Get-Content $dest -Raw | ConvertFrom-Json
  Write-Host "Completed=$($r.completed); Observations=$(@($r.observations).Count); Candidates=$($r.evidence_catalog_count)"
  if ($r.completed -ne $true) { Write-Warning "Incomplete run $name; preserve report; stop."; break }
}
Write-Host "Experimental outputs (private): $out"
Write-Host 'Do NOT score against B as a fresh blind holdout; original v0.8/v0.9 remain untouched.'
