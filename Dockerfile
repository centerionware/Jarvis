FROM registry.gitlab.centerionware.com:443/public-projects/jarvis:discord-bot-webui
COPY . /app/
WORKDIR /app
# port 8080 available to the world outside this container
run pip install -r /app/requirements.txt
# Run app.py when the container launches
#CMD ["python3", "app.py"]
