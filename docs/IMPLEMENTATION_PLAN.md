# Evidence pilot implementation plan

**Goal:** Execute the supplied P0–P4 protocol and preserve inspectable evidence.
**Architecture:** Separate public benchmark exports from private gold; independent SQL policy queries compete with the reference interpreter. Append-only local inference, immutable freeze manifests, task-paired analysis.
**Tech stack:** Python 3.12, stdlib, pytest, jsonschema, NumPy, Matplotlib, Ollama HTTP.
**Specifications:** docs/01_BRIEF.md through docs/07_DECISION_RULES.md.

The user explicitly authorized autonomous execution and reasonable decisions without routine clarification; this supersedes skill design/plan approval pauses. This directory is not a Git repository; use source hashes and snapshots rather than assuming commits/worktrees.

## Constraints and review focus
Synthetic data only; no paid APIs; <9 GB new weights; sequential model loading; no held-out tuning. Review completeness under selection, temporal precedence/ties, semantic near matches, immutable resumability, and actual state scoring rather than prose.

## Tasks and checks
- [x] P0: Save environment/catalog/source evidence, verify primary literature, finalize dev-only feasibility choices. Record every deviation.
- [x] P1: Write failing hand-checked oracle/state tests; implement five generators and independent SQL competitor; validate reproducibility, split isolation, provenance separation, counterfactual flips and order invariance.
- [x] P2: Write budget/metadata/leakage tests; implement full/head/random/BM25/generic extractive compression/oracle diagnostic. Check formal sufficiency and trivial exact-key performance on development only.
- [x] P3: Test invocation parsing, context guard, checkpoint uniqueness; perform real dev preflight for both models. Freeze protocol/config/data/code/prompt/grid before any held-out inference. Choose 100 or balanced 60 based on dev timing. Execute the entire declared grid, checkpoint every call, preserve errors without rerolls.
- [x] P4: Test paired bootstrap and state/failure accounting. Analyze independent units with linked stress tests separately; generate six raw-backed figures, report, decision and exact resume/reproduction commands. Run all tests and integrity checks; independent final review where skill-directed.

Shared interfaces: public task dictionaries → selectors and prompt constructor; private gold → evaluator only; raw invocation JSONL → analysis. Model-free query consumes only public dictionaries. Gold IDs never enter selectors or prompts except B6 diagnostic outside inference.
