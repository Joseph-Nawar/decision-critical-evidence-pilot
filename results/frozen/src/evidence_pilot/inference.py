"""Public-only local inference adapter and append-only invocation storage."""
import json
import os
import time
import urllib.request
from pathlib import Path
import jsonschema
from .common import dumps,digest,ACTION_SCHEMA

SYSTEM=('You decide synthetic procurement actions. Follow the workflow policy exactly. '
'Output only one JSON object with decision APPROVE, REJECT, or DEFER, target, and integer amount. '
"The target MUST be the PO- identifier immediately after 'Decide' in the request, never the scope identifier. "
'For APPROVE amount is the requested amount; for REJECT or DEFER it is 0. '
'Tool scope_counts are trustworthy counts of records in the original observed result by scope. '
'Count retained records for every scope needed by the policy: if any needed scope records were dropped, DEFER, '
'except a witnessed active block suffices for REJECT. source_complete describes upstream availability; '
'selection_complete describes whether this tool view kept all observed records. '
'Do not infer absence or aggregate completeness from a selected subset. '
'No external actions occur; return the structured action only.')

def prompt(t,payload):return dumps({'request':t['request'],'workflow_policy':t['policy'],'tool_evidence':payload})
def parse_action(s):
    try:
        a=json.loads(s);jsonschema.validate(a,ACTION_SCHEMA)
        if type(a['amount']) is not int:return None
        return a
    except (ValueError,TypeError,jsonschema.ValidationError):return None

def context_guard(input_bound,output_limit,context):return input_bound+output_limit<context

def api(endpoint,body=None,timeout=180):
    req=urllib.request.Request('http://localhost:11434/api/'+endpoint,
      data=None if body is None else json.dumps(body).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=timeout) as response:return json.load(response)

def completed(path):
    p=Path(path)
    if not p.exists():return set()
    ids=[]
    for line in p.read_text().splitlines():
        if line.strip():ids.append(json.loads(line)['unit_id'])
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate invocation identifiers')
    return set(ids)

def append_record(path,record):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    if record['unit_id'] in completed(p):raise ValueError('Refusing duplicate invocation')
    with p.open('a') as f:f.write(dumps(record)+'\n');f.flush();os.fsync(f.fileno())

def invoke(t,payload,model,config,unit_id):
    user=prompt(t,payload)
    # For ASCII benchmark text, a byte per token is a conservative bound.
    # Reserve 4096 tokens for templates, system message, and output grammar.
    bound=len(user.encode())+len(SYSTEM.encode())+4096
    r={'unit_id':unit_id,'task_id':t['task_id'],'parent_task_id':t.get('parent_task_id'),'model':model,
      'payload':payload,'payload_sha256':digest(payload),'prompt_sha256':digest([SYSTEM,user]),
      'input_byte_bound':bound,'context':config['num_ctx'],'output_limit':config['num_predict'],
      'started_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'action':None,'error':None}
    started=time.perf_counter()
    if not context_guard(bound,config['num_predict'],config['num_ctx']):
        r['error']='conservative_context_guard';r['wall_seconds']=time.perf_counter()-started;return r
    try:
        body={'model':model,'stream':False,'think':False,'format':ACTION_SCHEMA,'keep_alive':'10m',
          'messages':[{'role':'system','content':SYSTEM},{'role':'user','content':user}],
          'options':{k:config[k] for k in ['num_ctx','num_predict','temperature','seed']}}
        raw=api('chat',body,timeout=config['timeout_seconds']);r['raw_response']=raw
        r['action']=parse_action(raw.get('message',{}).get('content',''))
        if raw.get('done_reason')=='length':r['error']='output_token_limit'
        elif r['action'] is None:r['error']='invalid_schema'
        if not context_guard(raw.get('prompt_eval_count',config['num_ctx']),config['num_predict'],config['num_ctx']):
            r['error']='actual_context_overflow';r['action']=None
    except Exception as e:r['error']=f'{type(e).__name__}: {e}'
    r['wall_seconds']=time.perf_counter()-started
    return r

def unload(model):return api('generate',{'model':model,'keep_alive':0})
