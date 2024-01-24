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

mkdir /mnt/jarvis || true
cp /app/etc /mnt/jarvis/ -r

#Check if /var/run/docker.sock exists
if [ ! -e /var/run/docker.sock ]; then
    echo "File /var/run/docker.sock does not exist. Not launching Searxng."
else
    docker-compose --file /app/docker-compose.yml up -d
    #!/bin/bash

    # Find the Docker container using the specific image
    output=$(docker ps | grep "registry.gitlab.centerionware.com/public-projects/jarvis:InferenceAgent")

    # Extract the container ID
    container_id=$(echo $output | cut -d ' ' -f 1)

    docker network connect app_searxng ${container_id}
fi
# Print the container ID
# echo "Container ID: $container_id"
