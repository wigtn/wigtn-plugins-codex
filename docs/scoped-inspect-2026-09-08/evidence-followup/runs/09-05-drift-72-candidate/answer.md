{
  "saved_revision": 17,
  "fresh": false,
  "valid_artifacts": true,
  "drift_paths": [
    "docs/requirement-037.md",
    "docs/requirement-071.md"
  ],
  "tasks": [
    {
      "id": "TASK-037",
      "status": "stale",
      "eligible": false,
      "dependency_ids": ["TASK-001", "TASK-002"],
      "requirement_ids": ["FR-037"],
      "intended_paths": ["src/module_037.py"],
      "check_commands": ["python3 -m unittest tests.test_module_037"]
    },
    {
      "id": "TASK-072",
      "status": "ready",
      "eligible": true,
      "dependency_ids": ["TASK-001", "TASK-002"],
      "requirement_ids": ["FR-072"],
      "intended_paths": ["src/module_072.py"],
      "check_commands": ["python3 -m unittest tests.test_module_072"]
    }
  ]
}