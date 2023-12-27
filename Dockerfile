FROM registry.gitlab.centerionware.com:443/public-projects/jarvis:discord-bot-webui
COPY . /app/
WORKDIR /app
# port 8080 available to the world outside this container
run pip install -r /app/requirements.txt
run git clone https://github.com/comfyanonymous/ComfyUI.git /app/ComfyUI
run pip install -r /app/ComfyUI/requirements.txt
run git clone https://github.com/ltdrdata/ComfyUI-Manager.git /app/ComfyUI/custom_nodes/ComfyUI-Manager
# Run app.py when the container launches
#CMD ["python3", "app.py"]
