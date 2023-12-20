FROM registry.gitlab.centerionware.com:443/release-paradigm/compose-container:latest

WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

RUN apk add py3-pip  && pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 && pip3 install -r /app/requirements.txt
# Make port 8080 available to the world outside this container

# Run app.py when the container launches
#CMD ["python3", "app.py"]
