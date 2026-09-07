#!/usr/bin/env python3
"""Offline evidence, accounting, adjudication and CLI-contract regression tests."""
import hashlib
import importlib.util
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from migration_evidence import seal, seal_run
from migration_cases import PROMPTS, RUBRIC


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


scorer = load('migration_scorer', 'score-model-migration-eval.py')
runner = load('migration_runner', 'run-model-migration-eval.py')


def dump(path, value):
    path.write_text(json.dumps(value) + '\n')


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def fixture(self, case='ordinary', failed=False, usage=None):
        root = self.root
        for name in ['evaluator', 'snapshots']:
            (root / name).mkdir()
            (root / name / 'source.txt').write_text('synthetic input fixture')
        for arm in ['baseline', 'candidate']:
            source = root/'snapshots'/arm/'plugins/wigtn-plugins-with-codex/skills/verified-delivery/SKILL.md'
            source.parent.mkdir(parents=True)
            source.write_text('# Verified Delivery\nSynthetic skill fixture.\n')
        schedule = [{'arm': a, 'case': case, 'repeat': rep} for rep in [1, 2]
                    for a in ['bare', 'baseline', 'candidate']]
        protocol = {'schema_version': 2, 'model': 'gpt-6-astra', 'effort': 'medium',
                    'calls': len(schedule), 'schedule': schedule,
                    'review_rubric': {case: ['correct', 'scoped']},
                    'activation_required': {case: 'verified-delivery'} if case == 'delivery' else {}}
        dump(root / 'protocol.json', protocol)
        seal(root, ['protocol.json', 'evaluator', 'snapshots'], 'input-manifest.json')
        for i, item in enumerate(schedule):
            run = root / 'runs' / f'{i:02}'
            work = run / 'work'; work.mkdir(parents=True)
            (work / 'scores.py').write_text('def sorted_scores(scores):\n    return sorted(scores)\n')
            (run / 'answer.md').write_text('Synthetic fixture, not model output')
            (run / 'prompt.txt').write_text('Synthetic request')
            fails = failed and i == 5
            value = usage if usage is not None else {'input_tokens': 100, 'output_tokens': 1000 if fails else 10}
            events = [{'type': 'item.completed', 'item': {'type': 'command_execution',
                       'command': 'cat /plugin/verified-delivery/SKILL.md', 'exit_code': 0,
                       'aggregated_output': '# Verified Delivery\nSynthetic skill fixture.\n'}},
                      {'type': 'turn.completed', 'usage': value}]
            (run / 'events.jsonl').write_text('\n'.join(json.dumps(e) for e in events) + '\n')
            dump(run / 'meta.json', {**item, 'model': protocol['model'], 'effort': 'medium',
                 'exit_code': 0, 'duration_seconds': 1, 'oracle_before': {'exit_code': 1},
                 'oracle': {'exit_code': 1 if fails else 0}, 'draft_preserved': True,
                 'unsolicited_state': False, 'unexpected_changes': []})
            seal_run(run)
        return protocol

    def reviews(self):
        scorer.score(self.root, write_template=True)
        data = json.loads((self.root / 'reviews.template.json').read_text())
        for row in data['runs'].values():
            row['reviewer'] = 'synthetic-test-reviewer'
            for decision in row['criteria'].values():
                decision.update(verdict='pass', evidence='Synthetic criterion evidence')
            row['activation'] = {'status': 'confirmed', 'event_lines': [1], 'evidence': 'Synthetic tool-read trace'}
        path = self.root / 'reviews.json'; dump(path, data)
        return path

    def test_review_pending_is_not_pass(self):
        self.fixture()
        result = scorer.score(self.root)
        self.assertTrue(result['integrity_passed'])
        self.assertTrue(result['schedule_complete'])
        self.assertFalse(result['passed'])
        self.assertFalse(result['complete'])

    def test_adjudicated_packet_passes(self):
        self.fixture()
        self.assertTrue(scorer.score(self.root, self.reviews())['passed'])

    def test_early_stop_retains_observed_consumption(self):
        self.fixture()
        shutil.rmtree(self.root/'runs/05')
        result = scorer.score(self.root)
        self.assertTrue(result['integrity_passed'])
        self.assertFalse(result['schedule_complete'])
        candidate = next(g for g in result['groups'] if g['arm'] == 'candidate')
        self.assertEqual(candidate['observed_output_tokens'], 10)
        self.assertIsNone(candidate['all_attempt_output_tokens'])

    def test_changed_implementation_is_rejected(self):
        self.fixture()
        (self.root / 'runs/02/work/scores.py').write_text('def sorted_scores(scores): return []')
        result = scorer.score(self.root)
        self.assertFalse(result['integrity_passed'])
        self.assertTrue(all(g['all_attempt_output_tokens'] is None for g in result['groups']))

    def test_changed_events_rejected(self):
        self.fixture()
        (self.root / 'runs/02/events.jsonl').write_text('{}\n')
        self.assertFalse(scorer.score(self.root)['integrity_passed'])

    def test_input_snapshot_mutation_rejected(self):
        self.fixture()
        (self.root / 'snapshots/source.txt').write_text('changed')
        self.assertFalse(scorer.score(self.root)['integrity_passed'])

    def test_extra_work_file_rejected(self):
        self.fixture()
        (self.root / 'runs/00/work/unexpected.txt').write_text('extra')
        self.assertFalse(scorer.score(self.root)['integrity_passed'])

    def test_missing_seal_rejected(self):
        self.fixture()
        (self.root / 'runs/00/evidence-manifest.json').unlink()
        self.assertFalse(scorer.score(self.root)['integrity_passed'])

    def test_failure_cost_retained(self):
        self.fixture(failed=True)
        result = scorer.score(self.root, self.reviews())
        self.assertTrue(result['integrity_passed'])
        self.assertTrue(result['complete'])
        self.assertFalse(result['passed'])
        candidate = next(g for g in result['groups'] if g['arm'] == 'candidate')
        self.assertEqual(candidate['all_attempt_output_tokens'], 1010)
        self.assertEqual(candidate['task_successes'], 1)
        self.assertEqual(candidate['output_tokens_per_success'], 1010)
        self.assertEqual(candidate['oracle_failures'], 1)
        self.assertEqual(len(result['paired_all_attempt_deltas']), 2)

    def test_missing_usage_leaves_incomplete_total(self):
        self.fixture(usage={'input_tokens': 10})
        result = scorer.score(self.root)
        self.assertFalse(result['execution_passed'])
        self.assertTrue(all(g['all_attempt_output_tokens'] is None for g in result['groups']))

    def test_unknown_reasoning_is_null(self):
        self.fixture()
        self.assertIsNone(scorer.score(self.root)['runs'][0]['usage']['reasoning_output_tokens'])

    def test_stale_review_rejected(self):
        self.fixture()
        path = self.reviews(); data = json.loads(path.read_text())
        data['runs']['00']['answer_sha256'] = 'wrong'
        dump(path, data)
        result = scorer.score(self.root, path)
        self.assertFalse(result['review_complete'])
        self.assertTrue(result['review_errors'])

    def test_activation_needs_real_trace_reference(self):
        self.fixture(case='delivery')
        path = self.reviews(); data = json.loads(path.read_text())
        data['runs']['02']['activation']['event_lines'] = [2]
        dump(path, data)
        self.assertFalse(scorer.score(self.root, path)['passed'])
        data['runs']['02']['activation']['event_lines'] = [1]
        dump(path, data)
        self.assertTrue(scorer.score(self.root, path)['passed'])

    def test_skill_name_without_body_is_not_activation(self):
        self.fixture(case='delivery')
        run = self.root/'runs/02'
        events = [json.loads(line) for line in (run/'events.jsonl').read_text().splitlines()]
        events[0]['item']['aggregated_output'] = 'verified-delivery/SKILL.md'
        (run/'events.jsonl').write_text('\n'.join(json.dumps(e) for e in events)+'\n')
        (run/'evidence-manifest.json').unlink(); seal_run(run)
        self.assertFalse(scorer.score(self.root, self.reviews())['passed'])

    def test_invalid_turn_telemetry_is_not_complete(self):
        self.fixture()
        run = self.root/'runs/00'
        original = (run/'events.jsonl').read_text()
        variants = [original + original,
                    '{"type":"turn.completed","usage":{"input_tokens":-1,"output_tokens":10}}\n',
                    'broken json\n']
        for text in variants:
            with self.subTest(text=text[:35]):
                (run/'events.jsonl').write_text(text)
                (run/'evidence-manifest.json').unlink(); seal_run(run)
                result = scorer.score(self.root)
                self.assertTrue(result['integrity_passed'])
                self.assertFalse(result['execution_passed'])
                self.assertIsNone(result['groups'][0]['all_attempt_output_tokens'])

    def test_failed_turn_consumption_is_retained(self):
        self.fixture()
        run = self.root/'runs/00'
        with (run/'events.jsonl').open('a') as handle:
            handle.write('{"type":"turn.failed"}\n')
        (run/'evidence-manifest.json').unlink(); seal_run(run)
        result = scorer.score(self.root)
        self.assertFalse(result['execution_passed'])
        self.assertEqual(result['groups'][0]['all_attempt_output_tokens'], 20)

    def test_symlinked_evidence_rejected(self):
        self.fixture()
        (self.root/'runs/00/work/link').symlink_to(self.root/'protocol.json')
        self.assertFalse(scorer.score(self.root)['integrity_passed'])

    def test_empty_schedule_rejected(self):
        self.fixture()
        p = self.root / 'protocol.json'; data = json.loads(p.read_text()); data['schedule'] = []
        dump(p, data)
        self.assertFalse(scorer.score(self.root)['integrity_passed'])

    def test_oracle_catches_vacuous_test_and_passes_fix(self):
        work = self.root / 'work'; work.mkdir()
        source = work / 'scores.py'
        source.write_text('def sorted_scores(scores):\n    scores.sort()\n    return scores\n')
        (work / 'test_scores.py').write_text('assert True')
        self.assertEqual(runner.check_implementation(work, self.root/'before.log')['exit_code'], 1)
        source.write_text('def sorted_scores(scores):\n    return sorted(scores)\n')
        self.assertEqual(runner.check_implementation(work, self.root/'after.log')['exit_code'], 0)

    def test_offline_runner_to_scorer_integration(self):
        cli = self.root/'fake-codex'
        cli.write_text("""#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
args=sys.argv[1:]
if '--version' in args:
    print('FAKE CLI fixture; no model inference')
elif 'plugin' in args:
    print('{}')
elif 'debug' in args:
    print('wigtn-plugins-with-codex:product-spec' if Path(os.environ['CODEX_HOME']).name != 'bare' else '[]')
else:
    prompt=sys.stdin.read()
    work=Path(args[args.index('-C')+1])
    if (work/'scores.py').exists():
        (work/'scores.py').write_text('def sorted_scores(scores):\\n    return sorted(scores)\\n')
    Path(args[args.index('-o')+1]).write_text('Synthetic CLI fixture answer; not model generated')
    print(json.dumps({'type':'turn.completed','usage':{'input_tokens':100,'output_tokens':10}}))
""")
        cli.chmod(0o755)
        auth = self.root/'fake-auth.json'; auth.write_text('{}')
        root = self.root/'integration'
        process = subprocess.run([sys.executable, '-B', str(Path(runner.__file__)),
                    '--baseline', str(Path(__file__).resolve().parents[1]), '--root', str(root),
                    '--repeat', '1', '--codex', str(cli), '--execute'],
                    env={**os.environ, 'CODEX_AUTH_FILE': str(auth)}, capture_output=True, text=True)
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        result = scorer.score(root)
        self.assertTrue(result['integrity_passed'], result['integrity_errors'])
        self.assertTrue(result['execution_passed'])
        self.assertTrue(result['schedule_complete'])
        self.assertFalse(result['passed'])  # No semantic reviews or actual model activation.
        self.assertEqual(len(result['runs']), 12)

    def test_new_contract_cases_and_complete_criteria(self):
        self.assertEqual(len(RUBRIC['many-findings']), 6)
        for case in ['compact-review', 'external-review', 'many-findings']:
            self.assertTrue(PROMPTS[case])
            self.assertTrue(RUBRIC[case])
        result = subprocess.run([sys.executable, '-B', str(Path(runner.__file__)),
                                 '--baseline', str(Path(__file__).resolve().parents[1]),
                                 '--root', str(self.root/'dry'), '--suite', 'contracts'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(result.stdout)
        self.assertEqual(plan['calls'], 30)
        self.assertFalse((self.root/'dry').exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
