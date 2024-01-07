# Jarvis

MC - Main Controller branch. Designed to be a websocket endpoint agents can use to run the actual requests. Discord request comes in, gets sent to either Jarvis_MC.(image|text)_request(interaction, prompt), when the response is finished it'll be on the (thinking|drawing)_aid.queue like it was calling the api's directly before.

This image _does not_ do inference of any kind. It's the core routing and pipeworks. To run jarvis this will need to run, as well as at least one agent that provides both ImageRequest and TextRequest.

Ollama and Comfyui discord bot. Chat, image inspection, and image generation.

# 0xJarvis
* Ollama is running in WSL in docker with LiteLLM (Currently not used) with Jarvis (the discord.py based bot) on RX3080 with an AMD 2700x cpu on windows 11.
* ComfyUI runs based on the (internal) RX570 ComfyUI deployment branch, which enables comfyui to work on legacy AMD gpus on Linux hosts. It's been tested on a proxmox host on an HPE DL580gen9 with an AMD RX570. (It works but I don't recommend, 2s to process a single image is ages.) 

**New Main File:**
* discord_hear.py - provides basic discord echo bot.
* comfyui_api.py - Provides connectivity to comfyui's api. 
* thinking_aid.py - provides connectivity to ollama's api
* drawing_aid.py - provides a wrapper around comfyui that's the same syntax as thinking_aid so discord_hear.py can use similar notation
* sdxl-turbo-template.json - An SDXL workflow exported from comfyui in API mode (settings/enable dev mode options), use %prompt% to add a prompt and %negative_prompt% to add a negative prompt. Currently the image saved is the one comfyui_api.py responds with, future plan is to use previews and not store on the server
* requirements.txt - requirements
* startup/default.sh - run by base image and used to copy data if needed, in this project i believe it launches discord_hear.py
* supervisord/*.conf - init files, base image builds into /etc/supervisord.conf from all the files in this folder

## Notes:
 By default comfyui is not enabled. to enable it create your own comfyui.conf file, copy the contents of comfyui.conf into it, and change autostart to 1. Mount this new conf file over comfyui.conf in your `docker run ... registry.gitlab.centerionware.com/public-projects/jarvis/drawing-jarvis` command.
 You will need a lot of vram to effectively use both comfyui and ollama on the same gpu. My guess is 16GB might work okay, 24GB to be safe.

## Environment Variables and defaults

* COMFYUI_URL = "localhost:8188"
* OLLAMA_URL = "http://localhost:11434/api/generate"

## Launching example:
Be sure to change the ip or hostname to the host running comfyui
```sh
 docker login registry.gitlab.centerionware.com
docker run --name jarvis -d --gpus all -e COMFYUI_URL='192.168.1.1:8188' -e DISCORD_TOKEN=... -v 'c:\jarvis:/root/.ollama/models' -p 8188:8188 -p 8000:8000 registry.gitlab.centerionware.com/public-projects/jarvis:drawing-jarvis
```
LiteLLM OpenAI compatible proxy should now be available on the port 8000, it is insecure by default.
ComfyUI should be available on port 8188, it also is insecure. 

## Adding ollama-webui
```sh
 docker run -d -p 3000:8080 -e OLLAMA_API_BASE_URL=http://jarvis:11434/api --name ollama-webui --restart always ghcr.io/ollama-webui/ollama-webui:main
```
Note: You must create a network and add both jarvis and the webui so they can see each other:
```sh
docker network create -d bridge my-bridge-network
docker network connect my-bridge-network ollama-webui
docker network connect my-bridge-network jarvis
```
After creating the network, access the webui at localhost:3000

## Live container development
```sh
docker exec -it jarvis bash
apt install nano
nano whateverfile
python whateverfile.py
```
