#!/bin/bash
# Helper script for configure.py

set -e
cd "$( dirname "$0" )"/..
if [[ ! -d /home/pi/amplipi-dev/venv ]] || [[ ! -e /home/pi/amplipi-dev/venv/bin/activate && ! -e /home/pi/amplipi-dev/venv/Scripts/activate ]]; then
  echo ""
  echo "Setting up virtual environment"

  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"

  mkdir -p /home/pi/amplipi-dev/venv

  uv venv /home/pi/amplipi-dev/venv --python 3.8
fi

. venv/bin/activate
pip3 install --upgrade pip wheel # Avoid errors about using legacy 'setup.py install'
pip3 install -r requirements.txt
deactivate

echo "install python deps complete!"
