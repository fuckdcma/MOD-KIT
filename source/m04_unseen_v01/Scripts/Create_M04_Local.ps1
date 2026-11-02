param(
  [string]$UnityProject = 'D:\ModStudioAI\UnityLab\UnityTextLabB',
  [string]$PrivateDir = 'D:\ModStudioAI\Milestone04\PRIVATE_DO_NOT_UPLOAD'
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path (Join-Path $UnityProject 'ProjectSettings\ProjectVersion.txt'))) {
  throw "Create a separate Unity 6000.3.x project named UnityTextLabB in Unity Hub first: $UnityProject"
}
& py -3.12 (Join-Path $root 'src\m04_generate.py') --project $UnityProject --private-dir $PrivateDir
if ($LASTEXITCODE -ne 0) { throw 'M04 private lab generation failed. Inspect the error; no overwrite is allowed.' }
Write-Host 'NEXT: Open UnityTextLabB in Unity Hub, import TMP Essential Resources, then use Tools > Mod Studio AI > M04 > Generate Unseen Lab B Scene.'
Write-Host 'IMPORTANT: Never upload the generated project, its ProjectSettings/M04HoldoutLocal.json, seed, or private truth before the benchmark is frozen.'
