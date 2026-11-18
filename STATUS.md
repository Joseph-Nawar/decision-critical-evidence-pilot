# Pilot status — durable final checkpoint

**Status:** COMPLETE — executed P0–P4 using the prespecified balanced 60-task fallback.
**Scientific verdict:** **NO-GO for the implemented structured-workflow selector proposal.**
**Date:** 2026-11-18 (Africa/Cairo)

## Phase coverage

| Phase | Executed evidence |
| --- | --- |
| P0 | Environment and local model preflights; eight supplied primary papers and implementations verified, plus two related precedents; protocol frozen before test inference |
| P1 | 30 development + 100 independent test + 20 linked stress exports; repeat-generation, private/public separation, independent SQL agreement, action/state, counterfactual/order and metadata checks |
| P2 | B0/B1/B2/B3/B4/genericB5/B6 plus exact-key diagnostics; all byte caps and JSON contracts verified |
| P3 | 440/440 unique retained units, 440 actual backend responses, zero retained invocation/schema errors ; 360 mandatory + 40 B5 + 40 linked stress calls; two sequential local model families |
| P4 | 10,000 task-paired bootstrap draws bootstrap, model/family tables, mechanism/deferral/validity accounting, linked-stress descriptives, six visually checked PNG/PDF figure pairs, research report and verdict |

## Findings

- Independent headline n=60 (12/family; 4 cases in each 50/150/300-record bin per family). The other 40 frozen independent test tasks receive model-free diagnostics only. Variants never increase independent n.
- Qwen3 4B correctness: full 26/60; head 5/60; BM25 7/60; generic compression 2/20. Head minus full: −35.0pp, 95% CI [−48.33,−21.67]. BM25 minus full: −31.67pp,[−45.00,−18.33].
- Gemma4 11.9B correctness: full 23/60; head 18/60; BM25 21/60; generic compression 6/20. Head minus full: −8.33pp,[−23.33,6.67]. BM25 minus full: −3.33pp,[−20.00,13.33].
- Public deterministic SQL query:100/100 independent test cases correct. Oracle certificates fit the byte budget 100/100; largest certificate uses 46.5% of its cap. Neither low full-model competence nor these query-solvable templates justifies a broad new selector project.
- Current full test suite: 47 passed. Certificate replay: 150 oracle views + 309 sufficient selector views, zero discrepancies. Exact cross-model payload pairing: 220/220.

## Identities and artifacts

- Freeze SHA-256: `424d83723b2aca6f2df1696d138dff01b3389a504676670e5e6c6552f8aab2da`
- Protocol file SHA-256: `381c65c4f59109c55b7a93d948f1442f0f160d4da95cf8e8166f33984c749239`
- Canonical dataset manifest SHA-256: `f061e9aa66ad751fef649c356bc77a18047ffc84e9a05f9b8c7f045efa966862`
- Raw invocation file SHA-256: `8dc908666acf694c36c62534119f804151bc3d7d055368e5fd9efd835b5ad1d7`
- Environment: macOS 26.4 arm64, 16 GiB RAM, Python 3.12.15, Ollama 0.40.15. Qwen3:4b-instruct-2507-q4_K_M (`0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`); Gemma4:12b-it-qat (`38044be4f923e5a55264ed7df4eaac2676651a905f735197c504045140c02bd3`). Both unloaded after execution. No new complete model weights used; preferred download canceled for slow network. No paid API or real business actions.
- Main report: `results/PILOT_REPORT.md`; decision: `docs/GO_NOGO_DECISION.md`; source-backed audit: `docs/LITERATURE_MATRIX_VERIFIED.md`; limitations/reproduction: `docs/LIMITATIONS.md`, `docs/REPRODUCIBILITY.md`.
- Raw/scored results: `results/runs/heldout/raw.jsonl`, `results/scored.jsonl`; summaries/tables/figures: `results/summary.json`, `results/tables/`, `results/figures/`.
- Frozen original source/config/data manifest: `results/frozen/`. Exact original request bodies: 440 files +manifest in `results/replay_requests/`.

## Deviations and limitations

1. Preferred 600 mandatory calls replaced by the predeclared360-call balanced fallback, before test inference. Actual families differ from the preferred Qwen3.5/Ministral pair; full competence was low.
2. Four additional backend completions lost their response bodies at a deliberate session interruption. Missing raw units resumed once under the prespecified policy; retained results never rerolled. Unknown actions/tokens/client overhead remain unknown. Receipt: `results/runs/heldout/interruption.json`. Total observed backend completions: 2 smoke + 64 calibration + 440 retained test/stress + 4 lost = 510.
3. Four BM25 payloads (two tasks across both models) can change tied-record ORDER in a fresh process because query-set iteration changes floating accumulation by 8.88e-16. Membership and sufficiency are unchanged. Original source/output preserved; exact model-input exports provide faithful replay. See `results/bm25_hash_seed_audit.json` and `results/final_integrity_audit.json`.
4. Generic graph extraction is not a faithful released compressor; adaptive recovery untested. Synthetic templates, trusted scope counts, fixed date/group patterns, small models and limited task counts constrain interpretation. No positive novelty claim.

## Exact reproduction / resume commands

No pending units or execution blocker. Existing-unit resume (does not repeat completed units): `.venv/bin/python -m evidence_pilot run`.

Recompute the delivered analysis/report without inference:

```bash
.venv/bin/python -m evidence_pilot integrity
.venv/bin/python -m evidence_pilot analyze
.venv/bin/python -m evidence_pilot report
.venv/bin/python scripts/finalize_report.py
```

Exact request export without inference: `.venv/bin/python scripts/export_frozen_requests.py`.

Full setup, replay caveats and fresh-replication instructions: `docs/REPRODUCIBILITY.md`. All decisions/deviations are in the append-only `docs/EXPERIMENT_LOG.md`.
