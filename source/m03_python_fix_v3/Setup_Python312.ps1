param(
  [switch]$SkipPipUpgrade
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$venv = Join-Path $root '.venv'
$exe = Join-Path $venv 'Scripts\python.exe'
$verify = Join-Path $root 'Verify_Python312.py'

if (-not (Test-Path $verify)) {
  throw "Missing Verify_Python312.py next to Setup_Python312.ps1. Extract all files in the fix ZIP."
}
if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
  throw 'Python launcher `py` not found. Install Python 3.12 64-bit first.'
}
Write-Host 'Checking Python launcher...'
& py -3.12 --version
if ($LASTEXITCODE -ne 0) {
  throw 'Python 3.12 not found by py launcher. Run `py -0p` to list installations.'
}

if (-not (Test-Path $exe)) {
  Write-Host 'Creating local virtual environment .venv...'
  & py -3.12 -m venv $venv
  if ($LASTEXITCODE -ne 0) { throw 'Could not create local .venv.' }
}

Write-Host 'Validating venv Python (3.12 x64)...'
& $exe $verify
if ($LASTEXITCODE -ne 0) {
  throw 'Existing .venv has the wrong Python version/architecture. Rename .venv to .venv_backup, then rerun setup.'
}

if (-not $SkipPipUpgrade) {
  Write-Host 'Updating pip...'
  & $exe -m pip install --upgrade pip
  if ($LASTEXITCODE -ne 0) { throw 'pip upgrade failed.' }
}

# tpk_ar 0.2.4 is published as sdist only, so --only-binary=:all: must not
# apply to that dependency. Build/install it first (pure Python source package).
Write-Host 'Installing tpk_ar 0.2.4 (source distribution)...'
& $exe -m pip install 'tpk_ar==0.2.4'
if ($LASTEXITCODE -ne 0) {
  throw 'Could not install tpk_ar. Check PyPI connectivity or Python environment.'
}

Write-Host 'Installing UnityPy 1.25.4 and prebuilt Windows wheels...'
& $exe -m pip install --only-binary=:all: 'UnityPy==1.25.4'
if ($LASTEXITCODE -ne 0) {
  throw 'UnityPy install failed. Check internet, package index, and Python 3.12 x64.'
}

Write-Host 'Checking dependency consistency...'
& $exe -m pip check
if ($LASTEXITCODE -ne 0) { throw 'pip check found broken dependencies.' }

Write-Host 'Verifying UnityPy and lz4...'
& $exe $verify --check-deps
if ($LASTEXITCODE -ne 0) { throw 'Package verification failed.' }

Write-Host 'READY: Run .\Run_M03.ps1 -Mode tests, then -Mode scan-assets.'
