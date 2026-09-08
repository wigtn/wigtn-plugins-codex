{
  "saved_revision": 17,
  "fresh": true,
  "valid_artifacts": true,
  "drift_paths": [],
  "tasks": [
    {
      "id": "TASK-021",
      "status": "ready",
      "eligible": true,
      "dependency_ids": ["TASK-001", "TASK-002"],
      "requirement_ids": ["FR-021"],
      "intended_paths": ["src/module_021.py"],
      "check_commands": ["python3 -m unittest tests.test_module_021"]
    },
    {
      "id": "TASK-040",
      "status": "ready",
      "eligible": true,
      "dependency_ids": ["TASK-001", "TASK-002"],
      "requirement_ids": ["FR-040"],
      "intended_paths": ["src/module_040.py"],
      "check_commands": ["python3 -m unittest tests.test_module_040"]
    }
  ]
}