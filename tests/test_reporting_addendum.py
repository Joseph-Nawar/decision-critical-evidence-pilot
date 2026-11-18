"""Post-freeze reporting extension: preserve counts and disclose lost responses."""
import json
from scripts.finalize_report import finalize

def test_addendum_uses_all_test_query_counts_and_is_idempotent(tmp_path):
    def save(name,value):
        p=tmp_path/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value))
    report=tmp_path/'results/PILOT_REPORT.md';report.parent.mkdir()
    report.write_text('Report\nThe frozen independent test set contains 60 tasks across 5 observed families.\n| Mean byte reduction |\n')
    save('results/summary.json',{'independent_planned':60,'coverage':{'executed':440,'planned':440},'verdict':'NO-GO'})
    save('results/validation.json',{'counts':{'test':100}})
    save('results/model_free.json',[{'split':'test','task_id':'t','arm':'B4','sufficient':True,'score':{'correct':True},'payload_bytes':100,'full_bytes':100,'budget_bytes':80,'seconds':.1},{'split':'test','task_id':'t','arm':'B6','sufficient':True,'payload_bytes':30,'full_bytes':100,'budget_bytes':40,'seconds':.1}])
    save('results/runs/heldout/interruption.json',{'confirmed_additional_http_completions':4,'http_durations_seconds':[1,2]})
    save('results/environment/qwen-smoke.json',{'message':{'content':'{}'},'prompt_eval_count':10,'eval_count':2,'total_duration':1000000000})
    cp=tmp_path/'results/runs/development/raw.jsonl';cp.parent.mkdir(parents=True,exist_ok=True);cp.write_text(json.dumps({'raw_response':{'prompt_eval_count':20,'eval_count':3,'total_duration':2000000000}})+'\n')
    result=finalize(tmp_path);first=report.read_text()
    assert result['phase_calls']['smoke']['responses']==1
    assert result['phase_calls']['calibration']['responses']==1
    assert '100 frozen independent test tasks' in first
    assert result['retained_heldout_units']==440 and result['additional_lost_responses']==4
    assert '1/1' in first
    oracle=next(r for r in result['model_free_all_test'] if r['arm']=='B6')
    assert oracle['within_budget']==1
    assert 'all150' not in first
    finalize(tmp_path)
    assert report.read_text()==first
