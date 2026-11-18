# P2 — comparator specifications and scientific fairness

Implement all feasible conditions and test them with unit cases **before** held-out inference. A missing comparator must be documented, not renamed or faked. See the shared budget and evaluation rules in `03_PROTOCOL.md`.

| ID | Comparator | Exact role / restrictions |
| --- | --- | --- |
| B0 | **Full** | All available original evidence and completeness metadata; unconstrained reference. No silent truncation. |
| B1 | **Head truncation** | Select first records into the same budget; preserve valid JSON and truthful metadata. Record actual records kept. |
| B2 | **Seeded random** | Uniform or declared random record selection into budget; mainly model-free diagnostic. |
| B3 | **BM25 lexical retrieval** | Index model-visible records, rank against request, select within budget. Document tokenization and unit of indexing. No oracle relevance labels. |
| B4 | **Practical deterministic query/policy system** | Use schema-aware joins, aggregates, policy rules, and completeness checks over legitimate full structured input; test on every supported task, record assumptions about schema knowledge and user-intent parsing. **Not** the same as a gold action lookup or a selection oracle. |
| B5 | **Conventional compression** | Prefer verifiable existing open implementation suited to this task; otherwise label LLM summary or equivalent as **generic compression baseline**, not Squeez/DTOC/TreeAgent. Track compression model tokens, calls, latency, and any hallucinated completeness. |
| B6 | **Oracle sufficient evidence** | Gold-provenance-based upper bound for diagnostics only; never describe as non-oracular/deployable or include in fair comparisons. |
| Optional | Recovery-on-demand | Allow controlled extra information requests to a retained original store; compare with matching access rights and account for every turn/call. Do not call it DTOC unless faithful. |

## Shared implementation requirements
- Same underlying task, model, system policy text, output JSON schema, decoding configuration, and evaluation oracle for paired arms; only the tool-evidence treatment changes.
- Budget enforcement counts serialized bytes of **all** material supplied as selected tool data including completeness metadata. Record actual input tokens from runtime; do not use serialized bytes as token counts.
- If budget cannot fit a meaningful header, record an explicit insufficient-evidence representation; never forge an assertion that records were complete.
- Do not let the selection algorithm modify canonical business rules, infer hidden facts, or add an unsupported explanation that changes the action semantics.
- If deterministic query is privileged by having fully scripted task intent or policies, disclose that as an engineering counterfactual and do not claim strict apples-to-apples parity with the natural-language LLM arms.
- For B5, predefine whether compression operates on full evidence and what happens when that compressor itself exceeds context limits. Cost is measured end to end, including all upstream inference.
- Prove selected evidence is actually necessary/sufficient using the formal policy and completeness checks. Never infer sufficiency purely from keyword overlap.
- Save budget compliance, selected record IDs/hashes, true coverage, and failure reason per case.
