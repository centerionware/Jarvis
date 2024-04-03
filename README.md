# Jarvis
Ollama and Comfyui discord bot. Chat, image inspection, and image generation.

Agent branch. This branch provides an agent that will connect back to the main bot to provide processing power. This allows a distributed backend built to scale.

# Import Running in Windows Note:
 Run it from the ubuntu bash shell in WSL, not from the docker inside of powershell, or you will have a bad time. There's filesystem translation things that happen otherwise, and just don't do it. You may also run into out of space errors when you clearly have a lot of space available. Again, use docker from inside of ubuntu bash shell and not from the windows layer of wsl.

# 0xJarvis
* Ollama is running in WSL in docker with LiteLLM (Currently not used) with Jarvis (the discord.py based bot) on RX3080 with an AMD 2700x cpu on windows 11.
* ComfyUI runs based on the (internal) RX570 ComfyUI deployment branch, which enables comfyui to work on legacy AMD gpus on Linux hosts. It's been tested on a proxmox host on an HPE DL580gen9 with an AMD RX570. (It works but I don't recommend, 2s to process a single image is ages.) 

# Text Overlay
Move text_box.png into comfyui's input folder for the text overlay to work.

**New Main File:**
* discord_hear.py - provides basic discord echo bot.
* Jarvis_Agent.py - connects back to the Main Controller branch and provides an agent to do inference.
* comfyui_api.py - Provides connectivity to comfyui's api. 
* thinking_aid.py - provides connectivity to ollama's api
* drawing_aid.py - provides a wrapper around comfyui that's the same syntax as thinking_aid so discord_hear.py can use similar notation
* sdxl-turbo-template.json - An SDXL workflow exported from comfyui in API mode (settings/enable dev mode options), use %prompt% to add a prompt and %negative_prompt% to add a negative prompt. Currently the image saved is the one comfyui_api.py responds with, future plan is to use previews and not store on the server
* requirements.txt - requirements
* startup/default.sh - run by base image and used to copy data if needed, in this project i believe it launches discord_hear.py
* supervisord/*.conf - init files, base image builds into /etc/supervisord.conf from all the files in this folder

## Notes:

Adding search capabilities. searxng can be used to provide an Agent with the capabilities to search the internet across many search engines.
searxng needs `-v /mnt:/mnt`
## Environment Variables and defaults
These can be changed in case you'd prefer to use another comfyui or ollama server
* COMFYUI_URL = "localhost:8188"
* OLLAMA_URL = "http://localhost:11434/api/generate"
If you're running your own jarvis main node controller
* MNC_URL = "wss://register.jarvis.ai.centerionware.com" (Eg for localhost only: `ws://localhost/` )
## Launching example:
```sh
docker login registry.gitlab.centerionware.com
docker run --restart always --name jarvis_agent_nvidia -d --gpus all -v /mnt:/mnt -v '/home/deadc0de/comfyui/input:/app/ComfyUI/input' -v '/home/deadc0de/jarvis:/root/.ollama/models' -v '/home/deadc0de/comfyui/custom_nodes:/app/ComfyUI/custom_nodes' -v '/home/deadc0de/comfyui/models:/app/ComfyUI/models' -v '/var/run/docker.sock:/var/run/docker.sock' -p 8188:8188 -p 8000:8000 registry.gitlab.centerionware.com/public-projects/jarvis:InferenceAgent-nvidia

```

Note: If you wish to add searxng, docker in docker can be used. Simply mount /var/run/docker.sock to the container and the image will launch searxng, and connect the containers on a private network so the bot can use the api. this could be considered a security risk. Should probably consider migrating to podman in docker for the searxng, but this is already in place so whatever. Also ensure `-v /mnt/jarvis:/mnt/jarvis` is used so the pre-configured searxng configuration file can be used which enables json results (should be the only change ever to the default).


```sh
docker login registry.gitlab.centerionware.com
docker run --restart always --name jarvis_agent_nvidia -d --gpus all -v /mnt:/mnt -v '/home/deadc0de/jarvis:/root/.ollama/models' -v '/home/deadc0de/comfyui/custom_nodes:/app/ComfyUI/custom_nodes' -v '/home/deadc0de/comfyui/models:/app/ComfyUI/models' -p 8188:8188 -p 8000:8000 -v /var/run/docker.sock:/var/run/docker.sock registry.gitlab.centerionware.com/public-projects/jarvis:InferenceAgent-nvidia

```
LiteLLM OpenAI compatible proxy should now be available on the port 8000, it is insecure by default.
ComfyUI should be available on port 8188, it also is insecure. 

## Podman with CDI

```sh
sudo nvidia-ctk cdi generate --output=/etc/cdi/nvidia.yaml
podman run --restart always --name jarvis_agent_nvidia -d --gpus all -e DISABLE_IMAGE=true -v '/var/cache/models:/root/.ollama/models' -p 8188:8188 -p 8000:8000 -v /mnt:/mnt -v /var/run/podman/podman.sock:/var/run/docker.sock  --device=nvidia.com/gpu=all registry.gitlab.centerionware.com/public-projects/jarvis:InferenceAgent-nvidia
```

## Adding ollama-webui
```sh
 docker run -d -p 3000:8080 -e OLLAMA_API_BASE_URL=http://jarvis_agent_nvidia:11434/api --name ollama-webui --restart always ghcr.io/ollama-webui/ollama-webui:main
```
Note: You must create a network and add both jarvis and the webui so they can see each other:
```sh
docker network create -d bridge my-bridge-network
docker network connect my-bridge-network ollama-webui
docker network connect my-bridge-network jarvis_agent_nvidia
```
After creating the network, access the webui at localhost:3000

## Live container development
```sh
docker exec -it jarvis bash
apt install nano
nano whateverfile
python whateverfile.py
```
