# P1 — benchmark, data contracts, and oracle quality

## Core data model
Each instance has: unique `task_id`, `parent_task_id` if variant, `family`, `seed`, `context_size_bin`, private environment/state, policy specification, synthetic tool records from 1+ sources, user request, tool completeness/pagination metadata, executable expected action/state, and private evidence provenance. Create a strictly separate **model-facing export** containing only legitimately available request/policies/data; the gold export must never be loaded by selectors or the inference prompt constructor.

Synthetic workflows may include refunds/payments, booking capacity, procurement approval, policy-controlled service requests. Prefer coherent, consistent schemas and high-quality hard distractors over meaningless random JSON fields. Avoid private or real client/student data.

## Five task families — 20 independent held-out tasks each
1. **Cross-record dependencies:** join multiple source records; include linked identifiers, timestamps, and dependencies absent from literal query words.
2. **Exceptions / overrides:** general rule altered by an explicit higher-priority policy, exception, or amendment; specify unambiguous precedence and effective dates.
3. **Aggregation / ranking:** compute across a complete eligible set, including ties/missing-value rules; dropping one decisive record changes sum, rank, or threshold outcome.
4. **Negative evidence / completeness:** distinguish certified empty/full result vs empty partial page, missing source, and unknown state; safe decision may require defer/request-more instead of unsupported absence.
5. **Indirect semantic reference:** identify target via alias/description/relationship/temporal attributes and near matches, not an exact key from the request; deterministic oracle must unambiguously disambiguate.

## Construction rules
- 30 independent development tasks, 100 independent frozen test tasks (20/family); context bins ~50, 150, 300 records where feasible on local hardware. Generate sizes before evaluation. No changing held-out items to increase difficulty after seeing outcomes.
- Clear, verified rule interpreter/oracle; an independent assertion suite or reference implementation must test edge cases, tie-breaks, precedence, temporal constraints, and completeness.
- Include explicit counterfactual pairs: change exactly one decisive field/record/completeness status, rerun oracle, assert changed action and matched unaffected fields. Link variants, do not count them as new independent n.
- Include distractors supporting plausible but incorrect decisions; ensure cases cannot always be solved using the key directly quoted in the question. Compute and report a trivial exact-key baseline before freezing test split, using dev cases for revisions.
- Every task must have one fully specified reference outcome, including justified deferral only when actual evidence access requires it; do not leave ambiguous outcomes to subjective LLM judgement.
- For aggregates/absence, define why the selected subset is *sufficient*: all scope-relevant records plus trustworthy completeness proof, or a logical certificate covering the aggregate. Simple inclusion of a few relevant records is not enough.
- For policies involving current state, execute proposed action against an **isolated sandbox simulation** to score final state. No real payment, booking, communication, or account updates.

## Required validations
- Stable seeds and generator hashes; repeat-generation byte-identical checks.
- Unique task IDs, split non-overlap, near-duplicate checks, JSON/schema validity.
- No model-visible fields named or encoding `gold`, `correct_action`, `required_evidence`, or private provenance; automated leakage check.
- Oracle can solve each task deterministically; counterfactual outcome actually flips when expected.
- Completeness metadata cannot contradict record state.
- Baseline selectors cannot import oracle modules or read gold data by filesystem path.
- Golden action schema validation and state-transition unit tests.
- Inspect easy shortcuts via exact-ID and deterministic key filters; revise only dev generator/config before test freeze.

## Storage
Generate a versioned manifest (`data/manifests/`) with generator/config/hash/seed/split, plus separate raw tool payloads and hidden ground truth. Repository paths and CLI may be adapted by implementation; never accidentally feed gold labels to inference. Keep source, method, and experiment artifacts portable.
