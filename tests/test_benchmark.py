"""Hand-calculated fixtures catch precedence, closure and state-scoring bugs."""
import copy
import pytest
from evidence_pilot.benchmark import generate_task, families
from evidence_pilot.oracles import reference, execute, score, sufficient
from evidence_pilot.query import query_action

def task(family, records, **extra):
    return {'task_id':'fixture','family':family,'request':'Decide PO-X amount 100. scope blue. day 30.',
      'policy':'', 'payload':{'records':records,'source_complete':True,'scope_counts':{s:sum(r['scope']==s for r in records) for s in {r['scope'] for r in records}},'observed_count':len(records)}, **extra}

def test_exception_precedence_expiry_and_tie():
    t=task('exceptions',[
      {'id':'r1','kind':'rule','scope':'all','priority':0,'day':0,'until':99,'allow':True},
      {'id':'r2','kind':'rule','scope':'blue','priority':2,'day':20,'until':99,'allow':False},
      {'id':'r3','kind':'rule','scope':'blue','priority':9,'day':1,'until':29,'allow':True}])
    assert reference(t)['action']=={'decision':'REJECT','target':'PO-X','amount':0}
    assert query_action(t)=={'decision':'REJECT','target':'PO-X','amount':0}
    t['payload']['records'][1]['allow']=True
    assert reference(t)['action']['decision']=='APPROVE'

def test_aggregate_counts_all_and_threshold_equality():
    t=task('aggregation',[{'id':'1','kind':'charge','scope':'blue','amount':40,'eligible':True},
      {'id':'2','kind':'charge','scope':'blue','amount':60,'eligible':True},
      {'id':'3','kind':'charge','scope':'blue','amount':999,'eligible':False}])
    assert reference(t)['action']['decision']=='APPROVE'
    t['payload']['records'][0]['amount']=41
    assert reference(t)['action']['decision']=='REJECT'
    assert query_action(t)==reference(t)['action']

def test_negative_partial_absence_never_licenses_approval():
    t=task('negative',[])
    assert reference(t)['action']['decision']=='APPROVE'
    t['payload']['source_complete']=False
    assert reference(t)['action']['decision']=='DEFER'
    assert query_action(t)['decision']=='DEFER'
    t['payload']['records']=[{'id':'b','kind':'block','scope':'blue','active':True}]
    assert reference(t)['action']['decision']=='REJECT'

def test_action_execution_rejects_bool_amount_and_wrong_state():
    s={'target':'PO-X','status':'pending','released':0,'balance':200}
    a={'decision':'APPROVE','target':'PO-X','amount':100}
    assert execute(s,a)=={'target':'PO-X','status':'approved','released':100,'balance':100}
    assert s['balance']==200
    assert execute(s,dict(a,amount=True)) is None
    assert execute(s,dict(a,target='PO-Y')) is None
    assert not score(s,a,{'decision':'REJECT','target':'PO-X','amount':0})['correct']

@pytest.mark.parametrize('family',families)
def test_generator_reproducible_independent_query_counterfactual(family):
    for i in range(6):
        t,g=generate_task('dev',family,i,[50,150,300][i%3])
        assert (t,g)==generate_task('dev',family,i,[50,150,300][i%3])
        assert query_action(t)==g['action']
        shuffled=copy.deepcopy(t); shuffled['payload']['records'].reverse()
        assert reference(shuffled)['action']==g['action']
        twin=copy.deepcopy(t)
        field=g['counterfactual']
        if field['id'] is None: twin['payload']['source_complete']=field['value']
        else:
            next(r for r in twin['payload']['records'] if r['id']==field['id'])[field['field']]=field['value']
        assert reference(twin)['action']!=g['action']
        assert sufficient(t['payload'],g)
        assert not any(k in str(t) for k in ['correct_action','required_evidence','gold','counterfactual'])

def test_all_development_identifiers_unique():
    for family in families:
        for i in range(6):
            t,g=generate_task('development',family,i,[50,150,300][i%3])
            assert len({r['id'] for r in t['payload']['records']})==t['context_size_bin']

def test_missing_scope_rows_requires_defer():
    t=task('aggregation',[{'id':'1','kind':'charge','scope':'blue','amount':40,'eligible':True}])
    t['payload']['scope_counts']['blue']=2
    assert reference(t)['action']['decision']=='DEFER'

def test_query_checks_scope_closure_without_private_labels():
    t=task('aggregation',[{'id':'1','kind':'charge','scope':'blue','amount':40,'eligible':True}])
    t['payload']['scope_counts']['blue']=2
    assert query_action(t)['decision']=='DEFER'

def test_equal_priority_day_uses_lexicographic_id():
    t=task('exceptions',[
       {'id':'A','kind':'rule','scope':'blue','priority':2,'day':20,'until':99,'allow':True},
       {'id':'B','kind':'rule','scope':'blue','priority':2,'day':20,'until':99,'allow':False}])
    assert reference(t)['action']['decision']=='REJECT'
    assert query_action(t)['decision']=='REJECT'

def test_semantic_role_alias_future_and_near_match():
    t=task('semantic',[
       {'id':'alias','kind':'office_alias','scope':'blue','office':'Z'},
       {'id':'1','kind':'profile','scope':'Z','role':'buyer','day':3,'authorized':True},
       {'id':'2','kind':'profile','scope':'Z','role':'purchasing lead','day':20,'authorized':False},
       {'id':'3','kind':'profile','scope':'Z','role':'assistant buyer','day':29,'authorized':True},
       {'id':'4','kind':'profile','scope':'Z','role':'buyer','day':31,'authorized':True}])
    assert reference(t)['action']['decision']=='REJECT'
    assert query_action(t)['decision']=='REJECT'

def test_scope_prefix_shortcut_cannot_fit_all_evidence_in_budget():
    from evidence_pilot.common import dumps
    from evidence_pilot.selectors import budget,pack
    import re
    for f in families:
        for i in range(6):
            t,g=generate_task('development',f,i,[50,150,300][i%3])
            rs=[r for r in t['payload']['records'] if not re.fullmatch(r'D\d+',r['scope'])]
            p=pack(t['payload'],rs,10**9)
            assert not(sufficient(p,g) and len(dumps(p).encode())<=budget(t))

def test_negative_outcomes_not_determined_by_size():
    outcomes={50:set(),150:set(),300:set()}
    for i in range(6):
        n=[50,150,300][i%3];t,g=generate_task('development','negative',i,n)
        outcomes[n].add(g['action']['decision'])
    assert all(len(x)>1 for x in outcomes.values())

def test_partial_negative_support_covers_observed_scope():
    t=task('negative',[{'id':'a','kind':'block','scope':'blue','active':False}])
    t['payload']['source_complete']=False
    g=reference(t)
    assert g['action']['decision']=='DEFER'
    assert not sufficient(dict(t['payload'],records=[]),g)
