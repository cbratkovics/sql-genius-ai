#!/usr/bin/env bash
# The same effective verification entry point is used locally and by CI.
set -euo pipefail
repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"
export PYTHONPATH="$repo_root${PYTHONPATH:+:$PYTHONPATH}"
mode=${1:-all}
case "$mode" in
  versions)
    python --version
    python -m pip --version
    python -m ruff --version
    python -m mypy --version
    python -m pytest --version
    ;;
  deps) python -m pip check ;;
  lint) python -m ruff check backend ;;
  types) python -m mypy --config-file backend/mypy.ini -p backend ;;
  tests) python -m pytest -c backend/pytest.ini backend -q ;;
  all)
    for check in versions deps lint types tests; do
      "$repo_root/scripts/check-backend.sh" "$check"
    done
    ;;
  *) echo "Usage: $0 [all|versions|deps|lint|types|tests]" >&2; exit 2 ;;
esac
