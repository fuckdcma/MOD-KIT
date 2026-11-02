# Mod Studio Unity Text Provenance Dataset — v0.1

- **Purpose:** Evaluate whether a research agent can locate the provenance of five text items in an independently built Unity Mono Windows sample.
- **Origin:** Original scripts and assets created for this laboratory. No third-party game files.
- **Included labels:** T001–T005, categories `serialized_prefab`, `scriptable_object`, `hardcoded_managed`, `runtime_generated`, `external_json`.
- **Evidence:** REA managed metadata/CIL outputs from a fixed build, plus manual runtime observations and source-project ground truth.
- **Training status:** **Not train-ready**. Five ground-truth rows are only a seed evaluation fixture; they lack run-linked verified analyses.
- **Data split:** Assign by project/build and task family. Never expose ground-truth during blind tests.
- **Limitations:** One local Unity Mono build; no Unreal, IL2CPP, production titles, localization package, binary hooking or shader material repair.
- **Safety/IP:** Analyze only controlled or authorized binaries. Keep code, fonts and assets within their applicable licenses.
- **Version discipline:** Record Unity Editor version, TextMeshPro package version, REA version, SHA-256 of Assembly-CSharp.dll, and build configuration for each evaluation run.