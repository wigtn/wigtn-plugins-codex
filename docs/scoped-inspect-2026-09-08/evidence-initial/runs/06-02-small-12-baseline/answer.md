{
  "saved_revision": 17,
  "fresh": true,
  "valid_artifacts": true,
  "drift_paths": [],
  "tasks": [
    {
      "id": "TASK-007",
      "status": "ready",
      "eligible": true,
      "dependency_ids": ["TASK-001", "TASK-002"],
      "requirement_ids": ["FR-007"],
      "intended_paths": ["src/module_007.py"],
      "check_commands": ["python3 -m unittest tests.test_module_007"]
    },
    {
      "id": "TASK-012",
      "status": "ready",
      "eligible": true,
      "dependency_ids": ["TASK-001", "TASK-002"],
      "requirement_ids": ["FR-012"],
      "intended_paths": ["src/module_012.py"],
      "check_commands": ["python3 -m unittest tests.test_module_012"]
    }
  ]
}