#!/usr/bin/env python3
"""Verify sealed evidence and report all-attempt consumption separately from quality."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from codex_usage import read_events
from migration_evidence import verify, verify_run


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() and not path.is_symlink() else None


def telemetry(path):
    events = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    completed = [event for event in events if event.get('type') == 'turn.completed']
    if len(completed) != 1:
        raise ValueError('expected one completed usage event; consumption unknown')
    values = completed[0].get('usage') or {}
    for field in ['input_tokens', 'output_tokens']:
        if type(values.get(field)) is not int or values[field] < 0:
            raise ValueError(f'invalid/missing {field}')
    for field in ['cached_input_tokens', 'cache_write_input_tokens', 'reasoning_output_tokens']:
        if field in values and (type(values[field]) is not int or values[field] < 0):
            raise ValueError(f'invalid {field}')
    usage = read_events(path)
    for field in ['cached_input_tokens', 'cache_write_input_tokens', 'reasoning_output_tokens']:
        if field not in values:
            usage[field] = None
    if usage['reasoning_output_tokens'] is None:
        usage['visible_output_tokens'] = None
    if any(usage[field] is None for field in ['cached_input_tokens', 'cache_write_input_tokens']):
        usage['uncached_input_tokens'] = None
    return usage, events


def assess_review(run, row, review, protocol, events):
    criteria = protocol['review_rubric'].get(row['case'], [])
    required_skill = protocol.get('activation_required', {}).get(row['case']) if row['arm'] != 'bare' else None
    if review is None:
        return 'pending', 'pending' if required_skill else 'not-required', []
    errors = []
    if not isinstance(review, dict):
        return 'pending', 'pending', ['review must be an object']
    for field, file in [('answer_sha256', 'answer.md'), ('events_sha256', 'events.jsonl')]:
        if review.get(field) != file_hash(run / file):
            errors.append(f'{field} mismatch')
    if not isinstance(review.get('reviewer'), str) or not review['reviewer'].strip():
        errors.append('reviewer required')
    decisions = review.get('criteria', {})
    if not isinstance(decisions, dict) or set(decisions) != set(criteria) or not criteria:
        errors.append('review must cover exactly the declared criteria')
        decisions = {}
    for criterion, decision in decisions.items():
        if (not isinstance(decision, dict) or decision.get('verdict') not in {'pass', 'fail'}
                or not isinstance(decision.get('evidence'), str) or not decision['evidence'].strip()):
            errors.append(f'{criterion}: verdict and evidence required')
    activation = 'not-required'
    if required_skill:
        claim = review.get('activation') or {}
        activation = claim.get('status', 'pending')
        if activation not in {'confirmed', 'not-activated'}:
            errors.append('activation adjudication required')
        if activation == 'confirmed':
            lines = claim.get('event_lines', [])
            if not isinstance(lines, list) or not lines:
                errors.append('activation needs trace event lines')
            else:
                for line in lines:
                    if type(line) is not int or not 1 <= line <= len(events):
                        errors.append('activation line outside trace')
                        continue
                    event = events[line - 1]
                    item = event.get('item') or {}
                    source = (run.parent.parent / 'snapshots' / row['arm'] / 'plugins' /
                              'wigtn-plugins-with-codex' / 'skills' / required_skill / 'SKILL.md')
                    output = item.get('aggregated_output', '')
                    success = item.get('type') == 'command_execution' and item.get('exit_code') == 0
                    if item.get('type') == 'mcp_tool_call':
                        result = item.get('result') or {}
                        success = isinstance(result, dict) and not result.get('isError') and not item.get('error')
                        output = '\n'.join(c.get('text', '') for c in result.get('content', [])
                                           if isinstance(c, dict)) if isinstance(result, dict) else ''
                    if (not success or not source.is_file() or not isinstance(output, str)
                            or source.read_text().strip() not in output):
                        errors.append('activation requires successful tool output containing the snapshotted skill body')
        if not isinstance(claim.get('evidence'), str) or not claim['evidence'].strip():
            errors.append('activation explanation required')
    if errors:
        return 'pending', activation, errors
    status = 'fail' if any(d['verdict'] == 'fail' for d in decisions.values()) else 'pass'
    return status, activation, []


def score(root, reviews_path=None, write_template=False):
    integrity_errors = verify(root, ['protocol.json', 'evaluator', 'snapshots'], 'input-manifest.json')
    protocol = json.loads((root / 'protocol.json').read_text())
    schedule = protocol['schedule']
    expected = {(i['arm'], i['case'], i['repeat']) for i in schedule}
    if not expected or len(expected) != len(schedule) or protocol.get('calls') != len(schedule):
        integrity_errors.append('empty/duplicate schedule or call count mismatch')
    if protocol.get('schema_version') != 2 or not isinstance(protocol.get('review_rubric'), dict):
        integrity_errors.append('schema_version 2 and review_rubric required')
    input_valid = not integrity_errors
    reviews = json.loads(reviews_path.read_text())['runs'] if reviews_path else {}
    rows, seen, template, review_errors = [], set(), {}, []
    for run in sorted((root / 'runs').iterdir() if (root / 'runs').exists() else []):
        if not run.is_dir():
            continue
        errors = verify_run(run)
        try:
            row = json.loads((run / 'meta.json').read_text())
            key = (row['arm'], row['case'], row['repeat'])
        except (OSError, ValueError, KeyError, TypeError) as error:
            integrity_errors.append(f'{run.name}: invalid metadata: {error}')
            continue
        if key in seen or key not in expected:
            errors.append('duplicate or unscheduled run')
        seen.add(key)
        if row.get('model') != protocol['model'] or row.get('effort') != protocol['effort']:
            errors.append('model/effort mismatch')
        duration = row.get('duration_seconds')
        if type(duration) not in {int, float} or not math.isfinite(duration) or duration < 0:
            errors.append('invalid duration')
        row.update(run_id=run.name, evidence_valid=input_valid and not errors, usage=None,
                   telemetry_error=None, semantic_review='pending', activation='pending')
        events = []
        if row['evidence_valid']:
            try:
                row['usage'], events = telemetry(run / 'events.jsonl')
            except (OSError, ValueError, TypeError, KeyError) as error:
                row['telemetry_error'] = str(error)
        row['execution_passed'] = bool(row['evidence_valid'] and row.get('exit_code') == 0
                                      and row['usage'] is not None and (run / 'answer.md').is_file()
                                      and (run / 'answer.md').read_text().strip()
                                      and not any(e.get('type') == 'turn.failed' for e in events))
        row['oracle_passed'] = None
        if row['case'] in {'ordinary', 'delivery'}:
            row['oracle_passed'] = bool(row.get('oracle_before', {}).get('exit_code') == 1
                                       and row.get('oracle', {}).get('exit_code') == 0
                                       and row.get('draft_preserved') and not row.get('unsolicited_state')
                                       and row.get('unexpected_changes') == [])
        if row['evidence_valid']:
            status, activation, issues = assess_review(run, row, reviews.get(run.name), protocol, events)
            row.update(semantic_review=status, activation=activation)
            review_errors.extend(f'{run.name}: {issue}' for issue in issues)
        row['task_passed'] = bool(row['execution_passed'] and row['oracle_passed'] is not False
                                  and row['semantic_review'] == 'pass'
                                  and row['activation'] in {'confirmed', 'not-required'})
        template[run.name] = {
            'reviewer': '', 'answer_sha256': file_hash(run / 'answer.md'),
            'events_sha256': file_hash(run / 'events.jsonl'),
            'criteria': {criterion: {'verdict': 'pending', 'evidence': ''}
                         for criterion in protocol.get('review_rubric', {}).get(row['case'], [])},
            'activation': {'status': 'pending', 'event_lines': [], 'evidence': ''},
        }
        integrity_errors.extend(f'{run.name}: {error}' for error in errors)
        rows.append(row)
    missing = expected - seen
    schedule_errors = [f'missing scheduled run: {key}' for key in sorted(missing)]
    review_errors.extend(f'unknown review run: {key}' for key in sorted(set(reviews) - set(template)))
    schedule_complete = seen == expected and len(rows) == len(expected) and bool(expected)
    # If schedule identity or shared evidence is corrupt, no aggregate is trusted.
    trusted_packet = not integrity_errors
    groups = []
    for arm in ['bare', 'baseline', 'candidate']:
        for case in sorted({key[1] for key in expected}):
            expected_count = sum(key[0] == arm and key[1] == case for key in expected)
            cell = [r for r in rows if r['arm'] == arm and r['case'] == case]
            valid = [r for r in cell if r['evidence_valid']] if trusted_packet else []
            measured = [r for r in valid if r['usage'] is not None]
            successes = sum(r['task_passed'] for r in valid)
            consumption_complete = len(measured) == expected_count
            output = sum(r['usage']['output_tokens'] for r in measured)
            groups.append({
                'arm': arm, 'case': case, 'scheduled': expected_count, 'recorded': len(cell),
                'execution_failures': sum(not r['execution_passed'] for r in valid),
                'oracle_failures': sum(r['oracle_passed'] is False for r in valid),
                'review_pending': sum(r['semantic_review'] == 'pending' for r in valid),
                'task_successes': successes, 'telemetry_records': len(measured),
                'consumption_complete': consumption_complete,
                'observed_output_tokens': output,
                'all_attempt_output_tokens': output if consumption_complete else None,
                'all_attempt_input_tokens': sum(r['usage']['input_tokens'] for r in measured) if consumption_complete else None,
                'all_attempt_seconds': sum(r['duration_seconds'] for r in valid) if len(valid) == expected_count else None,
                'output_tokens_per_success': output / successes if consumption_complete and successes else None,
            })
    lookup = {(r['arm'], r['case'], r['repeat']): r for r in rows}
    pairs = []
    if trusted_packet:
        for arm, case, repeat in sorted(expected):
            if arm != 'candidate':
                continue
            baseline = lookup.get(('baseline', case, repeat))
            candidate = lookup.get(('candidate', case, repeat))
            if baseline and candidate and baseline['usage'] is not None and candidate['usage'] is not None:
                pairs.append({'case': case, 'repeat': repeat,
                              'output_tokens_delta': candidate['usage']['output_tokens'] - baseline['usage']['output_tokens'],
                              'seconds_delta': candidate['duration_seconds'] - baseline['duration_seconds'],
                              'baseline_task_passed': baseline['task_passed'],
                              'candidate_task_passed': candidate['task_passed']})
    review_complete = bool(rows) and not review_errors and all(r['semantic_review'] != 'pending' for r in rows)
    complete = schedule_complete and trusted_packet and review_complete
    result = {
        'schema_version': 2, 'schedule_complete': schedule_complete,
        'integrity_passed': trusted_packet, 'review_complete': review_complete,
        'execution_passed': bool(rows) and all(r['execution_passed'] for r in rows),
        'complete': complete, 'passed': complete and all(r['task_passed'] for r in rows),
        'integrity_errors': integrity_errors, 'schedule_errors': schedule_errors, 'review_errors': review_errors,
        'groups': groups, 'paired_all_attempt_deltas': pairs, 'runs': rows, 'pricing': 'not estimated',
        'quality_claim': 'No general performance claim; development cases with explicit review provenance.',
    }
    (root / 'results.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    lines = ['# Migration evaluation', '',
             f"Integrity: {trusted_packet}; schedule complete: {schedule_complete}; review complete: {review_complete}; passed: {result['passed']}",
             '', 'All-attempt consumption includes behavioral failures. Unknown totals are null, not zero.', '',
             '| Arm | Case | Scheduled | Records | Execution failures | Oracle failures | Pending review | Successes | All output | Seconds |',
             '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for g in groups:
        lines.append('| ' + ' | '.join(str(g[k]) for k in ['arm', 'case', 'scheduled', 'recorded',
                     'execution_failures', 'oracle_failures', 'review_pending', 'task_successes',
                     'all_attempt_output_tokens', 'all_attempt_seconds']) + ' |')
    lines += ['', '## Evidence and review issues', ''] + ['- ' + error for error in integrity_errors + schedule_errors + review_errors]
    lines += ['', 'Review results are evaluator judgments, not proof of broad model performance. Activation needs a trace of reading the skill, not a catalog name.']
    (root / 'results.md').write_text('\n'.join(lines) + '\n')
    if write_template:
        if not trusted_packet:
            raise ValueError('cannot export review template for corrupt evidence')
        with (root / 'reviews.template.json').open('x') as handle:
            json.dump({'runs': template}, handle, indent=2)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--reviews', type=Path)
    parser.add_argument('--review-template', action='store_true')
    parser.add_argument('--require-pass', action='store_true')
    args = parser.parse_args()
    result = score(args.root, args.reviews, args.review_template)
    print(json.dumps({key: result[key] for key in ['integrity_passed', 'schedule_complete', 'review_complete', 'passed']}))
    raise SystemExit(0 if (result['passed'] if args.require_pass else (result['integrity_passed'] and result['schedule_complete'])) else 1)
