# P4 scientific decision rules

Assign exactly one verdict: **GO**, **NARROW**, **NO-GO**, or **INCONCLUSIVE**. Protocol criteria are provisional screening heuristics until frozen before held-out inference. Do not use significance thresholds to manufacture confidence or interpret exploratory subgroup effects as established.

## GO — worth a full research project
The testbed is valid, resists trivial shortcuts, and shows a meaningful, repeatable **evidence-handling** failure rather than primarily bad model reasoning; full-evidence model correctness supports evaluating selection (approximately ≥70% is a pilot competence heuristic); comparison is fair with direct deterministic-query and conventional-method baselines; at least a plausible nontrivial scientific gap survives primary-literature review. A ≥10 percentage-point observed gap on relevant controlled conditions may be practically interesting, but must be accompanied by uncertainty, baseline analysis, and mechanism attribution.

## NARROW — revise the question
Only one focused setting (for example completeness-sensitive negative evidence, cross-source dependency recovery, or safe deferral) has a compelling failure; broad task-conditioned compression claims are too crowded or weak. Recommend **one** sharply scoped falsifiable next experiment, not a laundry list.

## NO-GO — stop/reframe
Valid cases are essentially solved by deterministic querying, trivial filtering, or established systems; full-evidence LLMs are too unreliable to isolate selection; the benchmark's hardness is artificial; or robust fair comparisons show no useful remaining evidence-handling gap. A negative result is successful research triage.

## INCONCLUSIVE — not enough evidence
Less than the scientifically meaningful paired coverage, invalid benchmark, missing indispensable comparator, unavailable model(s), significant system contamination, or confidence intervals too broad to decide. Do not convert blocked execution into a negative empirical finding.

## Required report outline
1. Research question, preregistered hypotheses, frozen configuration/hash.
2. Source-backed literature audit and overlap/novelty threats.
3. Synthetic workflows, task counts, example cases, generator/oracle validation, leakage checks.
4. Baselines and comparison fairness, including deterministic query privilege assumptions.
5. Runtime, exact model digest, quantization/context, number of completed calls/failures, test coverage.
6. Exact correctness rates (numerators/denominators), paired differences and 95% CIs, per-family and per-model results.
7. Evidence sufficiency vs action correctness; reason-vs-selection failure attribution, deferrals, schema failures, record order/counterfactual effects.
8. Payload bytes vs actual tokens vs total inference overhead and latency; no invented dollar costs.
9. Limitations: synthetic data, small model(s), calibration risk, power, dependence, unreproduced related methods.
10. Verdict and the **smallest justified next step**, or explicit stop recommendation.

Plots if supported: accuracy by model/arm; family performance; reduction-vs-accuracy; evidence-sufficiency-vs-success; failure mechanisms; end-to-end latency/call overhead. Every figure must be reconstructible from raw records and identify missing data.
