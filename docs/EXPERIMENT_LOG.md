# Append-only experiment log

## 2026-11-18 — Session start / P0
- Read AGENTS.md, STATUS.md, and all seven research specifications from disk. No prior-chat evidence used.
- Workspace contains starter documents only and no Git metadata. Preserve original specs; use SHA-256 source snapshots for reproducibility rather than invent a commit identity.
- Environment: macOS 26.4 arm64, 16 GiB RAM, Ollama 0.40.15 reachable locally. Python 3.12.15 available through uv; system Python 3.9 is below preferred floor and will not run the pilot.
- Verified preferred Ollama registry manifests: qwen3.5:4b model 2,648,593,216 bytes + projector 675,569,120; ministral-3:3b model 2,953,825,504 bytes. Combined new weight upper bound 6,277,987,840 bytes, below 9 GB. No paid endpoints.
- User autonomy instruction overrides routine skill approval handoffs; implementation follows existing research specs, with dev-only choices documented before freeze.

## 2026-11-18 — P1/P2 development validation and calibration v1
- Implemented five synthetic procurement families, private reference/state simulator, separate public-only SQLite B4, and B0/B1/B2/B3/B5 selectors. B5 is a generic query-biased graph extractive compressor, NOT a Squeez/DTOC/TreeAgent reproduction. B6 remains private diagnostic only.
- Initial dev generation caught six-digit record ID collisions. Added uniqueness rejection sampling and regression over all 30 real development seeds. No held-out data had been generated or inferred.
- Added explicit scope-count closure in reference and B4 after a partial-aggregate regression demonstrated unsafe approval without it. All 25 tests passed before preflight.
- Preferred Qwen3.5:4b download canceled after observed ~720 KB/s and >1h estimate; partial transfer only, not a loaded model. Use installed Qwen3:4b-instruct-2507-q4_K_M and Gemma4:12b-it-qat as two-family fallback. Their real JSON smoke calls succeeded sequentially. No new complete model weights downloaded.
- Calibration v1 prompt caused Qwen to confuse requested PO target with evidence scope. Preserve all v1 calls under results/runs/development/raw.jsonl and prompt/config snapshot results/calibration-v1/. Clarify target from public request for all arms, lower context from 49152 to 40960 after conservative dev byte bounds (max observed ~34267 + output160); no hidden information added. Run one final dev calibration before freeze. Earlier dev calls never count as test.
- Model-free evidence support is a conservative complete group certificate, not a claim that every included row is minimally necessary. Source completeness and observed scope-count certificates are explicit public tool metadata.

## 2026-11-18 — Independent prefreeze review and repairs
- Read-only scientific review found D-prefixed background scopes distinguishable from S/V/R/O relevant scopes: a public-only format filter retained sufficient evidence within budget for 30/30 development cases. Rejected this invalid hardness and regenerated DEVELOPMENT ONLY with same-namespace background entities and realistic irrelevant alias/contract/check or alias/profile chains. Added a regression explicitly rejecting that shortcut.
- Negative task outcomes had been perfectly confounded with size because both used index modulo three. Changed dev generator to a Latin rotation `(index + index//3) % 3`; regression verifies each dev size has multiple outcomes.
- Required observed-scope support for partial-source negative deferrals, rather than the empty certificate. Positive active-block witness remains sufficient even on an upstream partial result.
- Added stress public/private hashes to dataset manifest, validation and freeze integrity; added live model digest guard and freeze self-check; mutations are rejected by regressions.
- 37 tests passed after initial repairs, and later targeted integrity tests passed. All failures were prefreeze implementation findings, preserved in results/environment/test-*-red.log. No held-out outcomes inspected.
- Literature audit verified all eight supplied papers and inspected published implementations; added LLMLingua-2 and tau-bench. No positive novelty claim; broad pruning/completeness/recovery/state-scoring motivations have precedents. See verified matrix and source receipts.
- Predeclared reduced grid from development runtime: 60 balanced tasks × two models × three mandatory arms=360 calls, 20 balanced B5 tasks ×two=40, 10 linked variants ×two arms ×two models=40: total440. Generated benchmark remains100 independent test tasks; remaining40 are not in LLM grid. Stress comparisons are descriptive.

## 2026-11-18 — Final prefreeze implementation verification
- Whole suite: 45 passing tests, including independent hand-calculated cases, whole benchmark repeat-generation, scope closure, same-format distractors, negative outcome/size rotation, model digest mismatch, stress export tampering, freeze self-check, process locking, schema/state distinctions, paired denominators, error accounting and end-to-end figure/report fixtures. Full output: results/environment/tests-prefreeze.log.
- Near-duplicate audit uses multiset Jaccard on business record attributes after identifier removal and compares each test item to dev items in its family/bin. This measures template similarity, not identical input leakage; it is recorded, not used to revise held-out tasks. Exact public payload hashes must be unique.
- Six figure designs were visually checked on explicitly synthetic visualization fixtures; those fixtures are not experimental outcomes. Real result figures will be checked again after execution.
- Considered exact runner tokenization to reduce context allocation; `/api/tokenize` is unavailable while the internal llama-server endpoint exists. Retained the simpler, conservative byte-bound context guard and 40,960-token configuration; no undocumented internal endpoint is used by experiment code.

## 2026-11-18 — P0/P1/P2 complete; protocol frozen
- Freeze 424d83723b2aca6f2df1696d138dff01b3389a504676670e5e6c6552f8aab2da at 2026-11-18T15:54:59Z; protocol SHA 381c65c4f59109c55b7a93d948f1442f0f160d4da95cf8e8166f33984c749239; dataset SHA f061e9aa66ad751fef649c356bc77a18047ffc84e9a05f9b8c7f045efa966862.
- Validation: 30 development,100 independent test,20 linked stress exports;150 unique public payload hashes; all oracle/SQL/state/closure/leakage/budget/reproducibility/counterfactual/order assertions passed.
- Real calibration64 calls total,32 v1 +32 v2,zero errors. Final full-evidence development competence Qwen3 3/6 and Gemma4 5/6; no test inference or test tuning occurred.
- Frozen exact grid440 calls with the balanced60-task fallback; source/tests/config/protocol/dataset snapshots saved before inference. No scientific result claimed yet.

## 2026-11-18 — Deliberate session interruption / checkpoint recovery
- Unified execution stopped during held-out inference. Retained raw/progress checkpoint contains21 completed units, ending dependency005/Qwen/B1 at15:58:45Z. No runner process remains; frozen integrity still passes.
- Local Ollama log confirms four additional HTTP200 chat completions after that retained response (17:58:57,17:59:03,17:59:05,17:59:09 Cairo), whose response bodies are not present in retained raw records. Server evidence archived at results/environment/interruption-server-tail.log. Their sequential grid identities are inferred as dependency005/B3 and dependency006/B0,B1,B3; action outputs are UNKNOWN and will not be fabricated.
- Resume policy for missing raw units was specified before freeze. Resume those incomplete units once, preserving all21 retained outputs including any failures. This creates four additional lost-response attempts in call accounting; report them separately from the440 retained planned units. No unseen response was selected by outcome, and no successful retained call is repeated.
- Deviation affects exact call/token/time accounting: four backend completions have no retained action/usage; HTTP durations total23.19seconds, excluding client/selector overhead. Do not imply all invocation overhead is measured.

## 2026-11-18 — Post-freeze read-only validation and reporting extension
- Certificate replay over frozen exports:150 oracle certificate views plus309 views marked sufficient by public selectors reproduce the private reference action, zero discrepancies. Saved results/sufficiency_validation.json. No inference input or scoring rule changed.
- Model-free B4 solves100/100 independent test tasks. This is a query-system finding, not LLM accuracy and not a claim about arbitrary real-world tasks. Full structured access and fixed-template intent parsing are explicit privileges.
- Identifier-stripped business-attribute similarity is >=.95 for13/100 test cases relative to a development neighbor of the same family/size. All150 exact public payload hashes are unique. Treat this as template limitation, not an expanded independent domain count; do not revise tests from this audit.
- Added scripts/finalize_report.py and a separate reporting regression AFTER freeze. This idempotent, reporting-only extension corrects generated100 versus inferred60 wording, adds all-test model-free diagnostics, and discloses the interruption/lost-response accounting. It changes no frozen inference/source, primary statistic, pair denominator or decision rule. Frozen integrity continues to pass. Its output is created only from executed analysis artifacts.

## 2026-11-18 — First model complete
- Qwen retained220/220 planned units (200 independent-task arm calls +20 linked stress calls), zero invocation errors. Four prior lost-response completions remain separate in the interruption receipt.
- Scored the completed fixed Qwen grid for an interim checkpoint while Gemma runs. No subsequent setting/source/grid changes; no held-out tuning. results/interim_first_model.json is explicitly interim, not a final verdict.

## 2026-11-18 — Continued inference and oracle-budget diagnostic
- Retained checkpoint 344/440; errors {}. Gemma has completed the first three family grids; original source/configuration unchanged.
- All100 independent-test B6 conservative sufficient certificates fit the shared byte cap; maximum certificate/cap ratio0.4650168042. B6 remains an unbudgeted private upper bound, not a usable selector. Thus these cases establish no inherent evidence-size impossibility at this cap. Reporting-only table adds the measured budget-coverage count.

## 2026-11-18 — P3 complete / P4 actual analysis and replay audit
- All440 planned retained units completed with440 backend response bodies, zero invocation/schema errors, no missing/duplicate grid units. Both models unloaded and runner exited0. Minimum paired coverage60 independent tasks across two families is met; preferred100-task inference was not executed. Additional four lost-response completions remain separately accounted.
- Actual correctness B0/B1/B3: Qwen26/60,5/60,7/60; Gemma23/60,18/60,21/60. B5: Qwen2/20, Gemma6/20. Paired bootstrap10000 draws: Qwen head−35.0pp [−48.33,−21.67], lexical−31.67pp [−45,−18.33]; Gemma head−8.33pp [−23.33,6.67], lexical−3.33pp [−20,13.33]. All intervals95%; family analyses exploratory.
- Audit verified action/raw-response agreement, prompt/payload/model hashes, truthful metadata, budget/context guards,130 unique independent generation seeds and220/220 identical cross-model task/arm payload pairs. Actual raw SHA256:8dc908666acf694c36c62534119f804151bc3d7d055368e5fd9efd835b5ad1d7.
- Fresh-process source replay found four B3 payload ordering differences, two aggregation cases across both models. No record-membership or sufficiency changes. Eight fixed PYTHONHASHSEED values reproduced two orders; BM25 accumulates over an unordered query-term set, yielding score differences up to8.8818e-16. This is a disclosed reproducibility limitation; frozen source and completed outputs were not altered or rerun.
- Added tested export-only scripts/export_frozen_requests.py. It reconstructed440 original prompt/payload orders and hashes from raw records, creating results/replay_requests/ without inference. Exact input replay is available despite selector tie-order variation. Four lost response bodies remain unreconstructed.
- Generated six actual-data PNG/PDF figure pairs; visually inspected all six. Re-rendered failure breakdown with model panels to eliminate crowded labels, using identical frozen category counts. Reporting-only finalizer also supplies30 exploratory family paired comparisons,400-unit family failure accounting, eight linked-stress descriptive rows, action execution validity and complete phase-call usage counts. No primary scoring/statistic changed.
- Observed local backend responses:2 smoke +64 calibration +440 held-out=506 retained; plus4 lost completions=510 observed completions total. Usage/time sums exclude unknown lost-body usage. Generic B5 adds zero compressor model calls. No paid API calls or real-world business actions.
- Scientific verdict: NO-GO for this structured-workflow benchmark. Public deterministic SQL solves100/100; both full-evidence models miss the approximately70% competence screen; every oracle certificate fits the budget. Existing-method superiority and positive novelty are not established. Stop/reframe the broad selector proposal.

## 2026-11-18 — Final completion checkpoint
- P0–P4 executed under the frozen60-task fallback;440 retained planned units and all required artifacts complete. Final whole test suite47 passed; six actual-data figure pairs visually checked, with reporting-only failure-chart spacing corrected.
- No frozen source/config/data or raw model output was changed after inference. Reproducibility caveats (four lost responses and four cross-process BM25 ordering differences) are explicitly retained; exact440-input request export verified. No positive novelty claim and no proposed new selector training.
- NO-GO decision and smallest stop/reframe recommendation saved. Exact offline reproduction and idempotent resume commands are in STATUS.md and docs/REPRODUCIBILITY.md.

## 2026-11-18 — Delivery verification
- All six final PDF figures were rendered with native macOS Quick Look (Poppler unavailable) and visually inspected in addition to their PNG counterparts. No clipping, overlap or glyph defects remained. Temporary render files removed; final PNG/PDF exports retained.
- Final suite: 47 passed. Primary frozen source/data integrity passes. Exact 440-request export is verified and adds zero inference calls. All 220 cross-model task/arm payload pairs are identical.
- Final status, report, decision, limitations, append-only history, raw/scored data, paired/family/stress tables, six plots and reproduction commands are present. No unfinished experimental units remain in the declared grid.
