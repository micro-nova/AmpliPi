#!/bin/bash
# Helper script for configure.py

set -e
cd "$( dirname "$0" )"/..

VENV=/home/pi/amplipi-dev/venv
TARGET_PYTHON=3.8

export PATH="$HOME/.local/bin:$PATH"

if ! command -v uv &>/dev/null; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# Rebuild the venv if it's missing, or if it exists but isn't running the target Python version -
# e.g. a venv left over from testing a different branch pinned to a different Python. Without this
# check, uv pip install below would silently install today's packages into a stale interpreter
# instead of failing loudly, since it only cares that $VENV/bin/python exists.
current_python=""
if [[ -e $VENV/bin/python ]]; then
  current_python=$($VENV/bin/python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null)
fi
if [[ ! -d $VENV ]] || [[ ! -e $VENV/bin/python ]] || [[ "$current_python" != "$TARGET_PYTHON" ]]; then
  echo ""
  if [[ -n "$current_python" && "$current_python" != "$TARGET_PYTHON" ]]; then
    echo "Existing virtual environment is Python $current_python, rebuilding for Python $TARGET_PYTHON"
    rm -rf "$VENV"
  else
    echo "Setting up virtual environment"
  fi
  # --clear: uv refuses to write into a pre-existing directory otherwise, even an empty one
  uv venv $VENV --python $TARGET_PYTHON --clear
fi

# uv pip bypasses PEP 668 (Trixie blocks system pip) and doesn't require pip in the venv
uv pip install --python $VENV/bin/python -r requirements.txt

echo "install python deps complete!"
