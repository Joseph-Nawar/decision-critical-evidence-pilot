"""Catch budget overruns, dishonest closure and private-label dependencies."""
import ast
import copy
from pathlib import Path
import pytest
from evidence_pilot.benchmark import generate_task
from evidence_pilot.common import dumps
from evidence_pilot.selectors import select,budget,bm25

@pytest.mark.parametrize('arm',['B0','B1','B2','B3','B5'])
def test_budget_json_and_truthful_counts(arm):
    for n in [50,150,300]:
        t,g=generate_task('development','dependencies',2,n)
        p=select(t,arm)
        assert p['scope_counts']==t['payload']['scope_counts']
        assert p['source_complete']==t['payload']['source_complete']
        assert p['observed_count']==n
        assert p['retained_count']==len(p['records'])
        assert p['selection_complete']==(len(p['records'])==n)
        assert all(r in t['payload']['records'] for r in p['records'])
        if arm!='B0':assert len(dumps(p).encode())<=budget(t)
        else:assert len(p['records'])==n
        assert p==select(t,arm)

def test_bm25_uses_request_and_rare_terms():
    scores=bm25(['apple apple','apple banana','orange banana banana'],'orange')
    assert scores[2]>scores[0]==scores[1]

def test_no_private_data_or_reference_imports():
    for f in ['selectors.py','inference.py','query.py']:
        p=Path('src/evidence_pilot')/f
        if not p.exists():continue
        tree=ast.parse(p.read_text())
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom):assert node.module not in ['oracles','benchmark']
        assert '/private' not in p.read_text()
