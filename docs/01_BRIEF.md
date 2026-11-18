# Research brief and previous feasibility work

## Working title
**Decision-Critical Evidence Preservation in Budget-Constrained LLM Agents** (provisional).

## Central research question
Can task-conditioned evidence selection with explicit handling of incomplete information improve the **correctness and efficiency of LLM agent actions**, compared with truncation, lexical retrieval, conventional compression, and deterministic queries?

## Why this matters
A large JSON tool response may contain many records and rules; an agent may discard a low-ranked record that overturns an action, omit records needed to aggregate, or infer nonexistence from incomplete pages. A high reduction ratio or lexical relevance score does not guarantee a correct action. We care about selection **relative to the complete decision procedure** and whether an agent knows when it must abstain or retrieve more.

## Prior feasibility study — separate from this pilot
The supplied November 2026 review described an engineering preflight with 150 synthetic cases, 750 model-free selector evaluations, and five passing tests. Families: lookup, latest record, aggregation, existence/absence, multi-source decision. JSON sizes: 25, 100, 300 records. Results:

| Method | Required evidence retained | Avg. payload reduction |
| --- | ---: | ---: |
| Full output | 100% | 0% |
| First 10 records | 8.7% | 81.3% |
| Random 10 records | 7.3% | 81.3% |
| Exact-key filter | 100% | 94.9% |
| Oracle upper bound | 100% | 95.7% |

**Interpretation:** architecture can generate executable gold answers without human annotation, but the first dataset was too easy for exact-key filtering. Reductions were **serialized-byte estimates**, not actual model tokens; there was **no LLM inference or correctness measurement**. These values must never be cited as current-pilot outcomes. The first pilot's ZIP or memo may not exist in this repo; inspect before reuse and do not assume access.

## Where research could be interesting
- Cross-record dependencies and rule precedence.
- Aggregates where selected subsets lead to wrong conclusions.
- Negative evidence requiring completeness certificates.
- Semantic/indirect entity references and near matches.
- Safe deferral or additional information retrieval when evidence is inadequate.

These are *hypotheses about a research gap*, not novel contributions established by the previous review. The most dangerous alternative is simply to execute a structured query over the database (and avoid sending unneeded records to an LLM at all).

## Expected research decisions
- **GO:** Meaningful, reproducible, evidence-driven failure remains; current solutions do not adequately address it.
- **NARROW:** Only a specific failure mechanism remains worth studying.
- **NO-GO:** Simple structured querying or existing methods adequately solve the meaningful task.
- **INCONCLUSIVE:** Scientific evidence is missing/underpowered/contaminated.

Not authorized by this scope: manuscript submission, claiming novelty, training a new model, or building a proposed novel selector after the pilot without a separate decision.
