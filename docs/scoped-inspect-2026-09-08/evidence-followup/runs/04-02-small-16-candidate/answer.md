{
  "saved_revision": 17,
  "fresh": true,
  "valid_artifacts": true,
  "drift_paths": [],
  "tasks": [
    {
      "id": "TASK-009",
      "status": "ready",
      "eligible": true,
      "dependency_ids": ["TASK-001", "TASK-002"],
      "requirement_ids": ["FR-009"],
      "intended_paths": ["src/module_009.py"],
      "check_commands": ["python3 -m unittest tests.test_module_009"]
    },
    {
      "id": "TASK-016",
      "status": "ready",
      "eligible": true,
      "dependency_ids": ["TASK-001", "TASK-002"],
      "requirement_ids": ["FR-016"],
      "intended_paths": ["src/module_016.py"],
      "check_commands": ["python3 -m unittest tests.test_module_016"]
    }
  ]
}