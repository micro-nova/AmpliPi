#!/bin/bash
set -e
cd "$( dirname "$0" )"/..
python3 -m venv venv
. venv/bin/activate
pip3 install -r requirements.txt
deactivate
