# Jarvis


MC - Main Controller branch. Designed to be a websocket endpoint agents can use to run the actual requests. Discord request comes in, gets sent to either Jarvis_MC.(image|text)_request(interaction, prompt), when the response is finished it'll be on the (thinking|drawing)_aid.queue like it was calling the api's directly before.

This image _does not_ do inference of any kind. It's the core routing and pipeworks. To run jarvis this will need to run, as well as at least one agent that provides both ImageRequest and TextRequest.

Ollama and Comfyui discord bot. Chat, image inspection, and image generation.

# Shoutouts
-- epilepsy - You fucking rock my friend. Thank you for helping me test this on the eve of release when nobody else was there.

# 0xJarvis
* Ollama is running in WSL in docker with LiteLLM (Currently not used) with Jarvis (the discord.py based bot) on RX3080 with an AMD 2700x cpu on windows 11.
* ComfyUI runs based on the (internal) RX570 ComfyUI deployment branch, which enables comfyui to work on legacy AMD gpus on Linux hosts. It's been tested on a proxmox host on an HPE DL580gen9 with an AMD RX570. (It works but I don't recommend, 2s to process a single image is ages.) 

**New Main File:**
* discord_hear.py - provides basic discord echo bot.
* Jarvis_MC.py - the websocket server for the Jarvis Main Controller.
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

DISCORD_TOKEN : not set by default. Set your discord bot token here.

## Launching example:

```sh
docker login registry.gitlab.centerionware.com
docker run -p 5000:5000 --restart always --name jarvis_mnc -d -e DISCORD_TOKEN=... registry.gitlab.centerionware.com/public-projects/jarvis:drawing-multinode-controller
```


