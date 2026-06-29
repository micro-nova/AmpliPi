#!/bin/bash
# Helper script for configure.py

set -e
cd "$( dirname "$0" )"/..

VENV=/home/pi/amplipi-dev/venv

export PATH="$HOME/.local/bin:$PATH"

if [[ ! -d $VENV ]] || [[ ! -e $VENV/bin/python ]]; then
  echo ""
  echo "Setting up virtual environment"
  if ! command -v uv &>/dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
  fi
  uv venv $VENV --python 3.8
fi

# uv pip bypasses PEP 668 (Trixie blocks system pip) and doesn't require pip in the venv
uv pip install --python $VENV/bin/python -r requirements.txt

echo "install python deps complete!"
