# M04 Scoring v0.2 experimental protocol

1. Preserve original Windows build, SHA sealed REA/UnityPy input and original completed/failed v0.8 outputs.
2. Stage exactly seven **completed** reports: static baseline v0.8 r01, guided v0.8 r01-r03, autonomous bounded v0.9 r01-r03. v0.8 Autonomous failures are never included as 0/20.
3. Verify frozen source fingerprint, input hashes and built Assembly-CSharp.dll identity via report metadata. Private answers are read only by scorer, after validation.
4. Score source_and_text_matches separately from observed_supported_matches. Require both validated observed status and model confidence observed for latter.
5. Copy all final predictions into uniquely named PRIVATE lock directory, hash verify copies. Store case-level outcomes only PRIVATE; public report has aggregates and version tag.
6. Do not compare these as same-version A/B benchmark. Evaluate improvements and generalization with a new blind seed in later experiments.
