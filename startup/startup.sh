#!/bin/bash
# You can replace this file or add other files in higher level containers, or obviously mount a replacement for this file.

if [ ! -e /app/fix_env ]; then
    touch /app/fix_env
    echo "" >> /app/env
    printenv >> /app/env
    echo "environment updated"
else
    echo "File /app/fix_env already exists."
fi

python /app/jarvis.py

mkdir /mnt/jarvis || true
cp /app/etc /mnt/jarvis/ -r
