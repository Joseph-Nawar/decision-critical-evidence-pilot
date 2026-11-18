"""Idempotent reporting-only addendum; frozen primary analysis is unchanged."""
import json
import csv
import re
from collections import defaultdict, Counter
from pathlib import Path
MARKER='<!-- reporting-addendum -->'

def _short_model(model):
    return 'Gemma4 12B' if 'gemma4' in model else ('Qwen3 4B' if 'qwen3' in model else model)

def _render_failure_figure(root,summary,scored):
    # Reporting-only layout change; category definitions and counts are frozen.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    categories=['invalid_action','invocation_error','wrong_target','missing_evidence_associated','evidence_present_reasoning']
    labels=['Invalid schema','Invocation error','Wrong target','Missing evidence associated','Evidence present reasoning']
    groups=summary['model_arm'];models=sorted({r['model'] for r in groups})
    fig,axes=plt.subplots(1,len(models),figsize=(13,6),sharey=True,squeeze=False)
    for ax,model in zip(axes[0],models):
        selected=[r for r in groups if r['model']==model];x=list(range(len(selected)));bottom=[0.]*len(selected)
        for i,category in enumerate(categories):
            values=[100*sum(r['failure_category']==category for r in scored if r['split']=='test' and r['model']==model and r['arm']==g['arm'])/g['n'] for g in selected]
            ax.bar(x,values,bottom=bottom,color=f'C{i}',width=.7)
            bottom=[a+b for a,b in zip(bottom,values)]
        ax.set_xticks(x,[f"{g['arm']}\nn={g['n']}" for g in selected]);ax.set_ylim(0,100)
        ax.set_title(_short_model(model),fontweight='bold');ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
    axes[0,0].set_ylabel('Share of all observed calls (%)')
    fig.suptitle('Disjoint failure descriptions',fontsize=15,fontweight='bold')
    fig.legend([Patch(color=f'C{i}') for i in range(5)],labels,loc='lower center',bbox_to_anchor=(.5,.06),ncol=3,frameon=False,fontsize=10)
    fig.text(.5,.015,'Correct calls are not stacked. B5 uses the prespecified 20-task subset.',ha='center',fontsize=9)
    fig.subplots_adjust(bottom=.30,top=.84,wspace=.12,left=.08,right=.98)
    for extension in ['png','pdf']:fig.savefig(root/f'results/figures/failurebreakdown.{extension}',dpi=160)
    plt.close(fig)

def finalize(root=None):
    root=Path(root or Path(__file__).resolve().parents[1])
    def read(p):return json.loads((root/p).read_text())
    s=read('results/summary.json');v=read('results/validation.json');rows=read('results/model_free.json')
    ip=root/'results/runs/heldout/interruption.json'
    interruption=read(str(ip.relative_to(root))) if ip.exists() else {}
    groups=defaultdict(list)
    for r in rows:
        if r['split']=='test':groups[r['arm']].append(r)
    table='| Diagnostic over all independent test tasks | Support sufficient | Action correct | Within byte budget | Mean byte reduction |\n| --- | --- | --- | --- | --- |\n'
    diagnostics=[]
    for arm,rs in sorted(groups.items()):
        sufficient=sum(r['sufficient'] for r in rs);actions=[r for r in rs if 'score' in r]
        action=f"{sum(r['score']['correct'] for r in actions)}/{len(actions)}" if actions else 'not inferred'
        reduction=sum(1-r['payload_bytes']/r['full_bytes'] for r in rs)/len(rs)
        budget_rows=[r for r in rs if 'budget_bytes' in r]
        within_budget=sum(r['payload_bytes']<=r['budget_bytes'] for r in budget_rows) if budget_rows else None
        budget_display=f'{within_budget}/{len(budget_rows)}' if budget_rows and arm!='B4' else 'not applicable'
        display_reduction='not delivered to LLM' if arm=='B4' else f'{reduction:.1%}'
        table+=f'| {arm} | {sufficient}/{len(rs)} | {action} | {budget_display} | {display_reduction} |\n'
        diagnostics.append({'arm':arm,'n':len(rs),'sufficient':sufficient,'within_budget':within_budget,'action_observations':len(actions),'action_correct':sum(r['score']['correct'] for r in actions),'mean_byte_reduction':reduction})
    retained=s['coverage']['executed'];lost=interruption.get('confirmed_additional_http_completions',0)
    raw_path=root/'results/runs/heldout/raw.jsonl'
    raw=[json.loads(line) for line in raw_path.read_text().splitlines() if line.strip()] if raw_path.exists() else []
    responses=sum(bool(r.get('raw_response')) for r in raw)
    phase_responses={'smoke':[],'calibration':[],'heldout_including_stress':[r['raw_response'] for r in raw if r.get('raw_response')]}
    for filename in ['qwen-smoke.json','gemma-smoke.json']:
        path=root/'results/environment'/filename
        if path.exists():phase_responses['smoke'].append(json.loads(path.read_text()))
    for cohort in ['development','development-v2']:
        path=root/f'results/runs/{cohort}/raw.jsonl'
        if path.exists():
            phase_responses['calibration'].extend(r['raw_response'] for r in (json.loads(line) for line in path.read_text().splitlines() if line.strip()) if r.get('raw_response'))
    phase_calls={}
    phase_table='| Response cohort | Retained backend responses | Input tokens observed | Output tokens observed | Backend total seconds observed |\n| --- | --- | --- | --- | --- |\n'
    for cohort,rr in phase_responses.items():
        phase_calls[cohort]={'responses':len(rr),'input_tokens':sum(r.get('prompt_eval_count',0) for r in rr),'output_tokens':sum(r.get('eval_count',0) for r in rr),'backend_seconds':sum(r.get('total_duration',0) for r in rr)/1e9}
        q=phase_calls[cohort]
        phase_table+=f"| {cohort} | {q['responses']} | {q['input_tokens']} | {q['output_tokens']} | {q['backend_seconds']:.2f} |\n"
    certificate_path=root/'results/sufficiency_validation.json'
    if certificate_path.exists():
        cert=read('results/sufficiency_validation.json')
        certificate_text=(f"Read-only certificate replay after freeze tested {cert['oracle_certificates_tested']} oracle views and {cert['sufficient_selector_views_tested']} sufficient selector views; discrepancies: {len(cert['failures'])}. "+'[Certificate validation](sufficiency_validation.json). These are validation counts, not additional independent experiments.\n\n')
    else:certificate_text='Certificate replay artifact unavailable.\n\n'
    result={'reporting_only_postfreeze':True,'retained_heldout_units':retained,'additional_lost_responses':lost,
            'confirmed_heldout_backend_completions_including_lost':responses+lost if raw else None,
            'generated_independent_test_tasks':v['counts']['test'],'planned_llm_independent_tasks':s['independent_planned'],
            'model_free_all_test':diagnostics,'phase_calls':phase_calls}
    secondary=[]
    frozen_path=root/'results/frozen/manifest.json'
    scored_path=root/'results/scored.json'
    if frozen_path.exists() and scored_path.exists():
        from evidence_pilot.analysis import paired_comparison
        frozen=read('results/frozen/manifest.json');scored=read('results/scored.json')
        mechanism_counts=Counter((r['model'],r['family'],r['arm'],r['failure_category']) for r in scored if r['split']=='test')
        mechanism_path=root/'results/tables/family_failure_counts.csv';mechanism_path.parent.mkdir(parents=True,exist_ok=True)
        with mechanism_path.open('w',newline='') as out:
            writer=csv.writer(out);writer.writerow(['model','family','arm','failure_category','n'])
            writer.writerows([*key,n] for key,n in sorted(mechanism_counts.items()))
        result['family_failure_counted_units']=sum(mechanism_counts.values())
        task_family={r['task_id']:r['family'] for r in rows if r['split']=='test'}
        for family in sorted(set(task_family.values())):
            ids=[tid for tid in frozen['test_ids'] if task_family.get(tid)==family]
            for model in frozen['config']['models']:
                for arm in ['B1','B3','B5']:
                    expected=[tid for tid in ids if arm!='B5' or tid in frozen['compression_ids']]
                    secondary.append({'family':family,**paired_comparison(scored,model,arm,expected,iterations=frozen['config'].get('bootstrap_replicates',10000))})
        destination=root/'results/tables/family_paired_exploratory.csv';destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('w',newline='') as out:
            fields=list(secondary[0]) if secondary else []
            writer=csv.DictWriter(out,fieldnames=fields);writer.writeheader()
            writer.writerows({k:json.dumps(v) if isinstance(v,list) else v for k,v in row.items()} for row in secondary)
    result['secondary_family_comparisons']=len(secondary)
    if s.get('model_arm') and scored_path.exists():_render_failure_figure(root,s,scored)
    execution_table='| Model / arm | No executable action | Schema failures | Calls |\n| --- | --- | --- | --- |\n'
    for row in s.get('model_arm',[]):execution_table+=f"| {_short_model(row['model'])} / {row['arm']} | {row['execution_invalid']} | {row['schema_failures']} | {row['n']} |\n"
    linked=defaultdict(list)
    for row in s.get('stress_links',[]):linked[row['model'],row['arm'],row['variant']].append(row)
    stress_table='| Model / arm | Linked variant | Pairs | Parent and variant both correct | Same JSON action |\n| --- | --- | --- | --- | --- |\n'
    for (model,arm,variant),group in sorted(linked.items()):stress_table+=f"| {_short_model(model)} / {arm} | {variant} | {len(group)} | {sum(r['both_correct'] for r in group)} | {sum(r['same_action'] for r in group)} |\n"
    replay_note=''
    if (root/'results/bm25_hash_seed_audit.json').exists():
        replay_note=('**Selector replay limitation:** Four of 440 regenerated payloads (two B3 aggregation tasks across both models) can reorder tied records across Python processes. Eight fixed hash seeds reproduced two orders with identical record membership, byte caps and formal sufficiency; the maximum score difference was 8.88e-16. BM25 sums over an unordered query-token set, so floating-point tie order is not fully pinned. Frozen source and original outputs were preserved; no inference was rerun to fix this. Exact original model inputs are exported in [replay request manifest](replay_requests/manifest.json) by `.venv/bin/python scripts/export_frozen_requests.py`, which performs no inference. See [hash-seed audit](bm25_hash_seed_audit.json).\n\n')
    text=(f'\n\n{MARKER}\n\n**Final accounting and validity notes.** This reporting-only addendum was added after freeze. '
          'It changes no inference input, primary outcome, paired comparison, or verdict rule.\n\n'
          f"The benchmark has **{v['counts']['test']} frozen independent test tasks**, of which **{s['independent_planned']}** belong to the declared two-model LLM grid. "
          'The remaining independent cases receive model-free validation/query diagnostics only. Linked stress variants remain separate.\n\n'+table+
          '\nSupport retention is not model action accuracy. B6 is a private, unbudgeted certificate bound; EXACT_KEY is a literal-scope diagnostic. '
          'B4 receives unrestricted public structured records and preimplemented workflow/schema knowledge, with fixed-template intent parsing. '
          'Its success limits the case for an LLM selector on this task class; it does not establish that arbitrary real-world agent tasks are query-solvable.\n\n'
          'Secondary paired family differences with 95% task-bootstrap intervals use the same frozen algorithm and matched subsets: [exploratory family pairs](tables/family_paired_exploratory.csv). Small per-family samples and multiple comparisons preclude strong subgroup claims.\n\n'
          +execution_table+
          '\nA schema-valid action can still be rejected by the simulator, for example DEFER with a nonzero amount. These failures remain incorrect outcomes.\n\n'+stress_table+
          '\nLinked pairs are descriptive only (five parents per model/arm/variant), never added to independent n. Counterfactual reference actions change; order-only reference actions do not. Same action is not sufficient for correctness.\n\n'+replay_note+
          f'**Interruption accounting:** {retained} retained planned invocation records, plus {lost} confirmed backend completions with lost response bodies. '
          'The missing raw units were resumed once under the prespecified interruption policy; retained results were never rerolled. '
          'The lost actions, token counts and client/selector overhead cannot be reconstructed and are not invented. '
          'Reported primary correctness uses the retained planned grid; latency/usage tables omit lost-response overhead. '
          'See [interruption receipt](runs/heldout/interruption.json) and [experiment log](../docs/EXPERIMENT_LOG.md).\n\n'
          +phase_table+
          f'\nCalibration and smoke cohorts are excluded from test accuracy. The token/time sums above cover returned responses only; the {lost} lost bodies have unknown usage. Generic B5 adds zero compressor model calls; graph/selection CPU time is in retained unit records. These are not monetary-cost estimates.\n\n'
          '**Inference limits:** [Family-specific outcome/failure counts](tables/family_failure_counts.csv) separate evidence-present failures from missing-evidence-associated failures within dependency, precedence, aggregation, absence/coverage and alias/role tasks. Strict action-only outputs do not reveal whether an individual wrong result arose from arithmetic, rule precedence or entity resolution internally. Formal-support conditioning is descriptive and varies with family and arm. H2’s stronger predictive claim is not established by these tables. '
          'False deferral is relative to the full-source reference: when selected rows are missing, DEFER can be locally safe and policy-compliant while failing the original action objective. Missing-evidence-associated failure is not proven causal. Fixed arm order, prefix caching, background application activity and memory pressure can affect latency; '
          'no monetary savings or production throughput claim follows. A trusted scope-count interface and explicit policies are important benchmark assumptions. '
          'These are single-turn action decisions; adaptive recovery and multi-turn agent trajectories are not evaluated. Critical date patterns, policy templates and dependency depths repeat across generated cases; additional development-learned shortcuts may exist. The near-duplicate audit removes entity identifiers before comparing business-attribute multisets; high template similarity is reported in '
          '[near-duplicate audit](near_duplicate_audit.json), despite unique complete public payload hashes.\n\n'
          +certificate_text+
          '**Novelty and stop decision:** The verified sources already cover task-conditioned pruning, completeness certificates, reversible recovery, '
          'structural preservation and executed-state scoring. Generic B5 cannot establish failure of published learned/reversible compressors. '
          'A benchmark-limited NO-GO supports stopping the broad selector proposal for this fully structured workflow, without claiming evidence handling is solved generally.\n\n'
          'To regenerate this final addendum after the standard report command: `.venv/bin/python scripts/finalize_report.py`.\n')
    p=root/'results/PILOT_REPORT.md';original=p.read_text().split(MARKER)[0].rstrip()
    original=re.sub(r'Mean byte reduction(?: \(fraction\))* \|','Mean byte reduction (fraction) |',original)
    original=original.replace(f"The frozen independent test set contains {s['independent_planned']} tasks across",f"The prespecified LLM subset of the {v['counts']['test']} frozen independent test tasks contains {s['independent_planned']} tasks across")
    p.write_text(original+text)
    docs=root/'docs';docs.mkdir(exist_ok=True)
    query=next((r for r in diagnostics if r['arm']=='B4'),{})
    full_rows=[r for r in s.get('model_arm',[]) if r['arm']=='B0']
    full_text='; '.join(f"{_short_model(r['model'])} {r['correct']}/{r['n']} ({r['accuracy']:.1%})" for r in full_rows)
    competence_note=('Both tested models fall below the frozen approximately 70% competence screen; these results cannot cleanly isolate evidence selection from model reasoning.' if full_rows and all(r['accuracy']<.7 for r in full_rows) else 'Interpret model competence using the full-evidence results in the report.')
    oracle_row=next((r for r in diagnostics if r['arm']=='B6'),{})
    certificate_note=f"Oracle certificates within the byte cap: {oracle_row.get('within_budget','missing')}/{oracle_row.get('n','missing')}."
    decision=(f"# Pilot research decision\n\n**{s['verdict']}** for the implemented structured-workflow pilot.\n\n"
              +s.get('verdict_reason','See the executed research report.')+'\n\n'
              +f"Deterministic query correctness over all generated independent test cases: {query.get('action_correct','missing')}/{query.get('action_observations','missing')}. "
              +f"Full-evidence model correctness: {full_text or 'not available'}. "
              +competence_note+'\n\n'
              +certificate_note+' The verified literature already covers the broad pruning, completeness, recovery and state-scoring motivations; no positive novelty claim is supported. B5 is generic graph extraction, with no faithful released-method reproduction.\n\n'
              +'**Smallest justified next step:** stop the broad selector proposal on this benchmark. Conclusions apply to typed synthetic workflows with scripted intent/policy knowledge and trusted scope counts.\n\n'
              +f"Retained grid: {retained}/{s['coverage']['planned']} units; additional lost-response completions: {lost}. See [report](../results/PILOT_REPORT.md), [paired intervals](../results/tables/paired.csv), [limitations](LIMITATIONS.md) and [reproduction](REPRODUCIBILITY.md).\n")
    (docs/'GO_NOGO_DECISION.md').write_text(decision)
    limits_path=docs/'LIMITATIONS.md'
    base=limits_path.read_text().split(MARKER)[0].rstrip() if limits_path.exists() else '# Pilot limitations'
    limits_path.write_text(base+'\n\n'+MARKER+'\n\n'
       +'Executed coverage is the prespecified 60-task, two-family fallback (100 independent test tasks generated). Models were installed Qwen3 4B and Gemma4 11.9B, not the preferred Qwen3.5/Ministral pair. Full-evidence competence was low for both.\n\n'
       +'The 4 lost responses have unknown actions and usage. Four regenerated BM25 payloads can reorder tied records across processes; original membership/sufficiency and cross-model payload pairing are unchanged. Exact archived request exports preserve original model inputs. No experiment was rerun to repair this limitation.\n\n'
       +'Scope counts and upstream completeness are trusted by construction; date patterns, group sizes and policy templates repeat. Semantic matching is a controlled alias/role equivalence task. This does not establish realistic unstructured-agent difficulty. Action-only outputs cannot identify internal arithmetic versus precedence versus entity-matching causes.\n\n'
       +'B5 is generic, recovery is not evaluated, family comparisons are exploratory and linked stress pairs add no independent n. Inference timing includes fixed arm order and cache/resource effects; lost-response overhead and total economic cost are not measured. See the full [executed report](../results/PILOT_REPORT.md).\n')
    (root/'results/reporting_addendum.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':print(json.dumps(finalize()))
