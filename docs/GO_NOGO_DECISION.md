# Pilot research decision

**NO-GO** for the implemented structured-workflow pilot.

The public deterministic query solves every independent benchmark task; no selector contribution is established in this structured setting.

Deterministic query correctness over all generated independent test cases: 100/100. Full-evidence model correctness: Gemma4 12B 23/60 (38.3%); Qwen3 4B 26/60 (43.3%). Both tested models fall below the frozen approximately 70% competence screen; these results cannot cleanly isolate evidence selection from model reasoning.

Oracle certificates within the byte cap: 100/100. The verified literature already covers the broad pruning, completeness, recovery and state-scoring motivations; no positive novelty claim is supported. B5 is generic graph extraction, with no faithful released-method reproduction.

**Smallest justified next step:** stop the broad selector proposal on this benchmark. Conclusions apply to typed synthetic workflows with scripted intent/policy knowledge and trusted scope counts.

Retained grid: 440/440 units; additional lost-response completions: 4. See [report](../results/PILOT_REPORT.md), [paired intervals](../results/tables/paired.csv), [limitations](LIMITATIONS.md) and [reproduction](REPRODUCIBILITY.md).
