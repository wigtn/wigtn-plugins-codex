#!/usr/bin/env python3
"""Versioned ordinary-coding task bank for harness non-inferiority tests."""

from __future__ import annotations


TASKS = [
    {
        "id": "py-nonmutating-sort",
        "language": "python",
        "prompt": (
            "Fix sorted_scores so it returns records ordered by descending score "
            "without mutating the caller's list. Keep the public function signature "
            "and run the repository tests."
        ),
        "command": ["python3", "-m", "unittest", "discover", "-s", ".", "-p", "test*.py", "-v"],
        "allowed": ["scores.py", "test_scores.py"],
        "files": {
            "scores.py": (
                "def sorted_scores(records):\n"
                "    records.sort(key=lambda item: item['score'], reverse=True)\n"
                "    return records\n"
            ),
            "test_scores.py": (
                "import unittest\nfrom scores import sorted_scores\n\n"
                "class ScoresTest(unittest.TestCase):\n"
                "    def test_orders_descending(self):\n"
                "        rows = [{'score': 1}, {'score': 3}]\n"
                "        self.assertEqual([x['score'] for x in sorted_scores(rows)], [3, 1])\n\n"
                "if __name__ == '__main__': unittest.main()\n"
            ),
        },
        "fixed": {
            "scores.py": (
                "def sorted_scores(records):\n"
                "    return sorted(records, key=lambda item: item['score'], reverse=True)\n"
            )
        },
        "hidden": {
            "test_hidden.py": (
                "import unittest\nfrom scores import sorted_scores\n\n"
                "class HiddenTest(unittest.TestCase):\n"
                "    def test_input_is_unchanged(self):\n"
                "        rows = [{'score': 1}, {'score': 3}]\n"
                "        before = [dict(x) for x in rows]\n"
                "        result = sorted_scores(rows)\n"
                "        self.assertEqual(rows, before)\n"
                "        self.assertIsNot(result, rows)\n"
            )
        },
    },
    {
        "id": "py-ttl-boundary",
        "language": "python",
        "prompt": (
            "Fix is_fresh. Cache entries are valid strictly before expires_at and "
            "expired at the exact boundary. Preserve the API and run the tests."
        ),
        "command": ["python3", "-m", "unittest", "discover", "-s", ".", "-p", "test*.py", "-v"],
        "allowed": ["cache.py", "test_cache.py"],
        "files": {
            "cache.py": "def is_fresh(expires_at, now):\n    return now <= expires_at\n",
            "test_cache.py": (
                "import unittest\nfrom cache import is_fresh\n\n"
                "class CacheTest(unittest.TestCase):\n"
                "    def test_before_and_after(self):\n"
                "        self.assertTrue(is_fresh(10, 9))\n"
                "        self.assertFalse(is_fresh(10, 11))\n"
            ),
        },
        "fixed": {
            "cache.py": "def is_fresh(expires_at, now):\n    return now < expires_at\n"
        },
        "hidden": {
            "test_hidden.py": (
                "import unittest\nfrom cache import is_fresh\n\n"
                "class HiddenTest(unittest.TestCase):\n"
                "    def test_exact_expiry_is_stale(self):\n"
                "        self.assertFalse(is_fresh(10, 10))\n"
            )
        },
    },
    {
        "id": "py-idempotency-conflict",
        "language": "python",
        "prompt": (
            "Fix IdempotencyStore.record. Reusing a key with the same payload must "
            "return the original result; reusing it with a different payload must "
            "raise ValueError. Preserve the API and run tests."
        ),
        "command": ["python3", "-m", "unittest", "discover", "-s", ".", "-p", "test*.py", "-v"],
        "allowed": ["idempotency.py", "test_idempotency.py"],
        "files": {
            "idempotency.py": (
                "class IdempotencyStore:\n"
                "    def __init__(self):\n"
                "        self.entries = {}\n\n"
                "    def record(self, key, payload, result):\n"
                "        if key in self.entries:\n"
                "            return self.entries[key][1]\n"
                "        self.entries[key] = (payload, result)\n"
                "        return result\n"
            ),
            "test_idempotency.py": (
                "import unittest\nfrom idempotency import IdempotencyStore\n\n"
                "class StoreTest(unittest.TestCase):\n"
                "    def test_same_request_returns_first_result(self):\n"
                "        store = IdempotencyStore()\n"
                "        self.assertEqual(store.record('k', {'n': 1}, 'a'), 'a')\n"
                "        self.assertEqual(store.record('k', {'n': 1}, 'b'), 'a')\n"
            ),
        },
        "fixed": {
            "idempotency.py": (
                "class IdempotencyStore:\n"
                "    def __init__(self):\n"
                "        self.entries = {}\n\n"
                "    def record(self, key, payload, result):\n"
                "        if key in self.entries:\n"
                "            old_payload, old_result = self.entries[key]\n"
                "            if old_payload != payload:\n"
                "                raise ValueError('idempotency key payload conflict')\n"
                "            return old_result\n"
                "        self.entries[key] = (payload, result)\n"
                "        return result\n"
            )
        },
        "hidden": {
            "test_hidden.py": (
                "import unittest\nfrom idempotency import IdempotencyStore\n\n"
                "class HiddenTest(unittest.TestCase):\n"
                "    def test_different_payload_is_rejected(self):\n"
                "        store = IdempotencyStore()\n"
                "        store.record('k', {'n': 1}, 'a')\n"
                "        with self.assertRaises(ValueError):\n"
                "            store.record('k', {'n': 2}, 'b')\n"
            )
        },
    },
    {
        "id": "py-tenant-scope",
        "language": "python",
        "prompt": (
            "Fix visible_orders so it returns only rows whose tenant_id exactly "
            "matches the requested tenant, including tenant ID 0. Do not mutate "
            "the input and run the tests."
        ),
        "command": ["python3", "-m", "unittest", "discover", "-s", ".", "-p", "test*.py", "-v"],
        "allowed": ["orders.py", "test_orders.py"],
        "files": {
            "orders.py": (
                "def visible_orders(rows, tenant_id):\n"
                "    if not tenant_id:\n"
                "        return list(rows)\n"
                "    return [row for row in rows if row['tenant_id'] == tenant_id]\n"
            ),
            "test_orders.py": (
                "import unittest\nfrom orders import visible_orders\n\n"
                "class OrdersTest(unittest.TestCase):\n"
                "    def test_filters_tenant(self):\n"
                "        rows = [{'tenant_id': 1}, {'tenant_id': 2}]\n"
                "        self.assertEqual(visible_orders(rows, 1), [{'tenant_id': 1}])\n"
            ),
        },
        "fixed": {
            "orders.py": (
                "def visible_orders(rows, tenant_id):\n"
                "    return [row for row in rows if row['tenant_id'] == tenant_id]\n"
            )
        },
        "hidden": {
            "test_hidden.py": (
                "import unittest\nfrom orders import visible_orders\n\n"
                "class HiddenTest(unittest.TestCase):\n"
                "    def test_zero_tenant_is_scoped(self):\n"
                "        rows = [{'tenant_id': 0}, {'tenant_id': 1}]\n"
                "        before = [dict(x) for x in rows]\n"
                "        self.assertEqual(visible_orders(rows, 0), [{'tenant_id': 0}])\n"
                "        self.assertEqual(rows, before)\n"
            )
        },
    },
    {
        "id": "js-stable-unique",
        "language": "javascript",
        "prompt": (
            "Fix stableUnique so it removes duplicates while preserving first-seen "
            "order. Preserve the exported API and run the tests."
        ),
        "command": ["node", "--test"],
        "allowed": ["unique.js", "unique.test.js"],
        "files": {
            "package.json": "{\"type\":\"commonjs\"}\n",
            "unique.js": "exports.stableUnique = values => [...new Set(values)].sort();\n",
            "unique.test.js": (
                "const test = require('node:test');\nconst assert = require('node:assert/strict');\n"
                "const { stableUnique } = require('./unique');\n"
                "test('removes duplicates', () => assert.deepEqual(stableUnique(['a','a','b']), ['a','b']));\n"
            ),
        },
        "fixed": {
            "unique.js": "exports.stableUnique = values => [...new Set(values)];\n"
        },
        "hidden": {
            "hidden.test.js": (
                "const test = require('node:test');\nconst assert = require('node:assert/strict');\n"
                "const { stableUnique } = require('./unique');\n"
                "test('preserves encounter order', () => assert.deepEqual(stableUnique(['z','a','z','b']), ['z','a','b']));\n"
            )
        },
    },
    {
        "id": "js-pagination-window",
        "language": "javascript",
        "prompt": (
            "Fix page so limit means the number of returned items at any offset. "
            "Preserve the API and run tests."
        ),
        "command": ["node", "--test"],
        "allowed": ["page.js", "page.test.js"],
        "files": {
            "package.json": "{\"type\":\"commonjs\"}\n",
            "page.js": "exports.page = (items, offset, limit) => items.slice(offset, limit);\n",
            "page.test.js": (
                "const test=require('node:test'); const assert=require('node:assert/strict');\n"
                "const {page}=require('./page');\n"
                "test('first page',()=>assert.deepEqual(page([1,2,3],0,2),[1,2]));\n"
            ),
        },
        "fixed": {
            "page.js": "exports.page = (items, offset, limit) => items.slice(offset, offset + limit);\n"
        },
        "hidden": {
            "hidden.test.js": (
                "const test=require('node:test'); const assert=require('node:assert/strict');\n"
                "const {page}=require('./page');\n"
                "test('offset page',()=>assert.deepEqual(page([1,2,3,4,5],2,2),[3,4]));\n"
            )
        },
    },
    {
        "id": "js-retry-classification",
        "language": "javascript",
        "prompt": (
            "Fix shouldRetry. Retry only HTTP 408, 429, and 5xx responses; ordinary "
            "4xx responses are terminal. Preserve the API and run tests."
        ),
        "command": ["node", "--test"],
        "allowed": ["retry.js", "retry.test.js"],
        "files": {
            "package.json": "{\"type\":\"commonjs\"}\n",
            "retry.js": "exports.shouldRetry = status => status >= 400;\n",
            "retry.test.js": (
                "const test=require('node:test'); const assert=require('node:assert/strict');\n"
                "const {shouldRetry}=require('./retry');\n"
                "test('server errors retry',()=>assert.equal(shouldRetry(503),true));\n"
                "test('success does not retry',()=>assert.equal(shouldRetry(200),false));\n"
            ),
        },
        "fixed": {
            "retry.js": "exports.shouldRetry = status => status === 408 || status === 429 || status >= 500;\n"
        },
        "hidden": {
            "hidden.test.js": (
                "const test=require('node:test'); const assert=require('node:assert/strict');\n"
                "const {shouldRetry}=require('./retry');\n"
                "test('terminal 4xx',()=>{ assert.equal(shouldRetry(400),false); assert.equal(shouldRetry(404),false); });\n"
                "test('special 4xx',()=>{ assert.equal(shouldRetry(408),true); assert.equal(shouldRetry(429),true); });\n"
            )
        },
    },
    {
        "id": "js-half-open-overlap",
        "language": "javascript",
        "prompt": (
            "Fix overlaps for half-open intervals [start, end). Intervals that only "
            "touch at an endpoint do not overlap. Preserve the API and run tests."
        ),
        "command": ["node", "--test"],
        "allowed": ["interval.js", "interval.test.js"],
        "files": {
            "package.json": "{\"type\":\"commonjs\"}\n",
            "interval.js": "exports.overlaps = (aStart,aEnd,bStart,bEnd) => aStart <= bEnd && bStart <= aEnd;\n",
            "interval.test.js": (
                "const test=require('node:test'); const assert=require('node:assert/strict');\n"
                "const {overlaps}=require('./interval');\n"
                "test('real overlap',()=>assert.equal(overlaps(1,4,3,6),true));\n"
                "test('separate',()=>assert.equal(overlaps(1,2,3,4),false));\n"
            ),
        },
        "fixed": {
            "interval.js": "exports.overlaps = (aStart,aEnd,bStart,bEnd) => aStart < bEnd && bStart < aEnd;\n"
        },
        "hidden": {
            "hidden.test.js": (
                "const test=require('node:test'); const assert=require('node:assert/strict');\n"
                "const {overlaps}=require('./interval');\n"
                "test('touching is not overlap',()=>assert.equal(overlaps(1,3,3,5),false));\n"
            )
        },
    },
    {
        "id": "rb-clamp-boundary",
        "language": "ruby",
        "prompt": (
            "Fix clamp so values equal to max remain max and only larger values are "
            "clamped. Preserve the method signature and run tests."
        ),
        "command": [
            "ruby",
            "-I.",
            "-e",
            "Dir['test_*.rb'].sort.each { |file| require File.expand_path(file) }",
        ],
        "allowed": ["clamp.rb", "test_clamp.rb"],
        "files": {
            "clamp.rb": (
                "def clamp(value, minimum, maximum)\n"
                "  return minimum if value < minimum\n"
                "  return maximum if value > maximum\n"
                "  return maximum - 1 if value == maximum\n"
                "  value\n"
                "end\n"
            ),
            "test_clamp.rb": (
                "require 'minitest/autorun'\nrequire_relative 'clamp'\n\n"
                "class ClampTest < Minitest::Test\n"
                "  def test_inside\n    assert_equal 5, clamp(5, 0, 10)\n  end\n"
                "  def test_above\n    assert_equal 10, clamp(11, 0, 10)\n  end\n"
                "end\n"
            ),
        },
        "fixed": {
            "clamp.rb": (
                "def clamp(value, minimum, maximum)\n"
                "  return minimum if value < minimum\n"
                "  return maximum if value > maximum\n"
                "  value\n"
                "end\n"
            )
        },
        "hidden": {
            "test_hidden.rb": (
                "require 'minitest/autorun'\nrequire_relative 'clamp'\n\n"
                "class HiddenClampTest < Minitest::Test\n"
                "  def test_exact_max\n    assert_equal 10, clamp(10, 0, 10)\n  end\n"
                "end\n"
            )
        },
    },
    {
        "id": "rb-stable-dedupe",
        "language": "ruby",
        "prompt": (
            "Fix stable_unique so it removes duplicates and preserves first-seen "
            "order. Preserve the API and run tests."
        ),
        "command": [
            "ruby",
            "-I.",
            "-e",
            "Dir['test_*.rb'].sort.each { |file| require File.expand_path(file) }",
        ],
        "allowed": ["unique.rb", "test_unique.rb"],
        "files": {
            "unique.rb": "def stable_unique(values)\n  values.uniq.sort\nend\n",
            "test_unique.rb": (
                "require 'minitest/autorun'\nrequire_relative 'unique'\n\n"
                "class UniqueTest < Minitest::Test\n"
                "  def test_removes_duplicates\n"
                "    assert_equal ['a', 'b'], stable_unique(['a', 'a', 'b'])\n"
                "  end\n"
                "end\n"
            ),
        },
        "fixed": {
            "unique.rb": "def stable_unique(values)\n  values.uniq\nend\n"
        },
        "hidden": {
            "test_hidden.rb": (
                "require 'minitest/autorun'\nrequire_relative 'unique'\n\n"
                "class HiddenUniqueTest < Minitest::Test\n"
                "  def test_preserves_encounter_order\n"
                "    assert_equal ['z', 'a', 'b'], stable_unique(['z', 'a', 'z', 'b'])\n"
                "  end\n"
                "end\n"
            )
        },
    },
    {
        "id": "rb-state-transition",
        "language": "ruby",
        "prompt": (
            "Fix can_transition. Allowed transitions are new→running, "
            "running→done, and running→failed only. Preserve the API and run tests."
        ),
        "command": [
            "ruby",
            "-I.",
            "-e",
            "Dir['test_*.rb'].sort.each { |file| require File.expand_path(file) }",
        ],
        "allowed": ["state.rb", "test_state.rb"],
        "files": {
            "state.rb": (
                "def can_transition(from, to)\n"
                "  return true if to == 'done'\n"
                "  from == 'new' && to == 'running'\n"
                "end\n"
            ),
            "test_state.rb": (
                "require 'minitest/autorun'\nrequire_relative 'state'\n\n"
                "class StateTest < Minitest::Test\n"
                "  def test_basic\n"
                "    assert can_transition('new', 'running')\n"
                "    assert can_transition('running', 'done')\n"
                "  end\n"
                "end\n"
            ),
        },
        "fixed": {
            "state.rb": (
                "def can_transition(from, to)\n"
                "  (from == 'new' && to == 'running') ||\n"
                "    (from == 'running' && ['done', 'failed'].include?(to))\n"
                "end\n"
            )
        },
        "hidden": {
            "test_hidden.rb": (
                "require 'minitest/autorun'\nrequire_relative 'state'\n\n"
                "class HiddenStateTest < Minitest::Test\n"
                "  def test_invalid_and_failed\n"
                "    refute can_transition('new', 'done')\n"
                "    refute can_transition('done', 'running')\n"
                "    assert can_transition('running', 'failed')\n"
                "  end\n"
                "end\n"
            )
        },
    },
    {
        "id": "rb-safe-child",
        "language": "ruby",
        "prompt": (
            "Fix safe_child. It must return [path, true] only when name resolves "
            "inside root; absolute names and parent traversal return [nil, false]. "
            "Preserve the method signature and run tests."
        ),
        "command": [
            "ruby",
            "-I.",
            "-e",
            "Dir['test_*.rb'].sort.each { |file| require File.expand_path(file) }",
        ],
        "allowed": ["safe_path.rb", "test_safe_path.rb"],
        "files": {
            "safe_path.rb": (
                "def safe_child(root, name)\n"
                "  [File.expand_path(name, root), true]\n"
                "end\n"
            ),
            "test_safe_path.rb": (
                "require 'minitest/autorun'\nrequire_relative 'safe_path'\n\n"
                "class SafePathTest < Minitest::Test\n"
                "  def test_normal\n"
                "    assert_equal ['/srv/data/a.txt', true], safe_child('/srv/data', 'a.txt')\n"
                "  end\n"
                "end\n"
            ),
        },
        "fixed": {
            "safe_path.rb": (
                "def safe_child(root, name)\n"
                "  return [nil, false] if name.start_with?('/')\n"
                "  root_path = File.expand_path(root)\n"
                "  candidate = File.expand_path(name, root_path)\n"
                "  return [nil, false] unless candidate.start_with?(root_path + File::SEPARATOR)\n"
                "  [candidate, true]\n"
                "end\n"
            )
        },
        "hidden": {
            "test_hidden.rb": (
                "require 'minitest/autorun'\nrequire_relative 'safe_path'\n\n"
                "class HiddenSafePathTest < Minitest::Test\n"
                "  def test_rejects_traversal_and_absolute\n"
                "    assert_equal [nil, false], safe_child('/srv/data', '../secret')\n"
                "    assert_equal [nil, false], safe_child('/srv/data', '/tmp/x')\n"
                "  end\n"
                "end\n"
            )
        },
    },
]


BY_ID = {task["id"]: task for task in TASKS}
