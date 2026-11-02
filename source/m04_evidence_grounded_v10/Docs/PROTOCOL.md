# M04 v1.0 — Evidence-ID protocol (experimental; build-only)

Input: exactly frozen M03 v0.8 outputs `rea_evidence.jsonl`, `build_assets.json`, fingerprint; no Unity Editor source, private truth or seed. Code version is SHA256-recorded in each new local experiment config. Source validator is imported from an unchanged M03 file and checks `validation_status=observed` **before** a candidate ID can be presented to the model.

Candidate source categories currently considered: `(method with exact ldstr and TMP setter)` for `hardcoded_managed`, `(method with exact format literal + System.String.Format + TMP setter)` for `runtime_generated`, decoded `external_json` TextAsset fields, and existing **fully proven** `scriptable_object` build asset entries recognized by M03. Unresolved `unknown` MonoBehaviour values and raw candidates are excluded. Prefab scene snapshots are excluded.

Model is a selector only: input full canonical candidates are indexed locally; Qwen sees short summaries with opaque ID and returns an array of IDs. Each batch <=20 and requested default batch=10; model outputs do not set text, source type, method, evidence fields or confidence. Output is rebuilt from original catalog fields. Invalid IDs, duplicates, wrong JSON schema or timeout cannot be converted into a successful report. Candidate indices are derived from hashes of the complete record; no truncated text is used for identity.

The **static** frozen M03 validator cannot establish IL stack-to-setter dataflow; its `observed` value must not be represented as runtime proof. A real build asset value might be unused as UI. Unknown ScriptableObject class binding in B remains a known scanner limitation.

Benchmark status: M04 B already evaluated with earlier builds; do not call regression v1.0 on B an unseen holdout. For a new strictly blind B2, freeze script SHA + chosen prompt/parameters, generate a new local seed/project/build, lock three outputs per strategy *before* scoring, then publish only aggregate counts. No private truth or per-case strings in public repo or in chat during testing.
