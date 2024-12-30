FROM registry.gitlab.centerionware.com:443/public-projects/jarvis:discord-bot-webui
COPY . /app/
WORKDIR /app
# port 8080 available to the world outside this container
RUN pip install -r /app/requirements.txt
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /app/ComfyUI
RUN pip install -r /app/ComfyUI/requirements.txt
RUN git clone https://github.com/ltdrdata/ComfyUI-Manager.git /app/ComfyUI/custom_nodes/ComfyUI-Manager
run apt update && apt install libgl1 -y
copy ./text_box.png /app/ComfyUI/input/
# Run app.py when the container launches
#CMD ["python3", "app.py"]
