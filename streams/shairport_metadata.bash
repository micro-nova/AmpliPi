#!/bin/bash
# Clear out any previous album cover images, then navigate to the proper directory #
src_config_dir="$1"

# Execute from the stream scripts directory (sp_meta.py is located there)
cd "$(dirname "$0")"

# Start the metadata service with argument $1 being the source number #
cat ${src_config_dir}/shairport-sync-metadata | ./shairport-sync-metadata-reader | python3 sp_meta.py "${src_config_dir}"
