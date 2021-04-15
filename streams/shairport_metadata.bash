#!/bin/bash

HELP="Run Shairport Metadata reader\n
  usage: shairport_metadata.bash SRC_DIR WEB_DIR\n
\n
  SRC_DIR: The configuration directory for the AmpliPi source connected\n
  WEB_DIR: The web directory (where the pictures go)\n
"

if [[ $# -eq 2 ]] && [[ -d $1 ]]; then
  echo "Starting shairport-sync-metadata-reader"
  SRC_DIR="$1"
  WEB_DIR="$2"
else
  echo "incorrect parameters passed to shairport_metadata";
  echo -e $HELP;
  exit 1 ;
fi

# Get the stream scripts directory (sp_meta.py and shairport-sync-metadata-reader are located there)
scripts_dir="$(realpath $(dirname "$0"))"
echo "script dir=$scripts_dir"
test -d $scripts_dir || exit 1 ;

# Clear out any previous album cover images, then navigate to the proper directory #
rm -rf $WEB_DIR
mkdir -p $WEB_DIR
cd $WEB_DIR

# Start the metadata service with argument $1 being the source number #
cat ${SRC_DIR}/shairport-sync-metadata | ${scripts_dir}/shairport-sync-metadata-reader | python3 ${scripts_dir}/sp_meta.py "${SRC_DIR}"
