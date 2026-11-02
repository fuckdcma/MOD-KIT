param(
  [ValidateSet('baseline','prepare','scan-assets','provenance','agent','evaluate','tests','probe')]
  [string]$Mode = 'baseline',
  [string]$Members = 'D:\ModStudioAI\Research\REA\members.json',
  [string]$Artifact = 'D:\ModStudioAI\Research\REA\assembly_identity.json',
  [string]$BuildData = 'D:\ModStudioAI\Builds\UnityTextLab\UnityTextLab_Data',
  [string]$Server = 'http://127.0.0.1:9931',
  [string]$Model = 'local-qwen',
  [ValidateSet('auto','ollama','openai')]
  [string]$Transport = 'auto',
  [int]$Steps = 12,
  [int]$TimeoutSeconds = 600,
  [int]$NumPredict = 1280,
  [int]$BriefChars = 3900,
  [ValidateSet('guided','autonomous')]
  [string]$Strategy = 'guided',
  [ValidateSet('baseline','agent','guided','autonomous')]
  [string]$EvaluateTarget = 'baseline',
  [switch]$ScanAssetsFirst
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$src = Join-Path $root 'src\modstudio_m03.py'
$evidence = Join-Path $root 'AgentInput\rea_evidence.jsonl'
$out = Join-Path $root 'Outputs'
New-Item -ItemType Directory -Force -Path $out | Out-Null
# Use only project-local Python 3.12; never fall back to `py -3` (may select Python 3.15).
$venvPython = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path $venvPython)) {
  throw 'Missing Python 3.12 environment. Run .\Setup_Python312.ps1 first.'
}
$exe = $venvPython
$prefix = @()
function Invoke-LocalPython ([string[]]$arguments) {
  & $exe @prefix $src @arguments
  if ($LASTEXITCODE -ne 0) { throw "Python command failed with exit code $LASTEXITCODE" }
}
if ($Mode -eq 'tests') {
  & $exe @prefix -m unittest discover -s (Join-Path $root 'tests') -v
  if ($LASTEXITCODE -ne 0) { throw 'Unit tests failed' }
} elseif ($Mode -eq 'prepare') {
  if (-not (Test-Path $Members)) { throw "Missing REA members file: $Members" }
  $args1 = @('prepare','--members',$Members,'--out',(Join-Path $out 'rea_evidence_new.jsonl'))
  if (Test-Path $Artifact) { $args1 += @('--artifact',$Artifact) }
  Invoke-LocalPython $args1
} elseif ($Mode -eq 'baseline') {
  $a = @('baseline','--rea',$evidence,'--out',(Join-Path $out 'baseline_static.json'))
  if (Test-Path (Join-Path $out 'build_assets.json')) { $a += @('--assets',(Join-Path $out 'build_assets.json')) }
  Invoke-LocalPython $a
} elseif ($Mode -eq 'scan-assets') {
  Invoke-LocalPython @('scan-assets','--build-data',$BuildData,'--out',(Join-Path $out 'build_assets.json'))
} elseif ($Mode -eq 'provenance') {
  $assetFile = Join-Path $out 'build_assets.json'
  if (-not (Test-Path $assetFile)) { throw 'Missing build_assets.json. Run scan-assets first.' }
  Invoke-LocalPython @('provenance','--rea',$evidence,'--assets',$assetFile,'--out',(Join-Path $out 'provenance_links.json'))
} elseif ($Mode -eq 'probe') {
  Invoke-LocalPython @('probe','--server',$Server,'--model',$Model,'--transport',$Transport,'--timeout',[string]$TimeoutSeconds,
    '--out',(Join-Path $out 'ollama_probe.json'))
} elseif ($Mode -eq 'agent') {
  if ($ScanAssetsFirst) {
    Invoke-LocalPython @('scan-assets','--build-data',$BuildData,'--out',(Join-Path $out 'build_assets.json'))
  }
  # Keep results for guided/autonomous strategies separate; preserve v0.5 qwen_agent.json.
  $outAgent = Join-Path $out ("qwen_agent_" + $Strategy + ".json")
  $a = @('agent','--rea',$evidence,'--out',$outAgent,'--server',$Server,'--model',$Model,'--transport',$Transport,'--steps',[string]$Steps,'--strategy',$Strategy,
    '--timeout',[string]$TimeoutSeconds,'--num-predict',[string]$NumPredict,'--brief-chars',[string]$BriefChars)
  if (Test-Path (Join-Path $out 'build_assets.json')) { $a += @('--assets',(Join-Path $out 'build_assets.json')) }
  Invoke-LocalPython $a
} elseif ($Mode -eq 'evaluate') {
  if ($EvaluateTarget -eq 'agent') {
    # Legacy v0.5 agent output
    $report = Join-Path $out 'qwen_agent.json'
    $evaluationOut = Join-Path $out 'evaluation_private_agent.json'
  } elseif ($EvaluateTarget -eq 'guided') {
    $report = Join-Path $out 'qwen_agent_guided.json'
    $evaluationOut = Join-Path $out 'evaluation_private_guided.json'
  } elseif ($EvaluateTarget -eq 'autonomous') {
    $report = Join-Path $out 'qwen_agent_autonomous.json'
    $evaluationOut = Join-Path $out 'evaluation_private_autonomous.json'
  } else {
    $report = Join-Path $out 'baseline_static.json'
    $evaluationOut = Join-Path $out 'evaluation_private.json'
  }
  if (-not (Test-Path $report)) { throw "Missing $EvaluateTarget observations: $report" }
  Invoke-LocalPython @('evaluate','--observations',$report,'--truth',(Join-Path $root 'PrivateEvaluation\ground_truth_v01.csv'),'--out',$evaluationOut)

}
Write-Host "Completed: $Mode"
