#!/bin/bash
# GitHub issue #702: LMS stream choppy and distorted after not being used for a few days
# Reset any running LMS client streams on a consistent basis.
# ref: https://github.com/micro-nova/AmpliPi/issues/702

# All stream ids running LMS 
LMS_STREAM_IDS=$(curl -s localhost/api | jq -r '.sources[] | select(.info.type == "lms") | .input' | sed s/stream=//)

for id in ${LMS_STREAM_IDS}; do
    curl -s -X POST localhost/api/streams/${id}/restart >/dev/null
    sleep 3
done

