# Install ONLY the Unity Editor provenance collector and offline Python review script.
# No elevation required; no game binaries changed.
param(
  [string]$UnityProject = 'D:\ModStudioAI\UnityLab\UnityTextLab',
  [string]$DevRoot = 'D:\ModStudioAI',
  [switch]$Force
)
$ErrorActionPreference = 'Stop'
$packageRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$assets = Join-Path $UnityProject 'Assets'
if (-not (Test-Path -LiteralPath $assets -PathType Container)) {
  throw "Khong tim thay Unity project Assets: $assets. Hay truyen -UnityProject dung vi tri."
}
$destEditor = Join-Path $assets 'Editor'
$destResearch = Join-Path $DevRoot 'Research\Milestone02'
New-Item -ItemType Directory -Path $destEditor -Force | Out-Null
New-Item -ItemType Directory -Path $destResearch -Force | Out-Null
$copyJobs = @(
  @{ Source = (Join-Path $packageRoot 'Assets\Editor\ModStudioTextProvenanceCollector.cs'); Dest = (Join-Path $destEditor 'ModStudioTextProvenanceCollector.cs') },
  @{ Source = (Join-Path $packageRoot 'Tools\analyze_provenance.py'); Dest = (Join-Path $destResearch 'analyze_provenance.py') }
)
foreach ($job in $copyJobs) {
  if ((Test-Path -LiteralPath $job.Dest) -and -not $Force) {
    throw "Da ton tai $($job.Dest). Neu ban muon ghi de, chay lai voi -Force sau khi da sao luu."
  }
  Copy-Item -LiteralPath $job.Source -Destination $job.Dest -Force:$Force
  Write-Host "Installed: $($job.Dest)" -ForegroundColor Green
}
Write-Host 'Mo Unity Editor va chon Tools > Mod Studio AI > Export Text Provenance v0.1' -ForegroundColor Cyan