#!/usr/bin/env python3
"""Integration regression for stable symbolic requirement IDs found in live eval."""
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(os.environ.get('WIGTN_TEST_ROOT', Path(__file__).resolve().parents[1]))
PLUGIN = ROOT / 'plugins/wigtn-plugins-with-codex'
SCRIPTS = PLUGIN / 'scripts'
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT / 'scripts'))

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

importer = module('requirement_importer', SCRIPTS / 'import-requirements.py')
workgraph_cases = module('workgraph_cases', ROOT / 'scripts/check-workgraph-contract.py')
from workgraph_core import validate_graph

class SymbolicIDs(unittest.TestCase):
    def test_explicit_import_preserves_complete_ids(self):
        text = '''# Requirements
REQ-TTL: Lifetime is exactly 86400 seconds.
- **REQ-TENANT-ACCESS**: Keep tenant data isolated.
| REQ-MAX_LENGTH | Limit names to 80 characters. |
- fr-01: Preserve legacy numeric IDs.
REQ-1: Allow a one-digit source ID.
'''
        self.assertEqual(importer.explicit_requirements(text), [
            ('REQ-TTL', 'Lifetime is exactly 86400 seconds.'),
            ('REQ-TENANT-ACCESS', 'Keep tenant data isolated.'),
            ('REQ-MAX_LENGTH', 'Limit names to 80 characters.'),
            ('FR-01', 'Preserve legacy numeric IDs.'),
            ('REQ-1', 'Allow a one-digit source ID.'),
        ])

    def test_markdown_lists_and_checkboxes_remain_supported(self):
        for prefix in ['* ', '- ', '+ ', '1. ', '2) ', '### ', '- [ ] ', '- [x] ']:
            for identifier in ['FR-01', 'REQ-TTL']:
                with self.subTest(prefix=prefix, identifier=identifier):
                    self.assertEqual(importer.explicit_requirements(
                        prefix + identifier + ': Preserve preference.'),
                        [(identifier, 'Preserve preference.')])

    def test_acceptance_section_preserves_underscore_ids(self):
        self.assertEqual(importer.derived_acceptance(
            '## Acceptance Criteria\n- **REQ-MAX_LENGTH**: Limit to 80 characters.\n',
            'BM', 'story.md', set()),
            [('REQ-MAX_LENGTH', 'Limit to 80 characters.')])

    def test_prose_and_incomplete_ids_are_not_requirements(self):
        for text in ['tenant-scoped access is required.',
                     'See REQ-TTL: for background.',
                     'REQ-TTL', 'REQ-TTL:', 'REQ-TTL-: broken ID',
                     'REQ--TTL: broken ID']:
            with self.subTest(text=text):
                self.assertEqual(importer.explicit_requirements(text), [])

    def test_contracts_accept_same_symbolic_id(self):
        graph = json.loads(json.dumps(workgraph_cases.valid_graph()).replace('FR-01', 'REQ-TTL'))
        self.assertEqual(validate_graph(graph), [])
        evidence = json.loads((ROOT / 'tests/evidence/valid-acceptance.json').read_text().replace('FR-01', 'REQ-TTL'))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'evidence.json'
            path.write_text(json.dumps(evidence))
            result = subprocess.run([sys.executable, '-B', str(SCRIPTS / 'validate-evidence.py'), str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        # Dependency-free validators and published JSON schemas must agree.
        for name in ['workgraph', 'evidence-contract']:
            schema = json.loads((PLUGIN / f'schemas/{name}.schema.json').read_text())
            requirement = schema.get('$defs', schema.get('definitions', {})).get('requirement')
            if requirement is None:
                requirement = schema['properties']['requirements']['items']
            pattern = requirement['properties']['id']['pattern']
            for identifier in ['REQ-TTL', 'FR-01', 'REQ-1', 'REQ-MAX_LENGTH', 'REQ-TENANT-ACCESS']:
                self.assertIsNotNone(re.fullmatch(pattern, identifier), (name, identifier))
            for identifier in ['REQ--TTL', 'REQ-TTL-', 'REQ', 'REQ-TTL:']:
                self.assertIsNone(re.fullmatch(pattern, identifier), (name, identifier))

    def test_workgraph_import_plan_and_source_drift(self):
        with tempfile.TemporaryDirectory(prefix='wigtn-symbolic-id-') as directory:
            root = Path(directory)
            source = root / 'requirements.md'
            source.write_text('REQ-TTL: Lifetime is exactly 86400 seconds.\n')
            def cli(*args, expected=0):
                result = subprocess.run([sys.executable, '-B', str(SCRIPTS / 'wigtn.py'), '--root', str(root), *args], capture_output=True, text=True)
                self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
                return json.loads(result.stdout)
            cli('init', '--apply')
            cli('import', str(source), '--apply')
            cli('plan', '--apply')
            path = root / '.wigtn/workgraph.json'
            before = json.loads(path.read_text())
            self.assertEqual([r['id'] for r in before['requirements']], ['REQ-TTL'])
            self.assertTrue(before['tasks'])
            self.assertEqual(before['tasks'][0]['requirement_ids'], ['REQ-TTL'])
            source.write_text('REQ-TTL: Lifetime is exactly 900 seconds.\n')
            cli('diff', '--check', expected=1)
            cli('diff', '--apply')
            cli('import', str(source), '--apply')
            after = json.loads(path.read_text())
            self.assertEqual([r['id'] for r in after['requirements']], ['REQ-TTL'])
            self.assertIn('900', after['requirements'][0]['text'])
            self.assertEqual(after['tasks'][0]['id'], before['tasks'][0]['id'])
            self.assertNotEqual(after['requirements'][0]['source_sha256'], before['requirements'][0]['source_sha256'])
            self.assertEqual(validate_graph(after), [])

if __name__ == '__main__':
    unittest.main(verbosity=2)
