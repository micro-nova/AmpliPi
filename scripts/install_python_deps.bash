#!/bin/bash
set -e
cd "$( dirname "$0" )"/..
python3 -m venv venv # TODO --clear removes all packages, make this a flag to this script
. venv/bin/activate
pip3 install --upgrade pip wheel # Avoid errors about using legacy 'setup.py install'
pip3 install -r requirements.txt
deactivate
