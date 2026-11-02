# M04 blind-evaluation contract

## Threat model

The public MOD-KIT repository can contain generator source and evaluator algorithms, but must not contain generated holdout seed, actual case strings, labelled origin mapping, Editor source, or final private answer CSV/JSON before model outputs are frozen.

If a user publishes the UnityTextLabB source or `ProjectSettings/M04HoldoutLocal.json`, the holdout is compromised and a fresh seed/project is required. If a user shares the build with an AI for evidence analysis, that is intentional; do not share the answer key or generator spec with the same agent.

## Data boundaries

* `AgentInput`: M03 REA build metadata and UnityPy asset snapshots only.
* `Reference`: Local 256-bit seed, ground truth, private authoring spec and optional Editor verification.
* `Runs`: Immutable autonomous/guided per-run observations and model config; hash before private evaluation.
* `QA`: private per-case scoring followed by publication of aggregated metrics/hashes only.

Keep M03 v0.8 **frozen** across benchmark rounds. Record CLI version, model name/hash, context, elapsed time and input SHA. This package does not modify M03 code or train a model.

## Scoring boundaries

The private scorer uses text/template plus category matches to measure **label accuracy**; it separately tracks M03 validator's observed/static support. Neither is a proof of runtime UI dataflow. Scene-stored `TMP_Text.m_text` cannot establish original prefab source. A duplicated string in a Debug.Log and in a UI setter is an intentionally ambiguous negative; counting it solely by text would be unsound.

## Public limitations

All scripts are source-verifiable, but Unity compilation and runtime cannot be validated in this sandbox. New M04 source script is intentionally a separate untested Unity Editor integration until the user produces Windows log, player build and evidence.
