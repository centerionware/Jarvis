FROM python:3.9-slim
COPY . /app/

run chmod +x /app/start_script.sh && chmod +x /app/cron_script.sh
run apt update && apt-cache search linux-headers
RUN apt update && apt install -y supervisor bash git && rm  -rf /tmp/* && apt-get clean

RUN mkdir -p /var/log/supervisor

COPY docker-entrypoint.sh /usr/bin/docker-entrypoint.sh
RUN chmod +x /usr/bin/docker-entrypoint.sh

ENTRYPOINT ["/usr/bin/docker-entrypoint.sh"]

WORKDIR /app

