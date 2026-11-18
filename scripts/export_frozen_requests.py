"""Export original model requests from archived payloads; performs NO inference."""
import argparse
import json
from pathlib import Path
from evidence_pilot.common import ROOT,digest,ACTION_SCHEMA
from evidence_pilot.inference import SYSTEM,prompt

def export_requests(root=None,output=None):
    root=Path(root or ROOT);destination=Path(output) if output else root/'results/replay_requests'
    read=lambda p:json.loads((root/p).read_text())
    f=read('results/frozen/manifest.json')
    if digest({k:v for k,v in f.items() if k!='freeze_sha256'})!=f['freeze_sha256']:raise ValueError('Frozen manifest checksum mismatch')
    for name,sha in f.get('sources',{}).items():
        if digest((root/name).read_bytes())!=sha:raise ValueError(f'Frozen source mismatch: {name}')
    rows=[json.loads(line) for line in (root/'results/runs/heldout/raw.jsonl').read_text().splitlines() if line.strip()]
    if len({r['unit_id'] for r in rows})!=len(rows):raise ValueError('Duplicate units')
    destination.mkdir(parents=True,exist_ok=True);entries=[]
    for r in rows:
        if r['freeze_sha256']!=f['freeze_sha256']:raise ValueError('Unit freeze mismatch')
        if digest(r['payload'])!=r['payload_sha256']:raise ValueError('Archived payload mismatch')
        task=read(f'data/{r["split"]}/public/{r["task_id"]}.json');user=prompt(task,r['payload'])
        if digest([SYSTEM,user])!=r['prompt_sha256']:raise ValueError('Archived prompt mismatch')
        body={'model':r['model'],'stream':False,'think':False,'format':ACTION_SCHEMA,'keep_alive':'10m',
              'messages':[{'role':'system','content':SYSTEM},{'role':'user','content':user}],
              'options':{k:f['config'][k] for k in ['num_ctx','num_predict','temperature','seed']}}
        contents=json.dumps(body).encode();filename=digest(r['unit_id'])+'.json';path=destination/filename
        if path.exists() and path.read_bytes()!=contents:raise ValueError('Refusing to overwrite a different replay request')
        path.write_bytes(contents)
        entries.append({'unit_id':r['unit_id'],'file':filename,'request_file_sha256':digest(contents),
                        'prompt_sha256':r['prompt_sha256'],'payload_sha256':r['payload_sha256'],'model_digest':r['model_digest']})
    manifest={'count':len(entries),'freeze_sha256':f['freeze_sha256'],'raw_file_sha256':digest((root/'results/runs/heldout/raw.jsonl').read_bytes()),
              'note':'Exact archived model-facing payload/order; request reconstruction only, no inference performed','requests':entries}
    (destination/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');return manifest

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output-dir');args=parser.parse_args()
    r=export_requests(output=args.output_dir);print(json.dumps({'exported':r['count'],'directory':args.output_dir or str(ROOT/'results/replay_requests')}))
