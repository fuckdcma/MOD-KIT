# Progress ledger — 2026-11-02

## Milestone 01 — UnityTextLab / Mono / REA — VERIFIED LAB BASELINE

- Unity 6000.3.27f2 Windows Mono; build UnityTextLab.exe.
- 5 text displayed: New Game, Load Game, Quest Completed, Health dynamic, Hello Commander.
- REA static inspection exports `assembly_identity.json` + `members.json`. 9 type defs (including Module), 16 methods, 14 fields; Assembly SHA256: `ab9cf9e569815b6d1d1f49dbc455521bb426b6118b891c8c0a3052244d24a29e`.
- Player.log: `sameAtlas=True` on `Prefab_NewGame`, LiberationSans SDF; warnings GPU resource cleanup. Glyph Vietnamese not tested.

## Milestone 02 — Editor provenance — VERIFIED OUTPUT

- Collector scanned Unity source Editor: 5 scene TMP + 1 prefab TMP + 1 ScriptableObject + 1 Resources JSON = 8 records.
- Cross-check 5 cases; reference data must never be provided to blind agent.
- No collector warnings; data exported to `text_provenance.jsonl`, `manifest.json`.

## Milestone 03 — Build-only scanner — IN PROGRESS

- v0.1 rule baseline 1 exact + 1 template + 3 unknown.
- UnityPy 1.25.4 installation blocked initially by Python 3.15 C++ compile, fixed with Python 3.12.10 venv. `tpk_ar` needs sdist install before the `--only-binary` dependency restriction. Windows ExecutionPolicy requires per-process Bypass or `powershell -ExecutionPolicy Bypass -File`.
- UnityPy v0.1: first read TextAsset, failed 32 MonoBehaviour decode.
- v0.2 + TypeTreeGeneratorAPI: **32/32 MB decoded, 0 errors, 7 asset observations**, 6/6 build files; latest files in `evidence/m03/latest/`.
- Current evaluator: **2/5 exact, 1/5 template, 2/5 unproven**. No Qwen inference score yet.

## Not yet done

- T001 serialized prefab origin from build (only scene TMP snapshot).
- T002 ScriptableObject key + reader method verified end-to-end (class + value observed but proof chain incomplete).
- Qwen GGUF download/load test; agent tool use eval.
- SDF broken-cases lab, font 1:1 runtime mapping validation.
- Standalone mod bootstrap, hook adapter compiler/test, IL2CPP/Unreal.
