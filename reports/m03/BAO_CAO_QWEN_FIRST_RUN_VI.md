# QA — M03 Qwen local first run, 2026-11-02

## Observations (user supplied)

| Probe | Observed |
|---|---|
| Ollama | `qwen3.5:4b` GPU 100%, ~3.1 GB, context 4096 |
| Agent trace | Step 1 `search_literals("text")` -> 2 matches; step 2 JSON parse error at char 0 |
| Agent status | `completed=false`, `observations=[]` |
| Agent evaluator | 0 exact, 0 template, 5 not_proven (INVALID PERFORMANCE INTERPRETATION: aborted agent) |
| Tool baseline | 3 exact, 1 template, 1 unproven |
| Build scanner | 6/6 files, 32/32 MonoBehaviour decoded, no errors, one resolved serialized pointer |

## Analysis

GPU and Ollama inference are running; `qwen_agent.json` lacks a finished answer. Most likely protocol/output failure (OpenAI-compatible Qwen thinking/empty `content`, or malformed JSON). The trace does **not** capture raw message metadata, so the exact cause cannot be proven from these files alone.

## Fix v0.5

Native Ollama `think:false` / JSON mode, bounded retry and tool output; keep llama.cpp support. Fail-closed external URL restriction. No evaluation for incomplete agents. 50/50 unit tests pass, baseline remains semantically unchanged on user-provided assets.

## Next check

Install v0.5, run `tests -> agent` on local Ollama and only if `completed=true` run `evaluate -EvaluateTarget agent`. Upload `qwen_agent.json` and `evaluation_private_agent.json`; preserve trace and any PowerShell errors. This is a public laboratory functional test, not hidden generalization evaluation.
