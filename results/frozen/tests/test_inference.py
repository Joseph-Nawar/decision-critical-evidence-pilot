import json
import pytest
from evidence_pilot.inference import prompt,parse_action,completed,append_record,context_guard

def test_public_prompt_excludes_metadata_and_private_labels():
    t={'request':'Decide PO-X amount 1. scope A. day 30.','policy':'policy','family':'negative','seed':2,'task_id':'test-negative-001','payload':{}}
    s=prompt(t,{'records':[]})
    assert 'test-negative' not in s and 'seed' not in s and 'negative' not in s
    assert 'records' in s

def test_parse_strict_json_schema_no_bool_amount_or_extra_fields():
    good={'decision':'DEFER','target':'PO-X','amount':0}
    assert parse_action(json.dumps(good))==good
    assert parse_action(json.dumps(dict(good,amount=True))) is None
    assert parse_action(json.dumps(dict(good,explanation='x'))) is None
    assert parse_action('```json\n'+json.dumps(good)+'\n```') is None

def test_checkpoint_keeps_errors_and_refuses_duplicate(tmp_path):
    path=tmp_path/'raw.jsonl';r={'unit_id':'x','error':'timeout'}
    append_record(path,r)
    assert completed(path)=={'x'}
    with pytest.raises(ValueError):append_record(path,r)
    assert len(path.read_text().splitlines())==1

def test_context_guard_rejects_overflow_and_token_cap():
    assert context_guard(1000,100,4096)
    assert not context_guard(4050,100,4096)
