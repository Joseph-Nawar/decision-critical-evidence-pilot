# Persistent Codex instructions — Decision-Critical Evidence Pilot

This file is the durable instruction entrypoint for agents working in this repository. Read it **at the beginning of every session**, followed by `STATUS.md`, `docs/03_PROTOCOL.md`, and `docs/06_EXECUTION.md`; read the other specs before changing the components they govern. The user-facing kickoff prompt is in `prompts/CODEX_KICKOFF.md`.

## Mission
Carry out the **P0–P4 scientific feasibility pilot** described in `docs/01_BRIEF.md`. Deliver actual executed experiments, verified data, analysis, and an evidence-based GO / NARROW / NO-GO / INCONCLUSIVE decision. Do not stop after scaffolding, smoke tests, or a research plan if execution is feasible.

## Authority and guardrails
1. The repository specs provide persistent project context. If they conflict, prefer scientific integrity and record a resolution in `STATUS.md`. Do not silently alter frozen experimental decisions.
2. Never invent data, measurements, model calls, literature findings, sources, or completed work. Separate executed results from expectations, prior prototype results, and estimates.
3. No test-label, evidence-provenance, oracle, or private-state leakage into model-facing inputs or selectors. Never use held-out results for tuning. Never cherry-pick cases, remove failures, or replace unsuccessful outputs without recording the prespecified retry policy.
4. Judge **executed action/state correctness**, not fluent text, compression alone, or evidence recall alone. Preserve the distinction between evidence selection failure and model reasoning failure.
5. Always compare against a credible deterministic query/policy system; it may invalidate the research case. Oracle evidence is an upper bound, not a method.
6. Do not claim novelty without checking primary papers and published implementations; label approximations honestly. Keep reproducibility metadata and raw results.
7. No paid APIs, external real-world actions, or sensitive user information. Use synthetic data. No destructive or unrelated repository operations.
8. Prefer Python 3.11+, lightweight dependencies, local inference, testable code, documented commands. Keep local model downloads under 9 GB total new weights unless the user changes this limit. Models run sequentially, not simultaneously.
9. Make reasonable engineering decisions without routine clarification. If the preferred approach is unavailable, execute the best scientifically valid fallback, disclose coverage and limitations, and continue. Never assert completion for blocked stages.
10. Tests and validation must be executed. A failing result is information; do not conceal it.

## Resumability and context survival
- Treat `STATUS.md` as a living checkpoint. Update at every completed stage or meaningful interruption with phase, decisions, environment/models, completed counts, hashes, blockers, exact next command, and result locations.
- Maintain an append-only decision/deviation record in `docs/EXPERIMENT_LOG.md` (create when starting), with date, rationale, and impact on comparability.
- Design idempotent, checkpointed inference: task × model × baseline × replicate is a unique unit. Resume incomplete units without overwriting completed ones.
- Freeze the protocol before held-out inference, store a snapshot/hash in run artifacts, and explicitly label all post-freeze deviations.
- Prefer committed, documented artifacts over ephemeral chat context. Do not depend on current conversation to understand the research.

## Completion criteria
Required: reproducible generated benchmark, verified oracle and action execution, non-oracular baselines, actual model inference if feasible, paired analysis, six plots when data permit, research report, literature/novelty audit, and a defensible decision. If resource constraints prevent the minimum run, classify evidence as INCONCLUSIVE and preserve a clear resume path.
