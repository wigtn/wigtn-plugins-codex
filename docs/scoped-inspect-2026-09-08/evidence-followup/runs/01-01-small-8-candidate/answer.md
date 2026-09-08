{
  "saved_revision": 17,
  "fresh": true,
  "valid_artifacts": true,
  "drift_paths": [],
  "tasks": [
    {
      "id": "TASK-005",
      "status": "ready",
      "eligible": true,
      "dependency_ids": ["TASK-001", "TASK-002"],
      "requirement_ids": ["FR-005"],
      "intended_paths": ["src/module_005.py"],
      "check_commands": ["python3 -m unittest tests.test_module_005"]
    },
    {
      "id": "TASK-008",
      "status": "ready",
      "eligible": true,
      "dependency_ids": ["TASK-001", "TASK-002"],
      "requirement_ids": ["FR-008"],
      "intended_paths": ["src/module_008.py"],
      "check_commands": ["python3 -m unittest tests.test_module_008"]
    }
  ]
}