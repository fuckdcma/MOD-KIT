param(
  [string]$UnityProject = 'D:\ModStudioAI\UnityLab\UnityTextLabB'
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$project = (Resolve-Path $UnityProject -ErrorAction Stop).Path
if ((Split-Path $project -Leaf) -cne 'UnityTextLabB') { throw 'Safety: expected the UnityTextLabB project, never UnityTextLab.' }
$original = Join-Path $project 'Assets\M04\Runtime\M04LabRuntime.cs'
$originalMeta = "$original.meta"
$builder = Join-Path $project 'Assets\Editor\M04LabBuilder.cs'
$privateSpec = Join-Path $project 'ProjectSettings\M04HoldoutLocal.json'
$scene = Join-Path $project 'Assets\M04\Scenes\UnseenLabB.unity'
$runtime = Join-Path $project 'Assets\M04\Runtime'
$editor = Join-Path $project 'Assets\Editor'
foreach ($file in @($builder,$privateSpec,$scene)) {
  if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "Missing M04 file: $file" }
}
if (-not (Test-Path -LiteralPath $original -PathType Leaf)) {
  throw 'M04LabRuntime.cs not found; patch may already be applied. Do not overwrite existing scene/scripts.'
}
if (Get-Process -Name Unity -ErrorAction SilentlyContinue) {
  throw 'Close Unity Editor completely, then rerun the installer to avoid reimporting half-written scripts.'
}
$needle = 'var report = BuildPipeline.BuildPlayer(options);'
$guard = 'M04RepairMissingScripts.ValidateBeforeBuild();'
$builderText = [System.IO.File]::ReadAllText($builder)
if (-not $builderText.Contains($needle)) { throw 'M04LabBuilder.cs layout changed. Cannot safely inject build guard.' }
if ($builderText.Contains($guard)) { throw 'Build guard already present. Patch is probably already installed.' }
$targets = @(
  'M04Table.cs', 'M04TableReader.cs', 'M04JsonReader.cs', 'M04JsonPayload.cs'
)
foreach ($name in $targets) {
  if (Test-Path -LiteralPath (Join-Path $runtime $name)) { throw "Refusing to overwrite existing script: $name" }
}
$repairName = 'M04RepairMissingScripts.cs'
if (Test-Path -LiteralPath (Join-Path $editor $repairName)) { throw 'Refusing to overwrite existing Editor repair script.' }
$projectSettings = Join-Path $project 'ProjectSettings'
$backup = Join-Path $projectSettings ('M04PatchBackups\v02_' + [DateTime]::UtcNow.ToString('yyyyMMdd_HHmmss_fff'))
New-Item -ItemType Directory -Force -Path $backup | Out-Null
Copy-Item -LiteralPath $original -Destination (Join-Path $backup 'M04LabRuntime.cs')
if (Test-Path $originalMeta) { Copy-Item -LiteralPath $originalMeta -Destination (Join-Path $backup 'M04LabRuntime.cs.meta') }
Copy-Item -LiteralPath $builder -Destination (Join-Path $backup 'M04LabBuilder.cs')
foreach ($name in $targets) {
  Copy-Item -LiteralPath (Join-Path $root "UnityPatch\Assets\M04\Runtime\$name") -Destination (Join-Path $runtime $name)
}
Copy-Item -LiteralPath (Join-Path $root "UnityPatch\Assets\Editor\$repairName") -Destination (Join-Path $editor $repairName)
# Remove the ambiguous old script after a full backup; the scene repair will recreate the table asset and reader refs.
Remove-Item -LiteralPath $original
if (Test-Path $originalMeta) { Remove-Item -LiteralPath $originalMeta }
$builderText = $builderText.Replace($needle, ($guard + "`r`n        " + $needle))
[System.IO.File]::WriteAllText($builder,[string]$builderText,(New-Object System.Text.UTF8Encoding($false)))
Write-Host '[M04] Installed unambiguous MonoBehaviour/ScriptableObject scripts and build guard.'
Write-Host ('[M04] Original scripts backed up under: ' + $backup)
Write-Host '[M04] Existing scene, private seed, local spec and ground truth were NOT altered by this installer.'
Write-Host '[M04] Reopen Unity, allow compilation, open UnseenLabB scene, use Tools > Mod Studio AI > M04 > Repair Missing Script Bindings.'
Write-Host '[M04] Then Validate Scene Bindings, Play, and rebuild Windows Mono only after validation passes.'
