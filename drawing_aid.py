import subprocess
import queue
import threading
import time
import requests
import base64
import json
import os
import comfyui_api
import logging

def enqueue_output(queue, interaction, url, prompt):
    client = comfyui_api.Client(url)
    print("Sending prompt to comfyui")
    output = client.get_images(client.ws, prompt)
    print("Received output from comfyui") # + json.dumps(output))
    queue.put([output,interaction])
    client.ws.close()

class DrawingAid:
    def __init__(self, client, url="localhost:8188"):
        self.queue = []
        self.actual_queue = queue.Queue()
        self.command = None
        self.client=client
        self.url = url
        # read self.file from sdxl-turbo-template.json
        self.prompt = json.load(open("sdxl-turbo-template.json"))

    def __del__(self):
        print("Cleaning ThinkingAid")
        self.kill_pids()
    def dl_and_enc_image(self, url):
        #download the url using requests into memory
        #encode the image into base64
        #return the base64 encoded image
        image = requests.get(url).content
        return base64.b64encode(image).decode('utf-8')
    
    def launch(self, command,  interaction, old_messages, negative_prompt="", noise_seed=10301411218912, cfg=1.0):
        client_user = self.client
        # Copy self.prompt, go through it and modify %prompt% to be the "command" argument
        client_prompt = json.loads(json.dumps(self.prompt))
        for node in client_prompt:
            if "text" in client_prompt[node]["inputs"] and client_prompt[node]["inputs"]["text"] == "%prompt%":
                client_prompt[node]["inputs"]["text"] = command
                print("Set comfyui prompt")
            if "text" in client_prompt[node]["inputs"] and client_prompt[node]["inputs"]["text"] == "%negative_prompt%":
                client_prompt[node]["inputs"]["text"] = negative_prompt
                print("Set comfyui negative_prompt")
            if "noise_seed" in client_prompt[node]["inputs"]:
                client_prompt[node]["inputs"]["noise_seed"] = noise_seed
                print("Set comfyui noise_seed")
            if "cfg" in client_prompt[node]["inputs"]:
                client_prompt[node]["inputs"]["cfg"] = cfg
                print("Set comfyui cfg")
            #10301411218912
        stdout_thread = threading.Thread(target=enqueue_output, args=(self.actual_queue, interaction, self.url, client_prompt))#json.loads(client_prompt)))
        stdout_thread.daemon = True
        stdout_thread.start()

    def kill_pids(self):
        pass

    def hear(self):
        try:
            if(not self.actual_queue.empty()):
                while (not self.actual_queue.empty()):
                    self.queue.append(self.actual_queue.get(block=False))
        except Exception as e:
            pass