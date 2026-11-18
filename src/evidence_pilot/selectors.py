"""Non-oracular selectors. Input is exclusively the public export."""
import math
import random
import re
from collections import Counter
from .common import dumps

def tokens(s):return re.findall(r'[a-z0-9]+',s.lower())
def budget(t):return max(2000,int(.25*len(dumps(full(t['payload'])).encode())))
def full(p):
    return {**p,'retained_count':len(p['records']),'selection_complete':len(p['records'])==p['observed_count']}
def bm25(documents,query):
    docs=[Counter(tokens(s)) for s in documents];n=len(docs);avg=sum(sum(d.values()) for d in docs)/max(n,1)
    df=Counter(w for d in docs for w in d);out=[]
    for d in docs:
        length=sum(d.values());score=0
        for w in set(tokens(query)):
            tf=d[w]
            if tf:score+=math.log(1+(n-df[w]+.5)/(df[w]+.5))*tf*2.5/(tf+1.5*(.25+.75*length/max(avg,1)))
        out.append(score)
    return out

def graph_rank(documents,query):
    # Generic query-biased graph extractive compression; not a published-method reproduction.
    sets=[set(tokens(s)) for s in documents];n=len(sets)
    weights=[[len(a&b)/max(len(a|b),1) if i!=j else 0 for j,b in enumerate(sets)] for i,a in enumerate(sets)]
    sums=[sum(w) for w in weights];lex=bm25(documents,query);z=sum(lex)
    prior=[.5/max(n,1)+.5*v/max(z,1e-10) for v in lex]
    if z==0:prior=[1/max(n,1)]*n
    ranks=prior[:]
    for _ in range(20):
        ranks=[.15*prior[j]+.85*sum(ranks[i]*weights[i][j]/max(sums[i],1e-10) for i in range(n)) for j in range(n)]
    return ranks

def pack(p,ordered,limit,head=False):
    out={k:v for k,v in p.items() if k!='records'};out.update(records=[],retained_count=0,selection_complete=False)
    for record in ordered:
        candidate={**out,'records':out['records']+[record],'retained_count':len(out['records'])+1}
        candidate['selection_complete']=candidate['retained_count']==p['observed_count']
        if len(dumps(candidate).encode())<=limit:out=candidate
        elif head:break
    if len(dumps(out).encode())>limit:raise ValueError('Budget cannot fit truthful metadata header')
    return out

def select(t,arm):
    p=t['payload'];rs=p['records'];limit=budget(t)
    if arm=='B0':return full(p)
    order=list(range(len(rs)))
    if arm=='B2':random.Random(t['seed']+2718).shuffle(order)
    elif arm in ['B3','B5']:
        texts=[dumps(r) for r in rs]
        scores=(bm25 if arm=='B3' else graph_rank)(texts,t['request'])
        order.sort(key=lambda i:(-scores[i],i))
    elif arm!='B1':raise ValueError(arm)
    return pack(p,[rs[i] for i in order],limit,head=arm=='B1')
