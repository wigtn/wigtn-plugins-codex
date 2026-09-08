{
  "saved_revision": 17,
  "fresh": true,
  "valid_artifacts": true,
  "drift_paths": [],
  "tasks": [
    {
      "id": "TASK-051",
      "status": "draft",
      "eligible": false,
      "dependency_ids": ["TASK-001", "TASK-002"],
      "requirement_ids": ["FR-051"],
      "intended_paths": ["src/module_051.py"],
      "check_commands": ["python3 -m unittest tests.test_module_051"]
    },
    {
      "id": "TASK-100",
      "status": "draft",
      "eligible": false,
      "dependency_ids": ["TASK-001", "TASK-002"],
      "requirement_ids": ["FR-100"],
      "intended_paths": ["src/module_100.py"],
      "check_commands": ["python3 -m unittest tests.test_module_100"]
    }
  ]
}