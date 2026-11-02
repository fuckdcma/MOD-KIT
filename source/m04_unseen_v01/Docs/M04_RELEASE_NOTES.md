# Milestone 04 UnseenLab-B Generator v0.1 — Release notes

**Supported environment:** Unity 6000.3.x / Windows Mono / TextMeshPro. This release is NOT a standalone mod/hook and has NOT been compiled in Unity within this container.

- 20 locally generated cases (15 positive + 5 negative) with cryptographically generated 256-bit secret seed at **Windows execution time**.
- New separate UnityTextLabB scene/prefab/string-table/Resources JSON; generated IL methods include hardcoded and `String.Format` examples.
- Private ground truth kept outside public project; a public hash-only manifest is available.
- Separate M04 evaluator freezes M03 model outputs and scores only after predictions have been completed.
- Public metrics exclude individual text/ground-truth labels. False positives and ambiguous duplicate strings tracked conservatively.
- Frozen M03 v0.8 scanner/agent and REA evidence can be used without editing the original lab-A directory.
- Python smoke generation performed using temporary local secrets, removed afterward.
- Python unit tests: 26/26 passed. C# Unity compilation and runtime output: **not yet validated**.
