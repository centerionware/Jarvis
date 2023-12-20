#!/bin/bash

sleep_time=60s


# # Function to run the script
# update_ingress() {
#   sh /app/ingress_add_route.sh  
# }
# update_ingress

# Main loop
while true; do
  for i in /app/cron/*.sh
  do
    timeout 5 bash "$i"
  done
  sleep $sleep_time
done
