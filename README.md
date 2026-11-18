# Decision-Critical Evidence Preservation — Research Pilot

An executable, synthetic P0–P4 feasibility study of whether budgeted tool evidence preserves correct procurement actions. The study includes a competing deterministic SQL policy system, private executable references, real local model calls, paired analysis and a primary-source novelty audit.

Read [STATUS.md](STATUS.md) for factual phase coverage, invocation counts, hashes and the exact current resume command. The final analysis is written to [results/PILOT_REPORT.md](results/PILOT_REPORT.md), with [research decision](docs/GO_NOGO_DECISION.md), [limitations](docs/LIMITATIONS.md) and [reproducibility instructions](docs/REPRODUCIBILITY.md). A missing report during execution is not a completed result.

## Run / resume

Executed environment: Python3.12, local Ollama, pre-existing Qwen3 4B and Gemma4 12B weights, sequential inference. No paid APIs or real-world actions. Install a fresh environment with `uv venv --python 3.12 .venv` and `uv pip install --python .venv/bin/python -e . pytest`.

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m evidence_pilot integrity
.venv/bin/python -m evidence_pilot run
.venv/bin/python -m evidence_pilot diagnostics
.venv/bin/python -m evidence_pilot analyze
.venv/bin/python -m evidence_pilot report
```

`run` resumes incomplete frozen units and skips completed errors as well as successes. Do not overwrite the frozen manifest or raw records. For generation/preflight/fresh-replication details, read [REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md).

## Persistent specifications

Read AGENTS.md, STATUS.md, docs/03_PROTOCOL.md and docs/06_EXECUTION.md first; all docs/01_BRIEF.md through docs/07_DECISION_RULES.md govern the study. Implementation details: [benchmark specification](docs/BENCHMARK_SPEC_IMPLEMENTED.md). Decisions/deviations: [append-only log](docs/EXPERIMENT_LOG.md).

Private gold never enters selectors or prompts. B6 is an unbudgeted oracle diagnostic, not a method. B5 is generic graph extractive compression, not a faithful recent-method reproduction. Byte reductions are not token or monetary savings. Prior prototype numbers in the brief are separate from this pilot. A negative result is a useful outcome; no positive novelty claim is assumed.
