import subprocess
import queue
import threading
import time
import requests
import base64
import json
import os
import comfyui_api

def enqueue_output(queue, interaction, url, prompt):
    client = comfyui_api.Client(url)
    output = client.get_images(client.ws, prompt)
    queue.put([output,interaction])


class DrawingAid:
    def __init__(self, client, url="localhost:8188"):
        self.queue = []
        self.actual_queue = queue.Queue()
        self.command = None
        self.client=client
        self.url = url
        # read self.file from sdxl-turbo-template.json
        self.file = json.load(open("sdxl-turbo-template.json"))

    def __del__(self):
        print("Cleaning ThinkingAid")
        self.kill_pids()
    def dl_and_enc_image(self, url):
        #download the url using requests into memory
        #encode the image into base64
        #return the base64 encoded image
        image = requests.get(url).content
        return base64.b64encode(image).decode('utf-8')
    
    def launch(self, command,  interaction, old_messages):
        client_user = self.client
        # Copy self.prompt, go through it and modify %prompt% to be the "command" argument
        client_prompt = self.prompt.copy()
        for node in client_prompt:
            if("inputs" in client_prompt[node] and "text" in client_prompt[node]["inputs"]):
                client_prompt[node]["inputs"]["text"] = client_prompt[node]["inputs"]["text"].replace("%prompt%", command)
           
        stdout_thread = threading.Thread(target=enqueue_output, args=(self.actual_queue, interaction, self.url, client_prompt))
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