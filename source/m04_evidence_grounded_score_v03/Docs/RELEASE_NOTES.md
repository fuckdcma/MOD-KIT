# M04 Evidence-Grounded v1.0 Private Regression Scorer v0.3

2026-11-02. This release is a NEW, one-time, private evaluation wrapper for already-completed three v1.0 model runs against the earlier B integration set. The v0.2 evaluator's `score_one()` is vendored byte-for-byte unchanged, with static evidence support requiring both `validation_status=observed` and `confidence=observed`. The wrapper stages three version-identified run reports, SHA-checks original/copy evidence against the sealed fingerprint, verifies M03 v0.8 fingerprint, then hashes and privately locks exact predictions. No original data is overwritten.

Verified on synthetic data: 14/14 unit tests pass, including report contract validation, fail-closed, private/public boundaries and no-overwrite. The scorer has **not yet been executed on the user's Windows M04 B truth**, and no accuracy score for v1.0 is claimed.
