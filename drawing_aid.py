import subprocess
import queue
import threading
import time
import requests
import base64
import json
import os
#import comfyui_api
import logging

class DrawingAid:
    def __init__(self, client, url="localhost:8188"):
        self.queue = []
        self.actual_queue = queue.Queue()
        self.command = None
        self.MC = None
        self.client=client
        self.url = url
        # read self.file from sdxl-turbo-template.json
        self.prompt = json.load(open("sdxl-turbo-text-overlay-template.json"))
        self.batch_prompt = json.load(open("sdxl-turbo-batch-template.json"))
        self.textprompt = json.load(open("sdxl-turbo-text-template.json"))

        self.nt_prompt = json.load(open("sdxl-text-overlay-template.json"))
        self.nt_batch_prompt = json.load(open("sdxl-batch-template.json"))
        self.nt_textprompt = json.load(open("sdxl-text-template.json"))
    def set_MC(self, MC):
        self.MC = MC

    def __del__(self):
        print("Cleaning ThinkingAid")
        self.kill_pids()
    def dl_and_enc_image(self, url):
        #download the url using requests into memory
        #encode the image into base64
        #return the base64 encoded image
        image = requests.get(url).content
        return base64.b64encode(image).decode('utf-8')
    
    async def launch(self, command,  interaction, old_messages, negative_prompt="", noise_seed=10301411218912, cfg=1.0,
               overlay_text="", overlay_color=0, overlay_x=0, overlay_y=0, overlay_alignment="left", use_textlora=False, use_batch=True, use_nt=False):
        
        if(overlay_x < 0):
            overlay_x = 0
        if(overlay_y < 0):
            overlay_y = 0
        if(overlay_x > 512):
            overlay_x = 512
        if(overlay_y > 512):
            overlay_y = 512
        if(overlay_alignment not in ["left", "center", "right"]):
            overlay_alignment = "left"
        client_user = self.client
        # Copy self.prompt, go through it and modify %prompt% to be the "command" argument
        client_prompt = None
        if(use_nt):
            if(use_textlora):
                client_prompt = json.loads(json.dumps(self.nt_textprompt))
            else:
                if(use_batch == False and overlay_text != ""):
                    client_prompt = json.loads(json.dumps(self.nt_prompt))
                else:
                    client_prompt = json.loads(json.dumps(self.nt_batch_prompt))
        else:
            if(use_textlora):
                client_prompt = json.loads(json.dumps(self.textprompt))
            else:
                if(use_batch == False and overlay_text != ""):
                    client_prompt = json.loads(json.dumps(self.prompt))
                else:
                    client_prompt = json.loads(json.dumps(self.batch_prompt))

            # client_prompt = json.loads(json.dumps(self.prompt))
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
            if( client_prompt[node]["class_type"] == "EmptyLatentImage"):
                batch_size = 1
                if(use_batch): batch_size = 4
                client_prompt[node]["inputs"]["batch_size"] = batch_size
            if( client_prompt[node]["class_type"] == "Chatbox Overlay"):
                client_prompt[node]["inputs"]["text"] = overlay_text
                client_prompt[node]["inputs"]["color"] = overlay_color
                client_prompt[node]["inputs"]["start_x"] = overlay_x
                client_prompt[node]["inputs"]["start_y"] = overlay_y
                client_prompt[node]["inputs"]["alignment"] = overlay_alignment
            #10301411218912
        await self.MC.image_request(interaction, client_prompt, {"nt_image": 1 if use_nt is True else 0})
        #stdout_thread = threading.Thread(target=enqueue_output, args=(self.actual_queue, interaction, self.url, client_prompt))#json.loads(client_prompt)))
        #stdout_thread.daemon = True
        #stdout_thread.start()

    def kill_pids(self):
        pass

    def hear(self):
        try:
            if(not self.actual_queue.empty()):
                while (not self.actual_queue.empty()):
                    self.queue.append(self.actual_queue.get(block=False))
        except Exception as e:
            pass