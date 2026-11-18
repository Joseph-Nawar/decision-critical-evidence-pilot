"""Freeze must cover stress inputs and verify the model actually loaded."""
import copy
import json
from pathlib import Path
import pytest
from evidence_pilot import cli,common
from evidence_pilot.benchmark import generate

def test_generated_manifest_includes_stress_hashes(tmp_path,monkeypatch):
    monkeypatch.setattr(common,'ROOT',tmp_path)
    m=generate()
    stress=[r for r in m['tasks'] if r['split']=='stress']
    assert len(stress)==20
    assert all(r['parent_task_id'].startswith('test-') for r in stress)
    for r in stress:
        assert common.digest(json.loads((tmp_path/f'data/stress/public/{r["task_id"]}.json').read_text()))==r['public_sha256']

def test_model_digest_mismatch_blocks_before_call(monkeypatch):
    monkeypatch.setattr(cli,'api',lambda *args,**kwargs:{'models':[{'name':'model','digest':'changed'}]})
    with pytest.raises(ValueError,match='digest'):
        cli.assert_model_identity('model','frozen')

@pytest.mark.parametrize('export',['public','private'])
def test_mutating_stress_export_rejected_by_integrity(tmp_path,monkeypatch,export):
    monkeypatch.setattr(common,'ROOT',tmp_path);monkeypatch.setattr(cli,'ROOT',tmp_path)
    public={'task_id':'p-cf','payload':{'records':[]}};private={'action':'DEFER'}
    m={'tasks':[{'task_id':'p-cf','split':'stress','public_sha256':common.digest(public),'private_sha256':common.digest(private)}]}
    common.write('data/manifests/dataset.json',m)
    common.write('data/stress/public/p-cf.json',public);common.write('data/stress/private/p-cf.json',private)
    doc=tmp_path/'docs/03_PROTOCOL.md';doc.parent.mkdir();doc.write_text('frozen')
    frozen={'sources':{},'protocol_sha256':common.digest(doc.read_bytes()),'dataset_sha256':common.digest(m)}
    frozen['freeze_sha256']=common.digest(frozen);common.write('results/frozen/manifest.json',frozen)
    assert cli.integrity()
    common.write(f'data/stress/{export}/p-cf.json',{'tampered':True})
    with pytest.raises(AssertionError):cli.integrity()

def test_mutated_frozen_configuration_rejected(tmp_path,monkeypatch):
    monkeypatch.setattr(common,'ROOT',tmp_path);monkeypatch.setattr(cli,'ROOT',tmp_path)
    m={'tasks':[]};common.write('data/manifests/dataset.json',m)
    doc=tmp_path/'docs/03_PROTOCOL.md';doc.parent.mkdir();doc.write_text('frozen')
    f={'sources':{},'config':{'models':['m']},'protocol_sha256':common.digest(doc.read_bytes()),'dataset_sha256':common.digest(m)}
    f['freeze_sha256']=common.digest(f);f['config']['models']=['swapped'];common.write('results/frozen/manifest.json',f)
    with pytest.raises(AssertionError):cli.integrity()

def test_second_runner_is_rejected_and_lock_releases(tmp_path):
    lock=tmp_path/'run.lock'
    with cli.run_lock(lock):
        with pytest.raises(RuntimeError,match='runner'):
            with cli.run_lock(lock):pass
    with cli.run_lock(lock):pass

def test_near_duplicate_check_ignores_renamed_ids_but_checks_facts():
    a={'records':[{'id':'R1','scope':'S1','kind':'block','active':True}]}
    b={'records':[{'id':'R2','scope':'S2','kind':'block','active':True}]}
    c={'records':[{'id':'R3','scope':'S3','kind':'block','active':False}]}
    assert cli.shape_similarity(a,b)==1
    assert cli.shape_similarity(a,c)==0
