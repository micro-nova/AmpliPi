#!/bin/bash

date="$(date --iso-8601='seconds')"
backup_dir="${HOME}/backups"
suffix="${1}"
backup_filename="${backup_dir}/config_${date}${suffix}.tgz"

echo "taking a config backup..."
mkdir -p "${backup_dir}"
tar --one-file-system -czf "${backup_filename}" "${HOME}/.config/amplipi/"

# remove all backups older than 90 days
echo "removing old backups..."
find "${backup_dir}" -type f -ctime +90 -delete
echo "completed ${0}"
