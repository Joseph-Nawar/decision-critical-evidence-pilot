"""B4: independent SQL queries over public data; no private/oracle imports."""
import json
import re
import sqlite3

def query_action(t):
    # Deliberately separately parsed fixed-template intent. Known workflow/schema is privileged.
    s=t['request'];target=re.search(r'Decide (\S+)',s)[1]
    amount=int(re.search(r'amount (\d+)',s)[1]);scope=re.search(r'scope (\S+)\.',s)[1];day=int(re.search(r'day (\d+)',s)[1])
    con=sqlite3.connect(':memory:')
    con.execute('create table records (j text)')
    con.executemany('insert into records values (?)',[(json.dumps(r),) for r in t['payload']['records']])
    def rows(sql,params=()):return con.execute(sql,params).fetchall()
    def col(name):return f"json_extract(j,'$.{name}')"
    kind=col('kind');sc=col('scope');dt=col('day');rid=col('id')
    decision='DEFER';f=t['family'];complete=t['payload']['source_complete'];needed=[scope]
    if f=='dependencies':
        a=rows(f"select {col('vendor')} from records where {kind}='alias' and {sc}=?",(scope,))
        if a:
            needed.append(a[0][0])
            c=rows(f"select {rid},{col('active')} from records where {kind}='contract' and {sc}=? and {dt}<=? and {col('until')}>=? order by {dt} desc,{rid} desc limit 1",(a[0][0],day,day))
            if c:
                needed.append(c[0][0])
                check=rows(f"select {col('passed')} from records where {kind}='check' and {sc}=? and {dt}<=? order by {dt} desc,{rid} desc limit 1",(c[0][0],day))
                if check:decision='APPROVE' if c[0][1] and check[0][0] else 'REJECT'
    elif f=='exceptions':
        needed.append('all')
        r=rows(f"select {col('allow')} from records where {kind}='rule' and {sc} in (?,'all') and {dt}<=? and {col('until')}>=? order by {col('priority')} desc,{dt} desc,{rid} desc limit 1",(scope,day,day))
        if r:decision='APPROVE' if r[0][0] else 'REJECT'
    elif f=='aggregation':
        total=rows(f"select coalesce(sum({col('amount')}),0) from records where {kind}='charge' and {sc}=? and {col('eligible')}=1",(scope,))[0][0]
        decision='APPROVE' if total<=amount else 'REJECT'
    elif f=='negative':
        found=rows(f"select 1 from records where {kind}='block' and {sc}=? and {col('active')}=1 limit 1",(scope,))
        decision='REJECT' if found else ('APPROVE' if complete else 'DEFER')
    elif f=='semantic':
        a=rows(f"select {col('office')} from records where {kind}='office_alias' and {sc}=?",(scope,))
        if a:
            needed.append(a[0][0])
            r=rows(f"select {col('authorized')} from records where {kind}='profile' and {sc}=? and {col('role')} in ('buyer','purchasing lead') and {dt}<=? order by {dt} desc,{rid} desc limit 1",(a[0][0],day))
            if r:decision='APPROVE' if r[0][0] else 'REJECT'
    else:raise ValueError(f)
    missing=any(rows(f'select count(*) from records where {sc}=?',(key,))[0][0]!=t['payload']['scope_counts'].get(key,0) for key in needed)
    con.close()
    if (f!='negative' and (not complete or missing)) or (f=='negative' and decision=='APPROVE' and missing):decision='DEFER'
    return {'decision':decision,'target':target,'amount':amount if decision=='APPROVE' else 0}
