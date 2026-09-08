{
  "saved_revision": 17,
  "fresh": true,
  "valid_artifacts": true,
  "drift_paths": [],
  "tasks": [
    {
      "id": "TASK-004",
      "status": "ready",
      "eligible": true,
      "dependency_ids": ["TASK-001", "TASK-002"],
      "requirement_ids": ["FR-004"],
      "intended_paths": ["src/module_004.py"],
      "check_commands": ["python3 -m unittest tests.test_module_004"]
    },
    {
      "id": "TASK-006",
      "status": "ready",
      "eligible": true,
      "dependency_ids": ["TASK-001", "TASK-002"],
      "requirement_ids": ["FR-006"],
      "intended_paths": ["src/module_006.py"],
      "check_commands": ["python3 -m unittest tests.test_module_006"]
    }
  ]
}