"""Seeded, synthetic procurement workflows. Gold is written separately."""
import copy
import random
from collections import Counter
from .common import digest,write,ROOT
from .oracles import reference
families=['dependencies','exceptions','aggregation','negative','semantic']
POLICIES={
'dependencies': 'Resolve scope alias to vendor, then the latest contract (largest day, then lexicographically largest id) effective on request day, then its latest check on or before request day. APPROVE only if contract active and check passed; otherwise REJECT. Missing chain or incomplete source: DEFER.',
'exceptions':'Rules apply when scope equals requested scope or all, and day <= request day <= until. Choose highest priority, then latest day, then lexicographically largest id. APPROVE if winning allow is true, otherwise REJECT. No applicable rule or incomplete source: DEFER.',
'aggregation':'Sum amount of ALL eligible charges in requested scope. APPROVE if sum <= requested amount (equality allowed), otherwise REJECT. Incomplete source or missing any scope records: DEFER.',
'negative':'An active block in requested scope means REJECT even on partial source. If no active block, APPROVE only if source_complete and all scope records are present; otherwise DEFER. Inactive blocks do not block.',
'semantic':'Resolve scope office_alias to office code. In that office, buyer and purchasing lead are equivalent purchasing roles; assistant buyer is NOT equivalent. Choose latest profile day <= request day, then lexicographically largest id among purchasing roles. APPROVE if authorized, otherwise REJECT. No matching profile or incomplete source: DEFER.'}

def counts(records):return dict(sorted(Counter(r['scope'] for r in records).items()))
def generate_task(split,family,index,n):
    seed=int(digest([split,family,index])[:12],16);rng=random.Random(seed)
    used=set()
    def ident(prefix):
        while True:
            value=prefix+str(rng.randrange(100000,999999))
            if value not in used:
                used.add(value);return value
    scope=ident('S');ticket=ident('PO-');amount=rng.randrange(80,200);records=[]
    def row(kind,scope,**kw):
        r={'id':ident('R'),'kind':kind,'scope':scope,**kw};records.append(r);return r
    complete=True;cf=None
    if family=='dependencies':
        vendor=ident('V');row('alias',scope,vendor=vendor)
        row('contract',vendor,day=2,until=99,active=True)
        c=row('contract',vendor,day=20,until=99,active=True)
        row('check',c['id'],day=8,passed=bool(rng.randrange(2)))
        r=row('check',c['id'],day=25,passed=bool(rng.randrange(2)))
        cf={'id':r['id'],'field':'passed','value':not r['passed']}
    elif family=='exceptions':
        row('rule','all',priority=0,day=0,until=99,allow=True)
        row('rule',scope,priority=2,day=10,until=99,allow=True)
        r=row('rule',scope,priority=2,day=20,until=99,allow=bool(rng.randrange(2)))
        row('rule',scope,priority=9,day=0,until=29,allow=not r['allow'])
        row('rule',scope,priority=9,day=31,until=99,allow=not r['allow'])
        cf={'id':r['id'],'field':'allow','value':not r['allow']}
    elif family=='aggregation':
        k={50:6,150:14,300:28}[n]; vals=[rng.randrange(1,10) for _ in range(k-1)]
        # One decisive adjustment crosses threshold by exactly one cent.
        amount=sum(vals)+rng.randrange(20,35)
        for v in vals:row('charge',scope,amount=v,eligible=True)
        over=bool(rng.randrange(2));r=row('charge',scope,amount=amount-sum(vals)+(1 if over else 0),eligible=True)
        row('charge',scope,amount=amount*2,eligible=False)
        cf={'id':r['id'],'field':'amount','value':r['amount']+(-1 if over else 1)}
    elif family=='negative':
        mode=(index+index//3)%3
        complete=mode!=1
        for _ in range(4):row('block',scope,active=False)
        if mode==2:
            r=row('block',scope,active=True);cf={'id':r['id'],'field':'active','value':False}
        else:cf={'id':None,'field':'source_complete','value':not complete}
    elif family=='semantic':
        office=ident('O');row('office_alias',scope,office=office)
        row('profile',office,role='buyer',day=3,authorized=True)
        row('profile',office,role='assistant buyer',day=29,authorized=True)
        r=row('profile',office,role='purchasing lead',day=22,authorized=bool(rng.randrange(2)))
        row('profile',office,role='buyer',day=31,authorized=not r['authorized'])
        cf={'id':r['id'],'field':'authorized','value':not r['authorized']}
    else:raise ValueError(family)
    # Background entities use exactly the same ID namespaces and record schemas.
    other_scopes=[ident('S') for _ in range(6)]
    vendors=[ident('V') for _ in range(6)]
    offices=[ident('O') for _ in range(6)]
    if family=='dependencies':
        for s,v in zip(other_scopes,vendors):row('alias',s,vendor=v)
    if family=='semantic':
        for s,o in zip(other_scopes,offices):row('office_alias',s,office=o)
    while len(records)<n:
        k=rng.randrange(6);s=other_scopes[k]
        if family=='dependencies':
            c=row('contract',vendors[k],day=rng.randrange(35),until=99,active=bool(rng.randrange(2)))
            if len(records)<n:row('check',c['id'],day=rng.randrange(35),passed=bool(rng.randrange(2)))
        elif family=='exceptions':row('rule',s,priority=rng.randrange(10),day=rng.randrange(35),until=99,allow=bool(rng.randrange(2)))
        elif family=='aggregation':row('charge',s,amount=rng.randrange(1,90),eligible=bool(rng.randrange(2)))
        elif family=='negative':row('block',s,active=bool(rng.randrange(2)))
        else:row('profile',offices[k],role=rng.choice(['buyer','purchasing lead','assistant buyer']),day=rng.randrange(35),authorized=bool(rng.randrange(2)))
    rng.shuffle(records)
    assert len({r['id'] for r in records})==len(records)
    t={'task_id':f'{split}-{family}-{index:03}','parent_task_id':None,'family':family,'seed':seed,'context_size_bin':n,
       'request':f'Decide {ticket} amount {amount}. scope {scope}. day 30.', 'policy':POLICIES[family],
       'payload':{'source_complete':complete,'scope_counts':counts(records),'observed_count':len(records),'records':records}}
    g=reference(t);g['counterfactual']=cf;g['state']={'target':ticket,'status':'pending','released':0,'balance':amount+1000}
    return t,g

def variants(t,g):
    order=copy.deepcopy(t);order['parent_task_id']=t['task_id'];order['task_id']+='-order';order['payload']['records'].reverse()
    twin=copy.deepcopy(t);twin['parent_task_id']=t['task_id'];twin['task_id']+='-cf';c=g['counterfactual']
    if c['id'] is None:twin['payload']['source_complete']=c['value']
    else: next(r for r in twin['payload']['records'] if r['id']==c['id'])[c['field']]=c['value']
    return [order,twin]

def generate():
    manifest={'version':1,'tasks':[]}
    for split,count in [('development',6),('test',20)]:
        for family in families:
            for i in range(count):
                t,g=generate_task(split,family,i,[50,150,300][i%3])
                write(f'data/{split}/public/{t["task_id"]}.json',t);write(f'data/{split}/private/{t["task_id"]}.json',g)
                manifest['tasks'].append({'task_id':t['task_id'],'split':split,'family':family,'n':t['context_size_bin'],'public_sha256':digest(t),'private_sha256':digest(g)})
                if split=='test' and i<2:
                    for v in variants(t,g):
                        vg=reference(v);vg['state']=g['state']
                        write(f'data/stress/public/{v["task_id"]}.json',v);write(f'data/stress/private/{v["task_id"]}.json',vg)
                        manifest['tasks'].append({'task_id':v['task_id'],'parent_task_id':t['task_id'],'split':'stress','family':family,'n':t['context_size_bin'],'public_sha256':digest(v),'private_sha256':digest(vg)})
    write('data/manifests/dataset.json',manifest)
    return manifest
