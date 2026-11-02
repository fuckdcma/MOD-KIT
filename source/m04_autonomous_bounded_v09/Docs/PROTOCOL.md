# M04 v0.9 Experimental Trial Protocol

Record 3 separate cohorts, **never merge**:

- First-attempt M03 v0.8 Autonomous, num_predict=1280, num_ctx=4096; observed fail at step 8.
- Parameter-only M03 v0.8 Autonomous, num_predict=2560, num_ctx=4096; observed fail at step 8.
- M04 v0.9 Autonomous, num_predict=2560, num_ctx=8192, ledger bound and reset, 16 steps; **not yet observed**.

The probe returned 6.06 s and the first two conditions had identical `finish=length` JSON failure diagnostics, but that alone does not prove the exact reason for the truncation. Compare run completion and invalid JSON rates before any accuracy comparison. The environment is not a pristine unseen holdout because user-visible images already exposed some case values; this is an integration / generalization engineering regression.

Input equality: require source M03 v0.8 SHA256 equal the original evidence fingerprint; SHA256 of the two copied REA/Asset files equal original hashes. Outputs and configs stay in private local folders, no public repo sync. Source text and answer key excluded.

Retest policy: preserve all failures as immutable artifacts. If an experimental change fails, issue another *versioned* variant and fresh output folder. Never silently retry or rescore a failed first attempt as though it were completed. Do not call the model answer source-proven unless M03 validation marks it observed and the private scorer agrees after predictions locked. Do not conflate observed static method+literal evidence with actual runtime IL stack dataflow.
