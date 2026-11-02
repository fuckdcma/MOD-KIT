# Release notes — M04 v0.9 Autonomous bounded-context experiment

- Input from user: original M03 v0.8 Autonomous first attempt at 1280 tokens **failed** at step 8 after seven tool operations; retries 1–3 all invalid JSON, `finish=length`. Distinct 2560-token attempt with identical build-only inputs (SHA matched) **failed with exactly the same three model-response error details**. Guided (v0.8) already completed 3/3 (11 observations each) but unscored.
- Diagnosed output truncation. The exact role of context pressure versus output cap remains unresolved; code fixed 4096 context and accumulated full history. This patch is an engineering experiment, not proof of a root cause.
- Changed only Autonomous strategy implementation to bounded evidence ledger, two-message per step, retries use new bounded prompt; Ollama native `num_ctx` 8192 instead of 4096; script requests 2560 output tokens and 16 steps. Static evidence validation and Guided source blocks are fingerprint-equal to public v0.8.
- Script refuses existing output directory, verifies frozen source SHA and REA/UnityPy hashes against original fingerprint, copies inputs and stores fresh experiment config with previous failures' SHA when present. Does not read ground truth.
- Test status: **7/7 offline Python tests passing**. No Unity Editor, Windows PowerShell runtime, Qwen Ollama inference or M04 private scoring performed here.
- Use in fresh `Runs_AUTONOMOUS_BOUNDED_V09_LOCAL`, not original `Runs_LOCAL` or earlier retry folder. Never replace original model-run failure and don't present v0.9 trial as M03 v0.8 baseline.
