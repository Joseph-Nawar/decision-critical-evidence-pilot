"""Research orchestration; only evaluation stage reads private gold."""
import argparse
import fcntl
from contextlib import contextmanager
import json
import platform
import shutil
import subprocess
import time
from collections import Counter
from pathlib import Path
import yaml
from .common import ROOT,dumps,digest,write,load
from .benchmark import families,generate_task,generate,variants
from .oracles import reference,score,sufficient
from .query import query_action
from .selectors import select,budget,pack
from .inference import invoke,append_record,completed,unload,api,SYSTEM

def configuration():return yaml.safe_load((ROOT/'configs/pilot.yaml').read_text())
def dev_data():
    for f in families:
        for i in range(6):
            t,g=generate_task('development',f,i,[50,150,300][i%3])
            write(f'data/development/public/{t["task_id"]}.json',t);write(f'data/development/private/{t["task_id"]}.json',g)

def preflight():
    dev_data();config=configuration();path=ROOT/f'results/runs/{config.get("calibration_id","development")}/raw.jsonl';done=completed(path)
    # All five families and all size bins; extra long-rule case checks longest schema.
    cases=[(f,i) for f,i in zip(families,[0,1,2,0,1])]+[('exceptions',2)]
    for model in config['models']:
        for f,i in cases:
            t=load(f'data/development/public/development-{f}-{i:03}.json');g=load(f'data/development/private/{t["task_id"]}.json')
            arms=['B0','B1','B3'] if (f,i)!=('exceptions',2) else ['B0']
            for arm in arms:
                unit=f'{t["task_id"]}|{model}|{arm}|0'
                if unit in done:continue
                p=select(t,arm);r=invoke(t,p,model,config,unit);r.update(arm=arm,replicate=0,family=f)
                r['score']=score(g['state'],r['action'],g['action']);r['sufficient']=sufficient(p,g)
                append_record(path,r);done.add(unit)
                print(dumps({'unit':unit,'seconds':r['wall_seconds'],'correct':r['score']['correct'],'error':r['error'],'tokens':r.get('raw_response',{}).get('prompt_eval_count')}),flush=True)
        unload(model)
    metadata={'version':api('version'),'tags':api('tags'),'shows':{m:api('show',{'model':m}) for m in config['models']},'python':platform.python_version(),'platform':platform.platform()}
    write('results/environment/runtime.json',metadata)

def shape_similarity(a,b):
    def shape(payload):return Counter(dumps({k:v for k,v in r.items() if k not in ['id','scope','vendor','office']}) for r in payload['records'])
    x,y=shape(a),shape(b)
    return sum((x&y).values())/max(sum((x|y).values()),1)

def validate():
    manifest=load('data/manifests/dataset.json');checks=Counter();hashes=set();ids=set();publics=[]
    for row in manifest['tasks']:
        split=row['split'];tid=row['task_id'];t=load(f'data/{split}/public/{tid}.json');g=load(f'data/{split}/private/{tid}.json')
        assert digest(t)==row['public_sha256'] and digest(g)==row['private_sha256']
        assert tid not in ids;ids.add(tid);assert digest(t['payload']) not in hashes;hashes.add(digest(t['payload']))
        if split=='stress':
            base,bg=generate_task('test',row['family'],int(row['parent_task_id'].rsplit('-',1)[1]),row['n'])
            expected=next(v for v in variants(base,bg) if v['task_id']==tid)
            eg=reference(expected);eg['state']=bg['state']
            assert (t,g)==(expected,eg)
        else:assert (t,g)==generate_task(split,row['family'],int(tid.rsplit('-',1)[1]),row['n'])
        assert reference(t)['action']==g['action']==query_action(t)
        assert score(g['state'],g['action'],g['action'])['correct']
        assert sufficient(t['payload'],g)
        assert all(w not in dumps(t).lower() for w in ['gold','required_evidence','correct_action','counterfactual','support'])
        assert len(t['payload']['records'])==t['payload']['observed_count']==row['n']
        assert len({r['id'] for r in t['payload']['records']})==row['n']
        from .benchmark import counts
        assert t['payload']['scope_counts']==counts(t['payload']['records'])
        if split!='stress':
            stress=variants(t,g)
            assert reference(stress[0])['action']==g['action']
            assert reference(stress[1])['action']!=g['action']
        for arm in ['B0','B1','B2','B3','B5']:
            p=select(t,arm)
            assert arm=='B0' or len(dumps(p).encode())<=budget(t)
            assert p['scope_counts']==t['payload']['scope_counts']
        checks[split]+=1;publics.append((row,t))
    similarities=[]
    for row,t in publics:
        if row['split']=='test':
            choices=[(shape_similarity(t['payload'],d['payload']),devrow['task_id']) for devrow,d in publics if devrow['split']=='development' and devrow['family']==row['family'] and devrow['n']==row['n']]
            best,neighbor=max(choices)
            similarities.append({'test_id':row['task_id'],'nearest_development_id':neighbor,'shape_jaccard':best})
    write('results/near_duplicate_audit.json',{'definition':'Multiset Jaccard of business record attributes with entity identifiers removed; template similarity is not exact input duplication','pairs':similarities,'high_similarity_threshold':.95,'high_similarity_count':sum(r['shape_jaccard']>=.95 for r in similarities)})
    out={'valid':True,'counts':dict(checks),'unique_payload_hashes':len(hashes),'manifest_sha256':digest(manifest),'checks':['repeated generation','split uniqueness','oracle SQL agreement','isolated action execution','private export leakage','source counts','counterfactual flips','order invariance','all selector budgets']}
    write('results/validation.json',out);print(dumps(out))

def diagnostics():
    rows=[]
    for split in ['development','test','stress']:
        for path in sorted((ROOT/f'data/{split}/public').glob('*.json')):
            t=json.loads(path.read_text());g=load(f'data/{split}/private/{path.name}')
            for arm in ['B0','B1','B2','B3','B4','B5','B6','EXACT_KEY']:
                start=time.perf_counter()
                if arm=='B4':p=t['payload'];action=query_action(t)
                elif arm=='B6':
                    p=pack(t['payload'],[r for r in t['payload']['records'] if r['id'] in g['support']],10**9)
                    action=None
                elif arm=='EXACT_KEY':
                    from .common import intent
                    q=intent(t)
                    p=pack(t['payload'],[r for r in t['payload']['records'] if q['scope'] in dumps(r)],10**9);action=None
                else:p=select(t,arm);action=None
                r={'task_id':t['task_id'],'parent_task_id':t.get('parent_task_id'),'family':t['family'],'split':split,'arm':arm,
                   'sufficient':sufficient(p,g),'retained_records':len(p['records']),'full_records':t['context_size_bin'],
                   'payload_bytes':len(dumps(p).encode()),'full_bytes':len(dumps(select(t,'B0')).encode()),'budget_bytes':budget(t),
                   'selected_ids':[x['id'] for x in p['records']],'seconds':time.perf_counter()-start}
                if action is not None:r.update(action=action,score=score(g['state'],action,g['action']))
                rows.append(r)
    write('results/model_free.json',rows);print('model-free records',len(rows))

def freeze():
    config=configuration()
    assert config.get('test_tasks_per_family') in [12,20]
    assert not (ROOT/'results/frozen/manifest.json').exists(),'Freeze already exists; never overwrite'
    generate();validate()
    directory=ROOT/'results/frozen';directory.mkdir(parents=True,exist_ok=True)
    sources={}
    for path in sorted((ROOT/'src').rglob('*.py')):sources[str(path.relative_to(ROOT))]=digest(path.read_bytes())
    for path in sorted((ROOT/'tests').glob('*.py')):sources[str(path.relative_to(ROOT))]=digest(path.read_bytes())
    copied=['configs/pilot.yaml','docs/03_PROTOCOL.md','docs/07_DECISION_RULES.md','data/manifests/dataset.json']
    for rel in copied:
        dest=directory/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/rel,dest)
    ids=[f'test-{f}-{i:03}' for f in families for i in range(config['test_tasks_per_family'])]
    b5=[f'test-{f}-{i:03}' for f in families for i in range(config['compression_tasks_per_family'])]
    stress=[f'test-{f}-{i:03}-{v}' for f in families for i in range(config['stress_parents_per_family']) for v in ['order','cf']]
    run={'frozen_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'config':config,'sources':sources,
       'protocol_sha256':digest((ROOT/'docs/03_PROTOCOL.md').read_bytes()),'dataset_sha256':digest(load('data/manifests/dataset.json')),
       'prompt_sha256':digest(SYSTEM),'test_ids':ids,'compression_ids':b5,'stress_ids':stress,
       'models':[m for m in load('results/environment/runtime.json')['tags']['models'] if m['name'] in config['models']]}
    run['freeze_sha256']=digest(run);write('results/frozen/manifest.json',run)
    for rel in sources:
        dest=directory/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/rel,dest)
    print(dumps({k:v for k,v in run.items() if k not in ['sources','models','test_ids','compression_ids','stress_ids']}))

def integrity():
    frozen=load('results/frozen/manifest.json')
    assert digest({k:v for k,v in frozen.items() if k!='freeze_sha256'})==frozen['freeze_sha256'],'Frozen manifest checksum mismatch'
    assert digest((ROOT/'docs/03_PROTOCOL.md').read_bytes())==frozen['protocol_sha256']
    assert digest(load('data/manifests/dataset.json'))==frozen['dataset_sha256']
    for name,expected in frozen['sources'].items():assert digest((ROOT/name).read_bytes())==expected,name
    for row in load('data/manifests/dataset.json')['tasks']:
        for private,key in [('public','public_sha256'),('private','private_sha256')]:
            assert digest(load(f'data/{row["split"]}/{private}/{row["task_id"]}.json'))==row[key]
    return frozen

def assert_model_identity(model,expected):
    tags=api('tags')['models']
    observed=next((r['digest'] for r in tags if r['name']==model),None)
    if observed!=expected:raise ValueError(f'Model digest mismatch for {model}: expected {expected}, observed {observed}')

@contextmanager
def run_lock(path):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a') as handle:
        try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise RuntimeError('Another experiment runner already holds the lock')
        try:yield
        finally:fcntl.flock(handle,fcntl.LOCK_UN)

def run():
    with run_lock(ROOT/'results/runs/heldout/run.lock'):_run()

def _run():
    frozen=integrity();config=frozen['config'];path=ROOT/'results/runs/heldout/raw.jsonl';done=completed(path)
    for model in config['models']:
        assert_model_identity(model,next(x['digest'] for x in frozen['models'] if x['name']==model))
        for split,ids in [('test',frozen['test_ids']),('stress',frozen['stress_ids'])]:
            for tid in ids:
                t=load(f'data/{split}/public/{tid}.json')
                arms=config['mandatory_arms']+(['B5'] if tid in frozen['compression_ids'] else [])
                # Linked stress uses full and lexical only; independent headline n unchanged.
                if split=='stress':arms=['B0','B3']
                for arm in arms:
                    unit=f'{tid}|{model}|{arm}|0'
                    if unit in done:continue
                    start=time.perf_counter();p=select(t,arm);overhead=time.perf_counter()-start
                    r=invoke(t,p,model,config,unit)
                    r.update(arm=arm,replicate=0,family=t['family'],split=split,selection_seconds=overhead,
                      freeze_sha256=frozen['freeze_sha256'],model_digest=next(x['digest'] for x in frozen['models'] if x['name']==model))
                    append_record(path,r);done.add(unit)
                    # Progress only, no held-out scores while grid is running.
                    print(dumps({'completed':len(done),'unit':unit,'seconds':round(r['wall_seconds'],2),'error':r['error']}),flush=True)
                    write('results/runs/heldout/progress.json',{'completed':len(done),'last_unit':unit,'freeze_sha256':frozen['freeze_sha256']})
        unload(model)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['generate','validate','preflight','diagnostics','freeze','run','analyze','report','integrity']);a=parser.parse_args()
    if a.command=='generate':generate()
    elif a.command=='analyze':
        integrity()
        from .analysis import analyze
        analyze()
    elif a.command=='report':
        from .report import report
        report()
    else:globals()[a.command]()
