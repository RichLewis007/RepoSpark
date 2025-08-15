# 🧪 Test Harness for `quick-create-github-repo.sh`

This is a local test harness for verifying all checklist items in the GitHub repo bootstrap script.

## Contents

- `test_quick_create_repo.sh`: Main test runner
- `test-logs/`: Logs for each test scenario
- Run with:

```bash
chmod +x test_quick_create_repo.sh
./test_quick_create_repo.sh
```

## Notes

- This is a local test system.
- Requires: `gh`, `git`, Bash 5+
- All logs and outputs go to `test-logs/`
- You may want to set up dummy GitHub accounts or repos before using this live.
