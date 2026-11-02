# Run this AFTER installing Node.js and REA, and after building the Unity Mono project.
# Requires the actual build path; set it below. Do not assume the DLL path exists.
$assembly = "D:\ModStudioAI\Builds\UnityTextLab\UnityTextLab_Data\Managed\Assembly-CSharp.dll"
$outputDir = "D:\ModStudioAI\Research\REA"
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
if (-not (Test-Path $assembly)) { throw "Missing managed assembly: $assembly. Check build folder and Mono backend." }
rea inspect-managed-artifact $assembly --json | Out-File -FilePath (Join-Path $outputDir "assembly_identity.json") -Encoding utf8
rea inspect-managed-members $assembly --json | Out-File -FilePath (Join-Path $outputDir "members.json") -Encoding utf8
Write-Host "REA evidence exported to $outputDir"
