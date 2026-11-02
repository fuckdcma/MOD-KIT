# M04 Script Binding Fix v0.2 — 2026-11-02

- Repairs *structural script binding* defect in public M04 v0.1 lab generator template (several MonoBehaviour/ScriptableObject classes in `M04LabRuntime.cs`).
- Source stays public, never embeds user seed, private labels, generated spec or ground truth.
- Installer backs up original runtime script, its meta and Editor builder, then installs one type per Unity script asset and an Editor repair tool.
- Editor menu repairs 6 scene reader bindings and recreates existing table asset using on-disk LOCAL spec; table original and meta are saved under `ProjectSettings/M04RepairBackups`.
- Build menu gains pre-build validation to reject missing scripts before packaging.
- 9/9 Python static/contract tests pass. NOT Unity-compiled or Windows-run in the current environment; user's Unity Editor validation is required.
- Original (pre-repair) M04 build must never be evaluated. After clean rebuild, seal/re-run REA and evidence on new build hash.
