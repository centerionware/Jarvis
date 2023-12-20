#!/bin/bash
set -e

echo "" > /etc/supervisord.conf
for i in /app/supervisord/*.conf
do
    cat "$i" >> /etc/supervisord.conf
    echo "" >> /etc/supervisord.conf
done

cat /etc/supervisord.conf

if [ "$#" -eq 0 ] || [ "${1#-}" != "$1" ]; then
  exec supervisord -n "$@"
else
  supervisord -c /etc/supervisor/conf.d/supervisord.conf &
  exec "$@"
fi
exit
