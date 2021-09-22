#!/bin/bash
# call the built in tests python script, passing all of the args

set -e

# go to the base of amplipi
cd "$( dirname "$0" )/../.."

# use our virtual environment
./venv/bin/python -m amplipi.tests $@ # pass through all of the args
