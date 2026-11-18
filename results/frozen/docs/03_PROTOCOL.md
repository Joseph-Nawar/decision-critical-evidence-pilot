# P0 draft preregistration — experimental protocol

**Status:** FINAL FOR FREEZE, 2026-11-18. The execution-specific decisions below were selected using development data and runtime measurements only. The freeze command stores this document, configuration, public/private dataset hashes, source/tests, prompts and exact grid before any held-out inference. Post-freeze changes require an explicit deviation record.

## Main question and hypotheses
- **RQ1 / H1:** Under a matched tool-payload budget, naive head truncation and lexical selection reduce executed-action correctness versus full evidence on some nontrivial task families.
- **RQ2 / H2:** Decision-critical evidence sufficiency (including dependency and completeness constraints) predicts downstream success more strongly than raw compression percentage alone; this is an association, not proof of causality.
- **RQ3 / H3:** Some realistic tasks cannot be safely resolved by conventional ranked-record selection at a fixed small budget without recovery/deferral; existing methods and deterministic queries are competing explanations/solutions.
- **RQ4 (null-friendly):** When properly scoped deterministic querying solves these workflows, an LLM-centric selector may not offer a worthwhile systems contribution.

## Study units and split
- 30 development/calibration **independent** tasks; no inferences from this split counted as test results.
- 100 held-out independent tasks, 20 per required family, frozen before inference. Pre-plan 50/150/300 record-count bins approximately balanced per family if runtime supports full-context arms.
- Counterfactual twins and record-order variants are linked by `parent_task_id`; **not** treated as independent units.
- Use reproducible random seeds, generator version, input hashes, predefined test IDs, and exact dataset manifest. Freeze test set once, including counterfactual relationships.
- Pilot power is limited; confidence intervals and exploratory nature must be emphasized.

## Primary outcome
**Executed-action correctness**: validate a structured action and apply it to an isolated synthetic state; correct only when the action and resulting state match the executable reference specification. Include a correct `DEFER`/`REQUEST_MORE_EVIDENCE` only where required by policy and availability. Invalid outputs, wrong targets, wrong parameters, incorrect defer/reject, or incorrect state transitions fail.

## Secondary outcomes
Critical-evidence sufficiency/recall (requiring completeness for negatives/aggregates), unsafe or unsupported action rate, correct/false deferral, invalid schema, context/payload bytes, actual input and output tokens when available, retrieval/model call counts, compression overhead, wall clock / phase timing, memory pressure where measurable. **Byte reduction ≠ token savings ≠ net cost savings.**

## Experimental arms and budgets
- Mandatory LLM arms on each test task × each available model: **B0 full**, **B1 head**, **B3 lexical (BM25)**. Two independent small-model families targeted.
- **B4 deterministic query** on every supported test task; no LLM call required. Analyze its privilege assumptions separately; do not treat it as the oracle selector.
- **B2 seeded random** and **B6 oracle** are primarily model-free diagnostics; optional paired LLM inference only if preflight budget permits.
- **B5 compression** is an important comparator; include in primary LLM arms if feasible. Otherwise run on a prespecified, family-balanced subset or report genuinely blocked. Declare if compressor is an existing faithful implementation versus a generic summary baseline. Include all extra calls and costs.
- Optional recovery/retrieval baseline uses equal access rights and records retrieval steps.
- Primary budgeted arms target **25% of serialized full payload bytes**, inclusive of metadata, with a 2,000-byte floor where compatible with the context cap. Finalize this budget on development data before freezing. All selectors use the same per-task budget; results must report actual payload size, actual tokens, and truncation validity. Full context is an unconstrained reference, not a matched-budget arm.
- Baselines must receive the same user request, workflow policy, action schema, and completeness metadata. No gold-answer or relevance labels. No artificial help for the proposed approach.

## Models, prompting, and inference
- Preferred families to validate: Qwen3.5 4B and Ministral 3 3B via installed local inference runtime, not assumed to be available. Check exact tags/digests and licenses, memory/context feasibility, structured output quality.
- Default temperature 0, fixed seeds/versions when supported, defined context, output-token limit, reasoning-mode settings recorded. Common instructions across arms; output strict typed JSON action. Do not imply deterministic reproducibility if backend does not support it.
- One invocation record per task × model × arm × repeat, including errors and timeout handling. No undisclosed rerolls/retry selection.
- Full-context prompts must fit the actual available context; do not silently drop evidence. If long cases don't fit, adjust the study design on development data **before freeze**, or report unmatched/infeasible pairs separately.

## Required actual execution target and resource fallback
- Target 100 tasks × 2 models × 3 mandatory LLM arms = **600** mandatory calls, plus model-free B4 and extras if feasible.
- Run development preflight and a small smoke suite before scheduling the full held-out grid.
- If impractical, use a **predeclared balanced 60-task subset** (12 per family, selected deterministically from the frozen test manifest) across **both** models and 3 mandatory arms = 360 calls; report reduced statistical power and do not rechoose based on performance.
- If one model fails preflight, record that limitation; still perform the strongest feasible pilot. If <60 paired tasks or <2 model families, do not claim a complete two-model pilot; scientific verdict normally INCONCLUSIVE unless evidence strongly supports NO-GO on independent grounds.
- Resume idempotently after interruption; never record unexecuted units as complete.

## Main comparisons and statistics
- Paired correctness difference of each budgeted condition vs full, reported with n/N, percentage-point differences, and 95% CIs; stratify per model and family.
- Use paired task-level bootstrap or justified paired tests; cluster all variants by `parent_task_id`. Secondary family analyses are exploratory.
- Separately analyze absent critical evidence versus evidence-present reasoning errors, schema failures, invalid completeness inference, rule precedence, aggregation and semantic matching.
- No multiple-comparison overclaiming; describe uncertainty and negative results. Report paired denominators and missingness.
- Order sensitivity/counterfactual robustness on a prespecified feasible subset, separately from independent headline n.

## Interpretation limits
Synthetic workflows and formal oracles are controlled feasibility instruments, not proof of real-world deployment or clinical/financial safety. No human annotation is required for gold labels in this pilot; that does not guarantee realism. Results from small quantized local models may not generalize to more capable agents. Research novelty is an independent related-work question.


## Final execution decisions (development-only, 2026-11-18)

- Runtime: Python 3.12.15, Ollama 0.40.15 on a 16-GiB Apple Silicon Mac. Installed fallback families: `qwen3:4b-instruct-2507-q4_K_M` and `gemma4:12b-it-qat`; actual digests, quantization, licenses and model metadata are pinned in results/environment/runtime.json and the frozen manifest. Preferred Qwen3.5 4B download was canceled for observed network latency; no preferred-model outcome is implied.
- Freeze all 100 independent test tasks (20/family), but infer the predeclared balanced **first 12 manifest indices per family**: 60 independent tasks with 4 each of 50/150/300 records per family. Development timing made the preferred 600-call grid plus extras an approximately multi-hour workload; choose the documented reduced-power fallback before seeing any test outcome. The remaining 40 independent test tasks are not in the LLM inference grid and are never tuned upon.
- Mandatory held-out inference: 60 × 2 models × B0/B1/B3 = **360** calls. B5: first 4 indices per family, 20 tasks × 2 models = **40** extra calls. Linked stress: first 1 parent per family, order reversal + one-field counterfactual, B0/B3 × 2 models = **40** extra calls. Total **440** calls; 60 is the independent headline n. Stress exports for two parents/family are generated and hashed, but only the prespecified first parent is inferred.
- Development calibration v1 is retained separately. V2 clarifies that the action target is the PO identifier in the public request; request, policy and schema remain common across arms. Distractors now use the same identifier namespaces and business schemas as relevant entities, including unrelated alias/contract/check and alias/profile chains. Negative outcome mode is a Latin rotation across record-size bins, removing perfect outcome/size confounding. No changes were based on test performance.
- Context 40,960 tokens; maximum output 160 tokens; temperature 0; seed 20261118; thinking disabled. Conservative ASCII input bound: serialized public user prompt bytes + system bytes + 4096 reserved template/schema tokens + output limit must fit. Check actual runtime usage too. No silent B0 truncation is permitted. Sequential models, same decoding across arms; temperature zero is not a determinism guarantee.
- B5 is **generic query-biased graph extractive compression**, not a faithful named-method reproduction. It ranks complete records with token-set Jaccard links, 20 iterations, .85 propagation, .15 prior; prior is half uniform and half normalized BM25. No compressor inference calls or weights. This is engineering triage, not a claim about published learned/reversible methods. B5 uses full public evidence and the identical shared byte budget; no canonical policy modification.
- Budget is max(2000, floor(.25 × canonical B0 serialized tool bytes)), including source/scope-count metadata and retained/selection bookkeeping. All selected records remain exact public rows. B0 full is unconstrained. B2 seeded random and B6 private-support oracle are model-free only. B6 is an unbudgeted sufficient certificate diagnostic, not a deployable or matched-budget method.
- Public metadata contains truthful observed per-scope counts and upstream source completeness. Sufficiency requires all private relevant group records retained, or one positive block witness, plus any required source certificate. Partial-source negative deferral also retains all observed scope rows to distinguish missing a known positive from genuine upstream uncertainty. Support is a conservative proof, not minimal necessary evidence.
- B4 operates over every generated independent test task and stress export using independently implemented SQL, public records and fixed-template request parsing. It knows the workflow/schema and executable policy. This privilege and unrestricted structured access are an explicit engineering alternative, not natural-language parity with the LLM arms. Exact-scope filtering and the rejected format-prefix shortcut are development diagnostics.
- **Retry policy:** exactly one invocation per task/model/arm/replicate=0. Any timeout, transport failure, schema failure, output limit or context guard is retained as failure; no automatic retry or output substitution. A missing raw unit after interruption can be resumed once; completed errors are never rerun. Preserve append-only records. Whole-run process locking prevents simultaneous runners.
- **Statistics:** primary arm-minus-B0 correctness differences per model, task-paired percentile bootstrap with 10,000 draws and seed 20261118. B5 compares its 20 tasks to the matching B0 subset. Family and stress results are descriptive/exploratory; no independent-n inflation, causal attribution, multiplicity-adjusted significance or economic savings claim. Errors fail; missing planned calls are shown explicitly and make execution incomplete.
- Final source/config/data integrity and live model digest must pass before running or resuming. Freeze hash is self-checked. Report unsafe executed approvals separately from unsupported approvals, schema validity, wrong targets, evidence-present errors, and missing-evidence-associated failures. No claim that provenance sufficiency alone guarantees model reasoning.
