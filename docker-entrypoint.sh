#!/usr/bin/env bash
# Wrapper to be used inside docker container.

# Fix ownership of output files
finish() {
    # Fix ownership of output files
    user_id=$(stat -c '%u:%g' /data)
    chown -R ${user_id} /data
}
trap finish EXIT

# Call tool with parameters
toil_container "$@"
