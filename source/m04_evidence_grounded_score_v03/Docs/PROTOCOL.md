# M04 B: explicit integration-regression score v0.3

- **Version under test:** `M04_EvidenceGrounded_v10_EXPERIMENTAL_B_REGRESSION` (three frozen completed runs `evidence_r01..r03`).
- **Score contract:** exact function `score_one` from original M04 v0.2 source, bundled unchanged and SHA-256 pinned.
- **Preflight:** compare SHA-256 of original REA/UnityPy and experimental copies with sealed fingerprint; match original v0.8 M03 sha; verify experimental v1.0 config schema; verify report mode, strategy, completed and assembly identity; later Python checks all observations have verified static evidence and terminal finish without errors.
- **Privacy:** only after preflight read `ground_truth_PRIVATE.json`; private lock and per-case metrics under PRIVATE_DO_NOT_UPLOAD. Public aggregate under NEW local score folder. The output has counts/hashed provenance but no text, per-case IDs or false-positive source strings.
- **Scoring:** positive total 15, negative total 5; exact source+text matches vs accepted validator-supported matches counted separately. False-positive *claims* are not a rate across 5 negatives. Static validation does not establish runtime display.
- **Benchmark validity:** B's strings/images have been exposed, and model/code has been iterated on B. Must label this regression, not blind holdout. Original M03 v0.8 autonomous r01 failure and its 2560 retry remain reported as operational failures; no retroactive replacement.
- **Next:** freeze v1.0 source and prompt, generate new private B2, run predictions before looking at answers, then private evaluation.
