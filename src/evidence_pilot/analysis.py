"""Post-freeze evaluation. Private gold is read only here, never during selection."""
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from .common import ROOT, digest, dumps
from .oracles import score, sufficient
from .inference import parse_action


def planned_grid(frozen):
    config = frozen['config']
    units = set()
    for model in config['models']:
        for tid in frozen['test_ids']:
            arms = list(config['mandatory_arms']) + (['B5'] if tid in frozen['compression_ids'] else [])
            units.update(f'{tid}|{model}|{arm}|0' for arm in arms)
        for tid in frozen.get('stress_ids', []):
            units.update(f'{tid}|{model}|{arm}|0' for arm in ['B0', 'B3'])
    return units


def grid_coverage(rows, frozen):
    plan = planned_grid(frozen)
    counts = Counter(r['unit_id'] for r in rows)
    missing, unexpected = sorted(plan - counts.keys()), sorted(counts.keys() - plan)
    duplicates = sorted(k for k, n in counts.items() if n > 1)
    return {'planned': len(plan), 'executed': len(rows), 'unique_executed': len(counts),
            'missing': missing, 'unexpected': unexpected, 'duplicates': duplicates,
            'complete': not (missing or unexpected or duplicates)}


def paired_bootstrap(baseline, condition, iterations=10000, seed=20261118):
    if len(baseline) != len(condition):
        raise ValueError('Paired outcomes must have the same length')
    if not len(baseline):
        return {'delta_pp': None, 'ci_low_pp': None, 'ci_high_pp': None}
    differences = np.asarray(condition, dtype=float) - np.asarray(baseline, dtype=float)
    rng = np.random.default_rng(seed)
    distribution = differences[rng.integers(0, len(differences), size=(iterations, len(differences)))].mean(axis=1) * 100
    lo, hi = np.quantile(distribution, [.025, .975])
    return {'delta_pp': float(differences.mean() * 100), 'ci_low_pp': float(lo), 'ci_high_pp': float(hi)}


def paired_comparison(rows, model, arm, expected_ids, iterations=10000, seed=20261118):
    subset = [r for r in rows if r['model'] == model and r['task_id'] in expected_ids and r['arm'] in ['B0', arm]]
    index = {(r['task_id'], r['arm']): r for r in subset}
    if len(index) != len(subset):
        raise ValueError('Duplicate task/arm outcomes cannot be paired')
    ids = sorted(t for t in expected_ids if (t, 'B0') in index and (t, arm) in index)
    b0 = [index[t, 'B0']['correct'] for t in ids]
    ba = [index[t, arm]['correct'] for t in ids]
    return {'model': model, 'arm': arm, 'planned_pairs': len(expected_ids), 'n_paired': len(ids),
            'baseline_correct': sum(b0), 'arm_correct': sum(ba), 'task_ids': ids,
            **paired_bootstrap(b0, ba, iterations, seed)}


def score_invocation(raw, task, gold):
    action = raw.get('action')
    scored = score(gold['state'], action, gold['action'])
    schema_valid = parse_action(dumps(action)) is not None
    evidence = sufficient(raw['payload'], gold)
    correct = scored['correct'] and not raw.get('error')
    approval = isinstance(action, dict) and action.get('decision') == 'APPROVE'
    if correct:
        failure = 'correct'
    elif raw.get('error') and raw['error'] != 'invalid_schema':
        failure = 'invocation_error'
    elif not schema_valid or raw.get('error') == 'invalid_schema':
        failure = 'invalid_action'
    elif action['target'] != gold['action']['target']:
        failure = 'wrong_target'
    elif not evidence:
        failure = 'missing_evidence_associated'
    else:
        failure = 'evidence_present_reasoning'
    # B0 carries two public bookkeeping fields; compare against identical serialization.
    from .selectors import full
    full_bytes = len(dumps(full(task['payload'])).encode())
    payload_bytes = len(dumps(raw['payload']).encode())
    response = raw.get('raw_response') or {}
    return {**raw, **scored, 'correct': bool(correct), 'schema_valid': schema_valid,
            'sufficient': evidence, 'unsupported_action': bool(approval and (not evidence or not scored['correct'])),
            'wrong_target': bool(schema_valid and action['target'] != gold['action']['target']),
            'failure_category': failure, 'expected_action': gold['action'],
            'payload_bytes': payload_bytes, 'full_bytes': full_bytes,
            'byte_reduction': 1 - payload_bytes / full_bytes,
            'input_tokens': response.get('prompt_eval_count'), 'output_tokens': response.get('eval_count'),
            'total_seconds': raw.get('wall_seconds', 0) + raw.get('selection_seconds', 0)}


def _mean(values):
    usable = [x for x in values if x is not None]
    return float(np.mean(usable)) if usable else None


def aggregates(rows, keys):
    groups = defaultdict(list)
    for row in rows:
        groups[tuple(row[k] for k in keys)].append(row)
    result = []
    for values, group in sorted(groups.items(), key=lambda p: str(p[0])):
        result.append({**dict(zip(keys, values)), 'n': len(group), 'correct': sum(r['correct'] for r in group),
                       'accuracy': _mean([r['correct'] for r in group]),
                       'sufficient': sum(r['sufficient'] for r in group),
                       'schema_failures': sum(r['failure_category']=='invalid_action' for r in group),
                       'execution_invalid': sum(not r['valid'] for r in group),
                       'errors': sum(bool(r.get('error')) for r in group),
                       **{k: sum(bool(r[k]) for r in group) for k in ['unsafe', 'unsupported_action', 'true_defer', 'false_defer', 'wrong_target']},
                       **{f'mean_{k}': _mean([r.get(k) for r in group]) for k in ['payload_bytes', 'byte_reduction', 'input_tokens', 'output_tokens', 'selection_seconds', 'wall_seconds', 'total_seconds']},
                       'input_token_observations': sum(r.get('input_tokens') is not None for r in group),
                       'output_token_observations': sum(r.get('output_tokens') is not None for r in group)})
    return result


def _csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text(''); return
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader()
        writer.writerows({k: dumps(v) if isinstance(v, (dict, list)) else v for k, v in r.items()} for r in rows)


def _figures(root, rows, summary):
    if not rows:
        return []
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    figures = root / 'results/figures'; figures.mkdir(parents=True, exist_ok=True)
    output = []
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False,
                         'axes.titleweight': 'bold', 'axes.titlesize': 11})
    def short(model):
        lower=model.lower()
        if 'qwen3' in lower:return 'Qwen3 4B'
        if 'gemma4' in lower:return 'Gemma4 12B'
        return model if len(model)<=18 else model[:17]+'…'
    def save(fig, name):
        fig.tight_layout()
        for ext in ['png', 'pdf']:
            path = figures / f'{name}.{ext}'; fig.savefig(path, dpi=180, bbox_inches='tight')
            output.append(str(path.relative_to(root)))
        plt.close(fig)
    groups = summary['model_arm']
    models=list(dict.fromkeys(g['model'] for g in groups))
    arms=sorted({g['arm'] for g in groups})
    colors={arm:plt.get_cmap('tab10')(i) for i,arm in enumerate(arms)}
    index={(g['model'],g['arm']):g for g in groups}
    labels=[short(g['model'])+'\n'+g['arm'] for g in groups]
    fig, ax = plt.subplots(figsize=(8.5,4.7))
    width=.78/max(len(arms),1)
    for i,arm in enumerate(arms):
        x=np.arange(len(models))+(i-(len(arms)-1)/2)*width
        values=[100*index[m,arm]['accuracy'] if (m,arm) in index else np.nan for m in models]
        bars=ax.bar(x,values,width=width*.94,label=arm,color=colors[arm])
        for bar,m in zip(bars,models):
            if (m,arm) in index:
                g=index[m,arm];ax.text(bar.get_x()+bar.get_width()/2,bar.get_height()+1.5,f"{g['correct']}/{g['n']}",ha='center',va='bottom',fontsize=9)
    ax.set_xticks(np.arange(len(models)),[short(m) for m in models])
    ax.set(ylabel='Executed action correctness (%)',ylim=(0,113),title='Independent held-out tasks')
    ax.legend(title='Evidence arm',ncol=len(arms),loc='upper center',bbox_to_anchor=(.5,1.01),frameon=False,fontsize=9)
    ax.set_yticks([0,25,50,75,100]);ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
    fig.text(.5,-.015,'Bars include invocation failures; labels show correct / observed calls.',ha='center',fontsize=9)
    save(fig,'modelarm')

    fam=summary['family'];families=sorted({r['family'] for r in fam})
    columns=[(m,a) for m in models for a in arms]
    find={(r['family'],r['model'],r['arm']):r for r in fam}
    matrix=np.full((len(families),len(columns)),np.nan)
    for i,family in enumerate(families):
        for j,(model,arm) in enumerate(columns):
            if (family,model,arm) in find:matrix[i,j]=100*find[family,model,arm]['accuracy']
    fig,ax=plt.subplots(figsize=(max(8,len(columns)*1.05),max(3.6,len(families)*.65)))
    cmap=plt.get_cmap('Blues').with_extremes(bad='#eeeeee')
    im=ax.imshow(matrix,vmin=0,vmax=100,cmap=cmap,aspect='auto')
    ax.set_xticks(range(len(columns)),[a for m,a in columns],fontsize=10)
    model_axis=ax.secondary_xaxis('top')
    model_axis.set_xticks([i*len(arms)+(len(arms)-1)/2 for i in range(len(models))],[short(m) for m in models])
    model_axis.tick_params(length=0,pad=8)
    for boundary in range(1,len(models)):ax.axvline(boundary*len(arms)-.5,color='white',linewidth=2)
    ax.set_yticks(range(len(families)),[f.title() for f in families]);ax.set_title('Exploratory family correctness · correct / observed calls',pad=35)
    for i,family in enumerate(families):
        for j,(model,arm) in enumerate(columns):
            g=find.get((family,model,arm));label=f"{g['correct']}/{g['n']}" if g else 'missing'
            ax.text(j,i,label,ha='center',va='center',color='white' if matrix[i,j]>60 else '#17212b',fontsize=10)
    fig.colorbar(im,ax=ax,label='Correct (%)',shrink=.85)
    save(fig,'family')

    fig,ax=plt.subplots(figsize=(8,4.7));markers=['o','s','^','D']
    for mi,model in enumerate(models):
        for arm in arms:
            g=index.get((model,arm))
            if g:
                ax.scatter(100*g['mean_byte_reduction'],100*g['accuracy'],s=85,color=colors[arm],marker=markers[mi%4],edgecolor='white',linewidth=.6)
    arm_legend=[Patch(color=colors[a],label=a) for a in arms]
    model_legend=[plt.Line2D([],[],color='#444444',marker=markers[i%4],linestyle='',label=short(m)) for i,m in enumerate(models)]
    ax.legend(handles=arm_legend+model_legend,loc='best',ncol=2,fontsize=9)
    ax.set(xlabel='Mean serialized payload byte reduction (%)',ylabel='Executed action correctness (%)',ylim=(-3,103),title='Evidence reduction and action correctness')
    ax.grid(alpha=.15);fig.text(.5,-.015,'Each point is a model × arm aggregate. Byte reduction is not token savings.',ha='center',fontsize=9)
    save(fig,'reductionaccuracy')

    cond={(r['model'],r['arm'],r['sufficient']):r for r in summary['sufficiency_conditioned']}
    fig,axes=plt.subplots(1,len(models),figsize=(max(8,len(models)*4.7),4.5),squeeze=False,sharey=True)
    for ax,model in zip(axes[0],models):
        for flag,offset,color,label in [(True,-.19,'#277DA8','Sufficient'),(False,.19,'#E69F45','Insufficient')]:
            for i,arm in enumerate(arms):
                g=cond.get((model,arm,flag));x=i+offset
                if g:
                    y=100*g['accuracy'];ax.bar(x,y,width=.34,color=color,label=label if i==0 else None)
                    ax.text(x,y+2,f"n={g['n']}",ha='center',fontsize=8)
                else:ax.text(x,2,'—',ha='center',color='#888888')
        ax.set_xticks(range(len(arms)),arms);ax.set(title=short(model),ylim=(0,115));ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
    axes[0][0].set_ylabel('Executed action correctness (%)')
    fig.suptitle('Correctness conditional on formal evidence sufficiency',fontsize=12)
    fig.legend(handles=[Patch(color='#277DA8',label='Sufficient support'),Patch(color='#E69F45',label='Insufficient support')],loc='lower center',bbox_to_anchor=(.5,-.035),ncol=2,frameon=False)
    fig.text(.5,-.065,'Descriptive association; — denotes no observed calls in a condition.',ha='center',fontsize=9)
    save(fig,'sufficiencysuccess')

    categories=[('invalid_action','Invalid action'),('invocation_error','Invocation error'),('wrong_target','Wrong target'),('missing_evidence_associated','Missing evidence associated'),('evidence_present_reasoning','Evidence present reasoning')]
    fig,ax=plt.subplots(figsize=(max(8,len(groups)*1.05),4.8));bottom=np.zeros(len(groups))
    for category,label in categories:
        values=[sum(r['failure_category']==category for r in rows if r['model']==g['model'] and r['arm']==g['arm'])/g['n']*100 for g in groups]
        ax.bar(range(len(groups)),values,bottom=bottom,label=label,width=.7);bottom+=values
    ax.set_xticks(range(len(groups)),labels,fontsize=9)
    ax.set(ylabel='Share of all observed calls (%)',ylim=(0,100),title='Disjoint failure descriptions')
    ax.legend(loc='upper center',bbox_to_anchor=(.5,-.17),ncol=2,frameon=False,fontsize=9)
    ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True);save(fig,'failurebreakdown')

    fig,axes=plt.subplots(1,3,figsize=(14,4.6))
    for ax,key,title,ylabel in zip(axes,['total_seconds','input_tokens','output_tokens'],
                                  ['End-to-end wall time','Actual input tokens','Actual output tokens'],
                                  ['Mean seconds, including selector','Mean input tokens (observed usage)','Mean output tokens (observed usage)']):
        vals=[g[f'mean_{key}'] if g[f'mean_{key}'] is not None else np.nan for g in groups]
        ax.bar(range(len(groups)),vals,color=[colors[g['arm']] for g in groups],width=.72)
        ax.set_xticks(range(len(groups)),labels,rotation=45,ha='right',fontsize=8)
        ax.set(title=title,ylabel=ylabel);ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
        for i,value in enumerate(vals):
            if np.isnan(value):ax.text(i,0,'missing',rotation=90,ha='center',va='bottom',fontsize=8)
    fig.text(.5,-.025,'Input and output tokens use separate axes. Usage coverage and selector timing are recorded in tables.',ha='center',fontsize=9)
    save(fig,'latencytokens')
    return output


def analyze(root=None):
    root = Path(root or ROOT)
    read = lambda p: json.loads((root / p).read_text())
    frozen = read('results/frozen/manifest.json')
    path = root/'results/runs/heldout/raw.jsonl'
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []
    coverage = grid_coverage(rows, frozen)
    if coverage['duplicates']:
        raise ValueError('Duplicate raw units: no result will be selected arbitrarily')
    scored=[]; plan=planned_grid(frozen)
    for raw in rows:
        if raw['unit_id'] not in plan:
            continue
        tid=raw['task_id']; split='test' if tid in frozen['test_ids'] else 'stress'
        expected_unit=f'{tid}|{raw["model"]}|{raw["arm"]}|{raw.get("replicate",0)}'
        if expected_unit!=raw['unit_id'] or raw.get('freeze_sha256') != frozen['freeze_sha256']:
            raise ValueError(f'Invocation identity/freeze mismatch: {raw["unit_id"]}')
        if raw.get('payload_sha256') != digest(raw['payload']):
            raise ValueError(f'Payload integrity failure: {raw["unit_id"]}')
        task=read(f'data/{split}/public/{tid}.json'); gold=read(f'data/{split}/private/{tid}.json')
        from .inference import SYSTEM, prompt
        if raw.get('prompt_sha256') != digest([SYSTEM,prompt(task,raw['payload'])]):
            raise ValueError(f'Prompt integrity failure: {raw["unit_id"]}')
        scored.append({**score_invocation(raw,task,gold),'split':split,'family':task['family']})
    test=[r for r in scored if r['split']=='test']; stress=[r for r in scored if r['split']=='stress']
    paired=[]
    for model in frozen['config']['models']:
        for arm in list(frozen['config']['mandatory_arms'])+['B5']:
            if arm=='B0':continue
            paired.append(paired_comparison(test,model,arm,frozen['compression_ids'] if arm=='B5' else frozen['test_ids'],iterations=frozen['config'].get('bootstrap_replicates',10000)))
    conditioned=[]
    for g in aggregates(test,['model','arm','sufficient']):
        # Aggregate's sufficient count shares a key with the grouping flag; recover the flag.
        g['sufficient']=bool(g['sufficient']);conditioned.append(g)
    model_free=read('results/model_free.json') if (root/'results/model_free.json').exists() else []
    deterministic=[r for r in model_free if r['split']=='test' and r['arm']=='B4' and r['task_id'] in frozen['test_ids']]
    query_ids=Counter(r['task_id'] for r in deterministic)
    query={'n':len(deterministic),'planned':len(frozen['test_ids']), 'correct':sum(r['score']['correct'] for r in deterministic),
           'coverage_complete':set(query_ids)==set(frozen['test_ids']) and all(n==1 for n in query_ids.values())}
    complete=coverage['complete'] and query['coverage_complete']
    full=aggregates([r for r in test if r['arm']=='B0'],['model','arm'])
    if not complete:
        verdict='INCONCLUSIVE';reason='Frozen invocation grid or deterministic-comparator coverage is incomplete.'
    elif query['correct']==query['n'] and query['n']>0:
        verdict='NO-GO';reason='The public deterministic query solves every independent benchmark task; no selector contribution is established in this structured setting.'
    elif len(frozen['config']['models'])<2 or len(frozen['test_ids'])<60:
        verdict='INCONCLUSIVE';reason='Minimum independent paired task/two-family coverage is absent.'
    elif full and all(g['accuracy']<.7 for g in full):
        verdict='NO-GO';reason='Full-evidence competence is too low to isolate a useful evidence-selection effect.'
    else:
        verdict='INCONCLUSIVE';reason='A positive research claim requires substantive mechanism and literature review beyond automated statistics.'
    stress_links=[]
    index={(r['task_id'],r['model'],r['arm']):r for r in scored}
    for r in stress:
        variant='order' if r['task_id'].endswith('-order') else 'cf'
        parent=r.get('parent_task_id') or r['task_id'].rsplit('-',1)[0]
        original=index.get((parent,r['model'],r['arm']))
        if original is not None:
            stress_links.append({'task_id':r['task_id'],'parent_task_id':parent,'model':r['model'],'arm':r['arm'],
                                 'variant':variant,'parent_correct':original['correct'],'variant_correct':r['correct'],
                                 'both_correct':original['correct'] and r['correct'],
                                 'same_action':original.get('action')==r.get('action'),
                                 'expected_action_changes':original['expected_action']!=r['expected_action'],
                                 'valid_action_changes':original['schema_valid'] and r['schema_valid'] and original.get('action')!=r.get('action')})
    summary={'freeze_sha256':frozen['freeze_sha256'],'protocol_sha256':frozen.get('protocol_sha256'),
             'coverage':coverage,'independent_planned':len(frozen['test_ids']), 'models':frozen['config']['models'],
             'model_arm':aggregates(test,['model','arm']),'family':aggregates(test,['model','family','arm']),
             'sufficiency_conditioned':conditioned,'paired':paired,'stress':aggregates(stress,['model','family','arm']),
             'stress_links':stress_links,'stress_note':'Linked variants are descriptive only; never added to independent headline n or bootstrap.',
             'query':query,'model_free':model_free,'verdict':verdict,'verdict_reason':reason,
             'error_counts':dict(Counter(r['error'] for r in scored if r.get('error'))),
             'source_files':{'raw':str(path.relative_to(root)),'raw_sha256':digest(path.read_bytes()) if path.exists() else None,
                             'frozen':'results/frozen/manifest.json','model_free':'results/model_free.json'},
             'statistic':'Arm minus B0, paired independent-task percentile bootstrap, 10000 draws unless frozen otherwise; family/stress descriptive.'}
    out=root/'results';out.mkdir(exist_ok=True)
    (out/'scored.jsonl').write_text(''.join(dumps(r)+'\n' for r in scored))
    (out/'scored.json').write_text(dumps(scored)+'\n')
    for name in ['model_arm','family','paired','sufficiency_conditioned','stress','stress_links']:_csv(out/f'tables/{name}.csv',summary[name])
    (out/'tables/coverage.json').write_text(dumps(coverage)+'\n')
    _csv(out/'tables/scored.csv',[{k:v for k,v in r.items() if k not in ['payload','raw_response','actual_state','expected_state']} for r in scored])
    summary['figures']=_figures(root,test,summary)
    (out/'summary.json').write_text(dumps(summary)+'\n')
    print(dumps({'verdict':verdict,'executed':coverage['executed'],'planned':coverage['planned'],'complete':coverage['complete']}))
    return summary
