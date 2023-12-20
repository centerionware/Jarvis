FROM registry.gitlab.centerionware.com:443/public-projects/jarvis:python3.9-cuda-torch-torchvision-pyaudio

WORKDIR /app
ort 8080 available to the world outside this container
run pip install -r /app/requirements.txt
# Run app.py when the container launches
#CMD ["python3", "app.py"]
