{
  "saved_revision": 17,
  "fresh": false,
  "valid_artifacts": true,
  "drift_paths": [
    "docs/requirement-051.md",
    "docs/requirement-099.md"
  ],
  "tasks": [
    {
      "id": "TASK-051",
      "status": "stale",
      "eligible": false,
      "dependency_ids": ["TASK-001", "TASK-002"],
      "requirement_ids": ["FR-051"],
      "intended_paths": ["src/module_051.py"],
      "check_commands": ["python3 -m unittest tests.test_module_051"]
    },
    {
      "id": "TASK-100",
      "status": "ready",
      "eligible": true,
      "dependency_ids": ["TASK-001", "TASK-002"],
      "requirement_ids": ["FR-100"],
      "intended_paths": ["src/module_100.py"],
      "check_commands": ["python3 -m unittest tests.test_module_100"]
    }
  ]
}