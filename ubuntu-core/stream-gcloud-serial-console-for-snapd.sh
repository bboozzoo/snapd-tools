#!/bin/bash -e

INSTANCE="$1"

if [ -z "$INSTANCE" ]; then
    echo "first argument must be the GCE instance"
    exit 1
fi

next=0
truncate -s0 console-output.txt
while true; do
    next=$(
        gcloud compute \
            --project=snapd-spread \
            instances get-serial-port-output \
            --start="$next" \
            "$INSTANCE" \
            --zone=us-east1-b 3>&1 1>"console-output-bits.txt" 2>&3- | grep -Po -- '--start=\K[0-9]+')
    trimmedConsoleSnippet="$(sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' < console-output-bits.txt)"
    if [ -n "$trimmedConsoleSnippet" ]; then
        echo "$trimmedConsoleSnippet" >> console-output.txt
    fi
    sleep 1
done

