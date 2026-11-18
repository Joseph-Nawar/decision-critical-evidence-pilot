# P0–P4 execution runbook, artifact contract, and fallbacks

## P0 — environment and research freeze
1. Inspect working tree; don't overwrite other work. Determine Python/macOS/Apple Silicon/RAM/free disk, local inference tools and model tags. Record command outputs or factual summaries.
2. Verify literature from `02_LITERATURE.md` using original sources; create verified matrix and novelty risks, marking inaccessible sources honestly.
3. Implement a small dev preflight if needed to pick model/context/response limits. Target Qwen3.5 4B + Ministral 3 3B **only if exact compatible releases are verified**. Prefer local Ollama; avoid cloud paid APIs. New model weight downloads cumulative <9 GB; check free space.
4. Finalize `03_PROTOCOL.md` decisions on development data only; save frozen protocol/config snapshot + SHA256 and experiment manifests before seeing held-out outcomes. Log deviations explicitly.

## P1 — benchmark and oracle
Build generators, JSON schemas, complete policy/state reference implementation, private gold data, action simulator, split/hash manifests, hard-case properties and at least one independent oracle test. Run full validation including leakage tests and counterfactual checks. Ensure trivial filters don't solve nearly every family; adjust using dev split only. Freeze test set before real inference.

## P2 — baselines
Implement B0–B6 as specified in `05_BASELINES.md`, with B2/B6 model-free by default, B5 constrained by real availability. Unit test fidelity, JSON validity, budget compliance, deterministic query assumptions, and provenance sufficiency. If an existing method cannot reasonably run, record why and use a distinctly named generic compression baseline.

## P3 — actual local LLM evaluation
1. Perform real dev inference: load each model, constrained JSON action, representative short/long cases, latency/memory/context and parse checks. Check no silent truncation. Sequential models only.
2. Freeze final task/model/arm grid, prompts, decoding/retry policy, test IDs, hashes.
3. Execute preferred 100-task test across two model families × B0/B1/B3, plus B4 for all supported cases. If preflight shows this infeasible, predeclare 60-task balanced fallback before any test outcomes. Add B5 on all tasks or a prespecified balanced subset when feasible.
4. Store append-only raw invocation records, canonical outputs, action-state scores, token/time measurements, model digest, prompt/payload hashes, errors, retries. Make runs idempotent; checkpoint after each unit.
5. Include prespecified linked counterfactual/order stress cases only within available resource limits, separately counted from independent n.

## P4 — analysis and decision
Compute paired exact correctness and valid denominators; bootstrap 95% confidence intervals clustered at independent task level; subgroup analyses exploratory; distinguish missing-evidence failure from evidence-present reasoning error; quantify false/true defer, safety, schema, token overhead, model calls, timing. Make figures (model × arm, family, reduction-accuracy, evidence-success, failure breakdown, latency/cost) if data support them. Review literature novelty separately from performance. Apply `07_DECISION_RULES.md`. Produce a candid research report and clear reproducibility notes.

## Expected implementation layout
```text
AGENTS.md  README.md  STATUS.md
configs/pilot.yaml
src/evidence_pilot/{benchmark,oracles,selectors,inference,evaluation,analysis}/
scripts/  tests/
data/{manifests,development,test}/
results/{runs,tables,figures}/
docs/{LITERATURE_MATRIX_VERIFIED.md,NOVELTY_RISKS.md,EXPERIMENT_LOG.md,
      BENCHMARK_SPEC_IMPLEMENTED.md,REPRODUCIBILITY.md,LIMITATIONS.md,
      GO_NOGO_DECISION.md}
results/PILOT_REPORT.md
```
Adapt the implementation names as needed but keep the intended artifacts accessible. Do not create fake reports with empty or imagined results.

## CLI contract (or documented equivalent)
```bash
python -m evidence_pilot generate
python -m evidence_pilot validate
python -m evidence_pilot preflight
python -m evidence_pilot run
python -m evidence_pilot analyze
python -m evidence_pilot report
pytest
```
Make every command real before advertising it. Record exact setup, reproduction, and resume commands; ensure source versions and model digests are known. Final report must trace numerical claims back to raw structured records.

## Operational fallbacks
- Model unavailable / tag invalid: check actual local runtime, model catalog, quantization; select another comparable open family only if documented and within download/RAM budget. Never invent an installed model.
- Long context exceeds memory: adjust preflight/test record sizes **before test freeze**. Never silently truncate B0 or compare unmatched task coverage.
- Slow execution: reduce to **predeclared balanced 60 tasks** before seeing held-out outputs; preserve two-family mandatory paired grid if feasible. If cannot achieve it, label inference incomplete.
- B5 tool inaccessible: document faithful-reproduction blocker, use explicitly labeled generic compressor or mark missing. Never silently omit a key baseline in final conclusions.
- Network unavailable for literature: record verification gaps, retain provisional citations with caveats; do not manufacture papers' results.
- Runs interrupted: use deterministic IDs, append-only records and checkpoint-based resume; do not repeat successful calls or count unrun tasks.
- Tests or data checks fail: repair implementation without changing hidden reference outcomes opportunistically; revalidate and report modifications.
- Genuine blocker: finish runnable phases; report the exact uncompleted items, coverage, next command, and scientific limitations in `STATUS.md`.

## Final Codex response contract
Summarize: real phase coverage; independent task/model/arm counts; verified main numerical findings and confidence intervals; what actually failed and why; deterministic query vs other baselines; novelty gap; GO/NARROW/NO-GO/INCONCLUSIVE with rationale; report/artifact paths; exact reproduction/resume command. Keep conclusions matched to evidence, not aspirations.
