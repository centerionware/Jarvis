FROM registry.gitlab.centerionware.com:443/public-projects/jarvis:python3.9-cuda-torch-torchvision-pyaudio
COPY . /app/
WORKDIR /app
run apt install -y portaudio19-dev libespseak1 alsa-utils alsa-base libsndfile1-dev 
# port 8080 available to the world outside this container
run pip install -r /app/requirements.txt
# Run app.py when the container launches
#CMD ["python3", "app.py"]
