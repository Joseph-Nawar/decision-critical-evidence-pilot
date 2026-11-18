import json
import pytest
from scripts.export_frozen_requests import export_requests
from evidence_pilot.common import digest,dumps,ACTION_SCHEMA
from evidence_pilot.inference import SYSTEM,prompt

def test_export_replays_archived_payload_not_new_selector_and_rejects_tampering(tmp_path):
    def save(path,obj):
        p=tmp_path/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(dumps(obj))
    config={'num_ctx':40960,'num_predict':160,'temperature':0,'seed':20261118}
    frozen={'config':config,'sources':{}};frozen['freeze_sha256']=digest(frozen)
    save('results/frozen/manifest.json',frozen)
    task={'request':'Decide PO-X amount 10. scope S1. day 30.','policy':'Policy','payload':{'records':[{'id':'full'}]}}
    save('data/test/public/t.json',task)
    payload={'records':[{'id':'recorded-order'}]}
    raw={'task_id':'t','split':'test','model':'m','model_digest':'digest','unit_id':'t|m|B3|0','payload':payload,'payload_sha256':digest(payload),'prompt_sha256':digest([SYSTEM,prompt(task,payload)]),'freeze_sha256':frozen['freeze_sha256']}
    p=tmp_path/'results/runs/heldout/raw.jsonl';p.parent.mkdir(parents=True);p.write_text(dumps(raw)+'\n')
    result=export_requests(tmp_path)
    assert result['count']==1
    body=json.loads((tmp_path/'results/replay_requests'/result['requests'][0]['file']).read_text())
    assert body['messages'][1]['content']==prompt(task,payload)
    assert body['format']==ACTION_SCHEMA and body['options']==config
    assert export_requests(tmp_path)==result
    save('data/test/public/t.json',dict(task,request='changed'))
    with pytest.raises(ValueError,match='prompt'):export_requests(tmp_path)
