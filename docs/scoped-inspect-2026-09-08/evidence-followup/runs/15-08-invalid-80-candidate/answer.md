{
  "saved_revision": 17,
  "fresh": true,
  "valid_artifacts": false,
  "drift_paths": [],
  "tasks": [
    {
      "id": "TASK-041",
      "status": "ready",
      "eligible": false,
      "dependency_ids": ["TASK-001", "TASK-002"],
      "requirement_ids": ["FR-041"],
      "intended_paths": ["src/module_041.py"],
      "check_commands": ["python3 -m unittest tests.test_module_041"]
    },
    {
      "id": "TASK-080",
      "status": "ready",
      "eligible": false,
      "dependency_ids": ["TASK-001", "TASK-002"],
      "requirement_ids": ["FR-080"],
      "intended_paths": ["src/module_080.py"],
      "check_commands": ["python3 -m unittest tests.test_module_080"]
    }
  ]
}