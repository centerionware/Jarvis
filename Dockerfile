FROM python:3.9-slim
COPY . /app/

run chmod +x /app/start_script.sh && chmod +x /app/cron_script.sh
RUN apt update && apt install -y docker docker-compose nfs-common supervisor bash git gcc linux-headers-$(uname -r) && rm  -rf /tmp/* && apt-get clean

RUN mkdir -p /var/log/supervisor

COPY docker-entrypoint.sh /usr/bin/docker-entrypoint.sh
RUN chmod +x /usr/bin/docker-entrypoint.sh

ENTRYPOINT ["/usr/bin/docker-entrypoint.sh"]


WORKDIR /app

# Copy the current directory contents into the container at /app

# RUN apk add py3-pip 
#RUN git clone https://github.com/openai/triton.git --branch v2.1.0 && cd triton && pip install ninja cmake wheel && pip install -e python
RUN pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 
RUN pip3 install -r /app/requirements.txt
# Make port 8080 available to the world outside this container

# Run app.py when the container launches
#CMD ["python3", "app.py"]
