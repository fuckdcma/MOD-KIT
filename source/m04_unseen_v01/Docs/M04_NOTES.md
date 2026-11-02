# M04 implementation record

v0.1 is a local-only lab generator. It never packages a fixed answer key. Its Python test uses a *dummy* deterministic seed in temporary directories strictly for checking generator logic. Actual seed is created via `secrets.token_bytes(32)` at CLI runtime on the user's computer.

No output from UnityTextLabB, no unseen holdout score, and no evidence of Unity Editor compiling M04 is available yet. The proper next action is a separate Unity Hub project and the local generator command. Preserve A baseline files and do not upload generated private content to public MOD-KIT.
