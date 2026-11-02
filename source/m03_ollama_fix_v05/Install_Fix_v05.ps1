param(
    [string]$ProjectRoot = 'D:\ModStudioAI\Milestone03'
)
$ErrorActionPreference = 'Stop'
$patchRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$manifestFile = Join-Path $patchRoot 'SHA256_MANIFEST.json'
if (-not (Test-Path -LiteralPath $manifestFile -PathType Leaf)) { throw 'Missing SHA256_MANIFEST.json' }
$manifest = Get-Content -LiteralPath $manifestFile -Raw -Encoding UTF8 | ConvertFrom-Json
$targets = @('src\modstudio_m03.py','Run_M03.ps1','tests\test_ollama_v05.py')
if (-not (Test-Path -LiteralPath $ProjectRoot -PathType Container)) { throw "Missing Milestone03: $ProjectRoot" }
if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot 'src\modstudio_m03.py') -PathType Leaf)) { throw 'Missing M03 Python Agent source' }
if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot '.venv\Scripts\python.exe') -PathType Leaf)) { throw 'Missing M03 Python .venv' }
foreach ($t in $targets) {
    $s = Join-Path $patchRoot $t
    if (-not (Test-Path -LiteralPath $s -PathType Leaf)) { throw "Missing patch file: $s" }
    $m = $manifest.files | Where-Object { $_.path -eq ($t.Replace('\','/')) }
    if ($null -eq $m -or @($m).Count -ne 1) { throw "Missing manifest entry: $t" }
    $hash = (Get-FileHash -LiteralPath $s -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($hash -ne $m.sha256) { throw "SHA256 mismatch: $t" }
}
$backup = Join-Path $ProjectRoot ('Backups\M03_OllamaAgent_v05_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
$updated = @()
try {
    foreach ($t in $targets) {
        $src = Join-Path $patchRoot $t
        $dest = Join-Path $ProjectRoot $t
        if (Test-Path -LiteralPath $dest -PathType Leaf) {
            $bak = Join-Path $backup $t
            New-Item -ItemType Directory -Force -Path (Split-Path -Parent $bak) | Out-Null
            Copy-Item -LiteralPath $dest -Destination $bak -Force
        }
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dest) | Out-Null
        Copy-Item -LiteralPath $src -Destination $dest -Force
        $updated += $t
        Write-Host "Patched: $t"
    }
} catch {
    foreach ($t in $updated) {
        $dest = Join-Path $ProjectRoot $t
        $bak = Join-Path $backup $t
        if (Test-Path -LiteralPath $bak -PathType Leaf) {
            Copy-Item -LiteralPath $bak -Destination $dest -Force
        } elseif (Test-Path -LiteralPath $dest -PathType Leaf) { Remove-Item -LiteralPath $dest -Force }
    }
    throw
}
Write-Host "Backup of overwritten files: $backup"
Write-Host 'No pip installations; REA data, Unity build, PrivateEvaluation and Outputs remain untouched.'
Write-Host 'Run: powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode tests'
Write-Host 'Then: powershell -NoProfile -ExecutionPolicy Bypass -File .\Run_M03.ps1 -Mode agent -Server http://127.0.0.1:11434 -Model qwen3.5:4b'
