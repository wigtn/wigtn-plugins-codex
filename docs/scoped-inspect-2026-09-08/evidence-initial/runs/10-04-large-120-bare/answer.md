{
  "saved_revision": 17,
  "fresh": true,
  "valid_artifacts": true,
  "drift_paths": [],
  "tasks": [
    {
      "id": "TASK-061",
      "status": "ready",
      "eligible": true,
      "dependency_ids": ["TASK-001", "TASK-002"],
      "requirement_ids": ["FR-061"],
      "intended_paths": ["src/module_061.py"],
      "check_commands": ["python3 -m unittest tests.test_module_061"]
    },
    {
      "id": "TASK-120",
      "status": "ready",
      "eligible": true,
      "dependency_ids": ["TASK-001", "TASK-002"],
      "requirement_ids": ["FR-120"],
      "intended_paths": ["src/module_120.py"],
      "check_commands": ["python3 -m unittest tests.test_module_120"]
    }
  ]
}