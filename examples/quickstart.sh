#!/usr/bin/env bash
set -euo pipefail

recall-gate init
recall-gate add "This is a Python CLI project, not a WordPress project." --scope project --type correction --role all --priority high --importance 10
recall-gate add "Keep zero core dependencies." --scope project --type rule --role coder --priority high --importance 10
recall-gate add "Tests must use temp fixtures, not fragile example files." --scope project --type pitfall --role tester --priority high --importance 9
recall-gate add "README and CHANGELOG must stay in sync with public CLI behavior." --scope project --type rule --role writer --priority medium --importance 8

recall-gate brief "fix GitHub Actions test failure" --role tester --budget 300
