# Related work — **provisional leads, not verified citations**

The references and characterizations below are taken from the supplied earlier feasibility memo. **Codex must verify the papers, publication records, actual methods, datasets, source-code status, and overlap against original sources at P0.** Do not turn the provisional descriptions into unqualified facts in a research paper or final report.

| Candidate reference | Link | Provisional relevance / novelty threat |
| --- | --- | --- |
| How Good Are LLMs at Processing Tool Outputs? | https://aclanthology.org/2026.eacl-long.134/ | Structured JSON tool-output processing and evaluation baselines. |
| Associated research code | https://github.com/LongFuncEval/toolJSONprocessing | Potential reuse/benchmark comparison; inspect license and exact task design. |
| Squeez | https://arxiv.org/abs/2604.04979 | Task-conditioned pruning/compression of coding-agent outputs; do not call a different summarizer a reproduction. |
| DTOC | https://arxiv.org/abs/2609.26121 | External retention and on-demand recovery of tool outputs; reversible processing is not automatically novel. |
| TreeAgent | https://arxiv.org/abs/2611.13946 | Structure-aware/hierarchy-preserving processing; check actual contribution. |
| When Absence Is Evidence | https://arxiv.org/abs/2608.04591 | Complete/incomplete evidence and absence reasoning. |
| Agents Don't Paginate | https://arxiv.org/abs/2608.26130 | Ordering/retrieval evidence may not translate to downstream agent improvement. |
| Context Is a Pipeline, Not a Window | https://arxiv.org/abs/2610.36114 | Harness truncation and lost/broken evidence. |
| Token Reduction Is Not Cost Reduction | https://arxiv.org/abs/2607.12161 | Net economic cost can worsen despite token trimming. |

## P0 verification deliverables
Create `docs/LITERATURE_MATRIX_VERIFIED.md` with, for each verified paper: bibliographic metadata and date, experimental problem, input/output, method, benchmarks and metrics, downstream accuracy measurement, code/license/access, replication feasibility, direct overlap and candidate distinction, direct URL. Mark inaccessible/unverified items explicitly; do not invent content. Check closely related work discovered during verification, especially methods tackling completeness, dependency selection, and decision-oriented evaluation.

## Novelty analysis questions
1. Is decision-critical evidence preservation already formalized/evaluated elsewhere?
2. Does an existing tool-output compressor or retrieval system use an explicit evidence sufficiency check?
3. Does a reversible retrieval baseline already solve it?
4. Are the tasks simply database queries best expressed in SQL/policy code?
5. Would a new result be a benchmark/evaluation contribution, rather than a new algorithm?

Produce `docs/NOVELTY_RISKS.md` with an honest overlap matrix and unanswered questions; no positive novelty claim until tested.
