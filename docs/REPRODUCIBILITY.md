# Reproduce and resume the executed pilot

Use Python 3.11+ (executed with 3.12.15), a local Ollama service, and the pinned models already installed. There are no paid API calls. Models run sequentially. The experiment was frozen before Git metadata existed; its immutable source, protocol, configuration and dataset snapshots plus SHA-256 identities remain the scientific provenance. GitHub packaging adds a separate repository commit and refreshed file-hash manifest.

## Inspect/recompute existing results (no inference)

```bash
cd /path/to/decision-critical-evidence-pilot
.venv/bin/python -m pytest -q
.venv/bin/python -m evidence_pilot integrity
.venv/bin/python -m evidence_pilot validate
.venv/bin/python -m evidence_pilot diagnostics
.venv/bin/python -m evidence_pilot analyze
.venv/bin/python -m evidence_pilot report
.venv/bin/python scripts/finalize_report.py
```

`diagnostics` recomputes model-free public selectors, B4 and private B6. `analyze` checks frozen integrity first, then scores stored raw actions against private synthetic state, audits the exact grid, and resamples paired tasks. It performs no model inference. `report` renders the resulting tables and six figures into the Markdown report. The reporting-only finalizer adds full-benchmark diagnostic counts and the documented lost-response accounting; it does not alter frozen analysis. Inspect `results/summary.json`, `results/tables/`, `results/scored.jsonl` and `results/figures/`.

## Resume pending frozen inference

```bash
.venv/bin/python -m evidence_pilot run
.venv/bin/python -m evidence_pilot diagnostics
.venv/bin/python -m evidence_pilot analyze
.venv/bin/python -m evidence_pilot report
.venv/bin/python scripts/finalize_report.py
```

The runner self-checks the frozen manifest, protocol, sources/tests, dataset and current Ollama model digests. An exclusive process lock prevents duplicate concurrent runners. It skips every completed task/model/arm/replicate unit, including completed errors; no error rerolls. Each raw JSONL line is flushed and fsynced. The runner stores progress after each completed unit and never overwrites completed outputs. A hard interruption during an in-flight call can leave an unrecorded invocation; if this occurs, record the unresolved attempt and interruption in EXPERIMENT_LOG before resuming. Do not claim an exact provider call total if a response was lost. No such lost response should be inferred merely from a missing planned unit.

## Fresh reproduction in a separate directory

Copy the repository's specifications and frozen `src/`, `tests/`, `configs/` from `results/frozen/` into a fresh workspace. Preserve the original results and never clear or overwrite its completed raw grid. Install dependencies with:

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e . pytest
```

The exact executed environment is recorded in `results/environment/requirements-freeze.txt`; `pyproject.toml` declares the minimal libraries. For an exact dependency recreation, use the pinned package versions from that file, omitting its machine-specific editable-path line and reinstalling `-e .` locally.

The installed selected Ollama model digests are in `results/frozen/manifest.json`; resolve and verify those exact weights before execution. Model tags can change. Do not blindly download moving tags or exceed the <9-GB-new-weights rule. This pilot used pre-existing Qwen3 4B and Gemma4 12B weights; preferred model partial-download attempts are documented separately and are not experimental models.

```bash
.venv/bin/python -m evidence_pilot generate
.venv/bin/python -m evidence_pilot validate
.venv/bin/python -m evidence_pilot preflight
```

For a fresh replication of the SAME frozen design, transfer the original frozen manifest/source snapshots and verify regenerated public/private hashes match, then run the frozen grid. Creating a new freeze creates a separately identified replication and requires retaining its own environment/model identities and dev-only decisions. Never edit a frozen test set or prompt based on held-out outcomes. `freeze` refuses to overwrite an existing frozen manifest.

## Artifact lineage

- `data/manifests/dataset.json`: development, independent test, linked stress IDs and public/private hashes.
- `data/*/public`: legitimate observed records and common policies; `data/*/private`: reference action, state, conservative support; never selector input.
- `results/frozen`: exact protocol/configuration/source/tests/dataset snapshot and grid manifest.
- `results/runs/development*`: calibration only, never test metrics.
- `results/runs/heldout/raw.jsonl`: append-only actual local calls, responses, hashes, actual backend tokens/timings, errors, and model identity.
- `results/model_free.json`: selectors/B4/B6 diagnostics over all generated exports; B6 is privileged and unbudgeted.
- `results/scored.jsonl`: raw-backed action/state outcomes and evidence diagnostics.
- `results/tables/paired.csv`: matched denominators and 95% bootstrap intervals. Family/stress results are exploratory/descriptive.
- `results/literature`: primary-source and implementation audit receipts. No prior-work experiment was rerun.

Byte reductions do not equal token reductions or monetary savings. Actual token counts are backend measurements. Temperature zero and a seed do not guarantee bitwise reproduction across runtime/hardware versions.

## Hash definitions

JSON object hashes (task, payload, dataset and freeze manifests) use sorted-key, compact UTF-8 JSON without a trailing newline, as implemented in `evidence_pilot.common.digest`. Source, protocol and raw-file hashes use their literal bytes. A shell SHA-256 of a JSON file can therefore differ from its canonical-object hash by serialization/newline. The `integrity` command applies the correct definitions automatically.

## Exact input replay versus selector regeneration

The final audit found a small BM25 ordering limitation: four of 440 regenerated payloads (two aggregation tasks across both models) can reorder tied records under a new Python hash seed. Eight explicit hash seeds reproduced two orders, with the same record membership and sufficiency; floating scores differ by at most 8.88e-16. Frozen source was preserved. See `results/bm25_hash_seed_audit.json` and `results/selector_replay_check.json`.

For exactly the original model-facing payload and record order, use the retained raw requests, not a newly recomputed BM25 order:

```bash
.venv/bin/python scripts/export_frozen_requests.py
```

This real, tested command exports 440 request JSON files and `results/replay_requests/manifest.json`. It verifies frozen sources, each payload hash and the reconstructed prompt hash. It performs no inference and adds no model calls. The request manifest retains original unit order and model digests; any new replay must use a separate results directory and sequential models. Identical inputs do not promise bitwise-identical backend outputs. The four lost response bodies and their token usage remain unknown.
## GitHub repository snapshot

`results/reproduction_manifest.json` hashes the exact published file bytes (excluding itself). The original prepublication workspace manifest remains preserved locally as the ignored `results/reproduction_manifest.local.json`. The runtime metadata at `results/environment/runtime.json` keeps the model tags, digests, quantization and runtime information, with local absolute model-file paths omitted. The original runtime JSON is preserved locally as `results/environment/runtime.local.json` and is excluded from GitHub. The original editable-install and dependency-freeze captures are likewise preserved as ignored `*.local.*` files; their published copies use a repository-relative path. The same repository excludes generated `*.egg-info/`, the preferred-model download log, and intermediate red-test logs; these do not contain held-out results. Virtual environments, caches, model weights, temporary directories and scratch files are also excluded by `.gitignore`. The frozen source, generated benchmark, raw inference records, exact request payloads, scored outputs, audit receipts, reports, tables and figures are included.
