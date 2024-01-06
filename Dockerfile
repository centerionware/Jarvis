FROM registry.gitlab.centerionware.com:443/public-projects/jarvis:python3.9-supervisor-slim
COPY . /app/
WORKDIR /app
# port 8080 available to the world outside this container
RUN pip install -r /app/requirements.txt
#CMD ["python3", "app.py"]
