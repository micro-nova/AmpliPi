#!/bin/bash
# Ensure that vollibrespot is run from the proper directory
# This is required because of config.toml
# Vollibrespot will use default values in place of a real config.toml if one isn't found

HELP="Run this instead of doing something like './vollibrespot\n
  This script points to the proper configuration file.\n
"

set -e

# Get the stream scripts directory (vollibrespot is located there)
scripts_dir="$(realpath $(dirname "$0"))"
echo "script dir=$scripts_dir"
test -d $scripts_dir || exit 1 ;

# Test the source directory
if [[ -d $1 ]]; then
  echo "Source directory: $1"
  cd $1
else
  echo "Please provide a proper directory."
  exit 1
fi
# Change directory and start the service
${scripts_dir}/vollibrespot
