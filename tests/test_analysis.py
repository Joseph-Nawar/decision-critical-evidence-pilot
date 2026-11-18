"""Behavioral checks for denominators, failed invocations, and frozen coverage."""
import importlib
from pathlib import Path
import pytest


def implementation():
    assert Path('src/evidence_pilot/analysis.py').exists(), 'Analysis implementation is missing'
    return importlib.import_module('evidence_pilot.analysis')


def frozen():
    return {'config': {'models': ['m'], 'mandatory_arms': ['B0', 'B1', 'B3']},
            'test_ids': ['t0', 't1'], 'compression_ids': ['t0'], 'stress_ids': ['t0-order', 't0-cf']}


def row(tid, arm, correct=True):
    return {'task_id': tid, 'model': 'm', 'arm': arm, 'replicate': 0,
            'unit_id': f'{tid}|m|{arm}|0', 'correct': correct}


def test_grid_detects_missing_duplicate_and_unplanned_units():
    a = implementation()
    plan = a.planned_grid(frozen())
    assert len(plan) == 11
    rows = [{'unit_id': u} for u in sorted(plan)]
    assert a.grid_coverage(rows, frozen())['complete']
    audit = a.grid_coverage(rows[:-1] + [rows[0], {'unit_id': 'unexpected'}], frozen())
    assert len(audit['missing']) == 1
    assert audit['duplicates'] == [rows[0]['unit_id']]
    assert audit['unexpected'] == ['unexpected']
    assert not audit['complete']


def test_bootstrap_is_deterministic_and_constant_differences_are_exact():
    a = implementation()
    result = a.paired_bootstrap([1, 1, 1], [0, 0, 0], seed=12)
    assert result == a.paired_bootstrap([1, 1, 1], [0, 0, 0], seed=12)
    assert result['delta_pp'] == result['ci_low_pp'] == result['ci_high_pp'] == -100
    with pytest.raises(ValueError):
        a.paired_bootstrap([1], [])


def test_paired_denominator_uses_same_tasks_and_preserves_failed_calls():
    a = implementation()
    rows = [row('t0', 'B0'), row('t1', 'B0'), row('t0', 'B5', False)]
    r = a.paired_comparison(rows, 'm', 'B5', ['t0'])
    assert r['n_paired'] == 1 and r['planned_pairs'] == 1
    assert r['baseline_correct'] == 1 and r['arm_correct'] == 0
    assert r['delta_pp'] == -100
    missing = a.paired_comparison(rows, 'm', 'B3', ['t0', 't1'])
    assert missing['n_paired'] == 0 and missing['planned_pairs'] == 2
    assert missing['delta_pp'] is None


def test_invalid_output_and_runtime_error_are_failures_even_if_action_matches():
    a = implementation()
    state = {'target': 'PO-1', 'balance': 100, 'status': 'pending', 'released': 0}
    gold = {'state': state, 'action': {'decision': 'APPROVE', 'target': 'PO-1', 'amount': 10},
            'support': ['r'], 'complete_needed': True}
    task = {'payload': {'records': [{'id': 'r'}], 'source_complete': True, 'observed_count': 1}}
    base = {'payload': task['payload'], 'action': None, 'error': 'invalid_schema'}
    invalid = a.score_invocation(base, task, gold)
    assert not invalid['correct'] and not invalid['valid']
    assert invalid['failure_category'] == 'invalid_action'
    timed = a.score_invocation({**base, 'action': gold['action'], 'error': 'output_token_limit'}, task, gold)
    assert not timed['correct'] and timed['failure_category'] == 'invocation_error'


def test_unsupported_approval_and_evidence_present_reasoning_are_separate():
    a = implementation()
    gold = {'state': {'target': 'PO-1', 'balance': 100, 'status': 'pending', 'released': 0},
            'action': {'decision': 'REJECT', 'target': 'PO-1', 'amount': 0},
            'support': ['r'], 'complete_needed': False}
    task = {'payload': {'records': [{'id': 'r'}], 'source_complete': True, 'observed_count': 1}}
    r = {'payload': {'records': [], 'source_complete': False},
         'action': {'decision': 'APPROVE', 'target': 'PO-1', 'amount': 10}, 'error': None}
    s = a.score_invocation(r, task, gold)
    assert s['unsupported_action'] and s['unsafe']
    assert s['failure_category'] == 'missing_evidence_associated'
    s = a.score_invocation({**r, 'payload': task['payload']}, task, gold)
    assert s['failure_category'] == 'evidence_present_reasoning'


def test_wrong_target_is_schema_valid_but_not_executable():
    a = implementation()
    gold = {'state': {'target': 'PO-1', 'balance': 100, 'status': 'pending', 'released': 0},
            'action': {'decision': 'APPROVE', 'target': 'PO-1', 'amount': 10},
            'support': [], 'complete_needed': False}
    task = {'payload': {'records': [], 'source_complete': True, 'observed_count': 0}}
    result = a.score_invocation({'payload': task['payload'], 'error': None,
                               'action': {'decision': 'APPROVE', 'target': 'PO-other', 'amount': 10}}, task, gold)
    assert result['schema_valid'] and not result['valid'] and not result['correct']
    assert result['wrong_target'] and result['unsupported_action']
    assert result['failure_category'] == 'wrong_target'


def test_analysis_report_pipeline_writes_traceable_artifacts_and_six_figures(tmp_path):
    import json
    from evidence_pilot.benchmark import generate_task
    from evidence_pilot.common import digest, dumps
    from evidence_pilot.inference import SYSTEM, prompt
    from evidence_pilot.selectors import select
    from evidence_pilot.report import report
    a = implementation()
    task, gold = generate_task('test', 'aggregation', 0, 50)
    tid = task['task_id']
    def save(path, value):
        dest = tmp_path/path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(dumps(value))
    frozen_record = {'freeze_sha256': 'frozen-test-fixture', 'config': {'models': ['fixture'],
                     'mandatory_arms': ['B0', 'B1', 'B3'], 'bootstrap_replicates': 10000},
                     'test_ids': [tid], 'compression_ids': [tid], 'stress_ids': []}
    save('results/frozen/manifest.json', frozen_record)
    save(f'data/test/public/{tid}.json', task)
    save(f'data/test/private/{tid}.json', gold)
    save('results/model_free.json', [{'task_id': tid, 'split': 'test', 'family': 'aggregation',
                                    'arm': 'B4', 'score': {'correct': True}}])
    rows = []
    for arm in ['B0', 'B1', 'B3', 'B5']:
        payload = select(task, arm)
        rows.append({'unit_id': f'{tid}|fixture|{arm}|0', 'task_id': tid, 'model': 'fixture',
                     'arm': arm, 'replicate': 0, 'payload': payload,
                     'payload_sha256': digest(payload), 'prompt_sha256': digest([SYSTEM, prompt(task, payload)]),
                     'freeze_sha256': 'frozen-test-fixture', 'action': gold['action'] if arm != 'B1' else None,
                     'error': 'invalid_schema' if arm == 'B1' else None, 'wall_seconds': 1,
                     'selection_seconds': .01, 'raw_response': {'prompt_eval_count': 200, 'eval_count': 20}})
    raw = tmp_path/'results/runs/heldout/raw.jsonl'
    raw.parent.mkdir(parents=True)
    raw.write_text(''.join(dumps(r)+'\n' for r in rows))
    summary = a.analyze(tmp_path)
    assert summary['coverage']['complete']
    assert summary['verdict'] == 'NO-GO'
    assert summary['paired'][0]['n_paired'] == 1
    assert summary['paired'][0]['delta_pp'] == -100
    assert len(summary['figures']) == 12
    assert all((tmp_path/p).stat().st_size > 0 for p in summary['figures'])
    assert len((tmp_path/'results/scored.jsonl').read_text().splitlines()) == 4
    result = report(tmp_path)
    text = result.read_text()
    assert text.count('\n## ') == 10
    assert 'frozen-test-fixture' in text and 'NO-GO' in text
    assert (tmp_path/'docs/GO_NOGO_DECISION.md').exists()
    # A missing planned call remains missing; no fabricated failure row is created.
    raw.write_text(''.join(dumps(r)+'\n' for r in rows[:-1]))
    incomplete = a.analyze(tmp_path)
    assert incomplete['verdict'] == 'INCONCLUSIVE'
    assert len(incomplete['coverage']['missing']) == 1
    assert incomplete['paired'][-1]['n_paired'] == 0


@pytest.mark.parametrize('error', ['TimeoutError: timed out', 'conservative_context_guard', 'output_token_limit'])
def test_runtime_failure_without_action_is_not_a_schema_failure(error):
    a = implementation()
    task = {'payload': {'records': [], 'source_complete': True, 'observed_count': 0}}
    gold = {'state': {'target': 'PO-1', 'balance': 100, 'status': 'pending', 'released': 0},
            'action': {'decision': 'REJECT', 'target': 'PO-1', 'amount': 0},
            'support': [], 'complete_needed': False}
    scored = a.score_invocation({'payload': task['payload'], 'action': None, 'error': error}, task, gold)
    assert not scored['correct']
    assert scored['failure_category'] == 'invocation_error'
