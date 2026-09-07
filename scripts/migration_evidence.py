"""Hash recorded evaluation evidence; excludes auth homes and generated score reports.

Manifests detect accidental edits, not an adversary replacing both data and hashes.
"""
import hashlib
import json
from pathlib import Path


def hashes(root: Path, paths: list[str]) -> dict[str, str]:
    result = {}
    for relative in paths:
        entry = root / relative
        if not entry.exists() or entry.is_symlink():
            raise ValueError(f"missing or symlinked evidence: {relative}")
        entries = [entry, *sorted(entry.rglob('*'))] if entry.is_dir() else [entry]
        for path in entries:
            if path.is_symlink():
                raise ValueError(f"symlinked evidence: {path.relative_to(root)}")
            if path.is_file():
                result[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def seal(root: Path, paths: list[str], name: str) -> None:
    document = {"version": 1, "paths": paths, "sha256": hashes(root, paths)}
    with (root / name).open('x', encoding='utf-8') as handle:
        json.dump(document, handle, indent=2, sort_keys=True)
        handle.write('\n')


def verify(root: Path, paths: list[str], name: str) -> list[str]:
    try:
        document = json.loads((root / name).read_text())
        if document.get('version') != 1 or document.get('paths') != paths:
            return [f'{name}: evidence scope mismatch']
        actual = hashes(root, paths)
        expected = document['sha256']
        if not isinstance(expected, dict):
            raise ValueError('invalid hash mapping')
        return [f'{name}: changed/missing/extra evidence: {path}'
                for path in sorted(set(expected) | set(actual))
                if expected.get(path) != actual.get(path)]
    except (OSError, ValueError, KeyError, TypeError) as error:
        return [f'{name}: {error}']


def seal_run(run: Path) -> None:
    # Fixed scope: additional work files are detected inside the work subtree.
    paths = ['meta.json', 'prompt.txt', 'events.jsonl', 'work']
    for optional in ['answer.md', 'events.stderr', 'oracle.txt', 'oracle.stderr',
                     'oracle-before.txt', 'oracle-before.stderr']:
        if (run / optional).exists():
            paths.append(optional)
    seal(run, paths, 'evidence-manifest.json')


def verify_run(run: Path) -> list[str]:
    # Reconstruct scope rather than trusting a manifest to omit changed files.
    paths = ['meta.json', 'prompt.txt', 'events.jsonl', 'work']
    for optional in ['answer.md', 'events.stderr', 'oracle.txt', 'oracle.stderr',
                     'oracle-before.txt', 'oracle-before.stderr']:
        if (run / optional).exists():
            paths.append(optional)
    return verify(run, paths, 'evidence-manifest.json')
