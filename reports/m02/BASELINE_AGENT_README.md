# Baseline AI input — REA only

The file `model_input_rea_evidence.jsonl` contains only REA-derived method-level evidence; it intentionally excludes ground-truth labels and Unity Editor/asset values.

This file alone cannot reveal all serialized source strings. In a proper blind evaluation, provide the compiled Unity test-game build and a **read-only** Unity asset-inspection tool, plus REA, but **do not** provide the Unity source project, Editor provenance JSONL, ground_truth CSV, or private evaluation CSV.

Ask the agent to return source-kind, evidence path/method, candidate text or key, and confidence, using `unknown` where not observable. Model accuracy has not been benchmarked yet.