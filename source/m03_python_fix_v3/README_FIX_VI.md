# Mod Studio AI M03 — Python 3.12 Fix v3

Fix for `Could not find a version that satisfies the requirement tpk_ar`.

## Root cause

`tpk_ar==0.2.4` on PyPI is source-only, whereas the v2 setup passed `--only-binary=:all:` to pip when installing UnityPy. Pip cannot select tpk_ar. Python 3.12 itself is working.

## Install (PowerShell)

1. Backup old `Setup_Python312.ps1` and `Run_M03.ps1`.
2. Copy all 3 files from this archive to `D:\ModStudioAI\Milestone03`.
3. Run:

```powershell
cd D:\ModStudioAI\Milestone03
powershell -NoProfile -ExecutionPolicy Bypass -File .\Setup_Python312.ps1 -SkipPipUpgrade
.\Run_M03.ps1 -Mode tests
.\Run_M03.ps1 -Mode scan-assets
```

`Setup_Python312.ps1` first installs `tpk_ar==0.2.4` from its source distribution into the **project-only** `.venv`, then installs `UnityPy==1.25.4` with binary wheels. No global Python changes are made.

## Manual quick fix (without copying this archive)

```powershell
cd D:\ModStudioAI\Milestone03
& ".\.venv\Scripts\python.exe" -m pip install 'tpk_ar==0.2.4'
powershell -NoProfile -ExecutionPolicy Bypass -File .\Setup_Python312.ps1 -SkipPipUpgrade
.\Run_M03.ps1 -Mode scan-assets
```

## Checks

```powershell
& ".\.venv\Scripts\python.exe" -m pip check
& ".\.venv\Scripts\python.exe" .\Verify_Python312.py --check-deps
```

Success should produce `D:\ModStudioAI\Milestone03\Outputs\build_assets.json` after the scan. If it fails, send the console output. This setup has not been executed on your Windows PC; its source and package availability have been verified separately.
