{
  "saved_revision": 17,
  "fresh": true,
  "valid_artifacts": true,
  "drift_paths": [],
  "tasks": [
    {
      "id": "TASK-031",
      "status": "draft",
      "eligible": false,
      "dependency_ids": ["TASK-001", "TASK-002"],
      "requirement_ids": ["FR-031"],
      "intended_paths": ["src/module_031.py"],
      "check_commands": ["python3 -m unittest tests.test_module_031"]
    },
    {
      "id": "TASK-060",
      "status": "draft",
      "eligible": false,
      "dependency_ids": ["TASK-001", "TASK-002"],
      "requirement_ids": ["FR-060"],
      "intended_paths": ["src/module_060.py"],
      "check_commands": ["python3 -m unittest tests.test_module_060"]
    }
  ]
}