{
  "saved_revision": 17,
  "fresh": true,
  "valid_artifacts": true,
  "drift_paths": [],
  "tasks": [
    {
      "id": "TASK-071",
      "status": "ready",
      "eligible": true,
      "dependency_ids": ["TASK-001", "TASK-002"],
      "requirement_ids": ["FR-071"],
      "intended_paths": ["src/module_071.py"],
      "check_commands": ["python3 -m unittest tests.test_module_071"]
    },
    {
      "id": "TASK-140",
      "status": "ready",
      "eligible": true,
      "dependency_ids": ["TASK-001", "TASK-002"],
      "requirement_ids": ["FR-140"],
      "intended_paths": ["src/module_140.py"],
      "check_commands": ["python3 -m unittest tests.test_module_140"]
    }
  ]
}