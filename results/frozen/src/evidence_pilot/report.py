"""Render an evidence-linked report from executed analysis, never hypothetical results."""
import json
from pathlib import Path
from .common import ROOT


def _table(rows, columns):
    header='| '+' | '.join(label for _,label in columns)+' |\n'
    header+='| '+' | '.join('---' for _ in columns)+' |\n'
    def fmt(value):
        if value is None:return 'missing'
        if isinstance(value,float):return f'{value:.3f}'
        return str(value).replace('|',' / ')
    return header+''.join('| '+' | '.join(fmt(r.get(key)) for key,_ in columns)+' |\n' for r in rows)


def report(root=None):
    root=Path(root or ROOT)
    summary_path=root/'results/summary.json'
    if not summary_path.exists():
        raise FileNotFoundError('Run python -m evidence_pilot analyze before report')
    s=json.loads(summary_path.read_text());f=json.loads((root/'results/frozen/manifest.json').read_text())
    coverage=s['coverage'];config=f['config'];query=s['query']
    sections=[]
    sections.append('# Decision-critical evidence pilot — executed feasibility report\n\n'
                    f"Verdict: **{s['verdict']}**. {s['verdict_reason']}\n\n"
                    'This report summarizes stored invocations, including failed calls. Prior prototype numbers are excluded. '
                    'All conclusions are limited to the implemented synthetic benchmark.\n')
    sections.append('## 1. Research question and frozen protocol\n\n'
                    'Does budgeted evidence selection preserve executed procurement-action correctness relative to full evidence? '
                    'The preregistered hypotheses concern truncation/lexical losses, formal evidence sufficiency, safe deferral, '
                    'and the competing explanation that structured querying solves the task.\n\n'
                    f"Freeze SHA-256: `{s['freeze_sha256']}`. Protocol SHA-256: `{s.get('protocol_sha256')}`. "
                    f"Frozen at `{f.get('frozen_at','unrecorded')}`. Configuration and source snapshots: [frozen manifest](frozen/manifest.json). "
                    'See [protocol](../docs/03_PROTOCOL.md).\n')
    literature=[]
    for name in ['LITERATURE_MATRIX_VERIFIED.md','NOVELTY_RISKS.md']:
        path=root/'docs'/name
        if path.exists():literature.append(f'[{name}](../docs/{name})')
    sections.append('## 2. Literature and novelty\n\n'+
                    ('Primary-source review artifacts: '+', '.join(literature)+'. The source audit must be read separately; statistical results do not establish novelty. '
                     if literature else 'A verified literature audit has not been found. Novelty remains unresolved. ')+
                    'B5 is generic query-biased graph extractive compression, not a faithful reproduction of a published compressor. '
                    'Structured query execution, completeness certificates, database provenance, retrieval, and existing compression systems are substantial overlap threats.\n')
    model_free=s.get('model_free',[])
    families=sorted({r['family'] for r in s['family']})
    validation=root/'results/validation.json'
    validation_text=validation.read_text().strip() if validation.exists() else 'Validation artifact absent; consult execution log.'
    sections.append('## 3. Workflows, benchmark, and validity\n\n'
                    f"The frozen independent test set contains {s['independent_planned']} tasks across {len(families)} observed families: "+', '.join(families)+'. '
                    'Tasks are synthetic procurement decisions with executable APPROVE/REJECT/DEFER outcomes. '
                    'For example, a purchase can depend on an alias-linked contract and its latest check; aggregates need every eligible charge, '
                    'and a negative decision needs truthful source and retained-scope completeness. '
                    'Private gold support/action/state are excluded from model-facing selectors. '
                    'Linked order variants and counterfactual twins are not independent tasks.\n\n'
                    '[Dataset manifest](../data/manifests/dataset.json), [validation](validation.json). Validation artifact:\n\n'
                    '```json\n'+validation_text+'\n```\n')
    sections.append('## 4. Baselines and fairness\n\n'
                    'B0 receives full observed evidence; B1 receives head records; B3 uses BM25 lexical ranking. '
                    'B2 seeded random, B6 private-support oracle, and EXACT_KEY are model-free diagnostics. '
                    'B6 is an unbudgeted privileged upper bound and is not a usable method. '
                    'B5 uses generic graph extraction on the prespecified balanced subset. '
                    'Budgeted selectors share the serialized-byte cap, public request, policy, schema, scope counts, and upstream completeness. '
                    'B0 is unconstrained. A 2,000-byte floor can exceed 25% for small payloads.\n\n'
                    f"B4 deterministic query executes public policy over the full structured result: {query['correct']}/{query['n']} correct "
                    f"({query['planned']} planned). Its privilege is direct access to typed records and explicitly executable policy, "
                    'without the LLM payload restriction; it sees no private gold and can invalidate the need for an LLM selector in this setting. '
                    'Its SQL/reference agreement is a validation check, not a claim of realistic database coverage.\n')
    model_rows=f.get('models',[])
    sections.append('## 5. Runtime and coverage\n\n'
                    f"Stored calls: {coverage['executed']}/{coverage['planned']} planned units, {coverage['unique_executed']} unique. "
                    f"Missing: {len(coverage['missing'])}; unexpected: {len(coverage['unexpected'])}; duplicates: {len(coverage['duplicates'])}. "
                    f"Invocation errors: {sum(s['error_counts'].values())}. Errors count as failures and are never rerolled selectively. "
                    f"Context: {config.get('num_ctx')} tokens; output limit: {config.get('num_predict')}; "
                    f"temperature: {config.get('temperature')}; seed: {config.get('seed')}; retry policy: `{config.get('retry_policy')}`. "
                    'Models execute sequentially via local Ollama. Exact model metadata/digests:\n\n'
                    +_table(model_rows,[('name','Model'),('digest','Digest'),('size','Stored bytes')])+
                    '\n[Runtime metadata](environment/runtime.json), [coverage audit](tables/coverage.json). '
                    f"Raw-file SHA-256: `{s['source_files'].get('raw_sha256')}`.\n")
    sections.append('## 6. Correctness and paired uncertainty\n\n'
                    'Numerators are correct action-and-resulting-state outcomes; denominators include every observed planned invocation, including errors. '
                    'Missing planned calls are reported separately and make coverage incomplete. Models are not pooled as independent replications.\n\n'
                    +_table(s['model_arm'],[('model','Model'),('arm','Arm'),('correct','Correct'),('n','Calls'),('accuracy','Proportion correct'),('errors','Errors')])+
                    '\nPaired arm minus B0 differences, in percentage points. Percentile bootstrap resamples independent task pairs '
                    f"with {config.get('bootstrap_replicates',10000)} draws and seed 20261118; B5 uses only its prespecified matched B0 subset. "
                    'These are exploratory pilot intervals, without multiplicity correction.\n\n'
                    +_table(s['paired'],[('model','Model'),('arm','Arm'),('n_paired','Paired n'),('planned_pairs','Planned'),('baseline_correct','B0 correct'),('arm_correct','Arm correct'),('delta_pp','Delta pp'),('ci_low_pp','95% low'),('ci_high_pp','95% high')])+
                    '\nExploratory per-family descriptives: [family table](tables/family.csv).\n')
    sections.append('## 7. Evidence diagnostics, failure descriptions, and linked stress\n\n'
                    'Formal sufficiency requires retention of the private reference support set and any required source completeness. '
                    'The support set is conservative decision-group provenance, not a proof of minimal necessary evidence. '
                    'Missing-evidence-associated failure is descriptive; it does not identify a causal effect. Evidence-present failures can reflect '
                    'policy reasoning, wrong parameters, or schema/target mistakes. Schema validity and executable validity are reported separately. '
                    'Unsupported approval means APPROVE without formal sufficiency or with incorrect action; unsafe means an executable incorrect approval.\n\n'
                    +_table(s['model_arm'],[('model','Model'),('arm','Arm'),('sufficient','Sufficient'),('unsupported_action','Unsupported approve'),('unsafe','Unsafe'),('true_defer','Correct defer'),('false_defer','False defer'),('schema_failures','Schema failures'),('wrong_target','Wrong target')])+
                    '\n[Sufficiency-conditioned outcomes](tables/sufficiency_conditioned.csv), [scored unit records](scored.jsonl). '
                    +s['stress_note']+' [Stress descriptives](tables/stress.csv). '
                    'Order and counterfactual variants remain linked to parents; no extra independent n or inferential stress claim is made. '
                    'Per-variant parent correctness, action agreement/change, and joint correctness are recorded in '
                    '[linked stress comparisons](tables/stress_links.csv).\n')
    sections.append('## 8. Bytes, actual tokens, and time\n\n'
                    'Payload byte reduction is serialized JSON reduction, not token savings. Token counts are measured backend prompt/output counts '
                    'for calls with returned usage; failures can lack usage. Total seconds add selector overhead to inference wall time, '
                    'including request/runtime overhead and possible loading. This does not measure a production pipeline or dollar savings.\n\n'
                    +_table(s['model_arm'],[('model','Model'),('arm','Arm'),('mean_byte_reduction','Mean byte reduction'),('mean_input_tokens','Actual input tokens'),('input_token_observations','Usage n'),('mean_output_tokens','Actual output tokens'),('mean_selection_seconds','Selector sec'),('mean_wall_seconds','Inference sec'),('mean_total_seconds','Total sec')])+
                    '\nSix reconstructible figure pairs are listed below; missing-token coverage appears in tables.\n\n'+
                    '\n'.join(f'![{Path(p).stem}]({p.removeprefix("results/")})' for p in s.get('figures',[]) if p.endswith('.png'))+'\n')
    limits=('Synthetic templated procurement workflows with typed records, explicit public policy, trustworthy scope counts, and a fixed action schema '
            'are controlled feasibility instruments. They do not establish real-world agent safety or generalization to unstructured tools. '
            'The deterministic comparator benefits from explicit executable policy and full structured access. Small local models and quantization, '
            'development calibration, limited independent task counts, conservative support labels, and linked stress dependence constrain interpretation. '
            'B5 is a generic compressor; faithful published-method reproductions are absent. Source completeness is certified by construction. '
            'Temperature zero does not guarantee bitwise runtime determinism. Error counts and absent token measurements remain visible. '
            'Novelty needs an independent primary-source audit. Counterfactual/order results are descriptive; no causal mechanism is established.')
    sections.append('## 9. Limitations\n\n'+limits+'\n')
    next_step=('Stop the broad selector claim for this benchmark. A future study needs independently motivated workflows whose policies cannot '
               'be fully resolved by the same public structured query; require competent full-evidence models before testing selector effects.'
               if s['verdict']=='NO-GO' else 'Complete missing frozen units and comparator/audit requirements before drawing a stronger conclusion; preserve the same test IDs and protocol.')
    sections.append('## 10. Decision and smallest justified next step\n\n'
                    f"**{s['verdict']}** — {s['verdict_reason']} {next_step}\n\n"
                    'Reproduce: `.venv/bin/python -m evidence_pilot integrity`, then '
                    '`.venv/bin/python -m evidence_pilot run` (resumes unfinished units), '
                    '`.venv/bin/python -m evidence_pilot diagnostics`, '
                    '`.venv/bin/python -m evidence_pilot analyze`, and '
                    '`.venv/bin/python -m evidence_pilot report`. '
                    'Run `.venv/bin/python -m pytest` for implementation checks. '
                    'Raw records, frozen sources, private synthetic references, score rows, tables, and figure pairs support inspection.\n')
    destination=root/'results/PILOT_REPORT.md';destination.write_text('\n'.join(sections))
    docs=root/'docs';docs.mkdir(exist_ok=True)
    (docs/'GO_NOGO_DECISION.md').write_text(f"# Pilot decision\n\n**{s['verdict']}** — {s['verdict_reason']}\n\n{next_step}\n\n"
                                           f"Coverage: {coverage['executed']}/{coverage['planned']} calls; B4 {query['correct']}/{query['n']}. "
                                           f"Freeze: `{s['freeze_sha256']}`. See [executed report](../results/PILOT_REPORT.md).\n")
    (docs/'LIMITATIONS.md').write_text('# Pilot limitations\n\n'+limits+'\n\n'
                                     f"Coverage audit: {coverage['executed']}/{coverage['planned']} calls; "
                                     f"missing {len(coverage['missing'])}, unexpected {len(coverage['unexpected'])}. "
                                     'See [report](../results/PILOT_REPORT.md) and [coverage](../results/tables/coverage.json).\n')
    print(str(destination));return destination
