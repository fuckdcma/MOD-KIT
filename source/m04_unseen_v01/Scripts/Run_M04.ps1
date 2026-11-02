param(
  [ValidateSet('rea','evidence','probe','guided','autonomous','seal')]
  [string]$Mode='evidence',
  [string]$BuildData='D:\ModStudioAI\Builds\UnityTextLabB\UnityTextLabB_Data',
  [string]$ReaDir='D:\ModStudioAI\Milestone04\REA_B',
  [string]$RunsDir='D:\ModStudioAI\Milestone04\Runs_LOCAL',
  [string]$M03Root='D:\ModStudioAI\Milestone03',
  [string]$PrivateDir='D:\ModStudioAI\Milestone04\PRIVATE_DO_NOT_UPLOAD',
  [string]$Server='http://127.0.0.1:11434',
  [string]$Model='qwen3.5:4b',
  [ValidateRange(1,5)][int]$Repeats=3,
  [ValidateRange(30,3600)][int]$TimeoutSeconds=600,
  [ValidateRange(64,8192)][int]$NumPredict=1280,
  [ValidateRange(1500,20000)][int]$BriefChars=3900
)
$ErrorActionPreference='Stop'
$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $M03Root '.venv\Scripts\python.exe'
$m03 = Join-Path $M03Root 'src\modstudio_m03.py'
$work = Join-Path $RunsDir 'AgentInput'
$out = Join-Path $RunsDir 'Outputs'
$reaEvidence = Join-Path $work 'rea_evidence.jsonl'
$assets = Join-Path $work 'build_assets.json'
$assembly = Join-Path $BuildData 'Managed\Assembly-CSharp.dll'
if (-not (Test-Path $py) -or -not (Test-Path $m03)) { throw "M03 v0.8 environment not found: $M03Root" }
if ($RunsDir -match 'MOD-KIT') { throw 'RunsDir must NOT be in the public MOD-KIT repository.' }
New-Item -Force -ItemType Directory -Path $RunsDir,$work,$out | Out-Null
function PythonM03([string[]]$Arguments) {
  & $py $m03 @Arguments
  if ($LASTEXITCODE -ne 0) { throw "M03 command failed: $($Arguments[0])" }
}
if ($Mode -eq 'rea') {
  if (-not (Test-Path $assembly)) { throw "Missing B assembly $assembly; build UnityTextLabB with Mono first." }
  if (-not (Get-Command rea -ErrorAction SilentlyContinue)) { throw 'REA executable not found. Activate the REA CLI used in M01–M03.' }
  New-Item -Force -ItemType Directory -Path $ReaDir | Out-Null
  $utf8 = New-Object System.Text.UTF8Encoding($false)
  foreach ($entry in @(@('inspect-managed-artifact','assembly_identity.json'),@('inspect-managed-members','members.json'))) {
    $cmd = $entry[0];$dest = Join-Path $ReaDir $entry[1]
    if (Test-Path $dest) { throw "Existing REA snapshot will NOT be overwritten: $dest" }
    $json = & rea $cmd $assembly --json | Out-String
    if ($LASTEXITCODE -ne 0 -or -not $json.Trim()) { throw "REA export failed: $cmd" }
    [IO.File]::WriteAllText($dest,$json,$utf8)
    Write-Host "REA evidence exported: $dest"
  }
  exit 0
}
if ($Mode -eq 'seal') {
  & $py (Join-Path $root 'src\m04_seal.py') --build-data $BuildData --private-dir $PrivateDir --out (Join-Path $RunsDir 'build_manifest_public.json')
  if ($LASTEXITCODE -ne 0) { throw 'Failed to seal the build hash manifest.' }
  exit 0
}
if ($Mode -eq 'probe') {
  PythonM03 @('probe','--server',$Server,'--model',$Model,'--transport','ollama','--timeout',[string]$TimeoutSeconds,'--out',(Join-Path $out 'ollama_probe.json'))
  exit 0
}
if ($Mode -eq 'evidence') {
  if (-not (Test-Path $assembly)) { throw "Missing Mono B assembly: $assembly" }
  $members = Join-Path $ReaDir 'members.json'
  $artifact = Join-Path $ReaDir 'assembly_identity.json'
  if (-not (Test-Path $members) -or -not (Test-Path $artifact)) { throw 'Run -Mode rea first.' }
  if ((Test-Path $reaEvidence) -or (Test-Path $assets)) { throw 'Existing B evidence found; create a NEW RunsDir for a new build (no overwrite).' }
  PythonM03 @('prepare','--members',$members,'--artifact',$artifact,'--out',$reaEvidence)
  PythonM03 @('scan-assets','--build-data',$BuildData,'--out',$assets)
  PythonM03 @('baseline','--rea',$reaEvidence,'--assets',$assets,'--out',(Join-Path $out 'baseline_r01.json'))
  PythonM03 @('provenance','--rea',$reaEvidence,'--assets',$assets,'--out',(Join-Path $out 'provenance_links.json'))
  $evidenceManifest = @{
    schema = 'modstudio.m04.evidence_fingerprint.v0.1'
    m03_source_sha256 = (Get-FileHash $m03 -Algorithm SHA256).Hash.ToLowerInvariant()
    assembly_sha256 = (Get-FileHash $assembly -Algorithm SHA256).Hash.ToLowerInvariant()
    rea_input_sha256 = (Get-FileHash $reaEvidence -Algorithm SHA256).Hash.ToLowerInvariant()
    assets_input_sha256 = (Get-FileHash $assets -Algorithm SHA256).Hash.ToLowerInvariant()
    private_truth_in_model_input = $false
  }
  $evidenceManifest | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $RunsDir 'evidence_fingerprint_public.json') -Encoding UTF8
  Write-Host 'Evidence prepared using FROZEN M03 code. Inspect scanner errors before running models.'
  exit 0
}
if (-not (Test-Path $reaEvidence) -or -not (Test-Path $assets)) { throw 'No B build evidence. Run -Mode evidence first.' }
for ($i=1; $i -le $Repeats; $i++) {
  $name = '{0}_r{1:D2}.json' -f $Mode,$i
  $target = Join-Path $out $name
  if (Test-Path $target) { throw "Existing prediction is frozen, cannot overwrite: $target" }
  Write-Host "Research run: $name"
  $cfg = @{
    run = $name; strategy = $Mode; model = $Model
    transport = 'ollama'; server = $Server; timeout_seconds = $TimeoutSeconds
    num_predict = $NumPredict; brief_chars = $BriefChars
    m03_source_sha256 = (Get-FileHash $m03 -Algorithm SHA256).Hash.ToLowerInvariant()
    rea_input_sha256 = (Get-FileHash $reaEvidence -Algorithm SHA256).Hash.ToLowerInvariant()
    assets_input_sha256 = (Get-FileHash $assets -Algorithm SHA256).Hash.ToLowerInvariant()
  }
  $cfg | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $out ($name + '.config.json')) -Encoding UTF8
  PythonM03 @('agent','--rea',$reaEvidence,'--assets',$assets,'--out',$target,
              '--server',$Server,'--model',$Model,'--strategy',$Mode,'--transport','ollama',
              '--timeout',[string]$TimeoutSeconds,'--num-predict',[string]$NumPredict,
              '--brief-chars',[string]$BriefChars)
  $result = Get-Content $target -Raw | ConvertFrom-Json
  if ($result.completed -ne $true) {
    Write-Warning "Run $name incomplete. Do NOT evaluate it; inspect its trace and retain it."
    break
  }
}
Write-Host "Model runs stored separately under: $out"
