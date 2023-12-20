#!/bin/bash

set -e
chmod 755 /app/

if ! test -f "/app/first_run"; then
    cp -n -r /app/mnt/* /mnt/ || true
    touch /app/first_run
fi

for i in /app/startup/*.sh
do
    bash "$i"
done

